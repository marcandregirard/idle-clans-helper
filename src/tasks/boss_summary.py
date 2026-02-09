"""Boss fight participation summary scheduler.

Posts and updates a daily summary of boss fight participation based on poll reactions.
Collects reactions from daily and weekly boss poll messages, formats participant lists,
and updates the summary message in-place.
"""

import datetime
import logging
import os
from dataclasses import dataclass
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

# Boss emoji constants (shared with boss_scheduler.py)
BOSS_EMOJIS = ["🐔", "😈", "👹", "⚡", "🦁", "🐍"]
BOSS_NAMES = ["Griffin", "Hades", "Devil", "Zeus", "Chimera", "Medusa"]
GEM_EMOJI = "💎"
GEM_NAME = "Gem Quest"

# Member mapping (Discord username → Display name)
MEMBER_TO_DISCORD = {
    "ImaKlutz": "ImaKlutz",
    "guildan": "Guildan",
    "Charlster": "Gagnon54",
    "moraxam": "Morax",
    "yothos": "yothos",
    "Choufleur": "Steph",
    "g4m3f4c3": "g4m3f4c3",
    "Oliiviier": "oli",
}

MEMBER_TO_DISCORDID = {
	270655486318215168:  "ImaKlutz",
	199632692231274496:   "guildan",
	409718701236158465: "Charlster",
	344994648059674624:   "moraxam",
	448261978469695489:    "yothos",
	229776173146570755: "Choufleur",
	298522549661466625:  "g4m3f4c3",
	350298028902711308: "Oliiviier",
}

DEFAULT_CHANNEL = "tactical-dispatch"
DEFAULT_TIME = "9:30"


@dataclass
class BossParticipation:
    """Represents participation for a single boss."""

    daily_users: set[str]  # Users who reacted on daily poll
    weekly_users: set[str]  # Users who reacted on weekly poll


async def _fetch_poll_message(
    channel: discord.TextChannel, message_type: MessageType
) -> discord.Message | None:
    """Fetch a poll message from the database and Discord.

    Args:
        channel: Channel where the poll was posted
        message_type: Type of poll (DAILY or WEEKLY)

    Returns:
        Discord message if found, None otherwise
    """
    try:
        message_id = await get_scheduled_message(message_type, str(channel.id))
        if not message_id:
            logging.debug(
                "[boss_summary] no %s poll message found in database", message_type
            )
            return None

        message = await channel.fetch_message(int(message_id))
        logging.debug("[boss_summary] fetched %s poll message %s", message_type, message_id)
        return message
    except discord.NotFound:
        logging.warning(
            "[boss_summary] %s poll message %s not found in Discord",
            message_type,
            message_id,
        )
        return None
    except discord.HTTPException as e:
        logging.error(
            "[boss_summary] failed to fetch %s poll message: %s", message_type, e
        )
        return None
    except Exception as e:
        logging.error(
            "[boss_summary] unexpected error fetching %s poll: %s",
            message_type,
            e,
            exc_info=True,
        )
        return None


async def _get_reactions_for_emoji(
    message: discord.Message, emoji: str
) -> set[int]:
    """Get all user IDs who reacted with a specific emoji.

    Args:
        message: Discord message to check reactions on
        emoji: Emoji to filter by

    Returns:
        Set of user IDs who reacted with the emoji
    """
    user_ids = set()
    for reaction in message.reactions:
        if str(reaction.emoji) == emoji:
            try:
                async for user in reaction.users():
                    if not user.bot:
                        user_ids.add(user.id)
            except discord.HTTPException as e:
                logging.error(
                    "[boss_summary] failed to fetch users for reaction %s: %s", emoji, e
                )
            break
    return user_ids


