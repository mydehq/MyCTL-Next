"""Internal decorator facade for daemon built-in commands.

Syscommands mirror the plugin authoring experience, but they remain daemon
internals and may import myctld modules directly when needed.
"""

from __future__ import annotations

from .registry import SYSTEM_COMMAND_HANDLERS, SYSTEM_COMMAND_HELP, command, flag, flags

__all__ = [
    "SYSTEM_COMMAND_HANDLERS",
    "SYSTEM_COMMAND_HELP",
    "command",
    "flag",
    "flags",
]
