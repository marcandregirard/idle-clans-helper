import asyncio
import logging
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import aiohttp
from discord.ext import tasks

EST = ZoneInfo("America/New_York")
FETCH_TIMES = [time(hour=h, tzinfo=EST) for h in (0, 6, 12, 18)]

from src.db import async_session
from src.db.models import PlayerXpSnapshot

PLAYER_NAMES = (
    "yothos",
    "guildan",
    "Charlster",
    "ImaKlutz",
    "moraxam",
    "Choufleur",
    "g4m3f4c3",
    "Oliiviier",
)

API_BASE = "https://query.idleclans.com/api/Player/profile"


async def _fetch_player(
    session: aiohttp.ClientSession, player_name: str
) -> dict | None:
    url = f"{API_BASE}/{player_name}"
    backoff = 1

    for attempt in range(1, 4):
        try:
            async with session.get(url) as resp:
                if resp.status < 200 or resp.status >= 300:
                    logging.warning(
                        "[xp_fetcher] attempt %d for %s returned status %d",
                        attempt,
                        player_name,
                        resp.status,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                data = await resp.json()
                return data.get("skillExperiences")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.warning(
                "[xp_fetcher] attempt %d for %s failed: %s",
                attempt,
                player_name,
                e,
            )
            await asyncio.sleep(backoff)
            backoff *= 2
            continue

    logging.error("[xp_fetcher] all attempts failed for %s", player_name)
    return None


@tasks.loop(time=FETCH_TIMES)
async def fetch_player_xp() -> None:
    fetched_at = datetime.now(timezone.utc)
    timeout = aiohttp.ClientTimeout(total=15)
    stored = 0

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for player_name in PLAYER_NAMES:
            skill_xp = await _fetch_player(session, player_name)
            if skill_xp is None:
                continue

            try:
                async with async_session() as db:
                    db.add(
                        PlayerXpSnapshot(
                            player_name=player_name,
                            fetched_at=fetched_at,
                            **skill_xp,
                        )
                    )
                    await db.commit()
                stored += 1
            except Exception as e:
                logging.error(
                    "[xp_fetcher] error storing snapshot for %s: %s",
                    player_name,
                    e,
                    exc_info=True,
                )

    logging.info(
        "[xp_fetcher] cycle complete: stored %d/%d snapshots", stored, len(PLAYER_NAMES)
    )
