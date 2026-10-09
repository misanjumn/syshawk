"""Collect OS, kernel, hostname and uptime information."""

import platform
import socket
import subprocess
import sys
import time


def collect() -> dict:
    uname = platform.uname()
    boot_time = _boot_time()
    uptime_seconds = int(time.time() - boot_time)

    info = {
        "system": uname.system,
        "hostname": socket.gethostname(),
        "kernel": uname.release,
        "version": uname.version,
        "machine": uname.machine,
        "uptime_seconds": uptime_seconds,
        "uptime_human": _format_uptime(uptime_seconds),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    # Enrich with friendly OS name
    if uname.system == "Darwin":
        try:
            result = subprocess.run(
                ["sw_vers", "-productName"], capture_output=True, text=True
            )
            ver = subprocess.run(
                ["sw_vers", "-productVersion"], capture_output=True, text=True
            )
            info["os_name"] = f"{result.stdout.strip()} {ver.stdout.strip()}"
        except Exception:
            info["os_name"] = f"macOS {platform.mac_ver()[0]}"
    elif uname.system == "Linux":
        try:
            import distro
            info["os_name"] = f"{distro.name()} {distro.version()}"
        except ImportError:
            info["os_name"] = "Linux"
    elif uname.system == "Windows":
        info["os_name"] = f"Windows {platform.version()}"
    else:
        info["os_name"] = uname.system

    return info


def _boot_time() -> float:
    try:
        import psutil
        return psutil.boot_time()
    except Exception:
        return time.time()


def _format_uptime(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return " ".join(parts)
