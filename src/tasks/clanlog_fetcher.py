import asyncio
import logging
import os
from datetime import datetime, timezone

import aiohttp
from discord.ext import tasks
from sqlalchemy.dialects.postgresql import insert

from src.db import async_session, ClanLog, parse_log_type

DEFAULT_CLAN_LOG_URL = "https://query.idleclans.com/api/Clan/logs/clan/KlutzCo"


def _get_base_url() -> str:
    url = os.getenv("CLAN_LOG_URL", DEFAULT_CLAN_LOG_URL)
    # Strip any existing limit param so we can append our own
    if "?" in url:
        base, _, _ = url.partition("?")
        return base
    return url


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _parse_messages(data: list[dict]) -> list[dict]:
    results = []
    for item in data:
        raw_ts = item.get("timestamp")
        timestamp = _parse_timestamp(raw_ts) if raw_ts else None
        if timestamp is None:
            logging.warning("[clanlog] missing or unparseable timestamp (%s), using current time", raw_ts)
            timestamp = datetime.now(timezone.utc)

        message = item.get("message", "")
        results.append({
            "clan_name": item.get("clanName", ""),
            "member_username": item.get("memberUsername", ""),
            "message": message,
            "timestamp": timestamp,
            "log_type": parse_log_type(message),
        })
    return results


async def fetch_and_store(url: str) -> None:
    timeout = aiohttp.ClientTimeout(total=15)
    backoff = 1

    for attempt in range(1, 4):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status < 200 or resp.status >= 300:
                        logging.warning("[clanlog] attempt %d returned status %d", attempt, resp.status)
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.warning("[clanlog] attempt %d failed: %s", attempt, e)
            await asyncio.sleep(backoff)
            backoff *= 2
            continue

        parsed = _parse_messages(data)

        inserted = 0
        async with async_session() as db:
            for msg in parsed:
                stmt = (
                    insert(ClanLog)
                    .values(**msg)
                    .on_conflict_do_nothing(
                        constraint="uq_clan_log_identity",
                    )
                )
                result = await db.execute(stmt)
                if result.rowcount:
                    inserted += 1
            await db.commit()

        logging.info("[clanlog] fetched %d messages from %s, inserted %d", len(parsed), url, inserted)
        return

    logging.error("[clanlog] all attempts failed for %s", url)


@tasks.loop(hours=24)
async def bulk_fetch_clanlog():
    base = _get_base_url()
    await fetch_and_store(f"{base}?limit=500")


@tasks.loop(minutes=1)
async def recent_fetch_clanlog():
    base = _get_base_url()
    await fetch_and_store(f"{base}?limit=10")
