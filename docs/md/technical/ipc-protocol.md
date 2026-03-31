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

## 🔒 Payload Specifications

The communication between the client and server relies on strict structural payloads that map directly between Go and Python.

### 1. The Request Payload

The Client sends exactly one JSON object per command containing the context required for Python to resolve the command hierarchy.

**Client Request Structure**:

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

### 2. The Response Payload (Python -> Client)

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
- **`data`**: Can be a flat string or a nested object. The Client determines the output format:
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

```bash-vue
# Manually issue a ping request
echo '{"path": ["ping"]}' | nc -U {{metadata.paths.socket}}
```

---

## 🔐 Reserved System Namespace

The Engine contains a set of reserved commands that are always available, regardless of which plugins are loaded. Their routing keys are prefixed with `__sys_` to prevent collision with user-created plugin namespaces. These are dispatched inside `CommandRegistry` before the plugin routing table is ever consulted.

| Command Path    | Internal Handler | Purpose                                                                                                                           |
| :-------------- | :--------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `__sys_schema`  | `_sys_schema`    | Returns the full command hierarchy tree as a JSON object. Used exclusively by the Client on every boot to inflate its Cobra tree. |
| `__sys_version` | `_sys_version`   | Returns the daemon's `APP_VERSION` string. Also aliased as `version`, `--version`, `-v`, `ver`.                                   |
| `__sys_logs`    | `_sys_logs`      | Returns the last 30 lines of `$XDG_STATE_HOME/myctl/daemon.log`.                                                                  |

> [!IMPORTANT]
> The `__sys_schema` path is a critical internal contract. The Client always requests `["__sys_schema"]` — it must never be re-assigned or overridden by a plugin. Because the shadowing mechanism operates only on the plugin-tier routing table (see [Plugin Discovery](plugin-discovery.md)), system handlers are structurally immutable.

The full set of system aliases (e.g., `stop`, `exit`, `quit`) are registered in the `_system_handlers` dictionary at `CommandRegistry.__init__`. Because these are keys in the top-level dispatch map, any plugin with a matching Plugin ID (e.g., a plugin folder named `stop/`) would shadow them. This is an intentional design allowing advanced users to override default behavior.

---

## 🛡️ Client-Side Fault Tolerance

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

The `allowBootstrap` flag determines whether a cold-boot is permitted. It is set to `false` for commands that should not trigger a daemon boot (`stop`, `status`) — these commands check if the daemon is alive without attempting to start it. All other user commands pass `allowBootstrap: true` via `executeDaemonCommand`.

> [!NOTE]
> `myctl status` and `myctl stop` are special-cased in `main()`. Before the schema fetch, they call `fetchSchema(false)`. If the daemon is offline, they short-circuit and print a human-readable message (`"Daemon Status: offline"`) instead of triggering a cold boot. This prevents users from accidentally starting the daemon by checking its status.
