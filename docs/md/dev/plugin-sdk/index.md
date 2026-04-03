# Plugins SDK

MyCTL exposes a single, easy to use public api: `{{metadata.pkgs.sdk}}`, which can be used to build plugins to extend Command list:

## Core API Surface

The SDK provides a modern, type-safe way to define commands and interact with the system:

- `Plugin`: The primary registration helper for commands, flags, and lifecycle hooks.
- `Context`: Provides per-invocation metadata (args, environment, terminal state).
- `flag`: Helper used in function signatures to declare CLI parameters.
- `log`: A plugin-scoped logger that automatically attributes entries to your plugin ID.
- `style`: Helpers for consistent terminal output (colors, tables, bold text).

### Example: Hello World

```python
from {{metadata.pkgs.sdk}} import Plugin, Context, flag

plugin = Plugin()

@plugin.command("hello", help="Say hello")
async def hello(ctx: Context, name: str = flag("n", default="World", help="Who to greet")):
    # Flags are injected directly as typed arguments!
    return ctx.ok(f"Hello, {name}!")
```
