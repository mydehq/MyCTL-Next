# Plugin SDK: Building System Extensions

MyCTL is designed to be an extensible platform for desktop automation. By utilizing the **`myctl.api`** Python package, developers can create sophisticated system-native integrations with minimal boilerplate.

## ⭐ The MyCTL SDK Overview

The SDK provides a curated developer experience that bridges the Python daemon with the Client. It features:

- **Zero-Config Injection**: No manual environment setup required for plugins.
- **IPC Wrapping**: Automatic JSON-IPC request/response management.
- **Type Hinting**: Full autocompletion support for IDEs.
- **Lifecycle Hooks**: Professional-grade `@on_load` and `@periodic` hooks.

---

## 🏗 Plugin Structure

Every MyCTL plugin must follow a strict directory-based identity.

```text
plugins/
└── sysinfo/             <-- Plugin ID (must match directory)
    ├── pyproject.toml   <-- Manifest (Dependencies & Metadata)
    └── main.py          <-- Logic (Command handlers)
```

### 1. The Manifest (`pyproject.toml`)

MyCTL reads `[project]` for packaging metadata and `[tool.myctl]` for engine-specific configuration.

> [!IMPORTANT]
> **Name Enforcement**: The `[project].name` field MUST match the directory name exactly.

```toml
[project]
name = "sysinfo"               # MUST match the directory name
version = "1.0.0"
description = "System Monitor"  # Root group help text
dependencies = ["psutil>=5.9.0"]

[tool.myctl]
api_version = "{{metadata.versions.api_ver}}"
entry = "main.py"               # Entry point (default: main.py)

[tool.myctl.groups]             # Optional: help text for sub-groups
"cpu info" = "CPU detailed statistics"
```

| Field          | Table                 | Purpose                                                                                     |
| -------------- | --------------------- | ------------------------------------------------------------------------------------------- |
| `name`         | `[project]`           | **Must equal the directory name.** Mismatches cause the plugin to be rejected at load time. |
| `description`  | `[project]`           | Help text for the plugin's **root** command group                                           |
| `dependencies` | `[project]`           | Installed by `uv` automatically into the daemon's sandbox.                                  |
| `api_version`  | `[tool.myctl]`        | SDK compatibility check (e.g. `1.0.0`).                                                     |
| `"<path>"`     | `[tool.myctl.groups]` | Help text for a sub-group (space-separated path, e.g. `"cpu info"`)                         |

### 2. Dependency Management: The UV Advantage

MyCTL utilizes **`uv`** to automatically resolve and install plugin dependencies at discovery time.

- **Isolation**: Dependencies are synced directly into the daemon's managed virtual environment (`{{metadata.paths.venv}}`).
- **Speed**: `uv` ensures that checking for updates or installing new requirements happens in milliseconds during the daemon's Cold Boot.

---

## 🛠 Command Registration

Commands are registered using the `registry` proxy from the `myctl.api` package.

```python
from myctl.api import registry, ok, err, Request

@registry.add_cmd(path="cpu load", help="Displays current CPU usage")
async def get_cpu_load(req: Request):
    import psutil
    usage = psutil.cpu_percent(interval=1)
    return ok(f"CPU Load: {usage}%")
```

### The `Request` Object

Every handler receives a `req` object containing context from the user's terminal:

| Field  | Type             | Description                                           |
| ------ | ---------------- | ----------------------------------------------------- |
| `path` | `list[str]`      | Full command path (e.g. `["sysinfo", "cpu", "load"]`) |
| `args` | `list[str]`      | Raw positional arguments from the user                |
| `cwd`  | `str`            | Directory where the user executed the command         |
| `env`  | `dict[str, str]` | User's environment variables (e.g. `$DISPLAY`)        |

### Response Helpers: `ok()` and `err()`

> [!IMPORTANT]
> **Mandatory Returns**: Every handler MUST return one of the SDK response helpers. Raw strings, integers, or `None` are strictly prohibited and will result in a **System Error**.

```python
# Success: Data can be a string, dict, or list
return ok("Task complete")
return ok({"status": "online", "tasks": 5})

# Failure: Sets CLI exit_code to 1 by default
return err("Device not found")
return err("Permission denied", exit_code=13)
```

---

## 📋 Logging & Observability

Plugins have access to a scoped logger that writes to the central daemon log file (`{{metadata.paths.logs}}`).

```python
from myctl.api import logger

@registry.add_cmd("status")
async def get_status(req):
    logger.info("Fetching sink status...")
    logger.debug("req.args: %s", req.args)
    return ok("Online")
```

---

## 🚀 Lifecycle Hooks

### `@registry.on_load`

Registers an `async` function to run **once** during the daemon's boot phase after the plugin is loaded. Use it for initialization (e.g., establishing hardware connections).

```python
@registry.on_load
async def init_hardware():
    logger.info("Connecting to system sensors...")
```

> [!IMPORTANT]
> **Fail-Fast Boot**: If any `@on_load` hook fails, the **entire plugin is rejected** for the session and hidden from the CLI. This ensures system stability. If your initialization is "optional", wrap it in a `try/except` block.

### `@registry.periodic(seconds=N)`

Registers an `async` function to run in the **background** every `N` seconds. These tasks begin execution once the plugin is fully loaded and `on_load` has completed.

- **Use case**: Polling hardware, refreshing API tokens, monitoring system state.
- **Note**: Periodic tasks run in parallel; ensure they are lightweight and do not block the event loop.

```python
@registry.periodic(seconds=60)
async def check_battery():
    # Runs every minute in the background
    level = await get_battery_level()
    if level < 15:
        logger.warning(f"Battery low: {level}%")
```

> [!NOTE]
> **Resilient Runtime**: If a background task crashes, it is logged, but the engine **retries** the task at its next defined interval.

---

## 🖥️ Client Rendering

The **Client** automatically renders return values based on their type:

- **Strings**: Printed directly to `stdout`.
- **Dicts/Lists**: Automatically pretty-printed as **JSON**, making them pipeable to tools like `jq`.

---

## ✅ Development Workflow

1.  **Create Plugin**: `mkdir plugins/myplugin`
2.  **Declare Dependencies**: Add requirements to `pyproject.toml`.
3.  **Sync SDK**: Run `myctl sdk setup` to allow your IDE to resolve `myctl.api`.
4.  **Edit & Test**: Modify your plugin code, then reload:
    ```bash
    myctl restart                  # Kill the cached daemon
    myctl <plugin_id> <command>    # Triggers fresh Cold Boot
    ```

> [!WARNING]
> **Plugins are cached in RAM.** The daemon loads all plugin code into memory once during the Cold Boot phase. Editing a plugin's `main.py` on disk has **no effect** on the running daemon. You must run `myctl restart` (or `myctl stop`) to flush the in-memory cache and force a reload on the next invocation.
