"""Test decorator discovery and registration."""

import pytest
from myctl.api import Plugin, Context, FlagSpec


def test_plugin_command_decorator_registration():
    """Verify @plugin.command decorator registers handlers."""
    plugin = Plugin(name="test")

    @plugin.command("greet", help="Greet someone")
    def greet(ctx: Context):
        return "Hello"

    # Check decorator set the marker
    assert hasattr(greet, "__myctl_cmd__")
    assert greet.__myctl_cmd__["path"] == "greet"
    assert greet.__myctl_cmd__["help"] == "Greet someone"

    # Check handler is registered in plugin
    assert greet in plugin._commands


def test_plugin_flag_decorator_registration():
    """Verify @plugin.flag decorator registers flag metadata."""
    plugin = Plugin(name="test")

    @plugin.command("greet")
    @plugin.flag("name", "n", default="World", help="Name to greet")
    def greet(ctx: Context):
        return f"Hello, {ctx.flags.get('name')}"

    # Check flags are registered
    assert hasattr(greet, "__myctl_flags__")
    flags = getattr(greet, "__myctl_flags__")
    assert len(flags) == 1
    assert flags[0]["name"] == "--name"
    assert flags[0]["short"] == "-n"
    assert flags[0]["default"] == "World"
    assert flags[0]["help"] == "Name to greet"


def test_plugin_flags_decorator_registration():
    """Verify @plugin.flags decorator with list registration."""
    plugin = Plugin(name="test")

    flag_specs = [
        {"name": "verbose", "short": "v", "help": "Verbose output"},
        {"name": "quiet", "short": "q", "help": "Quiet output"},
    ]

    @plugin.command("run")
    @plugin.flags(flag_specs)
    def run(ctx: Context):
        return "Running"

    assert hasattr(run, "__myctl_flags__")
    flags = getattr(run, "__myctl_flags__")
    assert len(flags) == 2


def test_multiple_commands_registered():
    """Verify multiple commands can be registered on same plugin."""
    plugin = Plugin(name="multi")

    @plugin.command("list")
    def list_items(ctx: Context):
        return "list"

    @plugin.command("add")
    def add_item(ctx: Context):
        return "add"

    @plugin.command("delete")
    def delete_item(ctx: Context):
        return "delete"

    assert len(plugin._commands) == 3
    assert list_items in plugin._commands
    assert add_item in plugin._commands
    assert delete_item in plugin._commands


def test_handler_discovery_by_command_path():
    """Verify handlers can be discovered by command path."""
    plugin = Plugin(name="audio")

    @plugin.command("volume set")
    def set_volume(ctx: Context):
        return {"status": "ok"}

    @plugin.command("volume get")
    def get_volume(ctx: Context):
        return {"volume": 50}

    # Verify both commands can be found by their paths
    commands = plugin._commands
    paths = [getattr(cmd, "__myctl_cmd__", {}).get("path") for cmd in commands]

    assert "volume set" in paths
    assert "volume get" in paths


def test_flag_type_inference():
    """Verify flag types are correctly inferred from defaults."""
    plugin = Plugin(name="test")

    @plugin.command("test")
    @plugin.flag("count", "c", default=0, help="Count")
    @plugin.flag("name", "n", default="test", help="Name")
    @plugin.flag("enabled", "e", default=True, help="Enabled")
    def test_cmd(ctx: Context):
        return "ok"

    flags = getattr(test_cmd, "__myctl_flags__")
    flag_dict = {f["name"]: f for f in flags}

    assert flag_dict["--count"]["type"] == "int"
    assert flag_dict["--name"]["type"] == "str"
    assert flag_dict["--enabled"]["type"] == "bool"


def test_on_load_hook_registration():
    """Verify @plugin.on_load hook registration."""
    plugin = Plugin(name="test")
    hook_called = []

    @plugin.on_load
    def setup(ctx: Context):
        hook_called.append("setup")

    # Hook should be registered
    assert setup in plugin._load_hooks


def test_periodic_hook_registration():
    """Verify @plugin.periodic hook registration with seconds."""
    plugin = Plugin(name="test")

    @plugin.periodic(60)
    def monitor(ctx: Context):
        return {"status": "ok"}

    # Periodic hook should be registered with seconds interval
    assert (60, monitor) in plugin._periodic_hooks


def test_command_chain_with_multiple_flags():
    """Verify decorator stacking (command + multiple flags)."""
    plugin = Plugin(name="test")

    @plugin.command("deploy", help="Deploy service")
    @plugin.flag("env", "e", default="dev", help="Environment")
    @plugin.flag("force", "f", default=False, help="Force deploy")
    @plugin.flag("dry-run", "d", default=False, help="Dry run")
    def deploy(ctx: Context):
        return {"deployed": True}

    # Verify command is registered
    assert deploy in plugin._commands
    assert deploy.__myctl_cmd__["path"] == "deploy"

    # Verify all flags are registered
    flags = getattr(deploy, "__myctl_flags__", [])
    assert len(flags) == 3
    flag_names = {f["name"] for f in flags}
    assert "--env" in flag_names
    assert "--force" in flag_names
    assert "--dry-run" in flag_names
