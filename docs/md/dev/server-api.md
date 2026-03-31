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

Returns the full command hierarchy as a JSON tree. This is used by the Go client to inflate its Cobra tree dynamically.

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

---

## 📊 Runtime Status

### `status` (Daemon Status)

Returns telemetry for the running process.

- **Request**: `{ "path": ["status"] }`
- **Response Data**: String containing PID, Uptime, and Version.

### `logs`

Returns the path to the daemon log file.

- **Request**: `{ "path": ["logs"] }`
- **Response Data**: `/home/user/.local/state/myctl/daemon.log`

---

## 🔄 Lifecycle Management

### `stop`

Initiates a graceful shutdown of the daemon process.

- **Request**: `{ "path": ["stop"] }`
- **Response**: `Daemon shutting down...`

### `restart`

The daemon terminates gracefully. The next client connection will trigger a fresh cold boot via the Go orchestrator.

- **Request**: `{ "path": ["restart"] }`
- **Response**: `Daemon restarting...`

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
