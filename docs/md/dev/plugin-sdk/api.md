# API Reference

The `myctl.api` package currently exposes three primary SDK objects:

- `Plugin`: Declarative command/hook registration.
- `Context`: Per-invocation execution context passed to handlers.
- `log`: Context-aware logger proxy for plugin-scoped logging.

## Import Pattern

```python
from myctl.api import Plugin, Context, log
```

> [!IMPORTANT]
> Plugins must import only from `myctl.api`. Importing internal modules under `myctl.core` is blocked at runtime.

## `Plugin`

Create one plugin instance in `main.py` using the folder/plugin ID:

```python
plugin = Plugin("weather")
```

Registration decorators:

- `@plugin.command(path, help="...")`
- `@plugin.flag(name, short, default, help, ...)`
- `@plugin.on_load`
- `@plugin.periodic(seconds=...)`

`on_load` hooks can be declared either with no parameters or with `Context`:

```python
@plugin.on_load
async def boot(ctx: Context):
    log.info("booting plugin")
```

## `Context`

Every command handler receives a `Context` object.

| Attribute   | Type             | Description                                      |
| :---------- | :--------------- | :----------------------------------------------- |
| `path`      | `list[str]`      | Full command path matched by the router.         |
| `args`      | `list[str]`      | Remaining positional args after route parsing.   |
| `flags`     | `dict[str, Any]` | Parsed declarative flag values.                  |
| `cwd`       | `str`            | Client working directory.                        |
| `env`       | `dict[str, str]` | Client environment variables.                    |
| `plugin_id` | `str`            | Plugin namespace currently handling the request. |

## `log`

`log` is a context-aware logger proxy exported by `myctl.api`.

```python
from myctl.api import log
```

Use it anywhere in plugin code (handlers, hooks, helper modules) without passing `ctx` around:

```python
log.info("running task")
log.error("task failed: %s", reason)
```

Behavior:

- During command execution, `on_load`, and `periodic` hooks, `log` is automatically scoped to `myctl.plugin.<plugin_id>`.
- Outside active plugin execution, it falls back to the core logger namespace.

Because of this, `log` is the canonical logging API for plugin code.

### Example: `path`, `args`, and `flags`

Command:

```bash
myctl plugin init myplugin --author "Dev" --path /tmp
```

The generated plugin target is resolved from positional `args` first, then `--path`.

Inside handler:

```python
ctx.path   # ["plugin", "init"]
ctx.args   # ["myplugin"]
ctx.flags  # {"author": "Dev", "path": "/tmp", ...}
```

## Interactive Input

Use `ask` for multi-turn CLI interaction:

```python
password = await ctx.ask("Password: ", secret=True)
```

- `prompt`: Text shown in terminal.
- `secret=True`: Masks input in TTY-capable terminals.

## Returning Responses

Use `Context` helpers for responses:

```python
return ctx.ok({"status": "ready"})
return ctx.err("Permission denied", exit_code=13)
```

Handlers must return a valid SDK response object.

