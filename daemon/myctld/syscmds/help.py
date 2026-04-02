"""Daemon help built-in command."""

from __future__ import annotations

from myctl.api.context import Context, Response
from myctl.api.style import make_style

from ..config import APP_NAME
from .api import command


@command("help", help="Show command help")
async def help(ctx: Context, registry) -> Response:
    style = make_style(ctx.terminal)
    lines = [
        "\n" + style.bold(APP_NAME.capitalize()) + "\n",
        style.info(f"Usage: {APP_NAME} <command> [args]\n"),
        style.info("Args: "),
    ]
    for name, description in registry.system_help().items():
        lines.append(f"  - {style.success(name)}: {description}")

    plugin_ids = sorted(registry.plugins.keys())
    if plugin_ids:
        for plugin_id in plugin_ids:
            lines.append(f"  - {style.success(plugin_id)}: Plugin command namespace")

    return ctx.ok("\n".join(lines))
