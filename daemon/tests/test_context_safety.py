"""Test context safety - only safe fields exposed."""

import inspect

import pytest
from myctl.api import Context


def test_context_has_required_safe_fields():
    """Verify Context has exactly the safe fields."""
    ctx = Context()

    safe_fields = {
        "plugin_id",
        "command_name",
        "args",
        "flags",
        "user",
        "request_id",
        "cwd",
        "terminal",
        "path",
        "env",
    }

    # Get all public fields (not starting with _)
    context_fields = {
        f.name for f in ctx.__dataclass_fields__.values() if not f.name.startswith("_")
    }

    assert safe_fields == context_fields


def test_context_does_not_expose_registry():
    """Verify Context doesn't expose registry internals."""
    ctx = Context()

    # These should not be attributes
    registry_internals = ["registry", "dispatcher", "handler"]
    for attr in registry_internals:
        assert not hasattr(ctx, attr), f"Registry internal '{attr}' exposed in Context"


def test_context_does_not_expose_ipc():
    """Verify Context doesn't expose IPC internals."""
    ctx = Context()

    ipc_internals = ["socket", "ipc", "connection", "request"]
    for attr in ipc_internals:
        assert not hasattr(ctx, attr), f"IPC internal '{attr}' exposed in Context"


def test_context_does_not_expose_plugin_manager():
    """Verify Context doesn't expose plugin manager."""
    ctx = Context()

    manager_internals = ["manager", "loader", "plugins", "discovery"]
    for attr in manager_internals:
        assert not hasattr(ctx, attr), f"Manager internal '{attr}' exposed in Context"


def test_context_user_field_safety():
    """Verify user field only has name and id (minimal identity)."""
    ctx = Context()

    # User should have minimal fields
    assert hasattr(ctx.user, "name")
    assert hasattr(ctx.user, "id")

    # Check that user_dict doesn't have extra fields
    user_fields = {f.name for f in ctx.user.__dataclass_fields__.values()}
    # Should only be name and id
    assert user_fields == {"name", "id"}


def test_context_terminal_field_safety():
    """Verify terminal field only has capability metadata."""
    ctx = Context()

    terminal_fields = {f.name for f in ctx.terminal.__dataclass_fields__.values()}

    # Terminal should only have capability-related fields
    safe_terminal = {"is_tty", "color_depth", "no_color"}
    assert terminal_fields == safe_terminal


def test_context_no_daemon_app_reference():
    """Verify Context doesn't hold daemon app instance."""
    ctx = Context()

    # Should not have app reference
    assert not hasattr(ctx, "app")
    assert not hasattr(ctx, "_app")
    assert not hasattr(ctx, "engine")


def test_context_no_callable_lifecycle_methods():
    """Verify Context doesn't expose lifecycle control methods."""
    ctx = Context()

    lifecycle_methods = [
        "start",
        "stop",
        "reload",
        "restart",
        "load_plugin",
        "unload_plugin",
        "reload_plugin",
        "execute_lifecycle",
        "dispatch_internal",
    ]

    for method in lifecycle_methods:
        assert not hasattr(ctx, method) or method in ["ask"], (
            f"Lifecycle method '{method}' exposed in Context"
        )


def test_context_ok_err_methods_are_safe():
    """Verify ok() and err() return proper Response objects."""
    ctx = Context()

    # ok() should create successful response
    response = ctx.ok({"status": "ok"})
    assert response.status == 0  # OK
    assert response.data == {"status": "ok"}
    assert response.exit_code == 0

    # err() should create error response
    error_response = ctx.err("Something failed", exit_code=1)
    assert error_response.status == 1  # ERROR
    assert error_response.data == "Something failed"
    assert error_response.exit_code == 1


def test_context_ask_callback_safety():
    """Verify ask() callback is properly isolated."""
    ctx = Context()

    # Without callback set, ask() should raise RuntimeError
    with pytest.raises(RuntimeError):
        import asyncio

        asyncio.run(ctx.ask("Test prompt"))

    # Verify callback is a private field
    assert "_ask_callback" in ctx.__dataclass_fields__
    assert ctx.__dataclass_fields__["_ask_callback"].repr is False  # Not shown in repr


def test_context_immutability_by_convention():
    """Verify Context fields can be set (mutable dataclass but conventionally safe)."""
    ctx = Context()

    # Fields are mutable (dataclass), but that's OK since plugin handlers get fresh instances
    ctx.command_name = "test"
    assert ctx.command_name == "test"

    ctx.flags = {"key": "value"}
    assert ctx.flags == {"key": "value"}


def test_context_field_defaults():
    """Verify context fields have safe defaults."""
    ctx = Context()

    # All public accessible fields should have defaults
    assert isinstance(ctx.args, list) and ctx.args == []
    assert isinstance(ctx.flags, dict) and ctx.flags == {}
    assert isinstance(ctx.env, dict) and ctx.env == {}
    assert isinstance(ctx.path, list) and ctx.path == []
    assert ctx.cwd == "."
    assert ctx.command_name == ""
    assert ctx.plugin_id == ""
    assert len(ctx.request_id) > 0  # UUID hex


def test_context_private_fields_not_in_public_api():
    """Verify private fields (_ask_callback) are not part of public API."""
    ctx = Context()

    # Private fields should start with underscore
    private_fields = {f for f in ctx.__dataclass_fields__ if f.startswith("_")}

    # Should have _ask_callback
    assert "_ask_callback" in private_fields

    # These should not be documented as public fields to plugins
    public_api = {f for f in ctx.__dataclass_fields__ if not f.startswith("_")}

    # Public API shouldn't include private callback details
    assert not any("callback" in f for f in public_api)
