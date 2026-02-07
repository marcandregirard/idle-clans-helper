import logging
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import discord

from src.tasks.utils import find_channel_by_name

DEFAULT_CHANNEL = "general"

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

_GOLD_PATTERN = re.compile(r"^(.+?)\s+added\s+(\d+)x\s+Gold\.$")
_GOLD_COLOR = 0xFFD700
_MIN_AMOUNT = 1_000_000


def _format_amount(n: int) -> str:
    return f"{n:,}"


async def check_gold_donation(
    client: discord.Client,
    message_text: str,
    timestamp: datetime,
) -> None:
    match = _GOLD_PATTERN.match(message_text)
    if not match:
        return

    player_name = match.group(1)
    amount = int(match.group(2))

    if amount < _MIN_AMOUNT:
        return

    channel_name = os.getenv("GOLD_DONATION_CHANNEL", DEFAULT_CHANNEL)
    channel = find_channel_by_name(client, channel_name)
    if channel is None:
        logging.warning("[gold_donation] channel %s not found", channel_name)
        return

    est = ZoneInfo("America/New_York")
    est_time = timestamp.astimezone(est)

    display_name = MEMBER_TO_DISCORD.get(player_name, player_name)
    mention_text = f"@{display_name}" if display_name != player_name else player_name

    embed = discord.Embed(
        title="\U0001f514\U0001f389 Leadership Commendation",
        description=(
            f"Leadership commends **{mention_text}** for their exceptional "
            f"Clan Vault contribution. This selfless act of organizational "
            f"commitment exemplifies KlutzCo values. Well done."
        ),
        color=_GOLD_COLOR,
    )
    embed.add_field(name="Amount Donated", value=f"{_format_amount(amount)} Gold", inline=True)
    # Cross-platform time formatting (avoid %-I and %e which aren't supported on Windows)
    footer_text = f"{est_time.strftime('%b')} {est_time.day}, {est_time.year} at {est_time.strftime('%I:%M %p').lstrip('0')} {est_time.strftime('%Z')}"
    embed.set_footer(text=footer_text)

    try:
        await channel.send(embed=embed)
        logging.info("[gold_donation] sent celebration for %s's %d gold donation", player_name, amount)
    except discord.HTTPException as e:
        logging.error("[gold_donation] failed to send celebration: %s", e)