def _map_user_ids_to_names(user_ids: set[int], guild: discord.Guild) -> list[str]:
    """Convert Discord user IDs to display names.

    Args:
        user_ids: Set of Discord user IDs
        guild: Discord guild to look up members

    Returns:
        List of display names (sorted alphabetically)
    """
    names = []
    for user_id in user_ids:
        if user_id in MEMBER_TO_DISCORDID:
            if MEMBER_TO_DISCORDID[user_id] in MEMBER_TO_DISCORD:
                names.append(MEMBER_TO_DISCORD[MEMBER_TO_DISCORDID[user_id]])
            else:
                names.append(MEMBER_TO_DISCORDID[user_id])
        else:
            logging.warning("[boss_summary] unknown user ID %s, skipping", user_id)
    return sorted(names)


async def _collect_boss_data(
    channel: discord.TextChannel, guild: discord.Guild
) -> dict[str, BossParticipation]:
    """Collect boss participation data from daily and weekly polls.

    Args:
        channel: Channel where polls are posted
        guild: Discord guild for member lookups

    Returns:
        Dictionary mapping boss names to BossParticipation objects
    """
    boss_data = {}

    # Fetch poll messages
    daily_message = await _fetch_poll_message(channel, MessageType.DAILY)
    weekly_message = await _fetch_poll_message(channel, MessageType.WEEKLY)

    if not daily_message and not weekly_message:
        logging.warning(
            "[boss_summary] no poll messages found, summary will be empty"
        )
        return boss_data

    # Collect reactions for regular bosses
    for emoji, name in zip(BOSS_EMOJIS, BOSS_NAMES):
        daily_user_ids = set()
        weekly_user_ids = set()

        if daily_message:
            daily_user_ids = await _get_reactions_for_emoji(daily_message, emoji)

        if weekly_message:
            weekly_user_ids = await _get_reactions_for_emoji(weekly_message, emoji)

        # Convert user IDs to names
        daily_names = _map_user_ids_to_names(daily_user_ids, guild)
        weekly_names = _map_user_ids_to_names(weekly_user_ids, guild)

        boss_data[name] = BossParticipation(
            daily_users=set(daily_names), weekly_users=set(weekly_names)
        )

    # Collect reactions for Gem Quest (weekly only)
    if weekly_message:
        gem_user_ids = await _get_reactions_for_emoji(weekly_message, GEM_EMOJI)
        gem_names = _map_user_ids_to_names(gem_user_ids, guild)
        boss_data[GEM_NAME] = BossParticipation(
            daily_users=set(), weekly_users=set(gem_names)
        )

    return boss_data


def _format_summary_message(boss_data: dict[str, BossParticipation]) -> str:
    """Format boss participation data into a summary message.

    Args:
        boss_data: Dictionary mapping boss names to BossParticipation objects

    Returns:
        Formatted message string
    """
    lines = ["Today's boss fight summaries:", ""]

    # Find max boss name length for alignment
    max_length = max(len(name) for name in BOSS_NAMES + [GEM_NAME])

    # Format regular bosses
    for emoji, name in zip(BOSS_EMOJIS, BOSS_NAMES):
        participation = boss_data.get(name)
        if not participation:
            continue

        # Users who reacted on daily poll (with or without weekly) - no suffix
        daily_reactors = sorted(participation.daily_users)

        # Users who reacted ONLY on weekly poll (not on daily) - with [W] suffix
        weekly_only = sorted(participation.weekly_users - participation.daily_users)

        users = []
        users.extend(daily_reactors)
        users.extend(f"{u} [W]" for u in weekly_only)

        # Skip bosses with no participants
        if not users:
            continue

        padded_name = name.ljust(max_length)
        user_list = " · ".join(users)
        lines.append(f"{emoji} `{padded_name}:` {user_list}")

    # Format Gem Quest with extra newline
    if GEM_NAME in boss_data:
        participation = boss_data[GEM_NAME]
        if participation.weekly_users:
            lines.append("")
            padded_name = GEM_NAME.rjust(max_length)
            user_list = " · ".join(sorted(participation.weekly_users))
            lines.append(f"{GEM_EMOJI} `{padded_name}:` {user_list}")

    return "\n".join(lines)


