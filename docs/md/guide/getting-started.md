# Getting Started

Welcome to **MyCTL**. This guide helps you run your first commands and verify that the installation is working correctly.

## Runtime Model

MyCTL uses a lean client and a persistent background service.

- **Client (`myctl`)**: Runs your command and prints the result.
- **Engine (`myctld`)**: Background service that manages the plugin lifecycle.

> [!NOTE]
> The client starts the Engine automatically when needed. You do not need to start it manually.


## First Run

After [Installation](./install.md), verify the connection by running a simple health check:

```bash
myctl ping
```

On first run:

1. **Start up**: the client detects that the service is not running.
2. **Environment setup**: `uv` prepares the managed Python environment.
3. **Ready**: the service becomes available and the command runs.

**Output:** `pong`


## Explore Internal Plugins

MyCTL includes several "Internal Plugins" for system management:

```bash
# Check daemon status
myctl status

# Restart the Engine
myctl restart

# Show the Unified Schema
myctl schema
```

Try a plugin command:

```bash
myctl audio status
```


## What's Next?

- **[Command Reference](./command-reference.md)**: Complete command list with examples.
- **[Plugin SDK](../dev/plugin-sdk/)**: Build plugins with the public SDK.
- **[Technical](../technical/)**: Learn how the Engine works internally.
