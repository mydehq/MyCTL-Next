# Plugin SDK Guide

MyCTL is designed to be infinitely extensible via its Python-based Plugin SDK. By leveraging a curated **`myctl.api`** layer, developers can build deep system integrations with a professional, IDE-aware developer experience.

## Pro-Grade SDK Experience

### 1. Namespaced Import Layer
Instead of importing from the daemon's internal modules, you should always use the official **`myctl.api`** SDK. This layer is curated to provide a clean, stable surface while hiding the daemon's complex machinery.

```python
# The Clean way to build plugins
from myctl.api import registry, Request, ok, err
```

### 2. Full IDE Integration
Because the MyCTL daemon self-bootstraps and links itself into its isolated virtual environment, you get first-class autocompletion and type-hinting in any modern IDE (VSCode, PyCharm, etc.).

**How to set up your IDE:**
1.  Open your plugin's directory.
2.  Point your IDE's Python interpreter to: `~/.local/share/myctl/venv/bin/python`.
3.  **Result**: `from myctl.api import ...` will instantly resolve with documentation hovers and jump-to-definition.

## Building your first plugin

### 1. Create the Plugin Structure
Every plugin lives in its own directory within the XDG data home:
`~/.local/share/myctl/plugins/my-plugin/`

### 2. Define `plugin.toml`
This file defines your plugin's metadata and dependencies.
```toml
[plugin]
name = "weather"
description = "Get local meteorological data"
author = "soymadip"
version = "1.0.0"
deps = ["requests"] # Daemon will auto-install these during bootstrap
```

### 3. Create `plugin.py`
This is your entry point where you register your commands.
```python
from myctl.api import registry, Request, ok

@registry.add_cmd("weather", help="Get current sky condition")
async def sky_info(req: Request):
    # Any heavy logic should be async-first
    return ok("Sunny with a chance of code.")
```

## Standard API Reference

| Component | Description |
| :--- | :--- |
| **`registry.add_cmd(path, help)`** | Decorator to register an async function as a command. |
| **`Request`** | An object containing `args`, `env`, and `cwd` from the user. |
| **`ok(data)`** | Serialized success response with terminal output. |
| **`err(message)`** | Serialized error response with an error message. |

## Why "Async-First"?

Everything in the MyCTL daemon runs on a high-performance `asyncio` loop. This ensures that a single long-running task (like a weather API call) doesn't block the daemon from responding to other commands (like an audio mute). Always use `async def` for your command handlers!
