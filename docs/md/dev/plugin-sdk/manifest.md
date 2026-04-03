# Plugin Manifest

The `pyproject.toml` file defines a plugin's identity, metadata, and dependency requirements. In **{{metadata.versions.api}}**, the manifest also serves as a critical source of truth for CLI documentation via the **Help Metadata Bridge**.

## Manifest Reference

### `[project]` Table

Standard Python packaging metadata used to identify and document your plugin.

| Field             | Type            | Description                                                                                                             |
| :---------------- | :-------------- | :---------------------------------------------------------------------------------------------------------------------- |
| `name`            | `string`        | The stable Plugin ID. Must match the directory name exactly.                                                            |
| `version`         | `string`        | Semantic version of the plugin.                                                                                         |
| **`description`** | `string`        | **Help Metadata Bridge**: Used as the default help text for the root command (`{{metadata.pkgs.sdk}} <plugin> --help`). |
| `authors`         | `array[table]`  | Plugin authors.                                                                                                         |
| `dependencies`    | `array[string]` | PyPI/Git packages. Installed automatically using `uv`.                                                                  |

> [!TIP]
> **Help Precedence**: If you define an explicit help message in your code using `@plugin.root(help="...")`, it will override the `description` found in `pyproject.toml`.

### `[tool.{{metadata.pkgs.sdk}}]`

Engine-specific configuration.

| Field             | Type     | Default                       | Description                                                                      |
| :---------------- | :------- | :---------------------------- | :------------------------------------------------------------------------------- |
| **`api_version`** | `string` | `"{{metadata.versions.api}}"` | Targeted SDK version. Major version must match the Engine’s current API version. |
| **`entry`**       | `string` | `"main.py"`                   | The entry point where registration occurs.                                       |

{{metadata.pkgs.sdk}} uses `uv` to prepare plugin dependencies during discovery.

1. **Discovery**: The Engine reads the `dependencies` list.
2. **Sync**: `uv pip install` runs automatically in the plugin's isolated environment.
3. **Validation**: The plugin is only loaded if all dependencies are successfully resolved.
