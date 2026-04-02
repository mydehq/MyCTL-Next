"""Command registry and dispatcher for daemon built-ins and plugins.

The registry's core responsibility is **request dispatch** — routing incoming
requests to system commands or plugin handlers. Schema generation (command tree
building) is delegated to a specialized schema builder module.

This separation ensures the registry stays focused on routing logic and can be
easily tested in isolation from CLI schema concerns.

The module opts into ``from __future__ import annotations`` so type hints can
stay expressive without import-order coupling.

Read before: daemon/myctld/app.py; read after: daemon/myctld/schema.py
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import cast

from myctl.api.context import Context, Response
from myctl.api.logger import bind_logger_context, reset_logger_context

from .plugin.models import LoadedPlugin
from .schema import CommandNode, CommandTreeBuilder
from .syscmds import SYSTEM_COMMAND_HANDLERS, SYSTEM_COMMAND_HELP

log = logging.getLogger("myctl.registry")


CommandResult = Response | object
CommandHandler = Callable[[Context], CommandResult | Awaitable[CommandResult]]


@dataclass(slots=True)
class Registry:
    """Holds loaded plugins and performs request dispatch.

    The registry is responsible for routing incoming requests to the correct
    handler (system command or plugin command). Schema generation is delegated
    to CommandTreeBuilder.
    """

    plugins: dict[str, LoadedPlugin] = field(default_factory=dict)
    periodic_tasks: list[tuple[int, CommandHandler]] = field(default_factory=list)

    def system_help(self) -> dict[str, str]:
        """Return daemon built-in command descriptions."""
        return dict(SYSTEM_COMMAND_HELP)

    def schema(self) -> dict[str, CommandNode]:
        """Build full client-visible command schema (system + plugins).

        Delegates to CommandTreeBuilder for tree construction; registry's job
        is just to gather the metadata and hand it off.
        """
        return CommandTreeBuilder.build_full_schema(
            system_commands=self.system_help(),
            system_handlers=SYSTEM_COMMAND_HANDLERS,
            plugins=self.plugins,
        )

    async def dispatch(self, ctx: Context) -> Response:
        """Route a request context to system commands or plugin handlers."""
        if not ctx.path:
            return ctx.err("missing command path")

        # Stage 1: resolve built-in command namespace by longest path prefix.
        handler = None
        for length in range(len(ctx.path), 0, -1):
            candidate = " ".join(ctx.path[:length])
            handler = SYSTEM_COMMAND_HANDLERS.get(candidate)
            if handler is not None:
                break
        if handler is not None:
            log.info("dispatching built-in command %s", candidate)
            result = await handler(ctx, self)
            log.info("completed built-in command %s", candidate)
            return result

        # Stage 2: treat top-level token as plugin namespace.
        command = ctx.path[0]
        plugin = self.plugins.get(command)
        if plugin is None:
            return ctx.err(f"unknown command: {command}")

        # Bind plugin context to logs so one request is easy to trace.
        token = bind_logger_context(plugin_id=command)
        try:
            # Stage 3: match subcommand path inside the selected plugin.
            parts = ctx.path[1:]
            # Match the deepest command path first, so nested plugin commands
            # win over shorter parent paths.
            best_match: tuple[int, CommandHandler, dict[str, object]] | None = None
            for handler in getattr(plugin.plugin, "_commands", []):
                meta = getattr(handler, "__myctl_cmd__", {})
                cmd_path = str(meta.get("path", "")).split()
                if not cmd_path:
                    continue
                # Prefix match means a handler for `foo bar` can match when
                # user calls `plugin foo bar --flag`, while avoiding unrelated
                # handlers in the same plugin namespace.
                if parts[: len(cmd_path)] != cmd_path:
                    continue
                if best_match is None or len(cmd_path) > best_match[0]:
                    best_match = (len(cmd_path), handler, meta)

            if best_match is not None:
                _, handler, meta = best_match
                cmd_name = meta.get("path", "")
                log.info("dispatching plugin command %s %s", command, cmd_name)
                # Stage 4: execute handler (sync or async) and normalize output
                # into the Response protocol returned over IPC.
                result = handler(ctx)
                if inspect.isawaitable(result):
                    result = await cast(Awaitable[CommandResult], result)
                if isinstance(result, Response):
                    log.info("completed plugin command %s %s", command, cmd_name)
                    return result
                log.info("completed plugin command %s %s", command, cmd_name)
                return ctx.ok(result)
            log.warning("plugin '%s' has no commands", command)
            return ctx.err(f"plugin '{command}' has no commands")
        finally:
            # Always restore logger context to prevent cross-request leakage.
            reset_logger_context(token)
