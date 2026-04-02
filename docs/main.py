from myctl.api import Plugin, Context
from .src.commands import hello_message

plugin = Plugin("docs")


@plugin.command("hello", help="Confirm docs is working")
async def hello(ctx: Context):
    return ctx.ok(hello_message())
