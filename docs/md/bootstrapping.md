# Handshake & Bootstrapping

A critical piece of the MyCTL experience is that it **"just works"** even when the daemon is cold. This requires a sophisticated multi-stage bootstrapping process that translates from the system Python into a high-performance, isolated virtual environment.

## Stages of Execution

### 1. Go Lifecycle Detection
When you execute `myctl`, the Go client first checks if `/run/user/1000/myctl-daemon.sock` is active and responding.

- **If Active**: The client instantly proxies the command strings in JSON format.
- **If Missing**: The client enters the **Cold Boot** routine.

### 2. Cold Boot Spawning
The Go client executes the entry point script using the system Python interpreter:
`/usr/bin/python3 /usr/share/myctl/daemon/myctl-daemon`

At this stage, the process is not yet in its sandbox. The Go client "blocks," reading from the daemon's `stdout` pipe.

### 3. Self-Re-Execution (Daemon Side)
The first few lines of the `myctl-daemon` script perform a **Sandbox Identity Check**:

1.  Compare `sys.prefix` (current environment) against the target sandbox path (`~/.local/share/myctl/venv`).
2.  If it doesn't match:
    - Automatically create the venv if it's missing.
    - Run `uv sync` (or `pip install`) to link the namespaced `myctl` SDK package.
    - Execute `os.execv` to **replace the current process** with a new one running inside the correct virtual environment.

### 4. Portability & "The Ready Signal"
Once the process is running inside the sandbox, it binds the Unix Socket and starts the `asyncio` loop. Only when the socket is 100% ready to receive commands does the daemon print:

`__DAEMON_READY__`

The Go client, which has been waiting on the other end of the pipe, sees this token and immediately knows it can safely send the user's command.

## Why this matters

- **Zero Global Pollution**: MyCTL core dependencies (like `pydbus`, `pulsectl-asyncio`, etc.) are never installed globally. They live only in the isolated sandbox.
- **SDK Availability**: Because `uv sync` is used during bootstrapping, the `myctl.api` SDK is always linked, giving you flawless IDE autocompletion when developing plugins.
- **Performance**: This multi-stage handshake happens in milliseconds. After the first command, subsequent commands use the **Warm Boot** path, which has near-zero overhead.
