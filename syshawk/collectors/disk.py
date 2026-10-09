"""Collect disk/partition usage information."""

import psutil


def collect() -> list[dict]:
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        partitions.append({
            "mountpoint": part.mountpoint,
            "device": part.device,
            "fstype": part.fstype,
            "total_gb": _to_gb(usage.total),
            "used_gb": _to_gb(usage.used),
            "free_gb": _to_gb(usage.free),
            "percent": usage.percent,
        })
    return partitions


def io_counters() -> dict | None:
    try:
        io = psutil.disk_io_counters()
        if io:
            return {
                "read_mb": round(io.read_bytes / (1024 ** 2), 1),
                "write_mb": round(io.write_bytes / (1024 ** 2), 1),
            }
    except Exception:
        pass
    return None


def _to_gb(bytes_val: int) -> float:
    return round(bytes_val / (1024 ** 3), 1)
