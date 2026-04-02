# Daemon Architecture Vision

This document outlines the daemon architecture and serves as the single reference for the refactor. It prioritizes strict separation of concerns, developer ergonomics, and long-term maintainability.

## 1. Guiding Principles

This design strictly adheres to the core project principles:

-   **Lean Client / Fat Server**: The Go client is a simple IPC proxy. The Python daemon contains all business logic.
-   **Self-Bootstrapping**: The daemon manages its own `uv` environment via `mise`, ensuring it runs in a correct and isolated context.
-   **XDG Compliance**: All file paths (config, data, runtime) are resolved dynamically using `platformdirs` and XDG environment variables.
-   **Strict API Boundaries**: This is the cornerstone of the design. Plugins must be architecturally prevented from accessing internal engine components, ensuring stability and a clear development contract.

## 2. Proposed Directory & File Structure

To enforce the API boundary, the `daemon/` directory is restructured to separate the internal engine from the public plugin API into two distinct Python packages.

```text
daemon/
├── pyproject.toml       # Defines the project, dependencies, and scripts.
|
├── myctl/
│   └── api/             # The PUBLIC SDK package for plugins.
│       ├── __init__.py  # Exports the stable, public API (Plugin, log, etc.).
│       ├── commands.py  # Decorators and classes for command registration.
│       └── context.py   # Defines any public parts of the Context object.
│
└── myctld/              # The INTERNAL engine package. 100% private.
    ├── __init__.py
    ├── __main__.py      # Package entrypoint for running the daemon.
    ├── app.py           # Main application object, lifecycle management.
    ├── boot.py          # Self-bootstrapping and environment setup logic.
    ├── config.py        # Handles loading config from XDG paths.
    ├── ipc.py           # Manages the Unix socket and JSON-IPC protocol.
    └── registry.py      # Handles plugin discovery, loading, and sandboxed execution.
```

## 3. Key Architectural Concepts

### 3.1. Two Distinct Packages

-   **`myctl.api`**: This is the **only** package a plugin can import. It represents the stable, public-facing SDK. Its contents are minimal, explicit, and heavily documented. It contains decorators (`@command`), public data classes, and the global `log` proxy.
-   **`myctld`**: This is the engine. It is **not** importable by plugins. This separation is enforced by the Python path configuration during plugin loading, making it impossible for a plugin to import private daemon modules directly. This is a much cleaner and more robust solution than a runtime import guard.

### 3.2. The Bootstrapper (`myctld/__main__.py`)

The package entrypoint has one job: find the correct Python environment (or create it if it doesn't exist) using the logic from `myctld.boot`. Once the environment is ready, it executes `myctld.app` to start the main application.

### 3.3. The Application (`myctld.app`)

This is the daemon's main process controller.
1.  It initializes the `registry` to discover and load all plugins.
2.  It starts the `ipc` listener to wait for connections from the Go client.
3.  It enters the main event loop, dispatching requests from the IPC layer to the `registry`.

### 3.4. The Registry (`myctld.registry`)

This is the heart of the plugin system and the enforcer of the API boundary.
1.  It scans plugin directories as defined by the XDG specification.
2.  For each plugin, it creates a **sandboxed execution environment**. It carefully constructs a `sys.path` for the plugin that *only* includes the `myctl.api` package and the plugin's own `src` directory.
3.  It loads the plugin's `main.py` and registers its commands, hooks, and other components.
4.  When a command is dispatched, the registry binds the necessary context (like the plugin's identity for the logger) before executing the plugin's code within its sandbox.

This design provides a robust, secure, and maintainable architecture. It makes the contract with plugin developers crystal clear: "You can only use what's in `myctl.api`. Everything else is an implementation detail you don't need to worry about." This allows the engine's internals to be refactored, optimized, and changed without ever breaking a plugin.
