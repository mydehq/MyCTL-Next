"""
sysinfo — MyCTL plugin for system resource monitoring.

Tests:
  - on_load lifecycle hook (psutil import + version check)
  - Plugin-scoped logger
  - Nested command groups (cpu, mem, disk, net)
  - ok() with string, dict, and list payloads
  - err() with usage hints
  - req.args argument parsing
"""

from myctl.api import registry, logger, ok, err, Request

import psutil  # declared in pyproject.toml dependencies

# ── Lifecycle: on_load ──────────────────────────────────────────────────────
@registry.on_load
async def _setup():
    """Verify psutil is accessible and log the version at boot."""
    logger.info("sysinfo plugin loaded — psutil %s", psutil.version_info)


# ── Top-level: overview ─────────────────────────────────────────────────────
@registry.add_cmd("overview", help="One-line system resource snapshot")
async def overview(req: Request):
    cpu  = psutil.cpu_percent(interval=0.1)
    mem  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return ok({
        "cpu_percent":  cpu,
        "mem_used_mb":  round(mem.used  / 1024**2, 1),
        "mem_total_mb": round(mem.total / 1024**2, 1),
        "disk_used_gb": round(disk.used  / 1024**3, 2),
        "disk_total_gb":round(disk.total / 1024**3, 2),
    })


# ── CPU group ───────────────────────────────────────────────────────────────
@registry.add_cmd("cpu usage", help="Per-core CPU usage percentages")
async def cpu_usage(req: Request):
    percents = psutil.cpu_percent(interval=0.2, percpu=True)
    cores = {f"core{i}": f"{p}%" for i, p in enumerate(percents)}
    logger.debug("cpu_usage called — %d cores", len(percents))
    return ok(cores)


@registry.add_cmd("cpu freq", help="Current CPU clock frequency in MHz")
async def cpu_freq(req: Request):
    freq = psutil.cpu_freq()
    if not freq:
        return err("CPU frequency data unavailable on this system.")
    return ok({
        "current_mhz": round(freq.current, 1),
        "min_mhz":     round(freq.min,     1),
        "max_mhz":     round(freq.max,     1),
    })


@registry.add_cmd("cpu count", help="Number of logical and physical CPU cores")
async def cpu_count(req: Request):
    return ok({
        "logical":  psutil.cpu_count(logical=True),
        "physical": psutil.cpu_count(logical=False),
    })


# ── Memory group ─────────────────────────────────────────────────────────────
@registry.add_cmd("mem ram", help="Physical RAM usage breakdown")
async def mem_ram(req: Request):
    m = psutil.virtual_memory()
    return ok({
        "total_mb":     round(m.total     / 1024**2, 1),
        "available_mb": round(m.available / 1024**2, 1),
        "used_mb":      round(m.used      / 1024**2, 1),
        "percent":      m.percent,
    })


@registry.add_cmd("mem swap", help="Swap space usage")
async def mem_swap(req: Request):
    s = psutil.swap_memory()
    return ok({
        "total_mb": round(s.total / 1024**2, 1),
        "used_mb":  round(s.used  / 1024**2, 1),
        "percent":  s.percent,
    })


# ── Disk group ───────────────────────────────────────────────────────────────
@registry.add_cmd("disk usage", help="Disk usage for a given mount point (default: /)")
async def disk_usage(req: Request):
    path = req.args[0] if req.args else "/"
    try:
        d = psutil.disk_usage(path)
    except FileNotFoundError:
        return err(f"Mount point not found: {path}", exit_code=2)
    return ok({
        "path":      path,
        "total_gb":  round(d.total / 1024**3, 2),
        "used_gb":   round(d.used  / 1024**3, 2),
        "free_gb":   round(d.free  / 1024**3, 2),
        "percent":   d.percent,
    })


@registry.add_cmd("disk partitions", help="List all mounted disk partitions")
async def disk_partitions(req: Request):
    parts = psutil.disk_partitions()
    return ok([
        {"device": p.device, "mountpoint": p.mountpoint, "fstype": p.fstype}
        for p in parts
    ])


# ── Network group ─────────────────────────────────────────────────────────────
@registry.add_cmd("net stats", help="Bytes sent/received per network interface")
async def net_stats(req: Request):
    counters = psutil.net_io_counters(pernic=True)
    return ok({
        iface: {
            "bytes_sent": c.bytes_sent,
            "bytes_recv": c.bytes_recv,
            "packets_sent": c.packets_sent,
            "packets_recv": c.packets_recv,
        }
        for iface, c in counters.items()
    })


@registry.add_cmd("net interfaces", help="Active network interfaces and their addresses")
async def net_interfaces(req: Request):
    addrs = psutil.net_if_addrs()
    return ok({
        iface: [
            {"family": str(a.family), "address": a.address}
            for a in addr_list
        ]
        for iface, addr_list in addrs.items()
    })
