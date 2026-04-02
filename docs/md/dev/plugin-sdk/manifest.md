# Plugin Manifest

The `pyproject.toml` file defines a plugin's identity, metadata, and dependency requirements. MyCTL reads this file during discovery before loading any plugin code.

## Manifest Reference

### `[project]` Table

Standard Python packaging metadata.

| Field          | Type            | Description                                               |
| :------------- | :-------------- | :-------------------------------------------------------- |
| `name`         | `string`        | Must match the plugin directory name exactly.             |
| `version`      | `string`        | Semantic version of the plugin.                           |
| `description`  | `string`        | Help text displayed for the plugin root group in the CLI. |
| `authors`      | `array[table]`  | One or more plugin authors, usually captured during init. |
| `dependencies` | `array[string]` | PyPI/Git packages installed automatically through `uv`.   |

### `[tool.myctl]`

Metadata used by the MyCTL plugin engine.

| Field             | Type     | Default     | Description                                                                    |
| :---------------- | :------- | :---------- | :----------------------------------------------------------------------------- |
| **`api_version`** | `string` | `"1.0.0"`   | SDK version targeted by the plugin.                                            |
| **`entry`**       | `string` | `"main.py"` | Registration entry file. Keep this thin and delegate implementation to `src/`. |
| **`groups`**      | `dict`   | `{}`        | Help text for intermediate command groups.                                     |

### `[tool.myctl.groups]` Dictionary

Use this table to document command groups that contain nested commands.

```toml
[tool.myctl.groups]
"cpu info" = "Detailed CPU statistics and load monitoring"
"storage" = "Disk health and mount point management"
```

## Dependency Syncing

MyCTL uses `uv` to prepare plugin dependencies during discovery.

1. Discovery: the daemon reads the plugin's `dependencies` list.
2. Sync: `uv pip install` runs during discovery.
3. Isolation: packages resolve in the managed environment before the plugin is loaded.
