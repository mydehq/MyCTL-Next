# Command Reference

A comprehensive list of built-in commands and their usage. For a complete command tree, run `myctl help` at any time.

## ⚙️ Daemon Management

The `daemon` commands provide control over the persistent MyCTL process.

| Command | Action | Description |
| :--- | :--- | :--- |
| `daemon status` | Status | Returns whether the daemon process is alive. |
| `daemon stop` | Stop | Gracfully shuts down the Python server. |
| `daemon version`| Version | Displays the version of the Go proxy and the Daemon. |
| `daemon ping` | Health | Simple health-check (returns `pong`). |
| `daemon start` | Start | Forces the daemon to start manually. |

---

## 🔊 Audio Control

MyCTL integrates with PulseAudio and PipeWire for instant system sound management.

| Command | Namespace | Description |
| :--- | :--- | :--- |
| `audio sink list` | Audio | Lists all available system outputs (speakers, headphones). |
| `audio sink mute` | Audio | Toggles mute for the current default output. |
| `audio sink vol up`| Audio | Increments volume for the default sink by 5%. |
| `audio sink vol down`| Audio | Decrements volume for the default sink by 5%. |

---

## 🛠 Developer SDK

The `sdk` namespace is designed to help community developers build extensions quickly.

| Command | Action | Usage |
| :--- | :--- | :--- |
| `sdk path` | Path | Returns the path to the internal Python sandbox. |
| `sdk setup` | Setup | Automatically configures VSCode for plugin development. |

---

## 🌍 Extension & Plugins

User-installed plugins appear at the root of the command tree.

| Namespace | Source | Description |
| :--- | :--- | :--- |
| `weather` | Plugin | Community-built plugin for meteorological data. |
| `pkg` | System | (In-development) System package manager wrapper. |

## Why "Wait for completion"?

MyCTL executes all commands asynchronously. If you need to chain commands in a script, the Go client will wait for the daemon's response before exiting, ensuring your script runs in order.
