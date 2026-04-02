"""Daemon logs built-in command."""

from __future__ import annotations

from pathlib import Path

from myctl.api.context import Context, Response

from ..config import LOG_FILE
from .api import command


@command("logs", help="Show recent daemon logs")
async def logs(ctx: Context, registry) -> Response:
    log_file = Path(LOG_FILE)
    if not log_file.exists():
        return ctx.ok("No log file found.")

    try:
        lines = log_file.read_text().splitlines()
        tail = lines[-30:] if len(lines) > 30 else lines
        return ctx.ok("\n".join(tail))
    except Exception as exc:
        return ctx.ok(f"Failed to read logs: {exc}")
