import logging
import os

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

from src.discord_client import *
from src.commands.boss import *
from src.commands.boss_summary import *
from src.commands.keys import *
from src.commands.market_food import *

TOKEN: str = os.getenv("TOKEN") or ""


if __name__ == "__main__":
    client.run(TOKEN, log_level=logging.INFO)