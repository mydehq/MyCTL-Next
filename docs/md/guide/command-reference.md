# Command Reference

This page lists the built-in commands available to MyCTL users.
For the complete command tree, run `myctl help` at any time.

## ⚙️ System Management

These commands control the MyCTL service and its runtime state.

| Command              | Action  | Description                                         |
| :------------------- | :------ | :-------------------------------------------------- |
| **`daemon status`**  | Status  | Shows whether MyCTL is running.                     |
| **`daemon stop`**    | Stop    | Stops the MyCTL service gracefully.                 |
| **`daemon version`** | Version | Displays the installed client and service versions. |
| **`daemon ping`**    | Health  | Runs a quick health check and returns `pong`.       |
| **`daemon start`**   | Start   | Starts MyCTL if it is not already running.          |
| **`daemon logs`**    | Logs    | Displays recent service log output.                 |

### Global Flags

| Flag                   | Usage            | Description                                            |
| :--------------------- | :--------------- | :----------------------------------------------------- |
| **`-b, --background`** | `myctl start -b` | Executes the command and exits without following logs. |

---

## Audio Control

MyCTL includes audio commands for managing the default output device.

| Command                      | Namespace | Description                                                |
| :--------------------------- | :-------- | :--------------------------------------------------------- |
| **`audio sink list`**        | Audio     | Lists all available system outputs (speakers, headphones). |
| **`audio sink mute`**        | Audio     | Toggles mute for the current default output.               |
| **`audio sink volume up`**   | Audio     | Increments volume for the default sink by 5%.              |
| **`audio sink volume down`** | Audio     | Decrements volume for the default sink by 5%.              |

---

## SDK Utilities

The `sdk` namespace provides tools for plugin development setup.

| Command         | Action | Description                                          |
| :-------------- | :----- | :--------------------------------------------------- |
| **`sdk path`**  | Path   | Returns the path to the managed virtual environment. |
| **`sdk setup`** | Setup  | Configures your IDE for SDK autocompletion.          |

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
