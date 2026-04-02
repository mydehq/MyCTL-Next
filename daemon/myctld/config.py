"""Runtime constants and XDG-derived paths for myctld.

This module centralizes filesystem and version constants so all runtime code
shares a single source of truth for state, config, cache, runtime socket, and
plugin discovery locations.

It uses ``from __future__ import annotations`` to keep typing references
lightweight and consistently postponed across daemon modules.

Read before: daemon/myctld/__main__.py; read after: daemon/myctld/ipc.py
"""

from __future__ import annotations

from pathlib import Path

from platformdirs import (
    user_cache_dir,
    user_config_dir,
    user_runtime_dir,
    user_state_dir,
)

APP_NAME = "myctl"
DAEMON_NAME = "myctld"
APP_VERSION = "0.2.0"
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DAEMON_DIR = PACKAGE_ROOT
# XDG-based state/config/cache/runtime separation keeps filesystem layout
# predictable across distros and compatible with desktop environment norms.
STATE_DIR = Path(user_state_dir(APP_NAME))
CONFIG_DIR = Path(user_config_dir(APP_NAME))
CACHE_DIR = Path(user_cache_dir(APP_NAME))
# Socket path intentionally uses myctl runtime dir so client and daemon share
# one contract regardless of where daemon package is installed.
RUNTIME_DIR = Path(user_runtime_dir(APP_NAME))
SOCKET_PATH = RUNTIME_DIR / f"{DAEMON_NAME}.sock"
LOG_FILE = STATE_DIR / f"{DAEMON_NAME}.log"
# Plugin search path points to repository-level plugins during development.
PLUGIN_SEARCH_PATHS = [PACKAGE_ROOT.parent / "plugins"]
