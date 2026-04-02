# IPC Protocol: The NDJSON Handshake

MyCTL uses a lightweight, high-performance protocol based on **Newline-Delimited JSON (NDJSON)** over a native Unix Domain Socket. This protocol serves as the vital bridge between the agnostic Client and the persistent Python Engine.

## Why NDJSON?

In traditional socket programming, clients and servers must often implement complex framing (like HTTP `Content-Length`) to know exactly when a message ends. NDJSON simplifies this by guaranteeing that exactly one JSON object exists per line.

This enables the Client to achieve $O(1)$ parsing speed. It never manages streaming memory buffers; it simply reads until the newline character (`\n`):

```go
reader := bufio.NewReader(conn)
respLine, _ := reader.ReadString('\n')
```

Once the newline is reached, the Client unmarshals the payload, renders the output, and immediately terminates with the provided `ExitCode`.

---

## Payload Specifications

The communication between the client and server relies on strict structural payloads that map directly between Go and Python.

### 1. The Request Payload

The Client sends exactly one JSON object per command containing the context required for Python to resolve the command hierarchy.

**Client Request Structure**:

```go
type Request struct {
        Path     []string `json:"path"`
        Args     []string `json:"args"`
        Cwd      string   `json:"cwd"`
        Terminal struct {
                IsTTY      bool   `json:"is_tty"`
                ColorDepth  string `json:"color_depth"`
                NoColor     bool   `json:"no_color"`
        } `json:"terminal"`
        Env map[string]string `json:"env"`
}
```

**JSON Wire Format**:

```json
{
  "path": ["audio", "sink", "mute"],
  "args": ["--all"],
    "cwd": "/home/soymadip/Projects/MyCTL",
    "terminal": {
        "is_tty": true,
        "color_depth": "256",
        "no_color": false
    },
    "env": { "USER": "soymadip", "DISPLAY": ":0" }
}
```

> [!NOTE]
> **The `cwd` Context**: Since the Python Engine runs continuously in the background, its internal working directory does not match the user's shell. Passing `cwd` over IPC allows plugins to accurately resolve local paths (e.g., `myctl edit ./config.json`).

> [!IMPORTANT]
> The `terminal` block is required for all command requests. It is the source of truth for rendering decisions and replaces the old env-based capability guessing logic.

### 2. The Response Payload (Python -> Client)

The Python engine executes the handler and responds with exactly one JSON object.

**Go Struct (`cmd/main.go`)**:

```go
type Response struct {
    Status   int         `json:"status"`
    Data     interface{} `json:"data"`
    ExitCode int         `json:"exit_code"`
}
```

The transport uses numeric status codes rather than string literals:

| Code | Symbolic Name | Meaning                                            |
| :--- | :------------ | :------------------------------------------------- |
| `0`  | `OK`          | Command completed successfully.                    |
| `1`  | `ERROR`       | Command failed.                                    |
| `2`  | `ASK`         | Daemon is asking the client for interactive input. |

- For `OK`, `data` is the payload to render (string, dict, list).
- For `ERROR`, `data` is the error message.
- For `ASK`, `data` is an object with the prompt text and optional secret-input flag.

### Interactive `"ask"` Loop

The MyCTL client natively supports multi-turn IPC communication without buffering state. If `status == 2` (`ASK`):
1. The daemon sends a payload shaped like `{"prompt": "...", "secret": false}`.
2. The client prints the prompt to the terminal.
3. If `secret` is `true` and the user is in a TTY, the client reads masked input.
4. The client repacks the user's input as `{"data": "<input>"}\n` and sends it back over the **same open socket**.
5. The client continues reading from the socket recursively, waiting for a final `0` (`OK`), `1` (`ERROR`), or another `2` (`ASK`).

This guarantees typical non-interactive commands execute at pure $O(1)$ networking latency, whilst still supporting deep plugin interactivity.

---

## Socket Configuration

The architecture adheres to XDG standards to ensure isolation and security.

| Path                            | Purpose                 |
| :------------------------------ | :---------------------- |
| **`{{metadata.paths.socket}}`** | Primary IPC bind point. |

### Diagnostic Access

Because the protocol is plain-text NDJSON, you can debug the Python Engine independently using standard tools like `netcat` or `socat`:

```bash-vue
# Manually issue a ping request
echo '{"path": ["ping"], "terminal": {"is_tty": true, "color_depth": "16", "no_color": false}}' | nc -U {{metadata.paths.socket}}
```

---

## Reserved System Commands

The Engine contains built-ins that are always available, regardless of which plugins are loaded. These are dispatched before plugin routing.

| Command Path | Purpose                                                           |
| :----------- | :---------------------------------------------------------------- |
| `schema`     | Returns the full command hierarchy tree used by client hydration. |
| `status`     | Returns daemon runtime status snapshot.                           |
| `ping`       | Health check.                                                     |
| `start`      | Start command semantics in daemon command layer.                  |
| `restart`    | Restart command semantics.                                        |
| `stop`       | Graceful daemon shutdown.                                         |
| `sdk`        | SDK metadata and environment hints.                               |
| `logs`       | Returns recent daemon log lines.                                  |
| `help`       | Built-in help metadata.                                           |

> [!IMPORTANT]
> The `schema` path is a critical internal contract. The Client requests `["schema"]` to build its command tree.

System command names are reserved and handled before plugin dispatch.

---

## Client-Side Fault Tolerance

The Client implements a layered protocol for handling daemon-unreachable states, with "Cold Boot" as the recovery mechanism.

### The `sendIPCRequest` Decision Tree

```
Dial("unix", sockPath)
    |
    +--> Success --> Write Request --> Read Response --> Done
    |
    +--> Failure (ECONNREFUSED / ENOENT)
              |
              +--> allowBootstrap == false --> Return error ("daemon is offline")
              |
              +--> allowBootstrap == true
                        |
                        +--> BootstrapDaemon() --> Success --> Re-dial --> Done
                        |
                        +--> BootstrapDaemon() --> Failure --> Fatal error
```

The `allowBootstrap` flag determines whether a cold-boot is permitted. It is set to `false` for commands that should not trigger a daemon boot (`stop`, `status`).

> [!NOTE]
> `myctl status` and `myctl stop` are special-cased in `main()`. If daemon is offline, they return a friendly message without cold-booting.
