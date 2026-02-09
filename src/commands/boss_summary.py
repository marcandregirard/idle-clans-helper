"""Boss summary slash command.

Provides /boss_summary command to manually regenerate the boss fight participation summary.
"""

import logging

import discord

from src.discord_client import tree


@tree.command(
    name="boss_summary",
    description="Regenerate the boss fight participation summary"
)
async def boss_summary(interaction: discord.Interaction):
    """Manually regenerate boss summary (ephemeral confirmation)."""
    # Import here to avoid circular dependency
    from src.tasks.boss_summary import _regenerate_boss_summary

    await interaction.response.defer(ephemeral=True)

    try:
        await _regenerate_boss_summary(interaction.client)
        await interaction.followup.send(
            "✅ Boss summary has been regenerated!",
            ephemeral=True
        )
    except Exception as e:
        logging.error("[boss_summary_command] failed: %s", e, exc_info=True)
        await interaction.followup.send(
            "❌ Failed to regenerate boss summary. Check logs for details.",
            ephemeral=True
        )
