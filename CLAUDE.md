# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Discord bot (slash-command bot) for the Idle Clans game, providing boss and key lookup commands. Built with Python 3.13+ and discord.py.

## Commands

**Run locally (with uv):**
```bash
uv sync
uv run main.py
```

**Run locally (without uv):**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "discord-py>=2.6.2" "python-dotenv>=1.2.1"
python main.py
```

**Docker:**
```bash
docker build -t idle-clans-helper .
docker run idle-clans-helper
```

Requires a `.env` file with `TOKEN=<discord-bot-token>` (see `.env.example`).

No test suite or linter is configured.

## Architecture

- **`main.py`** — Entry point. Loads `.env`, imports the client and all command modules (which registers them), then starts the bot.
- **`src/discord_client.py`** — Creates the global `client` and `tree` (CommandTree) instances. On ready, syncs commands to Discord. All command modules import `client` and `tree` from here.
- **`src/commands/`** — Each file defines one slash command registered on the shared `tree`. Currently: `/boss` (lookup by boss name) and `/keys` (lookup by key name). Both support autocomplete and ephemeral responses.
- **`src/models/`** — `BossEntry` dataclass and the `ALL_BOSSES` list containing all boss data. This is the single source of truth for game data.

### Adding a new boss

Add a `BossEntry` to `ALL_BOSSES` in `src/models/__init__.py`. Both `/boss` and `/keys` commands build their lookup dicts from this list at import time, so no other changes are needed.

### Adding a new command

Create a new file in `src/commands/`, import `tree` from `src.discord_client`, register the command with `@tree.command()`, then add a wildcard import of the new module in `main.py`.

## CI/CD

GitHub Actions (`.github/workflows/docker-image.yml`) builds and pushes Docker images to GHCR on pushes to `main` and version tags (`v*.*.*`).
