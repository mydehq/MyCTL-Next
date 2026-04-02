from pathlib import Path
from myctl.api import Context, log


def _render_pyproject(plugin_id: str, authors: list[str], description: str) -> str:
    authors_toml = ", ".join(f'{{ name = "{name}" }}' for name in authors)
    return f"""[project]
name = "{plugin_id}"
authors = [{authors_toml}]
version = "0.1.0"
description = "{description}"
dependencies = []

[tool.myctl]
api_version = "2.0.0"
entry = "main.py"
"""


def _render_main(plugin_id: str) -> str:
    return f"""from myctl.api import Plugin, Context
from .src.commands import hello_message

plugin = Plugin("{plugin_id}")


@plugin.command("hello", help="Confirm {plugin_id} is working")
async def hello(ctx: Context):
    return ctx.ok(hello_message())
"""


def _render_commands(plugin_id: str) -> str:
    return f"""def hello_message() -> str:
    return "Hello from {plugin_id}"
"""


async def initialize_plugin(ctx: Context):
    """Initialize a new MyCTL plugin with boilerplate and src layout."""
    import os

    target_path = ctx.args[0] if ctx.args else ctx.flags.get("path", ".")
    target_dir = (Path(os.getcwd()) / target_path).resolve()
    plugin_id = target_dir.name

    try:
        if target_dir.exists() and not target_dir.is_dir():
            return ctx.err(f"Target path '{target_dir}' exists but is not a directory.")

        pyproject_toml = target_dir / "pyproject.toml"
        main_py = target_dir / "main.py"
        src_dir = target_dir / "src"
        src_init = src_dir / "__init__.py"
        commands_py = src_dir / "commands.py"

        for existing in (pyproject_toml, main_py, commands_py):
            if existing.exists():
                return ctx.err(f"Refusing to overwrite existing file: {existing}")

        desc = ctx.flags.get("desc", "A MyCTL Plugin")
        if desc == "A MyCTL Plugin":
            new_desc = await ctx.ask(f"- Description [default: {desc}]: ")
            if new_desc.strip():
                desc = new_desc.strip()

        author_input = ctx.flags.get("author", "MyCTL Developer")
        if author_input == "MyCTL Developer":
            new_author = await ctx.ask(
                f"- Author(s) [comma-separated, default: {author_input}]: "
            )
            if new_author.strip():
                author_input = new_author.strip()

        authors = [name.strip() for name in author_input.split(",") if name.strip()]
        if not authors:
            authors = ["MyCTL Developer"]

        target_dir.mkdir(parents=True, exist_ok=True)
        src_dir.mkdir(parents=True, exist_ok=True)

        pyproject_toml.write_text(_render_pyproject(plugin_id, authors, desc))
        main_py.write_text(_render_main(plugin_id))
        src_init.write_text('"""Plugin implementation package."""\n')
        commands_py.write_text(_render_commands(plugin_id))

        return ctx.ok(f"Plugin '{plugin_id}' initialized in {target_dir}")
    except Exception as exc:
        log.error("Plugin initialization failed: %s", exc)
        return ctx.err(f"Initialization error: {exc}", exit_code=2)
