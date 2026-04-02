# Plugin Loading

This page explains how MyCTL loads a plugin module from disk and turns it into runtime command handlers.

Plugin loading is a package-context import problem. The daemon has to:

- find the plugin directory
- validate its metadata
- isolate it in a unique module namespace
- import its `main.py`
- register decorators from that module
- keep the plugin available for dispatch

That is the whole job of plugin loading.

---

## 1. What A Plugin Is At Runtime

A plugin is a directory on disk with a `pyproject.toml` and a `main.py` entry module.

The directory name is the plugin ID. The manifest name must match the directory name exactly.

The daemon treats each plugin as its own import namespace so modules with common names do not collide.

---

## 2. Namespaced Imports

The daemon loads plugin code as if it lived under a package namespace such as `myctl_plugins.weather`.

That means these are separate modules even if they share the same source file names:

- `myctl_plugins.weather.main`
- `myctl_plugins.audio.main`

The plugin namespace is the reason relative imports inside a plugin stay isolated and predictable.

For example, `from .src.service import fetch_weather` resolves inside the plugin’s own namespace, not against another plugin.

---

## 3. On-Disk Layout

A plugin usually looks like this:

```text
plugins/weather/
├── pyproject.toml
├── main.py
└── src/
    ├── __init__.py
    └── service.py
```

The rules are simple:

- `main.py` registers commands and hooks
- `src/` holds implementation code
- `pyproject.toml` describes the package and its dependencies
- the folder name and `[project].name` must match

---

## 4. Loading Flow

The daemon loads a plugin in a fixed order:

1. discover the directory from the configured search tiers
2. read and validate `pyproject.toml`
3. check naming and API compatibility rules
4. create the plugin module namespace
5. import `main.py`
6. execute decorator registration
7. run optional startup hooks

If a step fails, that plugin is rejected and the daemon keeps running.

The key point is that plugin loading happens before command dispatch, so runtime execution only needs to read the already-registered metadata.

---

## 5. Why Namespace Loading Exists

Namespace loading prevents accidental cross-plugin imports.

Without it, two plugins could both contain files named `service.py` or `handlers.py`, and one plugin might accidentally import the other’s module.

With namespace loading:

- imports stay local to the plugin
- IDEs can resolve relative imports correctly
- module names remain deterministic
- the daemon can keep loading plugins without hardcoded per-plugin import hacks

This is a load-time isolation strategy, not a runtime sandbox.

---

## 6. What main.py Does

`main.py` should stay narrow.

Its job is to register commands, flags, and hooks, then hand off real logic to `src/` modules.

Example:

```python
from myctl.api import Plugin, Context
from .src.service import fetch_weather

plugin = Plugin()

@plugin.command("current", help="Get current weather")
async def cmd_current(ctx: Context):
    city = ctx.args[0] if ctx.args else "Kolkata"
    return ctx.ok(await fetch_weather(city))
```

The point of this pattern is to keep plugin registration obvious and keep business logic out of the entry module.

---

## 7. What src/ Does

`src/` contains the actual implementation.

This is where network calls, parsing, transformations, and internal helpers belong.

Example:

```python
import httpx


async def fetch_weather(city: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://wttr.in/{city}?format=j1", timeout=10.0)
        response.raise_for_status()

    current = response.json()["current_condition"][0]
    return {
        "city": city,
        "temp_c": current["temp_C"],
        "condition": current["weatherDesc"][0]["value"],
    }
```

That separation keeps command registration easy to scan and implementation easy to test.

---

## 8. Dependency Sync

If a plugin declares dependencies, the daemon syncs them before import.

That means the plugin’s imports are available by the time `main.py` runs.

The important behavior is:

- dependency sync happens before module import
- a dependency failure rejects only that plugin
- other plugins can still load

This is one of the reasons plugin loading is separate from dispatch.

---

## 9. Error Handling

Loading errors are contained to the plugin that failed.

Typical failures include:

- invalid metadata
- missing `main.py`
- bad imports
- dependency sync errors
- decorator or hook exceptions during initialization

The daemon logs the failure and continues loading the rest of the plugin set.

---

## 10. What Loading Does Not Do

Plugin loading does not:

- dispatch commands
- render CLI output
- parse IPC requests
- manage daemon lifecycle

Those responsibilities live elsewhere in the daemon.

---

## 11. Practical Debugging

If a plugin command does not appear, check:

- the plugin folder is in a valid discovery path
- `pyproject.toml` exists
- `[project].name` matches the folder name exactly
- `main.py` imports are valid
- the plugin registered commands during import

If imports fail, check:

- relative imports are used inside the plugin
- `src/__init__.py` exists when needed
- the symbols are actually exported by the imported module

---

## 12. Summary

Plugin loading is the part of the daemon that turns a plugin directory into a live Python namespace with registered commands.

The internal flow is:

- discover
- validate
- sync dependencies
- create namespace
- import entry module
- register decorators
- keep the plugin available for dispatch

That is the core loading contract.

