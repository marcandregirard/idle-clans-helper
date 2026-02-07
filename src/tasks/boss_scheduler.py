"""Boss quest poll scheduler.

Posts daily and weekly boss quest polls at midnight UTC. On Mondays, posts both
weekly poll (first) and daily poll (second). On other days, posts only daily poll.
"""

import asyncio
import datetime
import logging
import os
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks

from src.db import MessageType
from src.tasks.scheduled_message_ops import (
    delete_scheduled_message,
    get_scheduled_message,
    upsert_scheduled_message,
)
from src.tasks.utils import find_channel_by_name

# Boss emoji constants
BOSS_EMOJIS = ["🐔", "😈", "👹", "⚡", "🦁", "🐍"]
BOSS_NAMES = ["Griffin", "Hades", "Devil", "Zeus", "Chimera", "Medusa"]
GEM_EMOJI = "💎"

DEFAULT_CHANNEL = "tactical-dispatch"


def _get_ordinal_suffix(day: int) -> str:
    """Return ordinal suffix for day (st, nd, rd, th).

    Args:
        day: Day of month (1-31)

    Returns:
        Ordinal suffix string
    """
    if 10 <= day % 100 <= 20:
        return "th"
    suffix_map = {1: "st", 2: "nd", 3: "rd"}
    return suffix_map.get(day % 10, "th")


def _build_boss_poll_message(is_weekly: bool) -> tuple[str, list[str]]:
    """Build boss poll message content and list of emoji reactions.

    Args:
        is_weekly: True for weekly poll, False for daily poll

    Returns:
        Tuple of (message_content, emoji_list)
    """
    now = datetime.datetime.now(ZoneInfo("UTC"))

    if is_weekly:
        title = "What are your **weekly boss quests this week?**"
    else:
        day_with_suffix = f"{now.day}{_get_ordinal_suffix(now.day)}"
        date_str = now.strftime(f"%b {day_with_suffix}")
        title = f"What are your **daily boss quests today ({date_str})?**"

    # Build boss list with emojis
    boss_lines = [f"{emoji} {name}" for emoji, name in zip(BOSS_EMOJIS, BOSS_NAMES)]

    # Add gem quest for weekly polls
    if is_weekly:
        boss_lines.append(f"{GEM_EMOJI} Gem quest")

    message = f"{title}\n\n" + "\n".join(boss_lines)

    # Build emoji list for reactions
    emojis = BOSS_EMOJIS.copy()
    if is_weekly:
        emojis.append(GEM_EMOJI)

    return message, emojis


async def _delete_previous_message(
    client: discord.Client,
    channel: discord.TextChannel,
    message_type: MessageType,
) -> None:
    """Delete previous scheduled message if exists.

    Args:
        client: Discord client instance
        channel: Channel where message was posted
        message_type: Type of message to delete
    """
    try:
        # Get previous message ID from database
        prev_message_id = await get_scheduled_message(message_type, str(channel.id))

        if prev_message_id:
            try:
                # Fetch and delete the message
                prev_message = await channel.fetch_message(int(prev_message_id))
                await prev_message.delete()
                logging.info(
                    "[boss_scheduler] deleted previous %s message %s",
                    message_type,
                    prev_message_id,
                )
            except discord.NotFound:
                logging.warning(
                    "[boss_scheduler] previous %s message %s not found, skipping deletion",
                    message_type,
                    prev_message_id,
                )
            except discord.HTTPException as e:
                logging.error(
                    "[boss_scheduler] failed to delete previous %s message: %s",
                    message_type,
                    e,
                )

            # Always clean up database record, whether deletion succeeded or not
            await delete_scheduled_message(message_type, str(channel.id))
    except Exception as e:
        logging.error(
            "[boss_scheduler] error during message deletion: %s", e, exc_info=True
        )


async def _post_boss_poll(
    client: discord.Client,
    is_weekly: bool,
) -> None:
    """Post a boss poll message with deletion of previous message.

    Args:
        client: Discord client instance
        is_weekly: True for weekly poll, False for daily poll
    """
    message_type = MessageType.WEEKLY if is_weekly else MessageType.DAILY
    poll_name = "weekly" if is_weekly else "daily"

    try:
        # Get channel
        channel_name = os.getenv("BOSS_POLL_CHANNEL", DEFAULT_CHANNEL)
        channel = find_channel_by_name(client, channel_name)

        if channel is None:
            logging.warning(
                "[boss_scheduler] channel %s not found, cannot post %s poll",
                channel_name,
                poll_name,
            )
            return

        # Delete previous message
        await _delete_previous_message(client, channel, message_type)

        # Convert channel ID to string for database storage
        channel_id_str = str(channel.id)

        # Build message content
        message_content, emojis = _build_boss_poll_message(is_weekly)

        # Send message with retry logic
        message = None
        backoff = 0.5  # Start with 500ms delay

        for attempt in range(1, 4):
            try:
                message = await channel.send(message_content)
                logging.info(
                    "[boss_scheduler] posted %s poll message %s",
                    poll_name,
                    message.id,
                )
                break
            except discord.HTTPException as e:
                if attempt < 3:
                    logging.warning(
                        "[boss_scheduler] attempt %d to post %s poll failed: %s, retrying...",
                        attempt,
                        poll_name,
                        e,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    logging.error(
                        "[boss_scheduler] all attempts to post %s poll failed: %s",
                        poll_name,
                        e,
                    )
                    return

        if message is None:
            logging.error("[boss_scheduler] failed to post %s poll", poll_name)
            return

        # Add emoji reactions sequentially
        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
                await asyncio.sleep(0.15)  # Rate limit prevention
            except discord.HTTPException as e:
                logging.error(
                    "[boss_scheduler] failed to add reaction %s: %s", emoji, e
                )

        # Store message ID in database
        await upsert_scheduled_message(message_type, channel_id_str, str(message.id))

    except Exception as e:
        logging.error(
            "[boss_scheduler] unexpected error posting %s poll: %s",
            poll_name,
            e,
            exc_info=True,
        )


def create_boss_scheduler(client: discord.Client) -> tasks.Loop:
    """Create boss poll scheduler task that runs at midnight UTC.

    Args:
        client: Discord client instance

    Returns:
        Discord tasks.Loop instance configured to run at midnight UTC
    """

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZoneInfo("UTC")))
    async def post_boss_poll():
        """Post daily boss poll at midnight UTC, plus weekly on Mondays."""
        try:
            now = datetime.datetime.now(ZoneInfo("UTC"))
            is_monday = now.weekday() == 0  # Monday = 0

            # On Mondays, post weekly first, then daily
            if is_monday:
                await _post_boss_poll(client, is_weekly=True)
                # Small delay between messages
                await asyncio.sleep(1)

            # Always post daily (including on Mondays)
            await _post_boss_poll(client, is_weekly=False)

        except Exception as e:
            logging.error("[boss_scheduler] unexpected error: %s", e, exc_info=True)

    return post_boss_poll
