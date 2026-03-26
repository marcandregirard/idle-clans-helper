"""Boss poll slash command.

Provides /boss_poll command to manually re-post the daily and/or weekly boss poll.
Restricted to server administrators.
"""

import asyncio
import logging

import discord
from discord import app_commands

from src.discord_client import tree


@tree.command(name="boss_poll", description="Re-post the boss poll (admin only)")
#@app_commands.default_permissions(administrator=True)
@app_commands.describe(poll_type="Which poll to re-post")
@app_commands.choices(poll_type=[
    app_commands.Choice(name="daily", value="daily"),
    app_commands.Choice(name="weekly", value="weekly"),
    app_commands.Choice(name="both", value="both"),
])
async def boss_poll(interaction: discord.Interaction, poll_type: app_commands.Choice[str]):
    """Manually re-post the daily and/or weekly boss poll."""
    from src.tasks.boss_scheduler import _post_boss_poll

    await interaction.response.defer(ephemeral=True)

    try:
        if poll_type.value in ("weekly", "both"):
            await _post_boss_poll(interaction.client, is_weekly=True)
        if poll_type.value == "both":
            await asyncio.sleep(1)
        if poll_type.value in ("daily", "both"):
            await _post_boss_poll(interaction.client, is_weekly=False)
        await interaction.followup.send(
            f"✅ Boss poll ({poll_type.value}) has been re-posted!",
            ephemeral=True,
        )
    except Exception as e:
        logging.error("[boss_poll_command] failed: %s", e, exc_info=True)
        await interaction.followup.send(
            "❌ Failed to re-post boss poll. Check logs for details.",
            ephemeral=True,
        )
