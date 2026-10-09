"""Collect RAM and swap memory information."""

import psutil


def collect() -> dict:
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total_gb": _to_gb(ram.total),
        "used_gb": _to_gb(ram.used),
        "available_gb": _to_gb(ram.available),
        "percent": ram.percent,
        "swap_total_gb": _to_gb(swap.total),
        "swap_used_gb": _to_gb(swap.used),
        "swap_percent": swap.percent,
    }


def _to_gb(bytes_val: int) -> float:
    return round(bytes_val / (1024 ** 3), 1)
