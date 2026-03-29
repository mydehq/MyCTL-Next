# IPC Protocol Specification

MyCTL uses a lightweight, high-performance **Newline-Delimited JSON** (NDJSON) protocol over a Unix Domain Socket. This ensures that every command and response is a single, isolated line of communication, making it extremely fast to parse and proxy.

## Protocol Structure

### 1. Request Payload (Go -> Python)
The Go client sends exactly one JSON object per command. It does not perform any validation beyond checking the socket.

```json
{
  "args": ["audio", "sink", "mute"],
  "env": ["USER=soymadip", "XDG_SESSION_TYPE=wayland"],
  "cwd": "/home/soymadip/Projects/MyCTL"
}
```

- **`args`**: A raw list of the user's CLI arguments.
- **`env`**: Relevant environment variables to allow the daemon to act on behalf of the user.
- **`cwd`**: The current working directory where the user executed the command.

### 2. Response Payload (Python -> Go)
The Python daemon responds with exactly one JSON object.

```json
{
  "status": "ok",
  "data": "Default sink is now muted."
}
```

- **`status`**: Either `"ok"` (command succeeded) or `"error"` (command failed or not found).
- **`data`**: The raw text output that the Go client should print to the user's terminal.

## Socket Blueprint

- **Location**: `$XDG_RUNTIME_DIR/myctl-daemon.sock`
- **Fallback**: `/run/user/<UID>/myctl-daemon.sock`
- **Timeout**: The Go client has a default timeout of 5 seconds to receive a response.

## Why NDJSON?

### 1. O(1) Parsing
By mandating a single line per message, the Go client can simply read until the first `\n` and unmarshal that line directly. It never has to buffer multiple frames or manage complex streaming states.

### 2. Agnostic Slicing
Since the Go client is a "Pure Proxy," it doesn't need to understand the keys in the JSON object beyond `status` and `data`. This allows the daemon to evolve the protocol (e.g., adding `exit_code`) without requiring a recompile of the client binary.

### 3. Debugability
Because the protocol is plain-text JSON, you can debug the daemon directly using tools like `socat` or `nc -U`:

`echo '{"args": ["ping"]}' | nc -U $XDG_RUNTIME_DIR/myctl-daemon.sock`
