# Command Reference

A comprehensive list of built-in commands and their usage. For a complete command tree, run `myctl help` at any time.

## ⚙️ Daemon Management

The `daemon` commands provide control over the persistent MyCTL process and its managed environment.

| Command              | Action  | Description                                                  |
| :------------------- | :------ | :----------------------------------------------------------- |
| **`daemon status`**  | Status  | Returns whether the daemon process is alive and operational. |
| **`daemon stop`**    | Stop    | Gracefully shuts down the Python engine.                     |
| **`daemon version`** | Version | Displays the version of the Client and the Daemon.            |
| **`daemon ping`**    | Health  | Simple health-check (returns `pong`).                        |
| **`daemon start`**   | Start   | Ensures the daemon is running. (Follows logs without `-b`).  |
| **`daemon logs`**    | Logs    | Tails the daemon log file in the foreground.                 |

### Global Flags

| Flag                   | Usage            | Description                                            |
| :--------------------- | :--------------- | :----------------------------------------------------- |
| **`-b, --background`** | `myctl start -b` | Executes the command and exits without following logs. |

---

## 🔊 Audio Control

MyCTL integrates with PulseAudio and Pipewire for instant system sound management.

| Command                      | Namespace | Description                                                |
| :--------------------------- | :-------- | :--------------------------------------------------------- |
| **`audio sink list`**        | Audio     | Lists all available system outputs (speakers, headphones). |
| **`audio sink mute`**        | Audio     | Toggles mute for the current default output.               |
| **`audio sink volume up`**   | Audio     | Increments volume for the default sink by 5%.              |
| **`audio sink volume down`** | Audio     | Decrements volume for the default sink by 5%.              |

---

## 🛠️ Developer SDK

The `sdk` namespace provides tools for building and managing extensions.

| Command         | Action | Description                                                  |
| :-------------- | :----- | :----------------------------------------------------------- |
| **`sdk path`**  | Path   | Returns the path to the managed **UV virtual environment**.  |
| **`sdk setup`** | Setup  | Configures your IDE (VSCode/PyCharm) for SDK autocompletion. |

---

## 🌍 Extensions & Plugins

User-installed plugins appear at the root of the command tree. These are discovered automatically at startup.

| Namespace     | Tier | Description                                           |
| :------------ | :--- | :---------------------------------------------------- |
| **`weather`** | User | Example: Fetches meteorological data via OpenWeather. |
| **`sysinfo`** | Dev  | Example: Displays hardware resource utilization.      |

## 📜 Scripting & Automation

MyCTL is designed to be a first-class citizen in shell scripts.

- **Synchronous Execution**: The Client waits for the daemon's response before exiting, ensuring that sequential commands run in the correct order.
- **Exit Codes**: The daemon passes native exit codes (0 for success, non-zero for errors) back to the Client, allowing for standard shell error handling (`if myctl stop; then ...`).
