# Bootstrapping: Managed Daemon Runtime

MyCTL is designed with a managed runtime architecture. Instead of relying on the host's system Python, the client uses [uv](https://docs.astral.sh/uv/) to keep the daemon environment synchronized.

In plain terms, bootstrapping means: if the daemon is not running yet, the client starts it in a controlled Python environment and waits until it is ready to answer requests.

## 1. The Entry Point Handshake (Client)

Every execution of `myctl` begins with a connection attempt to the Unix socket at `$XDG_RUNTIME_DIR/myctl/myctld.sock`. If the socket is unreachable, the Client enters the **Cold Boot Sequence**.

This is the difference between a warm run and a cold boot:

- warm run: the daemon already exists, so the client connects immediately
- cold boot: the daemon is missing, so the client starts it first

### The Runtime Sequence

When the socket is unreachable, the Client does the following:

```sh
uv sync --project <daemon_root>
<managed_venv_python> -m myctld
```

This gives MyCTL:

- **Environment Isolation**: The runtime is bound to `{{metadata.paths.venv}}` via `UV_PROJECT_ENVIRONMENT`.
- **Explicit Sync**: `uv sync` ensures dependencies are up-to-date before launch.
- **Standalone Runtime Process**: the running daemon is `myctld` (not a long-lived `uv run` parent process).

### Orchestration Constraints

The Client sets a critical environment variable before sync and launch:

```go
cmd.Env = append(os.Environ(), fmt.Sprintf("UV_PROJECT_ENVIRONMENT=%s", venvPath))
```

Where `venvPath` resolves to `$XDG_DATA_HOME/myctl/venv`. This override pins all sync/launch actions to the managed venv. The venv path is deterministic and user-scoped.

That makes the daemon environment predictable even when the user has many other Python installations on the machine.

The daemon search path resolution follows this precedence:

1. **Development (relative)**: At build time, `runtime.Caller(0)` resolves the path of `daemon.go`, and `daemonRoot` is derived two directories up from it — pointing to the project's `daemon/` folder.
2. **Production (absolute)**: If the relative path is unreliable (e.g., the binary is stripped), the path falls back to `$XDG_DATA_HOME/myctl/daemon`. This is where `mise run install` copies the daemon during installation.

---

## 2. Handshake Protocol (`__DAEMON_READY__`)

To prevent race conditions where the CLI tries to send commands to a half-booted server, MyCTL utilizes a safe stdout handshake.

The idea is simple: the daemon prints one known token only after it has finished binding the socket and is ready to serve requests.

1.  **Block**: The Client opens a pipe to the daemon's stdout and blocks.
2.  **Initialize**: The Python engine loads the `CommandRegistry` and maps all available plugins.
3.  **Bind**: The Asyncio server binds to the Unix socket (`asyncio.start_unix_server`).
4.  **Signal**: Once the socket is ready to accept connections, the daemon flushes a unique token to stdout: `print("__DAEMON_READY__", flush=True)`.
5.  **Unblock**: The Client intercepts this token and resumes the original user command.

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

- **Readiness Gate**: Client bootstrap unblocks only after `__DAEMON_READY__` is observed.
- **Output Channel Discipline**: readiness token uses stdout; structured logs are emitted to stderr (console) and file.
- **Failure Detection**: If the daemon's stdout pipe closes before `__DAEMON_READY__` is seen — for example, due to a Python import error during startup — `scanner.Scan()` returns `false`, and the Client surfaces a `"daemon process terminated prematurely before ready signal"` error.

---

## 3. Persistent Lifecycle

Once booted, the daemon remains in the background to handle future requests with $O(1)$ response times.

- **Warm Boots**: Subsequent `myctl` commands connect directly to the existing socket.
- **Self-Healing**: If the daemon crashes or the socket is deleted, the very next `myctl` command will trigger the Cold Boot Sequence again automatically.
- **Single-Instance Guard**: if a live daemon already owns the socket, a second daemon process is rejected.
- **Clean Shutdown**: `myctl stop` and `SIGINT`/`SIGTERM` trigger graceful shutdown and socket cleanup.

The daemon is meant to stay alive across many client invocations, not to restart for every command.

---

## 4. XDG Compliance

MyCTL strictly follows the XDG Base Directory Specification:

| Path Type   | Location                  | Usage                                 |
| :---------- | :------------------------ | :------------------------------------ |
| **Runtime** | `$XDG_RUNTIME_DIR/myctl/` | Unix IPC Socket (`myctld.sock`)       |
| **Data**    | `$XDG_DATA_HOME/myctl/`   | Managed `venv` and user plugins       |
| **State**   | `$XDG_STATE_HOME/myctl/`  | Persistent engine logs (`daemon.log`) |
