"""Collect CPU information."""

import platform
import subprocess
import psutil
import cpuinfo


def collect() -> dict:
    info = cpuinfo.get_cpu_info()

    freq = psutil.cpu_freq()
    # interval=0 returns cached value instantly — fast enough for a snapshot
    psutil.cpu_percent(interval=None)  # prime the counter
    usage = psutil.cpu_percent(interval=0.1)
    temp = _cpu_temp()

    return {
        "brand": info.get("brand_raw", "Unknown"),
        "arch": info.get("arch", platform_arch()),
        "cores_physical": psutil.cpu_count(logical=False) or 1,
        "cores_logical": psutil.cpu_count(logical=True) or 1,
        "usage_percent": usage,
        "freq_mhz": round(freq.current, 1) if freq else None,
        "freq_max_mhz": round(freq.max, 1) if freq and freq.max else None,
        "temp_celsius": temp,
        "topology": _topology(),
    }


def _cpu_temp() -> float | None:
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        # try common keys
        for key in ("coretemp", "cpu_thermal", "k10temp", "acpitz"):
            if key in temps:
                entries = temps[key]
                if entries:
                    return round(entries[0].current, 1)
        # fallback: first available
        for entries in temps.values():
            if entries:
                return round(entries[0].current, 1)
    except (AttributeError, Exception):
        pass
    return None


def _topology() -> str | None:
    """Return a short topology string e.g. '1 socket · 1 core · 8 threads/core'"""
    system = platform.system()
    try:
        if system == "Linux":
            out = subprocess.run(
                ["lscpu"], capture_output=True, text=True
            ).stdout
            sockets = threads = cores = None
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("Socket(s):"):
                    sockets = line.split(":")[-1].strip()
                elif line.startswith("Core(s) per socket:"):
                    cores = line.split(":")[-1].strip()
                elif line.startswith("Thread(s) per core:"):
                    threads = line.split(":")[-1].strip()
            if sockets and cores and threads:
                return f"{sockets} socket · {cores} core/socket · {threads} thread/core"
        elif system == "Darwin":
            def _sysctl(key: str) -> str:
                return subprocess.run(
                    ["sysctl", "-n", key], capture_output=True, text=True
                ).stdout.strip()
            packages = _sysctl("hw.packages") or "1"
            cores    = _sysctl("hw.physicalcpu") or "?"
            logical  = _sysctl("hw.logicalcpu") or "?"
            return f"{packages} socket · {cores} cores · {logical} logical CPUs"
    except Exception:
        pass
    return None


def platform_arch() -> str:
    return platform.machine()
