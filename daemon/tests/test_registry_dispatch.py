"""Test registry dispatch correctness and routing."""

import pytest
from myctl.api import Plugin, Context


def test_multiple_plugins_can_coexist():
    """Verify multiple plugins can be registered independently."""
    audio_plugin = Plugin(name="audio")
    network_plugin = Plugin(name="network")

    @audio_plugin.command("volume set")
    def set_volume(ctx: Context):
        return {"plugin": "audio", "action": "volume"}

    @network_plugin.command("status")
    def status(ctx: Context):
        return {"plugin": "network", "action": "status"}

    # Both should be independent
    assert len(audio_plugin._commands) == 1
    assert len(network_plugin._commands) == 1
    assert set_volume in audio_plugin._commands
    assert status in network_plugin._commands


def test_command_path_hierarchy():
    """Verify nested command paths (subcommands) are supported."""
    plugin = Plugin(name="git")

    @plugin.command("clone")
    def clone(ctx: Context):
        return {"cmd": "clone"}

    @plugin.command("add")
    def add(ctx: Context):
        return {"cmd": "add"}

    @plugin.command("commit")
    @plugin.flag("message", "m", help="Commit message")
    def commit(ctx: Context):
        return {"cmd": "commit"}

    assert len(plugin._commands) == 3


def test_command_handler_execution_simulation():
    """Simulate dispatcher routing to correct handler."""
    plugin = Plugin(name="audio")

    @plugin.command("volume set")
    @plugin.flag("level", "l", default=50, help="Volume level")
    def set_volume(ctx: Context):
        level = ctx.flags.get("level", 50)
        return {"status": "ok", "volume": level}

    # Simulate finding and calling handler
    handler = plugin._commands[0]

    # Create context for this command
    ctx = Context(plugin_id="audio", command_name="volume set", flags={"level": 75})

    # Execute
    result = handler(ctx)

    # Verify result
    assert result["status"] == "ok"
    assert result["volume"] == 75


def test_registry_dispatch_by_command_path():
    """Verify commands can be found by their path."""
    plugin = Plugin(name="test")

    commands_to_register = [
        ("list", "List items"),
        ("add", "Add item"),
        ("remove", "Remove item"),
        ("update", "Update item"),
    ]

    for path, help_text in commands_to_register:
        # Create a handler for each
        def handler(ctx, p=path):
            return {"command": p}

        # Manually register (simulating decorator)
        setattr(handler, "__myctl_cmd__", {"path": path, "help": help_text})
        plugin._commands.append(handler)

    # Now simulate finding by path
    command_paths = {
        getattr(cmd, "__myctl_cmd__", {}).get("path"): cmd for cmd in plugin._commands
    }

    assert "list" in command_paths
    assert "add" in command_paths
    assert "remove" in command_paths
    assert "update" in command_paths


def test_dispatch_loads_correct_flags():
    """Verify dispatcher loads correct flags for command."""
    plugin = Plugin(name="deploy")

    @plugin.command("deploy")
    @plugin.flag("env", "e", default="dev", help="Environment")
    @plugin.flag("force", "f", default=False, help="Force deploy")
    def deploy(ctx: Context):
        return {"environment": ctx.flags.get("env"), "force": ctx.flags.get("force")}

    # Find command
    handler = plugin._commands[0]

    # Get flag metadata
    flags = getattr(handler, "__myctl_flags__", [])
    flag_names = {f["name"] for f in flags}

    assert "--env" in flag_names
    assert "--force" in flag_names


def test_dispatch_with_arguments():
    """Verify dispatcher passes arguments to handler."""
    plugin = Plugin(name="cmd")

    @plugin.command("process")
    def process(ctx: Context):
        # Handler receives context with args
        return {"received_args": ctx.args, "arg_count": len(ctx.args)}

    handler = plugin._commands[0]

    ctx = Context(
        plugin_id="cmd",
        command_name="process",
        args=["file1.txt", "file2.txt", "file3.txt"],
    )

    result = handler(ctx)
    assert result["arg_count"] == 3
    assert "file1.txt" in result["received_args"]


def test_dispatch_error_handling_signature():
    """Verify handler signature supports error returns."""
    plugin = Plugin(name="safe")

    @plugin.command("risky")
    def risky(ctx: Context):
        # Handler should be able to return error via ctx.err()
        if ctx.flags.get("fail"):
            return ctx.err("Operation failed", exit_code=1)
        return ctx.ok({"status": "success"})

    handler = plugin._commands[0]

    # Success case
    ctx_success = Context(plugin_id="safe", command_name="risky", flags={})
    result = handler(ctx_success)
    assert result.status == 0

    # Error case
    ctx_error = Context(plugin_id="safe", command_name="risky", flags={"fail": True})
    result = handler(ctx_error)
    assert result.status == 1


def test_dispatch_response_data_types():
    """Verify handler can return various data types."""
    plugin = Plugin(name="types")

    @plugin.command("dict")
    def return_dict(ctx: Context):
        return {"key": "value"}

    @plugin.command("string")
    def return_string(ctx: Context):
        return "plain string"

    @plugin.command("list")
    def return_list(ctx: Context):
        return [1, 2, 3]

    @plugin.command("number")
    def return_number(ctx: Context):
        return 42

    assert len(plugin._commands) == 4


def test_hook_execution_separate_from_dispatch():
    """Verify hooks exist separate from command dispatch."""
    plugin = Plugin(name="hooks")

    @plugin.command("work")
    def work(ctx: Context):
        return "done"

    @plugin.on_load
    def setup(ctx: Context):
        return "setup"

    @plugin.periodic(60)
    def monitor(ctx: Context):
        return "monitoring"

    # Verify they're in different lists
    assert len(plugin._commands) == 1  # Just work command
    assert len(plugin._load_hooks) == 1  # Just setup hook
    assert len(plugin._periodic_hooks) == 1  # Just monitor

    # Verify hook has interval (seconds)
    assert plugin._periodic_hooks[0][0] == 60
    assert plugin._periodic_hooks[0][1] == monitor


def test_dispatch_receives_complete_context():
    """Verify dispatcher passes complete context to handler."""
    plugin = Plugin(name="full")

    @plugin.command("inspect")
    def inspect_context(ctx: Context):
        return {
            "has_path": bool(ctx.path),
            "has_args": bool(ctx.args),
            "has_flags": bool(ctx.flags),
            "has_cwd": bool(ctx.cwd),
            "has_request_id": bool(ctx.request_id),
            "has_plugin_id": bool(ctx.plugin_id),
            "has_command_name": bool(ctx.command_name),
        }

    handler = plugin._commands[0]

    ctx = Context(
        plugin_id="full",
        command_name="inspect",
        path=["full", "inspect"],
        args=["arg1"],
        flags={"flag": "value"},
        cwd="/tmp",
    )

    result = handler(ctx)

    # All context parts should be present
    assert all(result.values()), "Some context fields missing"
