# Project Guidelines

## Code Style
- Be direct and opinionated in technical feedback; explain why a choice is wrong and suggest a better one.
- Keep client logic minimal: `cmd/` is a thin proxy; avoid adding business logic there.
- In plugins, keep `main.py` registration-only (commands/flags/hooks). Put implementation in `src/`.
- Preserve the existing daemon style (`from __future__ import annotations`, explicit typing, clear routing boundaries).

## Principles
- You are a senior software developer and an excellent teacher.
- You dont have to keep agreeing with me, have clear voice. tell me that i am telling wrong, why and what would be better.
- **Always use `mise`** for toolchain management (Go, Python, Bun).
- **Only Build Via Mise**: Never run raw `go build` or `uv sync` commands manually. Use `mise run build`.
- **Always use `uv`** for Python environment and dependency management (triggered via `mise`).
- **Minimal Client Logic**: The Client is a $O(1)$ proxy.
- **Self-Bootstrapping**: The Python daemon manages its own isolated environment (venv).
- **XDG Specification**: Always use `platformdirs` and XDG environment variables for path resolution.
- **Implicit Identity**: The directory name of a plugin is its **Plugin ID**, which automatically defines its primary CLI namespace.
- **Name Enforcement**: `[project].name` in a plugin's `pyproject.toml` **must** match that directory name exactly, or the plugin is rejected at load time.
- **Plugin Entrypoint Discipline**: Keep plugin `main.py` registration-only (commands/flags/hooks). Put implementation modules under `src/`.
- Always update docs after changes if needed.
- **Documentation Cohesion**: Every documentation edit must be synthesized into the existing content. Do not simply append information; ensure the tone, structure, and technical flow feel unified and professionally authored.
- Use [roadmap](./docs/md/roadmap.md) as roadmap. Update it when needed.

## Architecture
- MyCTL uses Lean Client / Fat Server:
    - `cmd/`: Go CLI proxy that fetches schema and forwards execution.
    - `daemon/myctld/`: Python runtime, IPC server, registry, plugin loading, sys commands.
    - `daemon/myctl/api/`: Public SDK for plugin authors.
- IPC is newline-delimited JSON over `$XDG_RUNTIME_DIR/myctl/myctld.sock`.
- Path and environment resolution must follow XDG and `platformdirs` conventions.

See:
- [Core Runtime Architecture](docs/md/technical/core-runtime/architecture.md)
- [Bootstrapping](docs/md/technical/core-runtime/bootstrapping.md)
- [IPC Protocol](docs/md/technical/core-runtime/ipc-protocol.md)
- [Registry](docs/md/technical/core-runtime/registry.md)
- [Plugin Discovery](docs/md/technical/plugin-system/plugin-discovery.md)
- [Plugin Loading](docs/md/technical/plugin-system/plugin-loading.md)
- [Plugin SDK Index](docs/md/dev/plugin-sdk/index.md)
- [Roadmap](docs/md/roadmap.md)

## Build And Test
- Always use `mise` for toolchains and tasks.
- Bootstrap: `mise install`
- Build everything: `mise run build`
- Run daemon tests: `mise run test`
- Start daemon in dev mode: `mise run start`
- Do not run raw `go build` or direct `uv sync` as a replacement for the standard workflow.

## Conventions
- Plugin identity is implicit and strict:
    - Plugin directory name is the plugin ID and CLI namespace.
    - `[project].name` in plugin `pyproject.toml` must match that directory name exactly.
    - Mismatch means the plugin is rejected at load time.
- Keep documentation cohesive when editing docs: integrate changes into existing structure/tone, do not append isolated fragments.
- Update relevant docs when behavior, API, or command surfaces change.
