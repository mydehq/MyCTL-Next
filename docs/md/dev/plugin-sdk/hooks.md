# Hooks

Hooks let your plugin run logic outside direct command execution.

- Use `@plugin.on_load` for one-time startup initialization.
- Use `@plugin.periodic` for recurring background work.

For logging behavior and API details, see the `log` section in [API Reference](./api.md).

## `@plugin.on_load`

`on_load` runs **once when the plugin is being loaded**.

Useful for tasks like:

- validating environment requirements
- creating clients or caches
- warming expensive resources before first command use

```python
from myctl.api import Plugin, Context, log

plugin = Plugin("myplugin")

@plugin.on_load
async def setup(ctx: Context):
    # Example: establish external connection once.
    log.info("Plugin loaded")
```

> [!DANGER] CAUTION
> If an `on_load` hook raises an exception, plugin load fails.  
> The plugin is not exposed in the command tree for that session.

## `@plugin.periodic`

`periodic` schedules recurring work at a fixed interval.

Useful for tasks like:

- refreshing cached data
- polling local or remote state
- emitting periodic health signals

```python
from myctl.api import Plugin

plugin = Plugin("myplugin")

@plugin.periodic(seconds=60)
async def refresh_cache():
    # Runs every 60 seconds.
    ...
```

> [!WARNING]
> Periodic tasks run concurrently with command handling.  
> If a run fails, the engine logs the error and retries on the next interval.

## Practical Guidance

- Keep hooks idempotent where possible.
- Keep startup hooks short to avoid slow plugin activation.
- Avoid long blocking I/O in periodic tasks.
- Put command registration in `main.py` and heavy logic in `src/` modules.
