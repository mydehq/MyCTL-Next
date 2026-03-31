# Lifecycle: Plugin State and Recovery

The MyCTL daemon treats plugins as transient logic blocks operating within a persistent host process. To ensure the daemon remains stable even when executing poorly written or failing plugins, it orchestrates a rigid, sandbox-driven lifecycle.

This document details the distinct execution phases a plugin undergoes and the error-recovery mechanisms that protect the Engine.

---

## 1. The Plugin Lifecycle Phases

Every plugin, upon discovery, transitions through sequential initialization phases. A failure at any phase aborts the sequence, triggering an immediate rollback.

### Phase 1: Discovery & Validation

Before any code is ever imported, the Engine validates the structural integrity of the plugin via `pyproject.toml`.

- **Identity Check**: The `project.name` must exactly match the physical directory name. If there is a mismatch, the plugin is rejected to prevent obscure routing bugs.
- **API Parity**: The plugin's declared `tool.myctl.api_version` is compared against the Engine's `API_VERSION`. Major version mismatches instantly halt the load process.

### Phase 2: Dependency Synchronization (`uv`)

If the validation succeeds and the plugin declares `dependencies` in its manifest, the Engine halts execution and forks out to `uv pip install`.

- The plugin's directory is passed directly into `uv`, which parses the `pyproject.toml` and installs the required packages into the central, locked `$XDG_DATA_HOME/myctl/venv`.
- This phase shields the Python environment from being mutated by random `subprocess` calls within a plugin.

### Phase 3: Module Load & Initialization

The final and most sensitive phase is the actual dynamic execution of the `main.py` entry point.

1.  **Sandbox Creation**: The module is injected with a local `__name__` equal to the Plugin ID.
2.  **SDK Hooking**: The `@registry.add_cmd` decorators fire, appending command routes to the central tree.
3.  **The `on_load` Execution**: The Engine searches the temporary `myctl.api._load_hooks` list. If the plugin registered an `@on_load` setup function, it is executed here sequentially.

### Phase 4: Background Runtime

Upon a successful `on_load`, the plugin is considered "Active" and the daemon resumes its standard operation.

- Action handlers (`@add_cmd`) only sit idle in memory until dispatched by IPC.
- Background tasks (`@periodic`) are extracted and passed to the `asyncio` event loop.

---

## 2. Fail-Fast Rollback Mechanism

The `on_load` function acts as a definitive health check. If a plugin's setup logic raises an unhandled exception, the `"Fail-Fast"` recovery sequence activates:

```python
plugin_failed = False
for hook in myctl.api._load_hooks:
    try:
        await hook()  # or hook() if synchronous
    except Exception as e:
        logging.error(f"Plugin '{plugin_id}' critical initialization failure: {e}")
        plugin_failed = True
        break

if plugin_failed:
    logging.critical(f"REJECTED plugin '{plugin_id}': Failed initialization. Rolling back.")
    # Safe Rollback
    del self._commands[plugin_id]
```

By safely deleting the `plugin_id` root from the `_commands` routing table, the daemon essentially pretends the plugin never existed. The process remains running, and other CLI commands function normally.

---

## 3. Background Task Resilience (`_periodic_wrapper`)

While a plugin failing to load is cleanly rejected, a plugin failing _during_ a background `@periodic` task poses a threat to the asynchronous architecture.

To prevent a bad `while True:` loop or network timeout from terminating the daemon or silently exiting an `asyncio.Task`, the Engine wraps every background job in a resilient boundary:

```python
async def _periodic_wrapper(self, interval: int, func: Callable):
    """Infinite loop for a background task with retry logic"""
    while True:
        try:
            await asyncio.sleep(interval)

            # Execute the user's plugin logic
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()

        except Exception as e:
            # Trap the error to keep the loop and task alive
            logging.error(
                f"Background task '{func.__name__}' ({interval}s) failed: {e}. "
                f"Retrying in {interval}s..."
            )
```

**Key Advantages:**

- **Zero-Crash Guarantee**: The `try...except Exception as e` acts as a global catch-all. An individual plugin's periodic loop can fail continuously without degrading daemon performance or killing the event loop.
- **Cool-Down Wait**: Because the `await asyncio.sleep(interval)` is located at the top of the `while` loop (before the logic executes), failing tasks inherently wait their designated interval before retrying, preventing unbounded CPU spin-locking if a task crashes immediately upon starting.
