# Bootstrapping: The Autonomous Lifecycle

MyCTL ensures a seamless developer experience ("it just works") even when the Python daemon is dormant. It achieves this through a multi-stage **Cold Boot Handshake**.

The Go client detects the dead connection, invokes a sandbox validation sequence, mutates the Python process, and safely waits for the `__DAEMON_READY__` token.

## 1. Socket Verification (`cmd/main.go`)

Every command execution (`myctl status`) immediately attempts a `net.Dial("unix", path)` against the defined `$XDG_RUNTIME_DIR/myctl/myctld.sock`.

If the dial succeeds, we follow the $O(1)$ [Warm Boot Flow](architecture.md). If the dial returns an `error`, the Go proxy catches it entirely before ever throwing a failure to the user, and immediately enters the **Cold Boot Sequence** via `BootstrapDaemon()`.

## 2. Process Identification (`cmd/daemon.go`)

To trigger the Daemon, the Go client must first locate a valid Python interpreter capable of executing `myctld`.

### Dynamically Locating Python
The client leverages `exec.LookPath("python3")` rather than a hardcoded absolute path like `/usr/bin/python3`.

**Why?** Operating systems like NixOS, macOS (Homebrew), or systems utilizing toolchain managers like `mise` install Python in highly non-standard locations. `exec.LookPath` flawlessly resolves the current environment's globally available Python, maintaining universal compliance.

The Go client spawns the `exec.Command`, binding its standard output to a local `bufio.Scanner`, and calls `.Start()`. At this precise moment, the Go execution blocks iteratively, yielding control solely to the `myctld` Python script.

## 3. Sandboxing & Process Mutation (`daemon/myctld`)

We deliberately design the engine to refuse execution within the user's global Python environment, eliminating conflicts with system package managers (`apt`, `pacman`).

### Stage A: The `sys.prefix` Invariant
The very first lines of `myctld` (before any complex standard libraries or SDKs are even imported) demand an absolute check of its own operating context.

It extracts the active environment via `sys.prefix` and compares it against the strict target sandbox path derived from `$XDG_DATA_HOME` (`~/.local/share/myctl/venv`).

If the values match, this indicates the process successfully booted directly inside its dedicated virtual environment, and the application procedurally starts the core Registry (`myctl.core`).

### Stage B: Autonomous `uv sync`
If `sys.prefix` implies a global runtime execution, the daemon halts. It discovers the absolute path to `astral-sh/uv` to enforce isolation.

`uv` (a fast Rust-based standard) is invoked as a subprocess to:
1. Initialize the target virtual environment if it does not exist.
2. Resolve and install the required structural dependencies (`pydbus`, `pulsectl-asyncio`).
3. Explicitly link the MyCTL Daemon (`pyproject.toml`) into the sandbox via an Editable Build (`pip install -e .`).

### Stage C: `os.execv` (The Crucial Step)
Once `uv sync` ensures perfect environment synchronization, the script must reboot *inside* that specific virtual environment.

Instead of spawning an orphaned child process via `subprocess.run`, the daemon executes:
```python
os.execv(python_sandbox_bin, [python_sandbox_bin, __file__] + sys.argv[1:])
```
This is a low-level POSIX call. It entirely replaces the current Python process image with a freshly initialized one pointing to the internal Virtual Environment `python` interpreter, maintaining the exact same PID and retaining the original terminal constraints. The original process structurally ceases to exist.

## 4. The Handshake (`__DAEMON_READY__`)

With `os.execv` complete, `myctld` restarts natively inside `~/.local/share/myctl/venv`.

It configures local dynamic paths (like injecting `myctl_sdk.pth` directly into `site-packages`), instantiates the `CommandRegistry`, models its N-Level plugins, and binds `asyncio.start_unix_server` to the socket location on disk.

Only when the Socket is 100% bound, successfully listening, and the `loop.run_forever()` call is structurally prepared, does the Python engine flush a dedicated token to standard output:

> **`__DAEMON_READY__`**

The Go proxy, which has been passively spinning its `bufio.Scanner` scanning the `stdoutPipe` throughout this entire `uv` -> `execv` lifecycle, intercepts this string.

```go
for scanner.Scan() {
    line := scanner.Text()
    if line == "__DAEMON_READY__" {
        log.Debug().Msg("Handshake successful: Unblocking proxy.")
        go cmd.Wait()  // Detach daemon
        return nil     // Unblock the user request
    }
}
```

The blocking iterator returns `nil`, seamlessly proceeding to map the user's original `myctl` operation across the newly available IPC socket path without generating any perceived application failure.
