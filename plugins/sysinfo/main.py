from myctl.api import Context, Plugin, log
from .src import handlers

plugin = Plugin()


@plugin.on_load
async def _setup(ctx: Context):
    log.info("sysinfo plugin loaded — psutil %s", handlers.get_psutil_version())


@plugin.command("overview", help="One-line system resource snapshot")
async def overview(ctx: Context):
    return ctx.ok(handlers.overview_data())


@plugin.command("cpu usage", help="Per-core CPU usage percentages")
async def cpu_usage(ctx: Context):
    data = handlers.cpu_usage_data()
    log.debug("cpu_usage called — %d cores", len(data))
    return ctx.ok(data)


@plugin.command("cpu freq", help="Current CPU clock frequency in MHz")
async def cpu_freq(ctx: Context):
    data = handlers.cpu_freq_data()
    if data is None:
        return ctx.err("CPU frequency data unavailable on this system.")
    return ctx.ok(data)


@plugin.command("cpu count", help="Number of logical and physical CPU cores")
async def cpu_count(ctx: Context):
    return ctx.ok(handlers.cpu_count_data())


@plugin.command("mem ram", help="Physical RAM usage breakdown")
async def mem_ram(ctx: Context):
    return ctx.ok(handlers.mem_ram_data())


@plugin.command("mem swap", help="Swap space usage")
async def mem_swap(ctx: Context):
    return ctx.ok(handlers.mem_swap_data())


@plugin.command("disk usage", help="Disk usage for a given mount point (default: /)")
async def disk_usage(ctx: Context):
    path = ctx.args[0] if ctx.args else "/"
    try:
        return ctx.ok(handlers.disk_usage_data(path))
    except FileNotFoundError:
        return ctx.err(f"Mount point not found: {path}", exit_code=2)


@plugin.command("disk partitions", help="List all mounted disk partitions")
async def disk_partitions(ctx: Context):
    return ctx.ok(handlers.disk_partitions_data())


@plugin.command("net stats", help="Bytes sent/received per network interface")
async def net_stats(ctx: Context):
    return ctx.ok(handlers.net_stats_data())


@plugin.command("net interfaces", help="Active network interfaces and their addresses")
async def net_interfaces(ctx: Context):
    return ctx.ok(handlers.net_interfaces_data())
