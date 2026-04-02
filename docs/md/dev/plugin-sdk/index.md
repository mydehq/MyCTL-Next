# Plugins SDK

MyCTL exposes one public plugin surface: `myctl.api`.

Use it to build plugins with the declarative API shown throughout the SDK docs:

## Current Surface

The plugin SDK currently provides:

- `Plugin` for declarative command/flag registration
- `Context` for safe per-invocation data
- `log` for plugin-scoped logging

## Reserved Command IDs

Plugin IDs live in a namespace that must not overlap with daemon built-in command IDs such as `schema`, `status`, or `plugin`.

- `plugin init` rejects a reserved name immediately at start.
- The daemon also validates conflicts at startup, before serving requests.
- The live built-in command registry is the source of truth, not a separate manual allow/deny list.

## Plugin Load Flow

When MyCTL starts, each plugin goes through a strict load sequence:

1. Discover plugin directories from configured tiers.
2. Validate plugin identity and API compatibility from `pyproject.toml`.
3. Sync declared dependencies using `uv`.
4. Import the plugin entry module and register commands/hooks.
5. Run `on_load`, then start `periodic` tasks.

If any step fails, that plugin is rejected and the daemon keeps running.
