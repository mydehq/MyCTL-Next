"""Daemon schema built-in command."""

from __future__ import annotations

from myctl.api.context import Context, Response

from .api import command


@command("schema", help="Dump the command schema")
async def schema(ctx: Context, registry) -> Response:
    """Return full command schema for dynamic clients."""
    return ctx.ok(registry.schema())
