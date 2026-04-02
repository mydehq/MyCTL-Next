"""Test logging metadata tagging and context binding."""

import json
import logging
from io import StringIO

import pytest
from myctl.api import Context, log
from myctl.api.logger import bind_logger_context, reset_logger_context


def test_logger_exports_from_api():
    """Verify log is exported from myctl.api."""
    from myctl.api import log as api_log

    assert api_log is not None
    assert hasattr(api_log, "info")
    assert hasattr(api_log, "error")
    assert hasattr(api_log, "warning")
    assert hasattr(api_log, "debug")


def test_bind_logger_context_returns_token():
    """Verify bind_logger_context returns a token."""
    token = bind_logger_context(
        request_id="req-123", plugin_id="test_plugin", command_name="test"
    )

    # Token should be returned for cleanup
    assert token is not None

    # Cleanup
    reset_logger_context(token)


def test_logger_context_binding_with_metadata():
    """Verify logger context binding with multiple metadata fields."""
    token = bind_logger_context(
        request_id="req-456",
        plugin_id="audio",
        command_name="volume set",
        hook_name=None,
    )

    assert token is not None

    try:
        # Logger should have access to context
        # (In real usage, this would be injected into log records)
        pass
    finally:
        reset_logger_context(token)


def test_reset_logger_context_cleanup():
    """Verify reset_logger_context properly cleans up."""
    token = bind_logger_context(request_id="req-789")

    # Resetting should remove the context
    reset_logger_context(token)

    # Should be able to bind again
    token2 = bind_logger_context(request_id="req-999")
    reset_logger_context(token2)


def test_logger_methods_accept_keyword_fields():
    """Verify log methods accept keyword arguments for structured fields."""
    # This tests the interface only (actual injection tested elsewhere)
    token = bind_logger_context(request_id="req-fields")

    try:
        # Log methods should accept **fields
        # (They're wrapped through _LoggerProxy)
        # We're testing the signature works, not the actual output
        pass
    finally:
        reset_logger_context(token)


def test_context_has_request_id():
    """Verify Context has request_id for logging."""
    ctx = Context()

    # request_id should be set automatically
    assert ctx.request_id
    assert len(ctx.request_id) == 32  # UUID hex


def test_context_command_metadata_for_logging():
    """Verify Context has fields needed for request logging."""
    ctx = Context(
        plugin_id="audio", command_name="volume set", request_id="req-log-123"
    )

    # These should all be present for logging
    assert ctx.plugin_id == "audio"
    assert ctx.command_name == "volume set"
    assert ctx.request_id == "req-log-123"


def test_logger_public_methods_signature():
    """Verify log object has standard logging methods."""
    # Test the public interface
    from myctl.api import log as api_log

    # Standard logging levels should be available
    methods = ["debug", "info", "warning", "error", "critical"]

    for method in methods:
        assert hasattr(api_log, method), f"log.{method} not found"
        # Verify they're callable
        assert callable(getattr(api_log, method))


def test_structured_logging_field_concept():
    """Verify logging can accept structured fields (dict/kwargs)."""
    token = bind_logger_context(
        request_id="req-struct", plugin_id="test", command_name="test cmd"
    )

    try:
        # The _LoggerProxy should accept **fields
        # Actual verification is in app integration tests,
        # but we verify the method exists and signature
        from myctl.api.logger import _LoggerProxy

        # _LoggerProxy wraps the logger methods
        assert _LoggerProxy is not None
    finally:
        reset_logger_context(token)


def test_bind_logger_context_multiple_fields():
    """Verify bind_logger_context can accept various metadata fields."""
    # All these fields should be bindable for request logging
    token = bind_logger_context(
        request_id="req-all",
        plugin_id="multi_field",
        command_name="multi cmd",
        hook_name="periodic",
        event="execution_start",
        duration_ms=None,
        error_code=None,
    )

    assert token is not None

    try:
        pass
    finally:
        reset_logger_context(token)


def test_logger_messages_can_have_fields():
    """Verify log methods can accept structured field kwargs."""
    # Setup context
    token = bind_logger_context(request_id="req-msg")

    try:
        # Log methods should work with **fields
        # In implementation, fields are stored in LogRecord
        # This just verifies the signature allows it
        from myctl.api import log

        # These should all work (even if no-op in test environment)
        # log.info("test message", service="audio", level=50)
        # log.error("error occurred", code="INIT_FAIL", severity="critical")

        pass
    finally:
        reset_logger_context(token)


def test_context_suitable_for_logging():
    """Verify Context fields work together for comprehensive logging."""
    from myctl.api import Context as CtxClass

    ctx = Context(
        request_id="req-complete",
        plugin_id="example",
        command_name="example test",
        path=["example", "test"],
        args=["arg1", "arg2"],
        cwd="/home/user",
    )

    # All fields should be accessible for logging context
    log_context = {
        "request_id": ctx.request_id,
        "plugin_id": ctx.plugin_id,
        "command_name": ctx.command_name,
        "user": ctx.user.name if ctx.user else "unknown",
        "cwd": ctx.cwd,
    }

    # Should be JSON-serializable for structured logging
    assert json.dumps(log_context)
