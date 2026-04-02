"""Daemon ping built-in command."""

from __future__ import annotations

from myctl.api.context import Context, Response
from myctl.api.style import make_style

from .api import command


@command("ping", help="Check daemon responsiveness")
async def ping(ctx: Context, registry) -> Response:
    return ctx.ok(make_style(ctx.terminal).success("pong"))
