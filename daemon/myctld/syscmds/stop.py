"""Daemon stop built-in command."""

from __future__ import annotations

from myctl.api.context import Context, Response
from myctl.api.style import make_style

from .api import command


@command("stop", help="Gracefully shut down the daemon")
async def stop(ctx: Context, registry) -> Response:
    return ctx.ok(make_style(ctx.terminal).warning("Daemon shutting down..."))
