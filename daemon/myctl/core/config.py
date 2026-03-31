import os
import sys
from pathlib import Path
from platformdirs import user_runtime_dir, user_state_dir, user_data_dir

# ── Project Metadata ─────────────────────────────────────────────────────────

APP_NAME = "myctl"
APP_VERSION = "0.2.0"
API_VERSION = "2.0.0"

# ── Dynamic Path Discovery ───────────────────────────────────────────────────

# The root directory of the myctld package (contains 'myctl/')
DAEMON_DIR = Path(__file__).resolve().parent.parent.parent
# The interpreter currently running the daemon (inside the uv venv)
VENV_PYTHON = Path(sys.executable)

# ── XDG-Compliant Path Resolution ────────────────────────────────────────────

# Socket: Primary is $XDG_RUNTIME_DIR/myctld.sock
# Fallback: /tmp/myctl-$UID.sock
RUNTIME_DIR = Path(user_runtime_dir(appname=APP_NAME, ensure_exists=True))
SOCKET_PATH = RUNTIME_DIR / "myctld.sock"

if not os.access(RUNTIME_DIR, os.W_OK):
    SOCKET_PATH = Path(f"/tmp/myctl-{os.getuid()}.sock")

# Logs: $XDG_STATE_HOME/myctl/daemon.log
LOG_DIR = Path(user_state_dir(appname=APP_NAME, ensure_exists=True))
LOG_FILE = LOG_DIR / "daemon.log"

USER_PLUGINS_PATH = Path(user_data_dir(appname=APP_NAME)) / "plugins"

# Plugins: Tiered Discovery (Highest to Lowest Priority)
PLUGIN_SEARCH_PATHS = [
    DAEMON_DIR.parent / "plugins",    # Dev Level (Project Root)
    USER_PLUGINS_PATH,                # User Level
    Path("/usr/share/myctl/plugins")  # System Level
]

def ensure_user_plugins():
    """Ensure the user plugin directory exists."""
    USER_PLUGINS_PATH.mkdir(parents=True, exist_ok=True)
