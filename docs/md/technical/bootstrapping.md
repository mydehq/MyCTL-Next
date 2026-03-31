# Bootstrapping: The UV Orchestration Layer

MyCTL is designed with a **Managed Runtime Architecture**. Instead of relying on the host's system Python—which can be inconsistent across distributions—the Client uses [uv](https://docs.astral.sh/uv/) to orchestrate a deterministic, high-performance execution environment.

## 1. The Entry Point Handshake (Client)

Every execution of `myctl` begins with a connection attempt to the Unix socket at `$XDG_RUNTIME_DIR/myctl/myctld.sock`. If the socket is unreachable, the Client enters the **Cold Boot Sequence**.

### The `uv` Orchestrator

The proxy verifies that `uv` is installed and then executes the daemon via:

```sh
uv run --project <daemon_root> python <daemon_script>
```

By leveraging `uv run`, MyCTL achieves:

- **Zero-Python Portability**: If `python3` isn't in the system path, `uv` will automatically download a managed Python version.
- **Environment Isolation**: The runtime is strictly bound to `{{metadata.paths.venv}}` via the `UV_PROJECT_ENVIRONMENT` variable.
- **Implicit Sync**: `uv` ensures all core dependencies (Pydantic, dbus-fast, etc.) are up-to-date before launching the server.

### Orchestration Constraints

The Client's daemon invocation sets a critical environment variable before spawning the process:

```go
cmd.Env = append(os.Environ(), fmt.Sprintf("UV_PROJECT_ENVIRONMENT=%s", venvPath))
```

Where `venvPath` resolves to `$XDG_DATA_HOME/myctl/venv`. This `UV_PROJECT_ENVIRONMENT` override is what pins `uv run` to MyCTL's managed venv, preventing it from creating a new, transient environment in `/tmp`. This is a hard constraint: **the venv path is deterministic and user-scoped**. It must persist across invocations, as plugins install their dependencies into this location.

The daemon search path resolution follows this precedence:

1. **Development (relative)**: At build time, `runtime.Caller(0)` resolves the path of `daemon.go`, and `daemonRoot` is derived two directories up from it — pointing to the project's `daemon/` folder.
2. **Production (absolute)**: If the relative path is unreliable (e.g., the binary is stripped), the path falls back to `$XDG_DATA_HOME/myctl/daemon`. This is where `mise run install` copies the daemon during installation.

---

## 2. Handshake Protocol (`__DAEMON_READY__`)

To prevent race conditions where the CLI tries to send commands to a half-booted server, MyCTL utilizes a safe stdout handshake.

1.  **Block**: The Client opens a pipe to the daemon's stdout and blocks.
2.  **Initialize**: The Python engine loads the `CommandRegistry` and maps all available plugins.
3.  **Bind**: The Asyncio server binds to the Unix socket (`asyncio.start_unix_server`).
4.  **Signal**: Once the socket is ready to accept connections, the daemon flushes a unique token to stdout: `print("__DAEMON_READY__", flush=True)`.
5.  **Unblock**: The Client intercepts this token, detaches the daemon process, and resumes the original user command.

### Handshake Internals

The Client manages the handshake via a `bufio.Scanner` on the daemon's `StdoutPipe`. The scanner loops over each line of output until it receives `__DAEMON_READY__`:

```go
scanner := bufio.NewScanner(stdoutPipe)
for scanner.Scan() {
    line := scanner.Text()
    if line == "__DAEMON_READY__" {
        go cmd.Wait() // Detach: prevent zombie process
        return nil
    }
    // Stream cold-boot progress to the terminal
    fmt.Printf("[myctl-boot] %s\n", line)
}
```

**Key mechanics:**

- **Log Streaming**: Any line printed to stdout by `uv` during environment sync (e.g., dependency resolution messages) is forwarded to the user's terminal prefixed with `[myctl-boot]`. This gives developers real-time feedback during a first-run setup.
- **Process Detachment (`go cmd.Wait()`)**: Once the ready signal is received, calling `go cmd.Wait()` in a goroutine detaches the daemon from the Client's foreground lifecycle. This is critical: without it, the daemon would become a zombie process once the Client exits. The goroutine absorbs the daemon's eventual exit status asynchronously, cleanly reclaiming OS resources. The daemon is then permanently adopted by the OS init system (PID 1).
- **Failure Detection**: If the daemon's stdout pipe closes before `__DAEMON_READY__` is seen — for example, due to a Python import error during startup — `scanner.Scan()` returns `false`, and the Client surfaces a `"daemon process terminated prematurely before ready signal"` error.

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
