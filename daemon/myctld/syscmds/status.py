"""Daemon status built-in command."""

from __future__ import annotations

import os
import sys
import time

from myctl.api.context import Context, Response
from myctl.api.style import make_style

from ..config import APP_NAME, DAEMON_NAME
from .api import command


@command("status", help="Show daemon status")
async def status(ctx: Context, registry) -> Response:
    style = make_style(ctx.terminal)
    uptime_seconds = int(
        time.time() - getattr(sys.modules.get("__main__"), "BOOT_TIME", time.time())
    )
    return ctx.ok(
        style.table(
            [
                ["Status", style.success("online")],
                ["Plugins", str(len(registry.plugins))],
                ["PID", str(os.getpid())],
                ["Uptime", f"{uptime_seconds}s"],
            ],
            headers=[style.bold(f"{APP_NAME.capitalize()} {DAEMON_NAME}"), ""],
        )
    )
