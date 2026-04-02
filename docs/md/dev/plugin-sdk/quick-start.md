# Quick Start

This guide walks through the standard plugin authoring workflow: create, register, reload, and validate.

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

Initialize your new plugin Dir with boilerplate files
The generator prompts for:

- description
- author(s)

```bash
myctl plugin init myplugin
cd myplugin
```

Or initialize directly to a target path with non-interactive defaults:

```bash
myctl plugin init ./myplugin --author "Your Name" --desc "My plugin"
```

The directory name (`myplugin`) becomes your **plugin ID**. It will bind to CLI like `myctl myplugin hello`

Then it creates the initial files:

- `pyproject.toml`
- `main.py` (registration-only)
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

The skeleton is already generated. You can now edit it.

### `main.py` (Registration)

```python
from myctl.api import Plugin, Context, log  # import sdk
from .src.commands import hello_msg         # import implementations

plugin = Plugin()  # Create instance of Plugin class

@plugin.command("hello", help="Confirm myplugin is working")  # register command "hello"
async def hello_msg(ctx: Context):
    return ctx.ok(hello_message())
```

### `src/commands.py` (Implementation)

```python
def hello_msg() -> str:
    return "Hello from myplugin"
```

## 5. Configure IDE SDK Support

To get

```bash
myctl sdk set <vscode|zed|pycharm>
```

This configures IDE import resolution for `myctl.api` autocompletion & type hints.

## 6. Reload and Validate

After editing plugin code, reload daemon:

```bash
myctl restart
```

Now test your command:

```bash
myctl myplugin hello
```

Expected output:

```text
Hello from myplugin
```

## Troubleshooting

### Command Not Visible

- Verify plugin folder name matches `[project].name`
- Run `myctl schema` and confirm your plugin in command tree exists
- Check `myctl logs` for discovery/load errors
- Restart daemon after file changes

### Import Errors

- Confirm `src/__init__.py` exists
- Use package-relative imports from `main.py` (`from .src...`)

### Dependency Import Failures

- Confirm dependency exists in `[project].dependencies`
- Run `uv add <package>` in plugin directory
- Restart daemon to reload plugin process state
