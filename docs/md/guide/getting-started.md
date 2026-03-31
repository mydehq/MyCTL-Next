# Getting Started

Welcome to **MyCTL**, the high-performance desktop controller for Linux. This guide covers how to quickly initialize the system and explore your first system commands.

## Architecture: The Lean Proxy

MyCTL operates on a **Lean Client / Fat Server** architecture.

- **Client (`myctl`)**: A sub-millisecond $O(1)$ CLI that handles user input and displays output.
- **Python Daemon (`myctld`)**: The persistent engine that manages system state and third-party plugins.

> [!NOTE]
> **Orchestration**: The Client uses `uv` to automatically bootstrap the daemon. You don't need to manually start the server before using MyCTL.


## 🚀 The First Run

After [Installation](./install.md), verify the connection by running a simple health check:

```bash
myctl ping
```

If this is your first time running MyCTL:

1.  **Cold Boot**: The Client detects the daemon is offline.
2.  **UV Sync**: `uv` automatically downloads a private Python runtime and syncs all engine dependencies.
3.  **Ready Signal**: Once the daemon is fully initialized, it signals the proxy to proceed.

**Output:** `pong`


## 🔊 Exploring Built-ins

MyCTL includes several native system integrations. Try the audio plugin:

```bash
# List all system audio outputs
myctl audio sink list

# Mute your default speaker
myctl audio sink mute

# Check the current daemon status
myctl daemon status
```


## What's Next?

- **[Command Reference](./command-reference.md)**: Full list of all builtin commands.
- **[Plugin SDK](../dev/plugin-sdk.md)**: Build new MyCTL extensions.
- **[Technical](../technical/overview.md)**: Read how things actually works internally.
