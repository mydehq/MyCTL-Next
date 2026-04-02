"""Plugin discovery manager.

Scans configured plugin roots, loads valid plugins, and stores discovered
runtime metadata for registry wiring.

Discovery is intentionally best-effort: a broken plugin should not prevent the
daemon from starting with healthy plugins.

The module uses postponed annotation evaluation to keep type hints expressive
without introducing import-time coupling.

Read before: daemon/myctld/plugin/loader.py; read after: daemon/myctld/plugin/models.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .loader import load_plugin
from .models import LoadedPlugin

log = logging.getLogger("myctl.plugin.manager")

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PluginManager:
    """Discover and cache loaded plugins across search paths."""

    search_paths: list[Path]
    plugins: dict[str, LoadedPlugin] = field(default_factory=dict)

    def discover(self) -> dict[str, LoadedPlugin]:
        """Load plugins from search paths; later entries cannot overwrite IDs."""
        discovered: dict[str, LoadedPlugin] = {}

        for search_path in self.search_paths:
            # Missing tiers are normal (for example user-level plugins may not exist).
            if not search_path.exists():
                continue
            for plugin_root in sorted(
                path for path in search_path.iterdir() if path.is_dir()
            ):
                try:
                    loaded = load_plugin(plugin_root)
                except Exception as exc:
                    # Discovery is best-effort: one broken plugin should not block the
                    # daemon from serving all other plugins.
                    logger.warning(
                        "failed to load plugin %s: %s",
                        plugin_root.name,
                        exc,
                    )
                    continue
                # Last discovered plugin with the same ID wins by assignment.
                # Search path order therefore defines precedence policy.
                discovered[loaded.plugin_id] = loaded
                logger.info(
                    "loaded plugin %s from %s",
                    loaded.plugin_id,
                    loaded.entrypoint,
                )

        self.plugins = discovered
        return discovered
