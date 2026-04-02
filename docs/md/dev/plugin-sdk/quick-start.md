# Quick Start

This guide walks through the standard plugin authoring workflow: create, register, reload, and validate.

## Prerequisites

Before starting plugin development, ensure:

- MyCTL is installed and working: [Installation Guide](../../guide/install)
- `uv` is available in your shell: [uv docs]({{metadata.tools.uv}})
- You are comfortable with basic Python imports and async functions

## Plugin Structure

```text
plugins/myplugin/
├── pyproject.toml
├── main.py
└── src/
    ├── __init__.py
    └── commands.py
```

| Element              | Purpose                                   |
| :------------------- | :---------------------------------------- |
| **Directory Name**   | Plugin ID (root CLI namespace)            |
| **`pyproject.toml`** | Plugin metadata, API target, dependencies |
| **`main.py`**        | Registration layer (commands/flags/hooks) |
| **`src/`**           | Implementation modules and business logic |

> [!IMPORTANT]
> Keep `main.py` registration-only. Place implementation in `src/` and import via relative imports (for example, `from .src.commands import ...`).

## 1. Create the Plugin Directory

Create your plugin dir under the configured plugin path:

```bash
mkdir -p {{metadata.paths.plugins}}/myplugin
cd {{metadata.paths.plugins}}/myplugin
```

The directory name (`myplugin`) becomes your **plugin ID**.

## 2. Initialize Boilerplate

Run the generator inside the plugin directory:

```bash
myctl plugin init
```

Or initialize directly to a target path with non-interactive defaults:

```bash
myctl plugin init ./myplugin --author "Your Name" --desc "My plugin"
```

The generator prompts for:

- description
- author(s)

Then it creates the initial files:

- `pyproject.toml`
- `main.py` (registration-only)
- `src/__init__.py`
- `src/commands.py`

> [!TIP]
> For multiple authors, provide a comma-separated list.

## 3. Add Dependencies (Optional)

From inside your plugin directory:

```bash
uv add requests # or any other package needed
```

Git dependencies are supported:

```bash
uv add "my-lib @ git+https://github.com/org/my-lib"
```

## 4. Register a First Command

If you used `myctl plugin init`, this skeleton is already generated. You can now edit it.

### `main.py` (registration)

```python
from myctl.api import Plugin, Context
from .src.commands import hello_message

plugin = Plugin("myplugin")

@plugin.command(path="hello", help="Confirm myplugin is working")
async def hello(ctx: Context):
    return ctx.ok(hello_message())
```

### `src/commands.py` (implementation)

```python
def hello_message() -> str:
    return "Hello from myplugin"
```

## 5. Configure IDE SDK Support

```bash
myctl sdk setup
```

This configures IDE import resolution for `myctl.api` autocompletion and type hints.

## 6. Reload and Validate

After editing plugin code, reload daemon state:

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

### Command not visible

- Verify plugin folder name matches `[project].name`
- Run `myctl schema` and confirm your plugin tree exists
- Check `myctl logs` for discovery/load errors
- Restart daemon after file changes

### Import errors

- Confirm `src/__init__.py` exists
- Use package-relative imports from `main.py` (`from .src...`)

### Dependency import failures

- Confirm dependency exists in `[project].dependencies`
- Run `uv add <package>` in plugin directory
- Restart daemon to reload plugin process state
