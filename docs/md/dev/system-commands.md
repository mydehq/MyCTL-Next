# System Commands (Internal Plugins)

System commands are the built-in functionalities of the {{metadata.pkgs.daemon}} Engine, such as `status`, `stop`, `schema`, and `plugin`. These are implemented as **Internal Plugins** to ensure architectural consistency across the entire ecosystem.

---

## 1. The Unified Plugin Model

In MyCTL, we treat **Internal Plugins** (system commands) and **External Plugins** (user extensions) as equal citizens in the routing table. Both use the same Modern SDK (V3) and follow the same metadata structure.

### Core Principles

- **Dogfooding**: Internal plugins must correctly use the `myctl` SDK. If a feature isn't available to internal plugins via the SDK, it shouldn't exist.
- **Location**: Internal plugins live in `daemon/myctld/plugins/internal/`.
- **Identity**: The directory name (e.g., `status/`) is used as the **Plugin ID** and automatically defines the CLI namespace.
- **Root Routing**: Most internal plugins use the `@plugin.root` decorator to Map the Plugin ID directly to the command execution.

---

## 2. System vs. External Plugins

While they share the same SDK, Internal Plugins have unique properties:

| Feature           | External Plugin                | Internal Plugin              |
| :---------------- | :----------------------------- | :--------------------------- |
| **SDK Import**    | `from myctl import Plugin`     | `from myctl import Plugin`   |
| **Engine Import** | ❌ Blocked (Process Isolation) | ✅ Allowed (Same Process)    |
| **Context Type**  | `Context`                      | `SystemContext`              |
| **Manifest**      | Required (`pyproject.toml`)    | Optional (Implicit Metadata) |

---

## 3. Implementation Specification (V3)

Under the **Typed Signature API**, internal plugins are concise and type-safe.

### Basic Command: `ping`

Internal plugins that perform a single action use the `@plugin.root` entry point.

```python
# daemon/myctld/plugins/internal/ping/main.py
from myctl import Plugin, Context

plugin = Plugin()

@plugin.root
async def ping_handler(ctx: Context):
    """Internal connectivity check."""
    return ctx.ok("pong")
```

### Privileged Command: `status`

Internal plugins receive a `SystemContext`, granting them access to the Engine's internal state.

```python
# daemon/myctld/plugins/internal/status/main.py
from myctl import Plugin
from ....core.models import SystemContext

plugin = Plugin()

@plugin.root
async def status_handler(ctx: SystemContext):
    """Show Engine health and loaded plugins"""
    registry = ctx.get_registry() # Privileged method

    return ctx.ok({
        "status": "online",
        "plugins": len(registry.plugins)
    })
```

---

## 4. The System Context Advantage

The `SystemContext` (found in `myctld.core.models`) implements the privileged `SystemProtocol`. This allows system commands to perform administrative tasks:

- **IPC Shutdown**: `ctx.request_shutdown()` allows the `stop` command to gracefully terminate the Engine process.
- **Registry Access**: `ctx.get_registry()` allows the `schema` and `plugin` commands to inspect and manage the live command tree.

---

## 5. Directory Structure

Internal plugins are organized within the Engine source:

```text
daemon/myctld/plugins/internal/
├── status/      # Handler for '{{metadata.pkgs.sdk}} status'
├── stop/        # Handler for '{{metadata.pkgs.sdk}} stop'
├── schema/      # Handler for '{{metadata.pkgs.sdk}} schema'
└── plugin/      # Multi-command plugin ('{{metadata.pkgs.sdk}} plugin list', etc.)
```

This structural purity ensures that the Go Client doesn't need to distinguish between "built-in" and "third-party" logic—it simply requests a command path, and the Engine dispatches it.
