from myctl.api import Context, Plugin

from .src.commands import get_status as impl_get_status, set_volume as impl_set_volume

plugin = Plugin()


@plugin.command("status", help="Get detailed sink status")
async def get_status(ctx: Context):
    sink_id = ctx.args[0] if ctx.args else "default"
    try:
        return ctx.ok(await impl_get_status(sink_id))
    except Exception as exc:
        return ctx.err(f"audio status failed: {exc}")


@plugin.command("volume set", help="Change sink volume level")
async def volume_set(ctx: Context):
    if not ctx.args:
        return ctx.err("missing volume level")

    if len(ctx.args) == 1:
        sink_id = "default"
        level = ctx.args[0]
    else:
        sink_id = ctx.args[0]
        level = ctx.args[1]

    try:
        return ctx.ok(await impl_set_volume(sink_id, level))
    except Exception as exc:
        return ctx.err(f"audio volume failed: {exc}")
