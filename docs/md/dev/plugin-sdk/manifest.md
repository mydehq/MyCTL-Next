# Plugin Manifest

The `pyproject.toml` file defines a plugin's identity, metadata, and dependency requirements. MyCTL reads this file during discovery before loading any plugin code.

## Manifest Reference

### `[project]` Table

Standard Python packaging metadata.

| Field          | Type            | Description                                                   |
| :------------- | :-------------- | :------------------------------------------------------------ |
| `name`         | `string`        | Must match the plugin directory name exactly.                 |
| `version`      | `string`        | Semantic version of the plugin.                               |
| `description`  | `string`        | Help text displayed for the plugin root group in the CLI.     |
| `authors`      | `array[table]`  | One or more plugin authors, usually captured during init.     |
| `dependencies` | `array[string]` | PyPI/Git packages. Will be installed automatically with `uv`. |

### `[tool.myctl]`

Metadata used by the MyCTL plugin engine.

| Field             | Type     | Default                       | Description                                                                  |
| :---------------- | :------- | :---------------------------- | :--------------------------------------------------------------------------- |
| **`api_version`** | `string` | `"{{metadata.versions.api}}"` | SDK version targeted by the plugin. Will be accepted till next major version |
| **`entry`**       | `string` | `"main.py"`                   | Plugin entry file. This is where cmds/flags must be registered               |

## Dependency Syncing

MyCTL uses `uv` to prepare plugin dependencies during discovery.

1. Discovery: the daemon reads the plugin's `dependencies` list.
2. Sync: `uv pip install` runs during discovery.
3. Isolation: packages resolve in the managed environment before the plugin is loaded.
