"""Tests for flag behavior and Context flag access semantics."""

from myctl.api import Plugin, Context


def test_flag_fallback_with_ctx_get():
    plugin = Plugin(name="serve")

    @plugin.command("serve", help="Run HTTP server")
    @plugin.flag("port", "p", default=8080, help="Port to bind")
    def serve(ctx: Context):
        # handler should rely on explicit ctx.flags values and fallback
        port = ctx.flags.get("port", 8080)
        return {"port": port}

    result_from_empty = serve(
        Context(plugin_id="serve", command_name="serve", flags={})
    )
    assert result_from_empty["port"] == 8080

    result_from_value = serve(
        Context(plugin_id="serve", command_name="serve", flags={"port": 9090})
    )
    assert result_from_value["port"] == 9090


def test_flag_metadata_stores_default_but_not_auto_inject():
    plugin = Plugin(name="serve")

    @plugin.command("serve")
    @plugin.flag("port", "p", default=8080, help="Port to bind")
    def serve(ctx: Context):
        # This is intentionally strict to show framework does not mutate ctx.flags
        return ctx.flags.get("port", None)

    flags_meta = getattr(serve, "__myctl_flags__", [])
    assert len(flags_meta) == 1
    assert flags_meta[0]["name"] == "--port"
    assert flags_meta[0]["short"] == "-p"
    assert flags_meta[0]["default"] == 8080

    # In the framework, flags are provided via context; defaults are not auto-injected.
    assert serve(Context(plugin_id="serve", command_name="serve", flags={})) is None
