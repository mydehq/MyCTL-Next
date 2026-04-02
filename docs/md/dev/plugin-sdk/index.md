# Plugin SDK

MyCTL is designed to be extensible through a stable, public SDK surface: `myctl.api`.

## Plugin Load Flow

When MyCTL starts, each plugin goes through a strict load sequence:

1. Discover plugin directories from configured tiers.
2. Validate plugin identity and API compatibility from `pyproject.toml`.
3. Sync declared dependencies using `uv`.
4. Import the plugin entry module and register commands/hooks.
5. Run `on_load`, then start `periodic` tasks.

If any step fails, that plugin is rejected and the daemon keeps running.
