from myctl.api import Plugin, Context
from .src.scaffold import initialize_plugin

plugin = Plugin("plugin")


@plugin.flag("author", "a", "MyCTL Developer", "Author name for the plugin")
@plugin.flag("desc", "d", "A MyCTL Plugin", "Description for the plugin")
@plugin.flag("path", "p", ".", "Target directory for the plugin")
@plugin.command("init", help="Initialize a new MyCTL plugin")
async def init(ctx: Context):
    return await initialize_plugin(ctx)
