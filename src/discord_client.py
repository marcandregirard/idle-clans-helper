import discord
import logging

from src.db import init_db


client = discord.Client(intents=discord.Intents.default())
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready() -> None:
    logging.info(f"Logged in as {client.user}")
    await init_db()
    logging.info("Database connection verified")
    await tree.sync()
    logging.info("Synced!")
    logging.info([k.name for k in tree.walk_commands()])
