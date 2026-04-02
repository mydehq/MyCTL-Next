"""Data models shared by plugin loader/manager/registry.

These lightweight dataclasses carry normalized plugin metadata between
discovery, registry wiring, and command dispatch.

The module opts into postponed annotation evaluation so type hints remain
readable and import-order independent.

Read before: daemon/myctld/plugin/manager.py; read after: daemon/myctld/plugin/__init__.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from myctl.api.plugin import Plugin


@dataclass(slots=True)
class LoadedPlugin:
    """Runtime metadata for one successfully loaded plugin."""

    # Stable identifier derived from plugin directory name.
    plugin_id: str
    # Root directory containing plugin package files.
    root: Path
    # Entry module executed by the loader (main.py).
    entrypoint: Path
    # SDK Plugin object used by registry for command dispatch.
    plugin: Plugin
    # Optional loaded module object, useful for debugging/introspection.
    module: ModuleType | None = None
