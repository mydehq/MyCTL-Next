# IPC Protocol: The NDJSON Handshake

MyCTL uses a lightweight, high-performance protocol based on **Newline-Delimited JSON (NDJSON)** over a native Unix Domain Socket. This protocol serves as the vital bridge between the agnostic Go Proxy and the persistent Python Engine.

## Why NDJSON?

In traditional socket programming, clients and servers must often implement complex framing (like HTTP `Content-Length`) to know exactly when a message ends. NDJSON simplifies this by guaranteeing that exactly one JSON object exists per line.

This enables the Go proxy to achieve $O(1)$ parsing speed. It never manages streaming memory buffers; it simply reads until the newline character (`\n`):

```go
reader := bufio.NewReader(conn)
respLine, _ := reader.ReadString('\n')
```

Once the newline is reached, the proxy unmarshals the payload, renders the output, and immediately terminates with the provided `ExitCode`.

---

## 🔒 Payload Specifications

The communication between the client and server relies on strict structural payloads that map directly between Go and Python.

### 1. The Request Payload (Go -> Python)

The Go client sends exactly one JSON object per command containing the context required for Python to resolve the command hierarchy.

**Go Struct (`cmd/main.go`)**:

```go
type Request struct {
    Path []string          `json:"path"`
    Args []string          `json:"args"`
    Cwd  string            `json:"cwd"`
    Env  map[string]string `json:"env"`
}
```

**JSON Wire Format**:

```json
{
  "path": ["audio", "sink", "mute"],
  "args": ["--all"],
  "env": { "USER": "soymadip", "DISPLAY": ":0" },
  "cwd": "/home/soymadip/Projects/MyCTL"
}
```

> [!NOTE]
> **The `cwd` Context**: Since the Python Engine runs continuously in the background, its internal working directory does not match the user's shell. Passing `cwd` over IPC allows plugins to accurately resolve local paths (e.g., `myctl edit ./config.json`).

### 2. The Response Payload (Python -> Go)

The Python engine executes the handler and responds with exactly one JSON object.

**Go Struct (`cmd/main.go`)**:

```go
type Response struct {
    Status   string      `json:"status"`
    Data     interface{} `json:"data"`
    ExitCode int         `json:"exit_code"`
}
```

- **`status`**: `"ok"` or `"error"`.
- **`data`**: Can be a flat string or a nested object. The Go Proxy determines the output format:
  - **Strings**: Printed directly to `stdout`.
  - **Dicts/Lists**: Pretty-printed as JSON for pipeability (e.g., to `jq`).
- **`exit_code`**: Governs shell scripting integration (e.g., `os.Exit(resp.ExitCode)`).

---

## 📁 Socket Configuration

The architecture adheres to XDG standards to ensure isolation and security.

| Path                            | Purpose                                          |
| :------------------------------ | :----------------------------------------------- |
| **`{{metadata.paths.socket}}`** | Primary IPC bind point.                          |
| **`/tmp/myctl-$UID.sock`**      | Legacy fallback if `XDG_RUNTIME_DIR` is missing. |

### Diagnostic Access

Because the protocol is plain-text NDJSON, you can debug the Python Engine independently using standard tools like `netcat` or `socat`:

```bash
# Manually issue a ping request
echo '{"path": ["ping"]}' | nc -U {{metadata.paths.socket}}
```
