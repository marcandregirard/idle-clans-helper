import logging
import os

from src.discord_client import *
from src.commands.boss import *
from src.commands.keys import *
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

TOKEN: str = os.getenv("TOKEN") or ""


if __name__ == "__main__":
    client.run(TOKEN, log_level=logging.DEBUG)