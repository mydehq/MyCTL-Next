from myctl.api import Context, Plugin, log

from .src.commands import build_flag_report

plugin = Plugin()


@plugin.command("flags", help="Inspect received flag values")
@plugin.flag("port", "p", default=8080, help="Port to bind")
@plugin.flag("host", "H", default="127.0.0.1", help="Host to bind")
@plugin.flag("mode", "m", default="dev", help="Runtime mode", choices=("dev", "prod"))
@plugin.flag("secure", "s", default=False, help="Enable secure mode")
@plugin.flag("goog", "g", default=False, help="Enable goog diagnostic flag")
@plugin.flag("retries", "r", default=3, help="Retry count for diagnostic flow")
@plugin.flag("profile", "P", default="local", help="Execution profile")
async def flags(ctx: Context):
    log.info("Received flags command with payload: %s", ctx.flags)
    return ctx.ok(build_flag_report(ctx, flags))
