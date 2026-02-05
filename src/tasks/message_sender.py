import asyncio
import logging
import os
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
from sqlalchemy import select, update

from src.db import async_session, ClanLog, ClanLogType
from src.tasks.gold_donation import check_gold_donation

DEFAULT_CHANNEL = "corporate-oversight"

_SKIP_TYPES = {
    ClanLogType.EVENT_STARTED,
    ClanLogType.COMBAT_QUEST_COMPLETED,
    ClanLogType.SKILLING_QUEST_COMPLETED,
}


def _find_channel_by_name(client: discord.Client, name: str) -> discord.TextChannel | None:
    for channel in client.get_all_channels():
        if isinstance(channel, discord.TextChannel) and channel.name == name:
            return channel
    return None


def _format_message(msg: ClanLog) -> str:
    est = ZoneInfo("America/New_York")
    utc_time = msg.timestamp.replace(tzinfo=ZoneInfo("UTC"))
    est_time = utc_time.astimezone(est)
    return f"`[{est_time.strftime('%b %e %H:%M')}]` {msg.message}"


async def _send_pending(client: discord.Client) -> None:
    channel_name = os.getenv("CLAN_MESSAGE_CHANNEL", DEFAULT_CHANNEL)
    channel = _find_channel_by_name(client, channel_name)
    if channel is None:
        logging.warning("[messagesender] channel %s not found", channel_name)
        return

    async with async_session() as db:
        stmt = (
            select(ClanLog)
            .where(ClanLog.message_sent == False)  # noqa: E712
            .order_by(ClanLog.timestamp.asc())
            .limit(10)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

    if not messages:
        return

    sent_ids: list[int] = []
    for msg in messages:
        if msg.log_type in _SKIP_TYPES:
            sent_ids.append(msg.id)
            continue

        text = _format_message(msg)
        try:
            await channel.send(text)
        except discord.HTTPException as e:
            logging.error("[messagesender] failed to send message id=%d: %s", msg.id, e)
            continue

        sent_ids.append(msg.id)
        if msg.log_type == ClanLogType.VAULT_DEPOSIT:
            await check_gold_donation(client, msg.message, msg.timestamp)
        await asyncio.sleep(0.15)

    if sent_ids:
        async with async_session() as db:
            await db.execute(
                update(ClanLog)
                .where(ClanLog.id.in_(sent_ids))
                .values(message_sent=True)
            )
            await db.commit()


def create_message_sender(client: discord.Client) -> tasks.Loop:
    @tasks.loop(seconds=30)
    async def send_messages():
        await _send_pending(client)

    return send_messages
