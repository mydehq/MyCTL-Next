"""Test plugin import isolation (can import myctl.api, not myctld)."""

import importlib
import sys
from pathlib import Path

import pytest


def test_plugin_can_import_myctl_api():
    """Verify plugins can import from myctl.api."""
    from myctl.api import Plugin, Context, log, style

    assert Plugin is not None
    assert Context is not None
    assert log is not None
    assert style is not None


def test_api_exports_required_symbols():
    """Verify myctl.api exports all required public symbols."""
    from myctl import api

    required = ["Plugin", "Context", "log", "style", "FlagSpec"]

    for symbol in required:
        assert hasattr(api, symbol), f"myctl.api missing required export: {symbol}"


def test_plugin_cannot_import_myctld():
    """Verify myctld is not exposed in the plugin SDK."""
    # This test ensures myctld modules are not exposed through myctl.api
    import myctl.api

    # myctld should not be accessible from the plugin API surface
    assert not hasattr(myctl.api, "myctld"), "myctld exposed through myctl.api"

    # The actual runtime sandboxing (preventing plugin imports of myctld)
    # is enforced at plugin load time in the plugin loader, not here.
    # This test verifies the API surface doesn't expose it.


def test_api_does_not_expose_registry():
    """Verify registry internals are not exposed in API."""
    from myctl.api import __dict__ as api_dict
    import myctl.api

    # Check that registry-related items are not in public API
    api_exports = dir(myctl.api)

    registry_internals = ["Registry", "registry", "dispatch", "handler"]
    for item in registry_internals:
        assert item not in api_exports, (
            f"Registry internal '{item}' exposed in myctl.api"
        )


def test_api_does_not_expose_ipc():
    """Verify IPC internals are not exposed in API."""
    from myctl import api

    api_exports = dir(api)
    ipc_internals = ["IPC", "ipc", "socket", "Socket"]

    for item in ipc_internals:
        assert item not in api_exports, f"IPC internal '{item}' exposed in myctl.api"


def test_api_does_not_expose_plugin_manager():
    """Verify plugin manager internals are not exposed."""
    from myctl import api

    api_exports = dir(api)
    manager_internals = ["PluginManager", "manager", "loader", "discovery"]

    for item in manager_internals:
        assert item not in api_exports, (
            f"Manager internal '{item}' exposed in myctl.api"
        )
