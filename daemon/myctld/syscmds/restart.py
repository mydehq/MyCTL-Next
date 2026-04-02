"""Daemon restart built-in command."""

from __future__ import annotations

from myctl.api.context import Context, Response
from myctl.api.style import make_style

from .api import command


@command("restart", help="Restart the daemon")
async def restart(ctx: Context, registry) -> Response:
    return ctx.ok(make_style(ctx.terminal).warning("Daemon restarting..."))
