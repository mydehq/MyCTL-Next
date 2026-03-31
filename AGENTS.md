# AGENTS.md — MyCTL System Design & Developer Guide

## Principles

Follow these always.

- **Always use `mise`** for toolchain management (Go, Python, Bun).
- **Only Build Via Mise**: Never run raw `go build` or `uv sync` commands manually. Use `mise run build`.
- **Always use `uv`** for Python environment and dependency management (triggered via `mise`).
- **Minimal Client Logic**: The Client is a $O(1)$ proxy.
- **Self-Bootstrapping**: The Python daemon manages its own isolated environment (venv).
- **XDG Specification**: Always use `platformdirs` and XDG environment variables for path resolution.
- **Implicit Identity**: The directory name of a plugin is its **Plugin ID**, which automatically defines its primary CLI namespace.
- **Name Enforcement**: `[project].name` in a plugin's `pyproject.toml` **must** match the directory name exactly, or the plugin is rejected at load time.
- Always update docs after changes if needed.
- **Documentation Cohesion**: Every documentation edit must be synthesized into the existing content. Do not simply append information; ensure the tone, structure, and technical flow feel unified and professionally authored.
- Use [roadmap](./docs/md/roadmap.md) as roadmap. Update it when needed.

---

## 1. Project Overview

MyCTL is a high-performance Linux desktop controller built on a **Lean Client / Fat Server** architecture.

### Core Components

- **`cmd/` (Thin Client)**: The high-performance CLI entry point. Fetches JSON schema from daemon at runtime to build Cobra CLI tree; forwards all execution to Python via JSON-IPC.
- **`daemon/` (Smart Server)**: Python 3.13+ namespaced package. Handles self-bootstrapping, N-level command routing, and native system integrations.
- **IPC**: Newline-delimited JSON over `$XDG_RUNTIME_DIR/myctl/myctld.sock`.

---

## 2. Directory Layout

```text
MyCTL/
├── bin/                 # Compiled executable (myctl)
├── cmd/                 # Go source (Flat Layout)
│   ├── main.go          # CLI Proxy
│   └── daemon.go        # Handshake & Bootstrapping
├── daemon/              # Python source
│   ├── myctld           # Entry point (Bootstrapper)
│   ├── pyproject.toml   # Project/SDK Definition
│   └── myctl/           # Namespaced Engine Package
│       ├── api/         # Public SDK (use 'add_cmd')
│       └── core/        # Internal Engine (IPC, Registry, App)
├── plugins/             # Dev-level plugins (highest priority tier)
└── docs/                # Technical Documentation (VitePress)
    └── md/              # Documentation Source
```

---

## 3. Documentation Portal

For deep technical dives, consult the **MyCTL Developer Portal**:

- [Architecture Overview](docs/md/technical/architecture.md)
- [Self-Bootstrapping Lifecycle](docs/md/technical/bootstrapping.md)
- [IPC Protocol Specification](docs/md/technical/ipc-protocol.md)
- [Command Registry Engine](docs/md/technical/registry.md)
- [Plugin Discovery Tier](docs/md/technical/plugin-discovery.md)
- [Server API Guide](docs/md/dev/server-api.md)
- [Plugin SDK Guide](docs/md/dev/plugin-sdk.md)

---

## 4. Development Workflow

1. **Bootstrap**: `mise install`
2. **Build**: `mise run build` (Builds Client + syncs daemon)
3. **Trace**: `LOG_LEVEL=DEBUG ./daemon/myctld`
4. **SDK Setup**: `myctl sdk setup` (Configures IDE for `myctl.api` autocompletion)
