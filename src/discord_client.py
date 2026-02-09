import discord
import logging

from src.db import init_db
from src.tasks.boss_scheduler import create_boss_scheduler
from src.tasks.boss_summary import create_boss_summary_scheduler
from src.tasks.clanlog_fetcher import bulk_fetch_clanlog, recent_fetch_clanlog
from src.tasks.message_sender import create_message_sender


client = discord.Client(intents=discord.Intents.default())
tree = discord.app_commands.CommandTree(client)

send_messages = create_message_sender(client)
post_boss_poll = create_boss_scheduler(client)
post_boss_summary = create_boss_summary_scheduler(client)


@bulk_fetch_clanlog.error
async def bulk_fetch_error(error: Exception) -> None:
    logging.error("[bulk_fetch_clanlog] task error: %s", error, exc_info=error)


@recent_fetch_clanlog.error
async def recent_fetch_error(error: Exception) -> None:
    logging.error("[recent_fetch_clanlog] task error: %s", error, exc_info=error)


@send_messages.error
async def send_messages_error(error: Exception) -> None:
    logging.error("[send_messages] task error: %s", error, exc_info=error)


@post_boss_poll.error
async def post_boss_poll_error(error: Exception) -> None:
    logging.error("[post_boss_poll] task error: %s", error, exc_info=error)


@post_boss_summary.error
async def post_boss_summary_error(error: Exception) -> None:
    logging.error("[post_boss_summary] task error: %s", error, exc_info=error)


@client.event
async def on_ready() -> None:
    logging.info(f"Logged in as {client.user}")
    await init_db()
    logging.info("Database connection verified")

    if not bulk_fetch_clanlog.is_running():
        bulk_fetch_clanlog.start()
    if not recent_fetch_clanlog.is_running():
        recent_fetch_clanlog.start()
    if not send_messages.is_running():
        send_messages.start()
    if not post_boss_poll.is_running():
        post_boss_poll.start()
    if not post_boss_summary.is_running():
        post_boss_summary.start()
    logging.info("Background tasks started")

    await tree.sync()
    logging.info("Synced!")
    logging.info([k.name for k in tree.walk_commands()])


@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    logging.error("[command] error in %s: %s", interaction.command.name if interaction.command else "unknown", error, exc_info=error)
    if not interaction.response.is_done():
        await interaction.response.send_message("An error occurred while processing your command.", ephemeral=True)
    else:
        await interaction.followup.send("An error occurred while processing your command.", ephemeral=True)
