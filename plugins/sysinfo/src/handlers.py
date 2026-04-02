import psutil


def get_psutil_version():
    return psutil.version_info


def overview_data():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": cpu,
        "mem_used_mb": round(mem.used / 1024**2, 1),
        "mem_total_mb": round(mem.total / 1024**2, 1),
        "disk_used_gb": round(disk.used / 1024**3, 2),
        "disk_total_gb": round(disk.total / 1024**3, 2),
    }


def cpu_usage_data():
    percents = psutil.cpu_percent(interval=0.2, percpu=True)
    return {f"core{i}": f"{p}%" for i, p in enumerate(percents)}


def cpu_freq_data():
    freq = psutil.cpu_freq()
    if not freq:
        return None
    return {
        "current_mhz": round(freq.current, 1),
        "min_mhz": round(freq.min, 1),
        "max_mhz": round(freq.max, 1),
    }


def cpu_count_data():
    return {
        "logical": psutil.cpu_count(logical=True),
        "physical": psutil.cpu_count(logical=False),
    }


def mem_ram_data():
    mem = psutil.virtual_memory()
    return {
        "total_mb": round(mem.total / 1024**2, 1),
        "available_mb": round(mem.available / 1024**2, 1),
        "used_mb": round(mem.used / 1024**2, 1),
        "percent": mem.percent,
    }


def mem_swap_data():
    swap = psutil.swap_memory()
    return {
        "total_mb": round(swap.total / 1024**2, 1),
        "used_mb": round(swap.used / 1024**2, 1),
        "percent": swap.percent,
    }


def disk_usage_data(path: str):
    disk = psutil.disk_usage(path)
    return {
        "path": path,
        "total_gb": round(disk.total / 1024**3, 2),
        "used_gb": round(disk.used / 1024**3, 2),
        "free_gb": round(disk.free / 1024**3, 2),
        "percent": disk.percent,
    }


def disk_partitions_data():
    parts = psutil.disk_partitions()
    return [
        {"device": p.device, "mountpoint": p.mountpoint, "fstype": p.fstype}
        for p in parts
    ]


def net_stats_data():
    counters = psutil.net_io_counters(pernic=True)
    return {
        iface: {
            "bytes_sent": c.bytes_sent,
            "bytes_recv": c.bytes_recv,
            "packets_sent": c.packets_sent,
            "packets_recv": c.packets_recv,
        }
        for iface, c in counters.items()
    }


def net_interfaces_data():
    addrs = psutil.net_if_addrs()
    return {
        iface: [{"family": str(a.family), "address": a.address} for a in addr_list]
        for iface, addr_list in addrs.items()
    }
