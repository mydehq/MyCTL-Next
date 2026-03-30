# Getting Started

Welcome to **{{ metadata.title }}**, {{ metadata.description }}
This guide will get you up and running in minutes.

## Quickstart

Follow the [Installation Guide](./install.md) to install **{{metadata.title}}** in your system

### 1. Test the Connection

Verify that MyCTL can talk to its intelligent daemon:

```bash
myctl ping
```

**Output:** `pong`

If the daemon is not running, MyCTL will automatically trigger a **Cold Boot**, setting up its isolated virtual environment and starting the background process for you. This may take a few seconds on the first run.

### 2. Check System Audio

One of the core built-in features is PulseAudio/PipeWire control:

```bash
# Get the current audio status
myctl audio status

# Mute the default output sink
myctl audio sink mute

# List all available sinks
myctl audio sink list
```

### 3. Manage the Daemon

You can manually control the persistent MyCTL process using the `daemon` namespace:

```bash
# Check if the daemon is currently running
myctl daemon status

# Gracefully stop the daemon
myctl daemon stop

# Start the daemon in the foreground (useful for debugging)
myctl daemon start --foreground
```

---

## What's Next?

- **[Command Reference](/guide/command-reference)**: Explore the full list of available CLI commands.
- **[Plugin SDK](/dev/plugin-sdk)**: Learn how to build your own system integrations using Python.
- **[System Architecture](/technical/architecture)**: Understand the "Lean Go / Fat Python" design.
