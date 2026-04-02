from myctl.api import Plugin, Context
from .src.commands import get_status as impl_get_status, set_volume as impl_set_volume

plugin = Plugin("audio")

@plugin.command("status", help="Get detailed sink status")
async def get_status(ctx: Context):
    sink_id = ctx.args[0] if ctx.args else "0"
    return ctx.ok(await impl_get_status(sink_id))

@plugin.command("volume set", help="Change sink volume level")
async def volume_set(ctx: Context):
    level = ctx.args[0] if ctx.args else "0"
    return ctx.ok(await impl_set_volume(level))
