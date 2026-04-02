# Daemon Commands

This page explains how built-in daemon commands work in MyCTL and how to add new ones.

Daemon commands are not plugins. They are internal `myctld` modules, but they use the same decorator-driven authoring style as plugins so the command surface feels consistent.

---

## 1. What A Daemon Command Is

A daemon command is a built-in action handled directly by the Python daemon.

Examples:

- `status`
- `schema`
- `logs`
- `start`
- `stop`
- `restart`
- `plugin reload`
- `sdk`

These commands live under `daemon/myctld/syscmds/` and are discovered automatically when the daemon starts.

Unlike plugins, daemon commands:

- do not need a plugin manifest
- do not need a `Plugin()` object
- can import `myctld` internals directly
- are part of the daemon's own runtime, not a user extension layer

---

## 2. How Discovery Works

The `daemon/myctld/syscmds/` package uses import-based discovery.

At startup, `daemon/myctld/syscmds/__init__.py` imports every real command module in the package and skips support files:

- `registry.py` stays private to the decorator implementation
- `api.py` is the public import facade for command authors
- underscore-prefixed helpers such as `_helpers.py` are ignored automatically

That means adding a new command is usually just:

1. create a new module in `daemon/myctld/syscmds/`
2. decorate a handler
3. let the package import it

---

## 3. The Authoring Shape

Daemon commands use a decorator-based shape that should feel familiar if you already know the plugin SDK.

### Basic Command

```python
from myctl.api.context import Context, Response
from myctl.api.style import make_style

from .api import command, flag


@command("health", help="Show daemon health")
@flag("verbose", "v", default=False, help="Show extra runtime details")
async def health(ctx: Context, registry) -> Response:
    style = make_style(ctx.terminal)
    if ctx.flags.get("verbose"):
        return ctx.ok(
            style.table(
                [
                    ["Status", style.success("healthy")],
                    ["Plugins", str(len(registry.plugins))],
                ]
            )
        )
    return ctx.ok(style.success("healthy"))
```

### Nested Command Path

Built-in commands can also use space-delimited paths:

```python
@command("plugin reload", help="Reload one or more plugins")
@flag("all", "a", default=False, help="Reload every plugin")
@flag("force", "f", default=False, help="Reload even if unchanged")
async def plugin_reload(ctx: Context, registry) -> Response:
    if ctx.flags.get("all"):
        return ctx.ok({"reloaded": "all"})

    target = ctx.args[0] if ctx.args else None
    if target is None:
        return ctx.err("missing plugin id", exit_code=2)

    return ctx.ok({"reloaded": target, "force": ctx.flags.get("force", False)})
```

The command path is metadata, not runtime branching. The registry reads the path and dispatches it automatically.

---

## 4. Flags

Flags are attached to the handler function with the same decorator style used by plugins.

### Single Flag

```python
@command("logs", help="Show daemon logs")
@flag("level", "l", default="info", help="Minimum log level")
async def logs(ctx: Context, registry) -> Response:
    level = ctx.flags.get("level", "info")
    return ctx.ok(f"logs at {level}")
```

### Multiple Flags

```python
@command("start", help="Start daemon")
@flags([
    {"name": "background", "short": "b", "default": False, "help": "Run in background"},
    {"name": "force", "short": "f", "default": False, "help": "Restart if already running"},
])
async def start(ctx: Context, registry) -> Response:
    ...
```

Flag rules:

- long names become `--kebab-case`
- short names become `-x`
- default values determine the type unless overridden
- help text is carried into schema/help output
- reserved or invalid names should fail early during registration

---

## 5. Internal Access

Daemon commands are internal code, so they can use daemon modules directly.

That is the main difference from plugins.

A syscommand can import:

- registry state
- config helpers
- logging helpers
- plugin manager state
- IPC helpers
- runtime services

That does not mean the code should be messy. It means the internal command layer should stay small and direct, while still using the shared decorator metadata model.

The import facade at `daemon/myctld/syscmds/api.py` exists only so command files read cleanly:

```python
from .api import command, flag, flags
```

The implementation still lives in `registry.py`.

---

## 6. Dispatch Flow

When a user runs a daemon command, the flow is:

1. the Go client sends a request over IPC
2. the daemon builds a `Context`
3. the registry looks up the longest matching built-in command path
4. the handler runs
5. the response is normalized and returned to the client

Built-in command lookup is path-based, so nested commands like `plugin reload` or `sdk setup` work the same way as one-word commands.

Flags are parsed from `ctx.flags`, and positional leftovers stay in `ctx.args`.

The registry does not need to know which command file defined the handler. It only needs the metadata that the decorators attached.

---

## 7. Reserved Names

Built-in command names are a reserved namespace.

That means a plugin cannot claim `status`, `schema`, `logs`, `plugin reload`, or any other daemon command path.

The daemon validates conflicts against the live built-in registry, so the built-in command list is the source of truth.

---

## 8. Files You Add

A new daemon command usually looks like this:

```text
daemon/myctld/syscmds/api.py
daemon/myctld/syscmds/status.py
daemon/myctld/syscmds/logs.py
daemon/myctld/syscmds/plugin.py
daemon/myctld/syscmds/_helpers.py
```

Rule of thumb:

- command modules: no leading underscore
- private helpers: leading underscore
- `api.py`: import facade for command authors
- `registry.py`: decorator implementation and registration state

---

## 9. Practical Example

If you want a new `health` command, you add a file like this:

```python
from myctl.api.context import Context, Response
from myctl.api.style import make_style

from .api import command, flag


@command("health", help="Check daemon health")
@flag("json", "j", default=False, help="Return JSON output")
async def health(ctx: Context, registry) -> Response:
    style = make_style(ctx.terminal)
    if ctx.flags.get("json"):
        return ctx.ok({"status": "healthy"})
    return ctx.ok(style.success("healthy"))
```

That is the whole shape:

- create a file
- add decorators
- use `ctx.flags` and `ctx.args`
- import daemon internals if needed
- let auto-discovery register it

---

## 10. Summary

Daemon commands are internal built-ins, but they are written with a plugin-like authoring experience.

That gives you:

- consistent command and flag metadata
- automatic discovery
- direct access to daemon internals
- a much smaller surface than the public plugin SDK

For the lower-level runtime details, read [Core Engine & Registry](../technical/core-runtime/registry).