async def _post_or_update_summary(
    client: discord.Client, channel: discord.TextChannel, content: str
) -> None:
    """Post new summary or update existing summary message.

    Args:
        client: Discord client instance
        channel: Channel where summary is posted
        content: Message content to post/update
    """
    channel_id_str = str(channel.id)

    # Try to get existing message ID
    existing_message_id = await get_scheduled_message(
        MessageType.BOSS_SUMMARY, channel_id_str
    )

    if existing_message_id:
        # Try to edit existing message
        try:
            message = await channel.fetch_message(int(existing_message_id))
            await message.edit(content=content)
            logging.info(
                "[boss_summary] updated existing summary message %s", existing_message_id
            )
            return
        except discord.NotFound:
            logging.warning(
                "[boss_summary] existing message %s not found, will post new message",
                existing_message_id,
            )
            # Clean up database record
            await delete_scheduled_message(MessageType.BOSS_SUMMARY, channel_id_str)
        except discord.HTTPException as e:
            logging.error(
                "[boss_summary] failed to edit message %s: %s, will post new message",
                existing_message_id,
                e,
            )
            # Clean up database record
            await delete_scheduled_message(MessageType.BOSS_SUMMARY, channel_id_str)

    # Post new message
    try:
        message = await channel.send(content)
        logging.info("[boss_summary] posted new summary message %s", message.id)

        # Store message ID in database
        await upsert_scheduled_message(
            MessageType.BOSS_SUMMARY, channel_id_str, str(message.id)
        )
    except discord.HTTPException as e:
        logging.error("[boss_summary] failed to post summary message: %s", e)


async def _regenerate_boss_summary(client: discord.Client) -> None:
    """Regenerate the boss fight participation summary.

    Args:
        client: Discord client instance
    """
    try:
        # Get channel
        channel_name = os.getenv("BOSS_SUMMARY_CHANNEL", DEFAULT_CHANNEL)
        channel = find_channel_by_name(client, channel_name)

        if channel is None:
            logging.warning(
                "[boss_summary] channel %s not found, cannot post summary", channel_name
            )
            return

        # Get guild for member lookups
        guild = channel.guild

        # Collect boss data from polls
        boss_data = await _collect_boss_data(channel, guild)

        # Format summary message
        content = _format_summary_message(boss_data)

        # Post or update summary
        await _post_or_update_summary(client, channel, content)

    except Exception as e:
        logging.error(
            "[boss_summary] unexpected error regenerating summary: %s", e, exc_info=True
        )


def create_boss_summary_scheduler(client: discord.Client) -> tasks.Loop:
    """Create boss summary scheduler task.

    Args:
        client: Discord client instance

    Returns:
        Discord tasks.Loop instance configured to run at specified time
    """
    # Parse time from environment
    time_str = os.getenv("BOSS_SUMMARY_TIME", DEFAULT_TIME)
    try:
        # Parse HH:MM format
        hour, minute = map(int, time_str.split(":"))
        run_time = datetime.time(hour=hour, minute=minute, tzinfo=ZoneInfo("America/New_York"))
        logging.info("[boss_summary] scheduler configured for %s Eastern", time_str)
    except (ValueError, AttributeError) as e:
        logging.error(
            "[boss_summary] invalid BOSS_SUMMARY_TIME format '%s', using default %s: %s",
            time_str,
            DEFAULT_TIME,
            e,
        )
        hour, minute = map(int, DEFAULT_TIME.split(":"))
        run_time = datetime.time(hour=hour, minute=minute, tzinfo=ZoneInfo("America/New_York"))

    @tasks.loop(time=run_time)
    async def post_boss_summary():
        """Post or update boss fight participation summary."""
        await _regenerate_boss_summary(client)

    return post_boss_summary
