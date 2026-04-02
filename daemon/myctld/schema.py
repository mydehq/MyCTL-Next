"""Command tree schema building for client CLI generation.

Responsible for converting plugin command metadata into a nested schema tree
that the Go client uses to dynamically hydrate the Cobra CLI tree at startup.

Separation of concerns: this module builds schemas; dispatch logic lives in
the registry.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, TypedDict, cast

from myctl.api.plugin import FlagSpec


class CommandNode(TypedDict, total=False):
    """Schema node exposed to clients for command tree generation."""

    type: Literal["command", "group"]
    help: str
    children: dict[str, CommandNode]
    flags: list[FlagSpec]


class CommandTreeBuilder:
    """Builds nested schema trees from plugin command metadata."""

    @staticmethod
    def _command_node(
        help_text: str,
        *,
        type_: Literal["command", "group"] = "command",
        children: dict[str, CommandNode] | None = None,
        flags: list[FlagSpec] | None = None,
    ) -> CommandNode:
        """Create a single schema node."""
        node: CommandNode = {"type": type_, "help": help_text}
        if children:
            node["children"] = children
        if flags:
            node["flags"] = flags
        return node

    @staticmethod
    def build_plugin_tree(commands: Sequence[Any], plugin_id: str) -> CommandNode:
        """Convert plugin-decorated handlers into a nested schema tree.

        Args:
            commands: List of handler functions with __myctl_cmd__ metadata.
            plugin_id: Plugin namespace identifier.

        Returns:
            Root CommandNode with nested children for all registered commands.
        """
        root: CommandNode = {
            "type": "group",
            "help": f"Main commands for plugin '{plugin_id}'",
            "children": {},
        }
        for func in commands:
            meta = getattr(func, "__myctl_cmd__", {})
            path = str(meta.get("path", "")).split()
            if not path:
                continue

            current = root
            for index, part in enumerate(path):
                is_last = index == len(path) - 1
                # We materialize nodes progressively so `foo bar baz` creates
                # group/group/command in a single pass.
                current_children = cast(
                    dict[str, CommandNode], current.setdefault("children", {})
                )
                if part not in current_children:
                    flag_meta = cast(
                        list[FlagSpec] | None, getattr(func, "__myctl_flags__", None)
                    )
                    help_text = str(meta.get("help", ""))
                    current_children[part] = CommandTreeBuilder._command_node(
                        help_text,
                        type_="command" if is_last else "group",
                        children={} if not is_last else None,
                        flags=flag_meta if is_last else None,
                    )
                current = current_children[part]
        return root

    @staticmethod
    def build_full_schema(
        system_commands: dict[str, str],
        system_handlers: dict[str, Any],
        plugins: dict[str, Any],
    ) -> dict[str, CommandNode]:
        """Build full client-visible command schema (system + plugins).

        Args:
            system_commands: Dict of command_name -> help_text for daemon commands.
            system_handlers: Dict of command_name -> handler for daemon commands.
            plugins: Dict of plugin_id -> LoadedPlugin for user plugins.

        Returns:
            Full nested schema tree ready for client consumption.
        """
        schema: dict[str, CommandNode] = {}

        def insert_path(
            path: list[str], help_text: str, flags: list[FlagSpec] | None = None
        ) -> None:
            current = schema
            for index, part in enumerate(path):
                is_last = index == len(path) - 1
                node = current.get(part)
                if node is None:
                    node = CommandTreeBuilder._command_node(
                        help_text if is_last else "",
                        type_="command" if is_last else "group",
                        children={} if not is_last else None,
                        flags=flags if is_last else None,
                    )
                    current[part] = node
                else:
                    if is_last:
                        node["help"] = help_text
                        if flags:
                            node["flags"] = flags
                    if not is_last and node.get("type") == "command":
                        node["type"] = "group"
                        node.setdefault("children", {})
                if not is_last:
                    current = cast(
                        dict[str, CommandNode], node.setdefault("children", {})
                    )

        # Insert daemon built-in commands
        for name, description in system_commands.items():
            path = name.split()
            handler = system_handlers.get(name)
            handler_flags = (
                getattr(handler, "__myctl_flags__", None)
                if handler is not None
                else None
            )
            insert_path(path, description, handler_flags)

        # Each plugin contributes a grouped subtree under its plugin_id.
        for plugin_id, loaded in plugins.items():
            schema[plugin_id] = CommandTreeBuilder.build_plugin_tree(
                getattr(loaded.plugin, "_commands", []), plugin_id
            )

        return schema
