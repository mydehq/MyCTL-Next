# Plugin SDK Guide

Developing a plugin for MyCTL is designed to be frictionless. By utilizing the **Zero-Boilerplate SDK**, developers can expose complex system functionality to the CLI without writing any networking or parsing logic.

## 🏗️ Technical Foundation

### 1. The Plugin ID (Implicit Identity)

The directory name where your plugin resides is its **Plugin ID**. This ID becomes the root command namespace for all functions defined within that folder.

Example: If your folder is `plugins/weather/`, your commands will automatically be prefixed with `myctl weather`.

### 2. The Sandbox Model

Plugins are executed inside a dedicated `uv` virtual environment. The daemon handles:

- **Dependency Management**: Automatically mirrors requirements defined in the plugin's metadata.
- **Isolation**: Each plugin is loaded as an independent module via `importlib`.

## 📦 Anatomy of a Plugin

Every plugin must contain two mandatory files:

### `pyproject.toml`

The standard Python manifest. MyCTL reads `[project]` for packaging metadata and `[tool.myctl]` for engine-specific configuration.

```toml
[project]
name = "weather"               # MUST match the plugin directory name exactly
version = "1.0.0"
description = "Quickly fetch current weather data"  # root group help
dependencies = ["requests", "rich"]

[tool.myctl]
api_version = "2.0.0"           # Must match the running daemon's major version
entry = "main.py"               # Entry point (omit to use default: main.py)

[tool.myctl.groups]             # Optional: help text for sub-command groups
"forecast"        = "Multi-day forecast commands"
"forecast daily"  = "Daily breakdown"    # nested group — space-separated path
```

| Field          | Table                 | Purpose                                                                                       |
| -------------- | --------------------- | --------------------------------------------------------------------------------------------- |
| `name`         | `[project]`           | **Must equal the directory name.** Mismatches cause the plugin to be rejected at load time.   |
| `version`      | `[project]`           | Semantic version                                                                              |
| `description`  | `[project]`           | Help text for the plugin's **root** command group                                             |
| `dependencies` | `[project]`           | Installed by `uv` automatically                                                               |
| `api_version`  | `[tool.myctl]`        | SDK compatibility check                                                                       |
| `entry`        | `[tool.myctl]`        | Entry point file (default: `main.py`)                                                         |
| `"<path>"`    | `[tool.myctl.groups]` | Help text for a sub-group (space-separated path, e.g. `"volume set"`)                        |

### `main.py` (The Entry Point)

This is where you define your logic using the `@registry` decorator.

```python
from myctl.api import registry, ok, err

@registry.add_cmd("get", help="Fetch the current temperature")
async def get_weather(req):
    # Your async logic here
    return ok("The temperature is 22°C")
```

## 🛠️ The `registry` API

The SDK is exposed via `myctl.api`. Import what you need:

```python
from myctl.api import registry, ok, err, Request
```

### `@registry.add_cmd(path, help="")`

Registers an `async` function as a CLI command under the plugin's namespace.

- **`path`**: The subcommand name. Use **space-separated strings** for deep nesting — the engine builds the full hierarchy automatically.
- **`help`**: Description shown in `myctl <plugin> --help`.

```python
@registry.add_cmd("volume set", help="Set volume to a percentage")
async def volume_set(req: Request):
    ...
```

This registers `myctl <plugin> volume set` as a command, with `volume` automatically created as an intermediate group.

### The `req` Object

Every handler receives a `Request` object:

| Field  | Type             | Description                                           |
| ------ | ---------------- | ----------------------------------------------------- |
| `path` | `list[str]`      | Full command path (e.g. `["audio", "volume", "set"]`) |
| `args` | `list[str]`      | Raw positional arguments from the user                |
| `cwd`  | `str`            | Working directory where the user ran `myctl`          |
| `env`  | `dict[str, str]` | User's environment variables                          |

### Argument Parsing (`req.args`)

Arguments are passed as a raw list — parse them manually:

```python
@registry.add_cmd("volume set", help="Set volume to a percentage")
async def volume_set(req: Request):
    if not req.args:
        return err("Usage: myctl audio volume set <0-100>")
    level = req.args[0]
    return ok(f"Volume set to {level}%")
```

### Response Helpers: `ok()` and `err()`

Always return one of the two SDK response helpers — never return a raw value directly.

```python
from myctl.api import ok, err

# Success — data can be a string, dict, or list
return ok("Done")
return ok({"level": 50, "muted": False})

# Failure — sets exit_code to 1 by default (overridable)
return err("Device not found")
return err("Permission denied", exit_code=3)
```

The `exit_code` is passed back to the shell, enabling script integration via `$?`.


### `@registry.on_load`

Registers an `async` function to run **once** after the plugin has been fully loaded, during the daemon's boot phase. Use it for one-time setup like connecting to hardware or verifying system state.

```python
from myctl.api import registry

pulse = None

@registry.on_load
async def setup():
    global pulse
    import pulsectl_asyncio
    pulse = pulsectl_asyncio.PulseAsync("myctl-audio")
    await pulse.connect()
```

If the hook raises an exception, the error is logged and the daemon continues — the plugin remains loaded but the setup is skipped.

## 📋 Logging

Plugins have access to a named logger that writes to the daemon's log file (`$XDG_STATE_HOME/myctl/daemon.log`). The logger is automatically scoped to `myctl.plugin.<plugin_id>` during discovery.

```python
from myctl.api import logger

@registry.add_cmd("status")
async def get_status(req):
    logger.info("Fetching sink status...")
    logger.debug("req.args: %s", req.args)
    return ok("Sink is online")
```

For plugins that prefer an explicit name, use `get_logger`:

```python
from myctl.api import get_logger
log = get_logger("audio")  # → myctl.plugin.audio
```


## 🖥️ Return Values & Client Rendering

Plugins return plain Python objects. The **Go client** is responsible for rendering them to the terminal after they travel through the IPC response — the plugin itself has no knowledge of the terminal.

### Strings

Return a plain string and it's printed directly to `stdout`, no formatting applied.

```python
@registry.add_cmd("hello")
async def hello(req):
    return "Hello from MyCTL!"
```

```text
Hello from MyCTL!
```

### Structured Data (Dicts & Lists)

Return a `dict` or `list` and the Go Proxy automatically **pretty-prints it as JSON**. This makes your output pipeable to tools like `jq` with no extra effort.

```python
@registry.add_cmd("info")
async def get_info(req):
    return {
        "status": "active",
        "version": "1.0.2",
        "tags": ["prod", "system"]
    }
```

```json
{
  "status": "active",
  "version": "1.0.2",
  "tags": ["prod", "system"]
}
```

## 🛠️ Development Workflow

1. **Create the Folder**: `mkdir plugins/myplugin`
2. **Setup SDK Links**: Run `myctl sdk setup` to allow your IDE to resolve `myctl.api` imports.
3. **Write Code**: Define your commands in `main.py`.
4. **Instant Hot-Reload**: The daemon detects changes in plugin directories. Simply run `myctl myplugin <command>` to see the new logic in action.
