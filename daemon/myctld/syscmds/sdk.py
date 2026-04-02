"""Daemon sdk built-in command."""

from __future__ import annotations

from myctl.api.context import Context, Response
from myctl.api.style import make_style

from ..config import APP_NAME
from .api import command


@command("sdk", help="Show SDK metadata and install hints")
async def sdk(ctx: Context, registry) -> Response:
    style = make_style(ctx.terminal)
    return ctx.ok(
        style.table(
            [
                ["SDK", f"{APP_NAME}.api"],
                ["Version", "0.2.0"],
                ["Plugins", str(len(registry.plugins))],
            ],
            headers=[style.bold(f"{APP_NAME.capitalize()} SDK"), ""],
        )
    )
