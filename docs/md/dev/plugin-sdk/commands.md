# Command & Flag Registration

This page documents how to define commands and flags in a plugin.

The API is declarative: you create one `Plugin` instance, decorate handlers, and MyCTL builds the CLI surface from that metadata.

## Registering Commands

Commands are registered with the `@plugin.command` decorator.

```python
from myctl.api import Plugin, Context

plugin = Plugin()

@plugin.command("wifi list", help="List available networks")
async def list_networks(ctx: Context):
    return ctx.ok(["wlan0", "wlan1"])
```

`@plugin.command(path, help="help text")`

- `path`: Space-separated command path within the plugin namespace.
- `help`: Short description displayed in CLI help output.

## Declarative Flags

Flags are registered with `@plugin.flag(...)` or `@plugin.flags([...])`.

MyCTL normalizes and exposes them in the command schema so the client can render help and parse flags consistently.

### Positional Signature

`@plugin.flag(name, short, default, help, *, flag_type=None, choices=None, required=False)`

| Argument    | Description                                                            |
| :---------- | :--------------------------------------------------------------------- |
| `name`      | Long flag name. Prefixes `--` automatically and normalizes `_` to `-`. |
| `short`     | Short alias. Prefixes `-` automatically.                               |
| `default`   | Default value. If omitted, the flag is treated as required.            |
| `help`      | Usage description shown in CLI help.                                   |
| `flag_type` | Optional explicit type override.                                       |
| `choices`   | Optional allowed values list.                                          |
| `required`  | Marks the flag as required even when a default is present.             |

### Inference and Normalization

1. If `default` is omitted, the flag is required.
2. If a default is provided, the flag is optional.
3. The type is inferred from `default` unless `flag_type` is provided.
4. Long names automatically receive `--`; short names receive `-`.

## Examples

### Required Flag

```python
@plugin.flag("output", "o", help="Where to save", required=True)
```

### Optional Flag with Default

```python
@plugin.flag("port", "p", 80, "Service port")
```

### Boolean Toggle

```python
@plugin.flag("force", "f", False, "Force execution")
```

### Multiple Flags

```python
@plugin.flags([
    {"name": "format", "short": "f", "default": "text", "help": "Output format"},
    {"name": "verbose", "short": "v", "default": False, "help": "Verbose output"},
])
```

`choices` restricts the flag to a fixed set of allowed values.

- `--format text` is valid
- `--format json` is valid
- `--format xml` returns a validation error

## Built-in Daemon Commands

Daemon built-ins use the same declarative pattern as plugins, but they live in `daemon/myctld/syscmds/`.

- each file in `syscmds/` defines one or more handlers
- decorators register handlers at import time
- the package loader imports modules automatically so registration happens without a manual registry list

```python
from myctl.api.context import Context, Response

from .registry import command, flag


@command("plugin init", help="Initialize a new plugin")
@flag("name", "n", help="Plugin name", required=True)
async def plugin_init(ctx: Context, registry) -> Response:
    return ctx.ok("plugin created")
```

That same decorator style keeps daemon built-ins and plugins visually consistent while still keeping the daemon engine private.
