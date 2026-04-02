"""Plugin module loading helpers for the daemon runtime.

The loader resolves plugin entrypoints from filesystem directories, constructs
namespace packages for safe imports, executes each plugin module, and validates
that a proper SDK ``Plugin`` object is exported.

Postponed annotation evaluation is enabled for clearer type hints without
creating extra import-order constraints.

Read before: daemon/myctld/syscmds.py; read after: daemon/myctld/plugin/manager.py
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

from .models import LoadedPlugin
from myctl.api.plugin import Plugin


def _ensure_package(name: str, package_path: Path) -> None:
    """Ensure namespace package exists in sys.modules for plugin imports."""
    module = sys.modules.get(name)
    if module is None:
        # Create a synthetic package so plugins can use relative imports
        # even though they are loaded from arbitrary filesystem paths.
        module = ModuleType(name)
        module.__path__ = [str(package_path)]
        module.__package__ = name
        sys.modules[name] = module
        return

    if not hasattr(module, "__path__"):
        # Namespace packages need a __path__ list for import resolution.
        module.__path__ = []
    if str(package_path) not in module.__path__:
        # Multiple plugin roots can contribute to one namespace.
        module.__path__.append(str(package_path))


def load_plugin(plugin_root: Path) -> LoadedPlugin:
    """Load one plugin entrypoint and return normalized runtime metadata."""
    entrypoint = plugin_root / "main.py"
    if not entrypoint.exists():
        raise FileNotFoundError(f"Missing plugin entrypoint: {entrypoint}")

    namespace_root = "myctl_plugins"
    plugin_package = f"{namespace_root}.{plugin_root.name}"
    # Prepare import namespace before executing plugin code.
    # This keeps each plugin isolated under myctl_plugins.<plugin_id>.
    _ensure_package(namespace_root, plugin_root.parent)
    _ensure_package(plugin_package, plugin_root)

    spec = spec_from_file_location(f"{plugin_package}.main", entrypoint)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load plugin module from {entrypoint}")

    module: ModuleType = module_from_spec(spec)
    # Execute plugin module exactly once and keep reference in LoadedPlugin.
    spec.loader.exec_module(module)

    plugin = getattr(module, "plugin", None)
    if not isinstance(plugin, Plugin):
        raise RuntimeError(
            f"Plugin entrypoint {entrypoint} must define `plugin = Plugin(...)`"
        )

    # plugin_id is always derived from directory name by project convention.
    return LoadedPlugin(
        plugin_id=plugin_root.name,
        root=plugin_root,
        entrypoint=entrypoint,
        plugin=plugin,
        module=module,
    )
