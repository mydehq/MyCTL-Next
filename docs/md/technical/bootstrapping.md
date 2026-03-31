# Bootstrapping: The UV Orchestration Layer

MyCTL is designed with a **Managed Runtime Architecture**. Instead of relying on the host's system Python—which can be inconsistent across distributions—the Go proxy uses [uv](https://docs.astral.sh/uv/) to orchestrate a deterministic, high-performance execution environment.

## 1. The Entry Point Handshake (`cmd/main.go`)

Every execution of `myctl` begins with a connection attempt to the Unix socket at `$XDG_RUNTIME_DIR/myctl/myctld.sock`. If the socket is unreachable, the Go client enters the **Cold Boot Sequence**.

### The `uv` Orchestrator

The proxy verifies that `uv` is installed and then executes the daemon via:

```go
uv run --project <daemon_root> python <daemon_script>
```

By leveraging `uv run`, MyCTL achieves:

- **Zero-Python Portability**: If `python3` isn't in the system path, `uv` will automatically download a managed Python version.
- **Environment Isolation**: The runtime is strictly bound to `{{metadata.paths.venv}}` via the `UV_PROJECT_ENVIRONMENT` variable.
- **Implicit Sync**: `uv` ensures all core dependencies (Pydantic, dbus-fast, etc.) are up-to-date before launching the server.

---

## 2. Handshake Protocol (`__DAEMON_READY__`)

To prevent race conditions where the CLI tries to send commands to a half-booted server, MyCTL utilizes a safe stdout handshake.

1.  **Block**: The Go proxy opens a pipe to the daemon's stdout and blocks.
2.  **Initialize**: The Python engine loads the `CommandRegistry` and maps all available plugins.
3.  **Bind**: The Asyncio server binds to the Unix socket.
4.  **Signal**: Once the socket is ready to accept connections, the daemon flushes a unique token: `__DAEMON_READY__`.
5.  **Unblock**: The Go proxy intercepts this token, detaches the daemon process, and resumes the original user command.

---

## 3. Persistent Lifecycle

Once booted, the daemon remains in the background to handle future requests with $O(1)$ response times.

- **Warm Boots**: Subsequent `myctl` commands connect directly to the existing socket, bypassing the `uv` check entirely for sub-millisecond execution.
- **Self-Healing**: If the daemon crashes or the socket is deleted, the very next `myctl` command will trigger the Cold Boot Sequence again automatically.

---

## 4. XDG Compliance

MyCTL strictly follows the XDG Base Directory Specification:

| Path Type   | Location                  | Usage                                 |
| :---------- | :------------------------ | :------------------------------------ |
| **Runtime** | `$XDG_RUNTIME_DIR/myctl/` | Unix IPC Socket (`myctld.sock`)       |
| **Data**    | `$XDG_DATA_HOME/myctl/`   | Managed `venv` and user plugins       |
| **State**   | `$XDG_STATE_HOME/myctl/`  | Persistent engine logs (`daemon.log`) |
