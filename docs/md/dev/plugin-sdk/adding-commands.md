# Command & Flag Registration

This page documents how to define commands and flags in a plugin.  


**The API is declarative**: you register handlers on a `Plugin` instance, and MyCTL builds the CLI surface from that metadata.

## Registering Commands

Commands are registered with the `@plugin.command` decorator.

```python
from myctl.api import Plugin, Context
from .src.wifi import list_network_names

plugin = Plugin("wifi")

@plugin.command("list", help="List available networks")
async def list_networks(ctx: Context):
    return ctx.ok(list_network_names())
```

`@plugin.command(path, help="help text")`

- **`path`**: Space-separated command path within the plugin hierarchy.
- **`help`**: Short description displayed in CLI help output.

## Declarative Flags

Flags are registered with the `@plugin.flag` decorator.


MyCTL pre-parses and validates them before the handler executes. This keeps handler code focused on business logic rather than argument parsing.

### Positional Signature

`@plugin.flag(name, short, default, help)`

| Argument      | Position | Default    | Description                                                                               |
| :------------ | :------- | :--------- | :---------------------------------------------------------------------------------------- |
| **`name`**    | 1        | Required   | Long flag name (eg "flag"). Prefix `--` is added automatically. Normalizes `_` to `   -`. |
| **`short`**   | 2        | Required   | Shorthand alias (eg, `"f"`). Prefix `-` is added automatically.                           |
| **`default`** | 3        | `REQUIRED` | Default value. If omitted, the flag is marked required.                                   |
| **`help`**    | 4        | `""`       | Usage description for the CLI.                                                            |

### Inference and Normalization

1. If `default` is omitted, the flag is required. If any value is provided, the flag is optional.
2. The flag type is inferred from `default`:
   - `False` or `True` → `bool`
   - `80` → `int`
   - Missing / `None` → `str`
3. Long names automatically receive `--`; shorthands receive `-`.

## Examples

### 1. Required Flag

```python
# Result: --output (str), -o, required
@plugin.flag("output", "o", help="Where to save", required=True)
```

### 2. Optional Flag with Default

```python
# Result: --port (int), -p, default 80
@plugin.flag("port", "p", 80, "Service port")
```

### 3. Boolean Toggle

```python
# Result: --force (bool), -f, toggle
@plugin.flag("force", "f", False, "Force execution")
```

### 4. Keyword-Only Parameters

```python
@plugin.flag("format", "f", "text", "Output format", choices=["text", "json"])
```
`choices` restricts the flag to a fixed set of allowed values.

- `--format text` is valid
- `--format json` is valid
- `--format xml` returns a flag validation error

This is useful when a command supports only a small set of formats or modes & *you want validation to happen before the handler runs*.

## Full Example

```python
from myctl.api import Plugin, Context, log

plugin = Plugin("server")

@plugin.flag("port", "p", 8080, "Port to bind")
@plugin.flag("force", "f", False, "Force restart")
@plugin.command("run", help="Run the server")
async def run_server(ctx: Context):
    if ctx.flags.get("force"):
        log.info("Force restart requested")
    return ctx.ok(f"Server running on :{ctx.flags.get('port')}")
```
