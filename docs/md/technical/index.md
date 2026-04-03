# Technical Documentation Overview

Welcome to the **MyCTL "Source of Truth" Technical Manual**.

This section provides an exhaustive, code-level view of how the system operates. It is designed to be so detailed that you should be able to understand the entire logic flow without reading the source code.

## Navigation Map

### 🛠️ [Core Architecture](./core/architecture.md)
*   **The Blueprint**: How the Go Client and Python Engine fit together.
*   **The Boundary**: The strict separation rules between the Engine and the SDK.
*   **Logical Runtime**: How the persistent background daemon stays alive.

### 🔌 [Plugin System](./plugins/discovery.md)
*   **Discovery**: How folders on disk are turned into executable logic.
*   **Security**: The Import Guard and namespace isolation that keeps the Engine safe.
*   **Lifecycle**: From cold-boot to hot-reload.

### 🚦 [Registry & Dispatch](./registry/dispatch.md)
*   **The Routing Table**: How a command path like `["foo", "bar"]` finds its handler.
*   **Privileged Access**: The difference between a standard and a System Context.
*   **Schema Inflation**: How the Engine tells the Client which commands exist.

### 🌐 [IPC & Protocols](./core/ipc-protocol.md)
*   **Wire Format**: The details of the NDJSON protocol over Unix Sockets.
*   **Schemas**: Exact JSON fields for all requests and responses.
*   **Interactive Flow**: How the "Ask" prompt-response cycle works.

### 📦 [SDK Specification](./sdk/protocols.md)
*   **The Interface**: Detailed method signatures for the `myctl` package.
*   **Structural Typing**: Why we use Protocols to decouple the SDK from the Engine.

---

> [!TIP]
> **New to the project?** Start with the **[Core Architecture](./core/architecture.md)** to understand the mental model behind MyCTL's "Lean Client / Fat Server" design.
