# Installation Guide

MyCTL is designed to be a high-performance system controller that runs with minimal system dependencies. This guide covers the two primary tools required to build and execute the system.

## 🛠 Prerequisites

Ensure the following tools are available in your system path:

1.  **<a :href="metadata.tools.go">Go 1.22+</a>**: Used to build and compile the lean CLI Client.
2.  **<a :href="metadata.tools.uv">uv</a>**: Our primary runtime orchestrator. `uv` manages the Python environment, dependencies, and daemon bootstrapping.

> [!NOTE]
> **Minimal System Requirement**: You do **not** need a globally installed Python 3 shell to use MyCTL. `uv` will automatically download and manage its own private Python runtime for the daemon.

---

## 🏗 Building from Source

MyCTL uses `mise` for streamlined task management (optional but recommended).

### 1. Build the Client

Compile the Client from the project root:

```bash
go build -o ./bin/myctl ./cmd
```

### 2. Verify UV Availability

MyCTL relies on `uv` to orchestrate the daemon. Confirm it is installed:

```bash
uv --version
```

---

## 🚀 The First Run

Once built, you can trigger the **Universal Orchestration** by running any command. This will prompt `uv` to create the isolated environment and sync all core dependencies:

```bash
./bin/myctl start
```

For professional desktop installations, you may wish to add the `./bin` directory to your shell's `PATH`.
