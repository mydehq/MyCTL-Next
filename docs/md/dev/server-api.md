# Server API Reference

This document serves as the **IPC reference for external developers**—frontends, automation tools, or alternative CLIs—that communicate with the MyCTL daemon directly over its Unix Socket.

> [!NOTE]
> **Prerequisites**: Familiarize yourself with the [IPC Protocol](../technical/ipc-protocol.md) for wire format details (NDJSON over Unix Socket).

## 📥 Request Pattern

All requests must be sent as single-line JSON objects followed by a newline (`\n`):

```json
{
  "path": ["<endpoint>"],
  "args": ["<arg1>", "<arg2>"],
  "cwd": "/absolute/path",
  "env": { "USER": "soymadip" }
}
```

## 📤 Response Pattern

The daemon responds with a single-line JSON object:

```json
{
  "status": "ok" | "error",
  "data": "Result string or JSON object",
  "exit_code": 0
}
```

---

## 🛠️ Health & Discovery

### `ping`

A lightweight liveness check.

- **Request**: `{ "path": ["ping"] }`
- **Response**: `{ "status": "ok", "data": "pong", "exit_code": 0 }`

### `__sys_version`

Returns the daemon's API version.

- **Request**: `{ "path": ["__sys_version"] }`
- **Response**: `{ "status": "ok", "data": "{{metadata.versions.api_ver}}", "exit_code": 0 }`

### `__sys_schema`

Returns the full command hierarchy as a JSON tree. This is used by the Client to inflate its command tree dynamically.

- **Request**: `{ "path": ["__sys_schema"] }`
- **Response**:

```json
{
  "status": "ok",
  "data": {
    "audio": {
      "type": "group",
      "help": "Audio controls",
      "children": {
        "volume": {
          "type": "command",
          "help": "Set volume"
        }
      }
    }
  }
}
```

### `__sys_logs`

Returns the most recent tail activity (up to 30 lines) directly from the persistent daemon log file.

- **Request**: `{ "path": ["__sys_logs"] }`
- **Response Data**: A single multi-line string of log output.
  ```json
  {
    "status": "ok",
    "data": "15:04:05 [INFO] Daemon started...\n15:04:06 [INFO] Plugin 'audio' loaded",
    "exit_code": 0
  }
  ```

---

## 📊 Runtime Status

### `status` (Daemon Status)

Returns telemetry for the running process.

- **Request**: `{ "path": ["status"] }`
- **Response Data**: String containing PID, Uptime, and Version.

### `logs`

A user-friendly alias for `__sys_logs`. It returns the most recent 30 lines from `$XDG_STATE_HOME/myctl/daemon.log` as a single raw text string.

- **Request**: `{ "path": ["logs"] }`
- **Response Data**: Multi-line string containing the recent log dump.

---

## 🔄 Lifecycle Management

### `stop`

Initiates a graceful shutdown of the daemon process.

- **Request**: `{ "path": ["stop"] }`
- **Response**: `Daemon shutting down...`

### `restart`

The daemon terminates gracefully. The next client connection will trigger a fresh initialization sequence, re-discovering all plugins from disk.

- **Request**: `{ "path": ["restart"] }`
- **Response**: `Daemon restarting...`

> [!TIP]
> **Plugin Development**: This is the primary mechanism for reloading edited plugin code. Since the daemon caches all plugin logic in RAM, running `myctl restart` is required after modifying any plugin's `main.py` or `pyproject.toml`.

---

## 🧩 Executing Plugins

Any plugin command can be dispatched by its full path. For example, to call `myctl audio volume set 50`:

**Request**:

```json
{
  "path": ["audio", "volume", "set"],
  "args": ["50"],
  "cwd": "/home/user",
  "env": { "USER": "soymadip" }
}
```

---

## 🔬 Diagnostic Probing

Because the protocol is plain-text, you can use standard Unix tools to probe the daemon:

```bash
# Get health check
echo '{"path": ["ping"]}' | nc -U $XDG_RUNTIME_DIR/myctl/myctld.sock

# Get full schema
echo '{"path": ["__sys_schema"]}' | nc -U $XDG_RUNTIME_DIR/myctl/myctld.sock
```
