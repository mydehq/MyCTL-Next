# API Reference

The `{{metadata.pkgs.sdk}}` package provides a fully-typed plugin SDK. All public symbols have explicit type hints for seamless IDE autocomplete and type checking.

Primary SDK objects:

- `Plugin`: Declarative command and root registration.
- `flag`: Metadata helper used in function signatures to declare CLI parameters.
- `Context`: A **Protocol** interface passed to handlers (Structural Typing).
- `log`: A **Logger** for plugin-scoped logging.
- `SimpleContext`: A concrete implementation used for unit testing plugins.

## Import Pattern

```python
from {{metadata.pkgs.sdk}} import Plugin, Context, flag, log
```

## `Plugin`

Create one plugin instance in `main.py`. The plugin identity is implicitly derived from the directory name.

```python
from {{metadata.pkgs.sdk}} import Plugin

plugin = Plugin()
```

### Registration Decorators

#### `@plugin.root`

Registers the primary entry point for the plugin (e.g., `{{metadata.pkgs.sdk}} <plugin>`).

#### `@plugin.command(path, help)`

Registers a subcommand. The `path` is relative to the plugin root (e.g., `{{metadata.pkgs.sdk}} <plugin> <path>`).

---

## Typed Signature Commands

Starting from {{metadata.versions.api}}, command handlers use standard Python function signatures to define their CLI contract. The SDK uses `inspect` to automatically parse, validate, and inject flags directly into your function.

### Example: Root Command with Flags

```python-vue
# {{metadata.pkgs.sdk}} <plugin> [-v|--verbose] [-c|--count]
@plugin.root
async def main(
    ctx: Context,
    verbose: bool = flag("v", default=False, help="Enable verbose logging"),
    count: int = flag("c", default=1, help="Operation count")
):
    # 'verbose' is a boolean, 'count' is an integer
    log.info("starting", count=count)
    ...
```

### Signature Rules

1. **Context First**: The first argument must be `ctx: Context`.
2. **Flag Helpers**: Every subsequent argument representing a CLI flag must use the `flag()` helper as its default value.
3. **Automatic Injection**: The Daemon parses the IPC payload and injects the typed values directly as keyword arguments.

---

## `Context`

Every command handler receives a `Context`. It provides various context/info about current request.

| Attribute      | Type             | Description                                         |
| :------------- | :--------------- | :-------------------------------------------------- |
| `api_version`  | `string`         | Targeted SDK version: `"{{metadata.versions.api}}"` |
| `path`         | `list[str]`      | Full command path matched by the router.            |
| `args`         | `list[str]`      | Remaining positional args after route parsing.      |
| `cwd`          | `str`            | Client working directory.                           |
| `env`          | `dict[str, str]` | Client environment variables.                       |
| `plugin_id`    | `str`            | Plugin namespace currently handling the request.    |
| `command_name` | `str`            | Resolved command name for the request.              |
| `terminal`     | `Terminal`       | Capabilities of the client terminal (color, tty).   |
| `request_id`   | `str`            | Unique request identifier.                          |

---

## `log`

`log` is a **Logger** protocol proxy exported by `{{metadata.pkgs.sdk}}`. Use it anywhere in plugin code without passing `ctx` around.

```python
from {{metadata.pkgs.sdk}} import log

log.info("running task")
log.info("starting greet", user="soymadip")
log.error("task failed: %s", reason)
```

Behavior:

- **Scoped**: Automatically scoped to `myctl.plugin.<plugin_id>`.
- **Structured**: Keyword arguments are stored in the JSONL `fields` object.
- **Traceable**: `command_name` are attached automatically.

## Returning Responses

Use `Context` helpers for responses:

```python
return ctx.ok({"status": "ready"})
return ctx.err("Permission denied", exit_code=13)
```
