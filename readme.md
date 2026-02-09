# Idle Clans Helper — Discord app

This repository contains a small Discord app (slash-command bot) that provides quick reference information for the Idle Clans game. It was adapted from and is based on the cgtools-lotr-discordbot project by Kevin Belisle:

https://github.com/KevBelisle/cgtools-lotr-discordbot

What this project does

- Registers simple slash commands using discord.py commands in `src/commands/`.
- Provides lookup commands for Idle Clans keys and bosses.
- Designed to run as a Discord application (bot) using a bot token stored in an environment variable.

Commands included

- `/keys` — look up boss information by key name.
- `/boss` — look up boss information by boss name.

Files of interest

- `main.py` — application entrypoint. Loads environment variables and starts the bot.
- `src/discord_client.py` — creates the discord client and command tree, syncs commands on ready.
- `src/commands/keys.py` — `/keys` command implementation and autocomplete.
- `src/commands/boss.py` — `/boss` command implementation and autocomplete.
- `pyproject.toml` — project metadata and Python dependencies.

Getting started (local)

1. Create a virtual environment and install dependencies (as Windows commands):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # or use Activate.bat for cmd.exe
pip install -r requirements.txt  # or `pip install "discord-py>=2.6.2" "python-dotenv>=1.2.1"`
```

2. Create a `.env` file in the project root with your Discord bot token:

```
TOKEN=your-bot-token-here
```

3. Run the bot:

```
python main.py
```

Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- Discord bot token

### Setup

1. Copy the environment file:
   ```bash
   cp .env.docker .env
   ```

2. Edit `.env` and set your Discord bot token:
   ```bash
   TOKEN=your_actual_token_here
   ```

3. (Optional) Customize other environment variables in `.env` (database credentials, channel names, etc.)

4. Start the bot:
   ```bash
   docker-compose up -d
   ```

5. View logs:
   ```bash
   docker-compose logs -f bot
   ```

6. Stop the bot:
   ```bash
   docker-compose down
   ```

### Database Backup

Backup the database:
```bash
docker-compose exec db pg_dump -U idle_clans idle_clans > backup.sql
```

Restore from backup:
```bash
docker-compose exec -T db psql -U idle_clans idle_clans < backup.sql
```

Notes

- The bot uses guild-registered application commands where available, and syncs commands on startup.
- The slash commands use ephemeral responses when `just_for_me` is `True` so users can hide the reply.
- When deploying with Docker, the PostgreSQL database runs in a container with persistent storage.
