"""Daemon plugin management built-in command."""

from __future__ import annotations

import shutil
from pathlib import Path

from myctl.api.context import Context, Response

from ..config import PLUGIN_SEARCH_PATHS
from .api import command


@command("plugin", help="Plugin management helper (init/list/remove)")
async def plugin(ctx: Context, registry) -> Response:
    if len(ctx.path) < 2:
        return ctx.ok("Usage: plugin <init|list|remove> ...")

    sub = ctx.path[1]
    if sub == "init":
        return plugin_init(ctx, registry)
    if sub == "list":
        return plugin_list(ctx, registry)
    if sub == "remove":
        return plugin_remove(ctx, registry)

    return ctx.err(f"unknown plugin command: {sub}")


# @command("plugin init", help="Initialize a new plugin")
async def plugin_init(ctx: Context, registry) -> Response:
    if len(ctx.path) < 3:
        return ctx.err("Usage: plugin init <plugin-name>")

    plugin_name = str(ctx.path[2]).strip()
    if not plugin_name:
        return ctx.err("Plugin name must not be empty")

    reserved = set(registry.system_help().keys())
    if plugin_name in reserved:
        return ctx.err(
            f"Plugin name '{plugin_name}' is reserved by system command namespace"
        )

    target_root = PLUGIN_SEARCH_PATHS[0] if PLUGIN_SEARCH_PATHS else Path("./plugins")
    plugin_dir = target_root / plugin_name

    if plugin_dir.exists():
        return ctx.err(f"Plugin already exists: {plugin_dir}")

    try:
        plugin_dir.mkdir(parents=True, exist_ok=False)
        (plugin_dir / "__init__.py").write_text("# plugin package\n")
        (plugin_dir / "main.py").write_text(
            "from myctl.api import Plugin, Context\n\n"
            f'plugin = Plugin("{plugin_name}")\n\n'
            '@plugin.command("hello", help="Say hello")\n'
            "async def hello(ctx: Context):\n"
            '    return ctx.ok("Hello from plugin")\n'
        )
    except Exception as exc:
        return ctx.err(f"Failed to create plugin: {exc}")

    return ctx.ok(f"Plugin created: {plugin_dir}")


async def plugin_list(ctx: Context, registry) -> Response:
    target_root = PLUGIN_SEARCH_PATHS[0] if PLUGIN_SEARCH_PATHS else Path("./plugins")
    if not target_root.exists():
        return ctx.ok("No plugin directory found")

    plugins = sorted(p.name for p in target_root.iterdir() if p.is_dir())
    return ctx.ok("\n".join(plugins) if plugins else "No plugins installed")


async def plugin_remove(ctx: Context, registry) -> Response:
    if len(ctx.path) < 3:
        return ctx.err("Usage: plugin remove <plugin-name>")

    plugin_name = str(ctx.path[2]).strip()
    if not plugin_name:
        return ctx.err("Plugin name must not be empty")

    target_root = PLUGIN_SEARCH_PATHS[0] if PLUGIN_SEARCH_PATHS else Path("./plugins")
    plugin_dir = target_root / plugin_name

    if not plugin_dir.exists() or not plugin_dir.is_dir():
        return ctx.err(f"Plugin not found: {plugin_name}")

    try:
        shutil.rmtree(plugin_dir)
    except Exception as exc:
        return ctx.err(f"Failed to remove plugin: {exc}")

    return ctx.ok(f"Plugin removed: {plugin_dir}")
