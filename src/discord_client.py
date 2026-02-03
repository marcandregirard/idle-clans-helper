import discord
import logging

from src.db import init_db
from src.tasks.clanlog_fetcher import bulk_fetch_clanlog, recent_fetch_clanlog
from src.tasks.message_sender import create_message_sender


client = discord.Client(intents=discord.Intents.default())
tree = discord.app_commands.CommandTree(client)

send_messages = create_message_sender(client)

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
    logging.info("Background tasks started")

    await tree.sync()
    logging.info("Synced!")
    logging.info([k.name for k in tree.walk_commands()])
