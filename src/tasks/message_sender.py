import asyncio
import logging
import os
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
from sqlalchemy import select, update

from src.db import async_session, ClanMessage
from src.tasks.gold_donation import check_gold_donation

DEFAULT_CHANNEL = "testing-ground"


def _find_channel_by_name(client: discord.Client, name: str) -> discord.TextChannel | None:
    for channel in client.get_all_channels():
        if isinstance(channel, discord.TextChannel) and channel.name == name:
            return channel
    return None


def _format_message(msg: ClanMessage) -> str:
    est = ZoneInfo("America/New_York")
    est_time = msg.timestamp.astimezone(est)
    return f"`[{est_time.strftime('%b %e %H:%M')}]` {msg.message}"


async def _send_pending(client: discord.Client) -> None:
    channel_name = os.getenv("CLAN_MESSAGE_CHANNEL", DEFAULT_CHANNEL)
    channel = _find_channel_by_name(client, channel_name)
    if channel is None:
        logging.warning("[messagesender] channel %s not found", channel_name)
        return

    async with async_session() as db:
        stmt = (
            select(ClanMessage)
            .where(ClanMessage.message_sent == False)  # noqa: E712
            .order_by(ClanMessage.timestamp.asc())
            .limit(10)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        if not messages:
            return

        sent_ids: list[int] = []
        for msg in messages:
            text = _format_message(msg)
            try:
                await channel.send(text)
            except discord.HTTPException as e:
                logging.error("[messagesender] failed to send message id=%d: %s", msg.id, e)
                continue

            sent_ids.append(msg.id)
            await check_gold_donation(client, msg.message, msg.timestamp)
            await asyncio.sleep(0.15)

        if sent_ids:
            await db.execute(
                update(ClanMessage)
                .where(ClanMessage.id.in_(sent_ids))
                .values(message_sent=True)
            )
            await db.commit()


def create_message_sender(client: discord.Client) -> tasks.Loop:
    @tasks.loop(seconds=30)
    async def send_messages():
        await _send_pending(client)

    return send_messages
