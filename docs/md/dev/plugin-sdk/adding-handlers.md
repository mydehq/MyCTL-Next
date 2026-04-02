# Command & Flag Registration

This page documents how to define commands and flags in a plugin.

**The API is declarative**: you register handlers on a `Plugin` instance, and MyCTL builds the CLI surface from that metadata.

## Prerequisites

Before registering any handler, we need to import SDK, implementations & make instance of `Plugin` class.

```bash
from myctl.api import Plugin, Context
from .src.wifi import list_network_names

plugin = Plugin()
```

## Registering Commands

Commands are registered with the `@plugin.command` decorator.

`@plugin.command(path, help="help text")`

- **`path`**: Space-separated command path within the plugin hierarchy.
- **`help`**: Short description displayed in CLI help output.

<big>Example:</big>

Register `myctl myplugin list` command:

```python
@plugin.command("list", help="List available networks")
async def list_networks(ctx: Context):
    return ctx.ok(list_network_names())  # Return success state with network list
```

## Register Flags

Flags are extra options you attach to a command: ports, modes, paths, booleans, etc.

You register them with `@plugin.flag(...)`.

`@plugin.flag(name, short, *, default=None, help, flag_type=None, choices=None, required=False)`

### Positional Parameters

| Position |  Parameter  | Type  | Default | Description                                                                                 |
| :------: | :---------: | :---- | :-----: | :------------------------------------------------------------------------------------------ |
|    1     | **`name`**  | `str` |    —    | **(required)** <br/> Long flag name (e.g., "port").<br> Prefix `--` is added automatically. |
|    2     | **`short`** | `str` |    —    | **(required)** <br/> Shorthand alias (e.g., "p"). <br> Prefix `-` is added automatically.   |

### Keyworded Parameters

|    Parameter    | Type               | Default | Description                                                                            |
| :-------------: | :----------------- | :-----: | :------------------------------------------------------------------------------------- |
|   **`help`**    | `str`              |    —    | **(required)** <br/> Usage description displayed in CLI help.                          |
|  **`default`**  | `object`           | `None`  | Default value if flag not provided. <br> If omitted, flag is optional with no default. |
| **`flag_type`** | `type \| None`     | `None`  | Explicitly specify the flag's type. Auto-detected from default if not provided.        |
|  **`choices`**  | `Sequence[object]` | `None`  | Restrict flag to a fixed set of allowed values.                                        |
| **`required`**  | `bool`             | `False` | Whether the flag must be provided by the user.                                         |

Below are the commonest scenarios and how to express them.

---

<big><b>Examples:</b></big>

### 1. Optional Flag with a Default

Use this when the flag is **nice to have**, but your command still works without it.

```python
@plugin.flag("port", "p", default=8080, help="Port to bind")
@plugin.command("serve", help="Run HTTP server")
async def serve(ctx: Context):
    port = ctx.flags["port"]  # Always present, falls back to 8080
    ...
```

**User experience:**

- `myctl myplugin serve` → uses port `8080`
- `myctl myplugin serve --port 9090` → uses port `9090`

**Key points:**

- If you supply `default=...`, the flag becomes **optional**.
- The type is inferred from the default (`8080` → `int`).

### 2. Required Flag (User Must Provide It)

Use this when the command **cannot run** without the flag.

```python
@plugin.flag("output", "o", help="Where to save the report", required=True)
@plugin.command("report", help="Generate a report")
async def generate_report(ctx: Context):
    output_path = ctx.flags["output"]  # Guaranteed to be present
    ...
```

**User experience:**

- `myctl myplugin report` → validation error: `--output` is required
- `myctl myplugin report --output /tmp/report.json` → runs normally

**Key points:**

- `required=True` marks the flag as mandatory.
- You typically **don't** provide a default when `required=True`; the value comes from the user.

---

### 3. Boolean Toggle (On/Off Switch)

Use this for simple switches like `--force`, `--verbose`, or `--dry-run`.

```python
@plugin.flag("force", "f", default=False, help="Force execution")
@plugin.command("cleanup", help="Clean temporary files")
async def cleanup(ctx: Context):
    if ctx.flags["force"]:
        ...
```

**User experience:**

- `myctl myplugin cleanup` → `force == False`
- `myctl myplugin cleanup --force` → `force == True`

**Key points:**

- With `default=False`, the type is inferred as `bool`.
- You check the flag as a normal boolean in your handler.

---

### 4. Flag with a Restricted Set of Choices

Use this when only a small number of values make sense (e.g. output formats, modes, levels).

```python
@plugin.flag(
    "format",
    "f",
    default="text",
    help="Output format",
    choices=["text", "json"],
)
@plugin.command("show", help="Show system info")
async def show(ctx: Context):
    format_ = ctx.flags["format"]
    ...
```

**User experience:**

- `myctl myplugin show` → `format == "text"`
- `myctl myplugin show --format json` → `format == "json"`
- `myctl myplugin show --format xml` → validation error (`xml` not in `choices`)

**Key points:**

- `choices=[...]` restricts the set of valid values.
- Validation happens **before** your handler runs.

---

### 5. Controlling the Flag Type Explicitly

Most of the time, the type is inferred from `default`. If you need more control (or no default), you can use `flag_type`.

```python
@plugin.flag("retries", "r", default=3, help="Retry count", flag_type=int)
@plugin.command("sync", help="Sync with server")
async def sync(ctx: Context):
    retries = ctx.flags["retries"]  # int
    ...
```

You usually only need `flag_type` when:

- You don't provide a default but still want a specific type.
- You want to be explicit for readability.

---

### 6. Multiple Flags at Once

If a command has several flags, you can define them in a single block using `@plugin.flags([...])`.

```python
@plugin.flags([
    {
        "name": "port",
        "short": "p",
        "default": 8080,
        "help": "Port to bind",
    },
    {
        "name": "force",
        "short": "f",
        "default": False,
        "help": "Force restart",
    },
])
@plugin.command("run", help="Run the server")
async def run_server(ctx: Context):
    port = ctx.flags["port"]
    force = ctx.flags["force"]
    ...
```

This is just a convenience wrapper around stacking multiple `@plugin.flag(...)` decorators; it behaves the same at runtime.

---

### Summary

- Use `default=...` to make a flag **optional** with a fallback.
- Use `required=True` when the user **must** provide a value.
- Use `choices=[...]` to limit the allowed values.
- Use `flag_type=...` when you want to be explicit about the type.
- Use `@plugin.flags([...])` to keep a bunch of related flags in one place.

## Full Example

```python
from myctl.api import Plugin, Context, log

plugin = Plugin()

@plugin.flags([
    {"name": "port", "short": "p", "default": 8080, "help": "Port to bind"},
    {"name": "force", "short": "f", "default": False, "help": "Force restart"},
])
@plugin.command("run", help="Run the server")
async def run_server(ctx: Context):
    if ctx.flags.get("force"):
        log.info("Force restart requested")
    return ctx.ok(f"Server running on :{ctx.flags.get('port')}")
```
