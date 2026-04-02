"""Test configuration and shared fixtures."""

import sys
from pathlib import Path

import pytest

# Add daemon directory to path for imports
DAEMON_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(DAEMON_DIR))


@pytest.fixture
def temp_plugin_dir(tmp_path):
    """Create a temporary directory for test plugins."""
    return tmp_path / "plugins"


@pytest.fixture
def sample_plugin_code():
    """Sample valid plugin code for testing."""
    return """
from myctl.api import Plugin, Context

plugin = Plugin(name="test_plugin")

@plugin.command("test", help="Test command")
def test_cmd(ctx: Context):
    return {"status": "ok"}

@plugin.command("greet", help="Greet someone")
@plugin.flag("name", "n", default="World", help="Name to greet")
def greet(ctx: Context):
    return f"Hello, {ctx.flags.get('name')}!"
"""
