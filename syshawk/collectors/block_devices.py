"""Collect block device information (lsblk-style)."""

import platform
import subprocess
import json


def collect() -> list[dict]:
    system = platform.system()
    if system == "Linux":
        return _linux()
    elif system == "Darwin":
        return _macos()
    return []


def _linux() -> list[dict]:
    try:
        out = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL,ROTA"],
            capture_output=True, text=True
        )
        data = json.loads(out.stdout)
        return _parse_linux(data.get("blockdevices", []))
    except Exception:
        return []


def _parse_linux(devices: list, depth: int = 0) -> list[dict]:
    result = []
    for dev in devices:
        result.append({
            "name":       dev.get("name", ""),
            "size":       dev.get("size", ""),
            "type":       dev.get("type", ""),
            "fstype":     dev.get("fstype") or "",
            "mountpoint": dev.get("mountpoint") or "",
            "model":      (dev.get("model") or "").strip(),
            "rotational": dev.get("rota") == "1",
            "depth":      depth,
        })
        for child in dev.get("children", []):
            result += _parse_linux([child], depth + 1)
    return result


def _macos() -> list[dict]:
    try:
        out = subprocess.run(
            ["diskutil", "list", "-plist"],
            capture_output=True, text=True
        )
        import plistlib
        data = plistlib.loads(out.stdout.encode())
        result = []
        for disk in data.get("AllDisksAndPartitions", []):
            dev_id = disk.get("DeviceIdentifier", "")
            size_bytes = disk.get("Size", 0)
            result.append({
                "name":       dev_id,
                "size":       _fmt_bytes(size_bytes),
                "type":       "disk",
                "fstype":     disk.get("Content", ""),
                "mountpoint": "",
                "model":      "",   # skipped — diskutil info is slow
                "rotational": False,
                "depth":      0,
            })
            for part in disk.get("Partitions", []):
                p_id = part.get("DeviceIdentifier", "")
                result.append({
                    "name":       p_id,
                    "size":       _fmt_bytes(part.get("Size", 0)),
                    "type":       "part",
                    "fstype":     part.get("Content", ""),
                    "mountpoint": part.get("MountPoint", ""),
                    "model":      "",
                    "rotational": False,
                    "depth":      1,
                })
        return result
    except Exception:
        return []


def _macos_model(dev_id: str) -> str:
    try:
        out = subprocess.run(
            ["diskutil", "info", dev_id],
            capture_output=True, text=True
        )
        for line in out.stdout.splitlines():
            if "Device / Media Name" in line or "Media Name" in line:
                return line.split(":", 1)[-1].strip()
    except Exception:
        pass
    return ""


def _fmt_bytes(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"
