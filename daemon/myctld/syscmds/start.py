"""Daemon start built-in command."""

from __future__ import annotations

from myctl.api.context import Context, Response
from myctl.api.style import make_style

from .api import command


@command("start", help="Ensure the daemon is running")
async def start(ctx: Context, registry) -> Response:
    return ctx.ok(make_style(ctx.terminal).success("Daemon started successfully."))
