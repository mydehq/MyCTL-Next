# IPC Protocol Specification

MyCTL uses a lightweight, high-performance protocol based on **Newline-Delimited JSON (NDJSON)** over a native Unix Domain Socket.

This protocol acts as the vital bridge between the agnostic Go Proxy and the intelligent Python Daemon, ensuring every command and response is processed as a single, isolated stream of bytes.

## Why NDJSON?

In traditional socket programming, clients and servers must either track continuous byte-streams or implement complex content-length header framing (like HTTP) to know exactly when a message ends.

NDJSON guarantees that exactly one JSON struct exists per line.

This enables the Go proxy to achieve $O(1)$ parsing speed. It never manages streaming memory buffers; it simply executes:
```go
reader := bufio.NewReader(conn)
respLine, err := reader.ReadString('\n')
```
Once it hits the newline character (`\n`), it directly unmarshals the single, contained JSON string and immediately terminates the proxy tunneling entirely, freeing the process and yielding `ExitCode` back to the user application shell natively.


## 🔒 Payload Specifications

The communication between the client and server relies on strict structural payloads mimicking exact Go struct representations (`Request`, `Response`, `CommandNode`).

### 1. The Request Payload (Go -> Python)

The Go client sends exactly one JSON object per command containing the context required for Python to resolve the command contextually.

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
  "path": ["audio", "volume", "set"],
  "args": ["50", "--verbose"],
  "env": {"USER": "soymadip", "XDG_SESSION_TYPE": "wayland"},
  "cwd": "/home/soymadip/Projects/MyCTL"
}
```

#### The `cwd` Context Trap
Because the Python Daemon runs continuously in the background using `sys.prefix`, standard library calls like `os.getcwd()` will almost always return an internal system path like `/run/user/1000`. 
By passing the `cwd` over IPC, the Go proxy guarantees that plugins built under `myctl.api` can accurately determine the exact directory from which the user initiated the command interaction.

### 2. The Response Payload (Python -> Go)

The Python daemon executes the handler identified by the `path`, waits for execution (via `await`), and strictly responds with exactly one JSON object.

**Go Struct (`cmd/main.go`)**:
```go
type Response struct {
	Status   string      `json:"status"`
	Data     interface{} `json:"data"`
	ExitCode int         `json:"exit_code"`
}
```

**JSON Wire Format**:
```json
{
  "status": "ok",
  "data": "Volume adjusted to 50%",
  "exit_code": 0
}
```

*   **`status`**: `"ok"` or `"error"`. 
*   **`data`**: Any struct, string, or interface representing standard output logic. The Go Proxy determines output types autonomously. If `data` is a flat string, it pushes directly to `os.Stdout`. If `data` incorporates nested dictionaries or arrays, the generic `interface{}` maps natively back into formatted `json.MarshalIndent` representing clean JSON CLI tools instantly.
*   **`exit_code`**: Governs shell scripting integration by safely executing `os.Exit(resp.ExitCode)` in the Go context natively.


## 📁 Socket Configuration

The architecture strictly adheres to XDG configuration rules to prevent cross-user permission violations.

| Path | Purpose |
| :--- | :--- |
| **`$XDG_RUNTIME_DIR/myctl/myctld.sock`** | The fundamental IPC bind point for the Daemon (`os.Getuid()`). |
| **`/tmp/myctl-$UID.sock`** | The legacy fallback algorithm if `RUNTIME_DIR` is natively missing. |

### Diagnostic Access
Because the entire protocol is plain-text NDJSON over a standard socket, you can directly debug the intelligent Python Daemon completely independently of the Go proxy by streaming bytes purely via GNU `socat` or `nc -U`:

```bash
# Issue an NDJSON request natively on Linux via netcat
echo '{"path": ["ping"]}' | nc -U $XDG_RUNTIME_DIR/myctl/myctld.sock
```
