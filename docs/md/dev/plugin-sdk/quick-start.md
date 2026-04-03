# Quick Start

This guide walks through the steps to Initialize a plugin.

## Prerequisites

Before starting plugin development, ensure:

- MyCTL is installed and working: [Installation Guide](../../guide/install)
- `uv` is available in your shell: [uv docs]({{metadata.tools.uv}})
- You are **comfortable with basic Python imports and async functions**

## Plugin Structure

```text
plugins/myplugin/
├── pyproject.toml
├── main.py
└── src/
    ├── __init__.py
    └── cmds.py
```

| Element              | Purpose                                   |
| :------------------- | :---------------------------------------- |
| **Directory Name**   | Plugin ID (root CLI namespace)            |
| **`pyproject.toml`** | Plugin metadata, API target, dependencies |
| **`main.py`**        | Registration layer (commands/flags/hooks) |
| **`src/`**           | Implementation modules and business logic |

> [!IMPORTANT]
> It's encouraged to keep `main.py` registration-only.  
> Place implementation in `src/` & import via relative imports (e.g. `from .src.cmds import ...`).

## 1. Create Your Plugin Directory

### TODO: initilize in plugin dir.

Initialize your new plugin Dir with boilerplate files in plugin directory. It checks if the id is available & not in [system commands](/docs/md/dev/system-commands.md).

The generator prompts for:

- description
- author(s)

```bash-vue
{{metadata.pkgs.sdk}} plugin init myplugin
cd {{metadata.paths.plugins}}/myplugin
```

Or initialize directly to a target path with non-interactive defaults:

```bash
{{metadata.pkgs.sdk}} plugin init myplugin --author "Your Name" --desc "My plugin"
```

The directory name (`myplugin`) becomes your **plugin ID**. It will bind to CLI (like `{{metadata.pkgs.sdk}} myplugin hello`).

Then it creates the initial files:

- `pyproject.toml`
- `main.py`
- `src/__init__.py`
- `src/commands.py`

## 3. Add Dependencies (Optional)

From inside your plugin directory:

```bash
uv add requests # or any other package needed
```

Git dependencies are also supported:

```bash
uv add "my-lib @ git+https://github.com/org/my-lib"
```

## 4. Register a First Command

The skeleton is already generated. You can now edit it using the modern **Typed Signature** API.

### `main.py` (Registration)

```python
from {{metadata.pkgs.sdk}} import Plugin, Context, flag, log   # import sdk
from .src.commands import hello_msg            # import implementations

plugin = Plugin()  # Registration-only instance

@plugin.root
async def main(ctx: Context, name: str = flag("n", default="World", help="Who to greet")):
    # Flags are injected directly!
    # Logic is delegated to src/ modules
    result = hello_msg(name)
    return ctx.ok(result)
```

### `src/commands.py` (Implementation)

```python
def hello_msg(name: str) -> str:
    return f"Hello, {name} from myplugin"
```

## 5. Configure IDE Support

To get

```bash
{{metadata.pkgs.sdk}} sdk set <vscode|zed|pycharm>
```

This configures IDE import resolution for `{{metadata.pkgs.sdk}}` autocompletion & type hints.

## 6. Reload and Validate

After editing plugin code, reload daemon:

```bash
{{metadata.pkgs.sdk}} restart
```

Now test your command:

```bash
{{metadata.pkgs.sdk}} myplugin hello
```

Expected output:

```text
Hello from myplugin
```

## Reserved Command IDs

Plugin IDs must not overlap with daemon built-in command IDs.

- If a plugin directory name matches an internal plugin ID (e.g., `status`, `stop`, `plugin`), the plugin will be rejected at load time.
- The Engine's internal registry is the final source of truth for command availability.

## Troubleshooting

### Command Not Visible

- Verify plugin folder name matches `[project].name`
- Run `{{metadata.pkgs.sdk}} schema` and confirm your plugin in command tree exists
- Check `{{metadata.pkgs.sdk}} logs` for discovery/load errors
- Restart daemon after file changes

### Import Errors

- Confirm `src/__init__.py` exists
- Use package-relative imports from `main.py` (`from .src...`)

### Dependency Import Failures

- Confirm dependency exists in `[project].dependencies`
- Run `uv add <package>` in plugin directory
- Restart daemon to reload plugin process state
