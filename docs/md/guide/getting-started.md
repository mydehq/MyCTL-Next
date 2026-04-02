# Getting Started

Welcome to **MyCTL**. This guide helps you run your first commands and verify that the installation is working correctly.

## Runtime Model

MyCTL uses a lean client and a persistent background service.

- **Client (`myctl`)**: Runs your command and prints the result.
- **Python service**: Keeps the command environment available between runs.

> [!NOTE]
> The client starts the service automatically when needed. You do not need to start it manually.


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


## Explore Built-in Commands

MyCTL includes built-in commands for common system tasks. Try the audio commands:

```bash
# List all system audio outputs
myctl audio sink list

# Mute your default speaker
myctl audio sink mute

# Check the current service status
myctl daemon status
```


## What's Next?

- **[Command Reference](./command-reference.md)**: Complete command list with examples.
- **[Plugin SDK](../dev/plugin-sdk/)**: Build plugins with the public SDK.
- **[Technical](../technical/overview.md)**: Learn how MyCTL works internally.
