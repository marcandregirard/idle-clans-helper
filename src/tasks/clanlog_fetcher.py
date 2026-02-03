import asyncio
import logging
import os
from datetime import datetime, timezone

import aiohttp
from discord.ext import tasks
from sqlalchemy.dialects.postgresql import insert

from src.db import async_session, ClanMessage

DEFAULT_CLAN_LOG_URL = "https://query.idleclans.com/api/Clan/logs/clan/KlutzCo"


def _get_base_url() -> str:
    url = os.getenv("CLAN_LOG_URL", DEFAULT_CLAN_LOG_URL)
    # Strip any existing limit param so we can append our own
    if "?" in url:
        base, _, _ = url.partition("?")
        return base
    return url


def _parse_timestamp(value) -> datetime | None:
    if isinstance(value, str):
        # ISO 8601 / RFC 3339
        try:
            return datetime.fromisoformat(value).astimezone(timezone.utc)
        except ValueError:
            pass
        # YYYY-MM-DD HH:MM:SS
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
        # Numeric string (epoch seconds or ms)
        try:
            n = int(value)
            if len(value) == 13:
                return datetime.fromtimestamp(n / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(n, tz=timezone.utc)
        except (ValueError, OSError):
            pass
    elif isinstance(value, (int, float)):
        try:
            if value > 1e12:
                return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        except (ValueError, OSError):
            pass
    return None


def _parse_messages(data: list[dict]) -> list[dict]:
    results = []
    for item in data:
        clan_name = item.get("clanName") or item.get("clan_name")
        member_username = item.get("memberUsername") or item.get("member_username")
        message = item.get("message")
        raw_ts = item.get("timestamp") or item.get("time")

        if not raw_ts:
            logging.warning("[clanlog] item missing timestamp, skipping")
            continue

        timestamp = _parse_timestamp(raw_ts)
        if timestamp is None:
            logging.warning("[clanlog] failed to parse timestamp: %s", raw_ts)
            continue

        results.append({
            "clan_name": clan_name or "",
            "member_username": member_username or "",
            "message": message or "",
            "timestamp": timestamp,
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
                    insert(ClanMessage)
                    .values(**msg)
                    .on_conflict_do_nothing(
                        constraint="uq_clan_message_identity",
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
