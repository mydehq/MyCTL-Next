# Permission Model (Planned)

> [!WARNING]
> This page describes planned design work. The permission model below is not fully implemented in the current codebase.

## Why This Exists

As plugin ecosystems grow, MyCTL will need stronger safety boundaries around what plugins can import and execute.

The planned model is capability-based:

- Plugin declares required capabilities
- Runtime enforces allow/deny decisions
- Unsafe actions are blocked with explicit errors

---

## Planned Capabilities

Examples of capability categories:

- `system_info` (read-only system metrics)
- `notifications` (desktop notifications)
- `audio` (audio control APIs)
- `network` (outbound HTTP/network access)
- `shell_exec` (command execution)

Higher-risk capabilities would require stronger user consent.

---

## Planned Enforcement Layers

### 1) Manifest Declaration

Plugin declares capabilities in `pyproject.toml`.

### 2) Import Control

Runtime import filtering restricts unauthorized modules.

### 3) API Guarding

SDK APIs validate capability access before executing sensitive operations.

---

## Planned User Experience

- Low-risk plugins: load without prompt
- Higher-risk plugins: explicit consent prompt
- Denied plugins: clear error and block execution

---

## Current Status

Implemented today:

- Plugin validation (`pyproject.toml`, naming, API compatibility)
- Discovery/load isolation and error handling

Not implemented yet:

- Full capability declaration + enforcement pipeline
- Interactive consent flow for high-risk permissions
- Import-level deny/allow runtime policy

---

## Where to Track Progress

- [Project Roadmap](../roadmap.md)
- [Plugin Discovery](../plugin-system/plugin-discovery.md)
- [Plugin Loading](../plugin-system/plugin-loading.md)
