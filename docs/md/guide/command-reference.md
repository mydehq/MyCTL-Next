# Command Reference

This page lists the built-in commands available to MyCTL users.
For the complete command tree, run `myctl help` at any time.

## ⚙️ System Management

These commands control the MyCTL service and its runtime state.

| Command       | Action    | Description                                                   |
| :------------ | :-------- | :------------------------------------------------------------ |
| **`status`**  | Status    | Shows daemon runtime status and telemetry table.              |
| **`stop`**    | Stop      | Stops the daemon gracefully and cleans up the socket.         |
| **`ping`**    | Health    | Runs a liveness check and returns `pong`.                     |
| **`start`**   | Start     | Starts daemon in foreground mode by default.                  |
| **`restart`** | Restart   | Restarts daemon runtime.                                      |
| **`logs`**    | Logs      | Shows recent daemon log output (tail, not persistent follow). |
| **`schema`**  | Discovery | Dumps command schema used by the client proxy.                |
| **`help`**    | Help      | Shows daemon-managed help metadata.                           |
| **`sdk`**     | SDK       | Shows SDK metadata and environment hints.                     |

### Global Flags

| Flag                   | Usage            | Description                                             |
| :--------------------- | :--------------- | :------------------------------------------------------ |
| **`-b, --background`** | `myctl start -b` | Starts daemon in background mode and exits immediately. |

---

## Audio Control

MyCTL includes audio commands for managing the default output device.

| Command                    | Namespace | Description                                     |
| :------------------------- | :-------- | :---------------------------------------------- |
| **`audio status`**         | Audio     | Shows current sink status.                      |
| **`audio volume set <n>`** | Audio     | Sets sink volume level (plugin implementation). |

---

## SDK Utilities

The `sdk` namespace provides tools for plugin development setup.

| Command   | Action | Description                                 |
| :-------- | :----- | :------------------------------------------ |
| **`sdk`** | Info   | Returns SDK metadata and environment hints. |

---

## Extensions & Plugins

User-installed plugins appear at the root of the command tree and are discovered automatically at startup.

| Namespace     | Tier | Description                                   |
| :------------ | :--- | :-------------------------------------------- |
| **`weather`** | User | Example: Retrieves weather information.       |
| **`sysinfo`** | Dev  | Example: Shows hardware resource utilization. |

## Scripting & Automation

MyCTL is designed to work cleanly in shell scripts.

- **Synchronous Execution**: The client waits for the service response before exiting, so commands can be chained reliably.
- **Exit Codes**: MyCTL returns standard shell exit codes, so you can use it in conditionals and scripts.
