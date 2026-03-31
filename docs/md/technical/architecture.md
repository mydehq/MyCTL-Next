# Architecture: The Managed Runtime Engine

MyCTL subverts the traditional CLI model. Instead of hardcoding commands, parsing logic, and execution functions into a single compiled binary, MyCTL employs a **100% Logic-Less Go Proxy** orchestrated by **UV** and backed by a **Persistent Python Engine**.

This architecture guarantees sub-millisecond CLI responsiveness from a portable binary, while maintaining a rich, stateful, and dynamically extensible backend environment that is entirely self-managed.

## 🗺️ Codebase Topology

To understand the architecture, developers must first map the concepts to the physical repository. The codebase is strictly bifurcated:

- **`cmd/` (The Proxy Layer)**
  - `main.go`: The central Go tunnel. Responsible for dialing the Unix Socket, fetching the JSON schema, inflating the Cobra CLI tree, and proxying raw arguments.
  - `daemon.go`: The **UV-Native Orchestrator**. Only invoked if the Unix Socket is missing. It manages the runtime environment and launches the engine.
- **`daemon/` (The Engine Layer)**
  - `myctld`: The Python entry point. An extremely lean bootstrapper designed for execution via `uv run`.
  - `myctl/core/registry.py`: The brain. Constructs the $O(1)$ routing dictionary, loads plugins via `importlib`, and handles SDK auto-injection.
  - `myctl/core/ipc.py`: The `asyncio` Unix Socket server loop.
- **`plugins/` (The Extension Tier)**
  - Tiered directories containing a `pyproject.toml` manifest and a standard `main.py` logic entry.

---

## 🏎️ The Logic-Less Client (Go)

The `myctl` binary is written in Go to guarantee ultra-fast cold starts and a zero-dependency system footprint. However, its source code contains zero domain logic—it doesn't even know what commands it supports natively.

### 1. Dynamic Tree Inflation (`spf13/cobra`)

Usually, developers hardcode commands via `rootCmd.AddCommand()`. MyCTL instead fetches a JSON payload from the Python daemon during initialization. The client recursively traverses this JSON using the `buildCobraCommand` function, unmarshaling the payload into living `*cobra.Command` pointers.

This means the Go binary automatically inherits new features and documentation updates directly from Python without ever requiring a recompile.

### 2. The Unknown Flags Bypass

Because the Go proxy builds its CLI tree dynamically, it cannot know ahead of time what specific flags (e.g., `--volume 50`) a deeply nested plugin might require. To prevent Cobra from failing, the client applies a global bypass:

```go
cmd.FParseErrWhitelist.UnknownFlags = true
```

This hack forces Cobra to collect unmapped flags and pass them blindly into the unparsed argument slice. The Go proxy then shovels this raw array across the IPC tunnel, allowing Python to perform the actual deterministic parsing.

### 3. Pristine Console Output (`zerolog`)

Standard Go loggers are often unsuitable for professional CLI tools. MyCTL leverages `zerolog` with a heavily customized `ConsoleWriter`. We strip timestamps and generic field names to provide color-coded terminal output that mimics native shell applications.

---

## 🧠 The Persistent Engine (Python)

The core execution logic resides in a continuous, stateful `myctld` Python daemon ({{metadata.versions.python_min}}). While Python scripts are traditionally slow to start, pushing the engine into the background solves this constraint while maintaining a rich system-integration ecosystem.

### 1. Asynchronous Concurrency (`asyncio`)

The daemon binds to a Unix Socket using `asyncio.start_unix_server`. This architecture ensures that slow tasks (e.g., hardware IO or network requests) never block the system execution loop. Multiple CLI interactions can be processed concurrently within the same event loop.

The `myctld` server structurally insulates itself. If the Go proxy attempts to launch the daemon from a global `$PATH`, the daemon autonomously spawns an isolated `uv` virtual environment and replaces its own process image to lock itself inside the sandbox (detailed entirely in [Self-Sustaining Lifecycle](bootstrapping.md)).

Furthermore, absolutely everything the daemon touches adheres to strict XDG Base Directory standards:

| Component        | Path Strategy                          | Default Environment Path     |
| :--------------- | :------------------------------------- | :--------------------------- |
| **Sandbox Venv** | `xdg.DataHome`                         | `{{metadata.paths.venv}}`    |
| **User Plugins** | `xdg.DataHome`                         | `{{metadata.paths.plugins}}` |
| **Socket IPC**   | `xdg.RuntimeDir` -> `$UID` -> fallback | `{{metadata.paths.socket}}`  |

---

## 🔄 Core Operational Flow

The interaction is completely governed by the status of the Unix Socket.

```mermaid
sequenceDiagram
    participant CLI as Go Proxy
    participant UV as UV Orchestrator
    participant Socket as Unix Socket
    participant Engine as Python Engine

    Note over CLI: User executes `myctl <command>`

    CLI->>Socket: Dial("unix", path)
    alt Socket Found (Warm Boot)
        CLI->>Socket: NDJSON Request Payload
        Socket-->>Engine: StreamReader.readline()
        Engine->>Engine: N-Level Route Dispatch
        Engine-->>Socket: NDJSON Response
        Socket-->>CLI: Parse JSON & os.Exit(ExitCode)
    else Socket Missing (Cold Boot)
        Note over CLI, UV: Handshake Sequence
        CLI->>UV: uv run --project <daemon_root>
        UV->>Engine: Launch managed python
        Engine->>Engine: Discover plugins & Inject SDK
        Engine-->>CLI: "__DAEMON_READY__" Token
        Note right of CLI: (Handshake complete. Proxy resumes.)
    end
```
