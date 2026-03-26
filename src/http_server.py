"""Lightweight HTTP server for triggering bot actions from the host.

Endpoints:
  POST /boss-poll?type=daily|weekly|both
  POST /boss-summary

Requires the HTTP_SECRET env var to be set. Pass it as:
  Authorization: Bearer <secret>
"""

import asyncio
import logging
import os

import discord
from aiohttp import web


def _check_auth(request: web.Request) -> bool:
    secret = os.getenv("HTTP_SECRET")
    if not secret:
        return True  # no secret configured, allow all
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {secret}"


def create_http_server(client: discord.Client) -> web.Application:
    app = web.Application()

    async def boss_poll(request: web.Request) -> web.Response:
        if not _check_auth(request):
            return web.Response(status=401, text="Unauthorized")

        poll_type = request.rel_url.query.get("type", "daily")
        if poll_type not in ("daily", "weekly", "both"):
            return web.Response(status=400, text="type must be daily, weekly, or both")

        if not client.is_ready():
            return web.Response(status=503, text="Bot not ready")

        from src.tasks.boss_scheduler import _post_boss_poll

        try:
            if poll_type in ("weekly", "both"):
                await _post_boss_poll(client, is_weekly=True)
            if poll_type == "both":
                await asyncio.sleep(1)
            if poll_type in ("daily", "both"):
                await _post_boss_poll(client, is_weekly=False)
            logging.info("[http_server] boss poll (%s) triggered via HTTP", poll_type)
            return web.Response(text=f"Boss poll ({poll_type}) posted")
        except Exception as e:
            logging.error("[http_server] boss poll failed: %s", e, exc_info=True)
            return web.Response(status=500, text=str(e))

    async def boss_summary(request: web.Request) -> web.Response:
        if not _check_auth(request):
            return web.Response(status=401, text="Unauthorized")

        if not client.is_ready():
            return web.Response(status=503, text="Bot not ready")

        from src.tasks.boss_summary import _regenerate_boss_summary

        try:
            await _regenerate_boss_summary(client)
            logging.info("[http_server] boss summary triggered via HTTP")
            return web.Response(text="Boss summary regenerated")
        except Exception as e:
            logging.error("[http_server] boss summary failed: %s", e, exc_info=True)
            return web.Response(status=500, text=str(e))

    app.router.add_post("/boss-poll", boss_poll)
    app.router.add_post("/boss-summary", boss_summary)

    return app


async def start_http_server(client: discord.Client) -> None:
    port = int(os.getenv("HTTP_PORT", "8080"))
    app = create_http_server(client)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info("[http_server] listening on port %d", port)
