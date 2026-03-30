# Server API Reference

This document is the **IPC reference for external client developers** — anyone building a frontend, alternative CLI, or automation tool that communicates with the MyCTL daemon directly over its Unix Socket.

> **Prerequisites**: Familiarise yourself with the [IPC Protocol Specification](../technical/ipc-protocol.md) for the wire format (NDJSON over Unix Socket) before using this reference.

The socket is located at `$XDG_RUNTIME_DIR/myctl/myctld.sock`.

All requests follow this structure:

```json
{ "path": ["<endpoint>"], "args": [], "cwd": "/", "env": {} }
```

All responses follow:

```json
{ "status": "ok" | "error", "data": <any>, "exit_code": 0 }
```

## Health & Discovery

### `ping`

A lightweight liveness check.

**Request**

```json
{ "path": ["ping"] }
```

**Response**

```json
{ "status": "ok", "data": "pong", "exit_code": 0 }
```

### `version`

Returns the daemon's API version. Use this to verify compatibility before issuing other requests.

**Request**

```json
{ "path": ["version"] }
```

**Response**

```json
{ "status": "ok", "data": "2.0.0", "exit_code": 0 }
```

### `schema`

Returns the full command tree as a JSON graph. This is the primary endpoint for dynamically building a CLI or UI — it includes all loaded plugins and their subcommands.

**Request**

```json
{ "path": ["schema"] }
```

**Response**

```json
{
  "status": "ok",
  "data": {
    "audio": {
      "type": "group",
      "help": "Manage PulseAudio/Pipewire sinks and sources",
      "children": {
        "volume": {
          "type": "group",
          "children": {
            "set": { "type": "command", "help": "Set volume to a percentage" }
          }
        }
      }
    },
    "ping": { "type": "command", "help": "Health check (returns pong)" }
  },
  "exit_code": 0
}
```

## Runtime Status

### `status`

Returns runtime telemetry for the running daemon.

**Request**

```json
{ "path": ["status"] }
```

**Response**

```json
{
  "status": "ok",
  "data": "MyCTL Daemon\n  Status:   online\n  Version:  0.2.0\n  PID:      12345\n  Uptime:   142s",
  "exit_code": 0
}
```

## Lifecycle

### `stop`

Initiates a graceful shutdown. The daemon unbinds the socket before terminating to prevent stale lock files.

**Request**

```json
{ "path": ["stop"] }
```

**Response**

```json
{ "status": "ok", "data": "Daemon shutting down...", "exit_code": 0 }
```

### `restart`

Triggers a graceful restart. The daemon exits; the next client connection will trigger a fresh cold boot.

**Request**

```json
{ "path": ["restart"] }
```

**Response**

```json
{ "status": "ok", "data": "Daemon restarting...", "exit_code": 0 }
```

## Plugin Commands

Any plugin command can be dispatched by its full path. For example, to call `myctl audio volume set` with argument `50`:

**Request**

```json
{
  "path": ["audio", "volume", "set"],
  "args": ["myctl", "audio", "volume", "set", "50"],
  "cwd": "/home/user",
  "env": { "USER": "soymadip" }
}
```

Use `schema` first to discover available paths dynamically.

## Testing Directly

The NDJSON protocol means you can probe the daemon with standard Unix tools, no client library required:

```bash
echo '{"path": ["ping"]}' | nc -U $XDG_RUNTIME_DIR/myctl/myctld.sock
echo '{"path": ["schema"]}' | nc -U $XDG_RUNTIME_DIR/myctl/myctld.sock
```
