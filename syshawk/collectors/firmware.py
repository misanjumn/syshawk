"""Collect firmware / BIOS / UEFI information."""

import json
import platform
import subprocess


def collect() -> dict:
    system = platform.system()
    if system == "Darwin":
        return _macos()
    elif system == "Linux":
        return _linux()
    elif system == "Windows":
        return _windows()
    return {}


def _macos() -> dict:
    info = {"boot_mode": "UEFI"}  # all modern Macs use UEFI
    try:
        # Both data types in one system_profiler call — much faster
        out = subprocess.run(
            ["system_profiler", "SPHardwareDataType", "SPiBridgeDataType"],
            capture_output=True, text=True, timeout=5
        ).stdout
        for line in out.splitlines():
            line = line.strip()
            if "Boot ROM Version" in line:
                info["bios_version"] = line.split(":", 1)[-1].strip()
            elif "SMC Version" in line:
                info["smc_version"] = line.split(":", 1)[-1].strip()
            elif "Secure Boot" in line:
                info["secure_boot"] = line.split(":", 1)[-1].strip()
    except Exception:
        pass
    return info


def _linux() -> dict:
    import os
    import re

    info = {}

    # dmidecode — requires root on most distros; skip empty/error output silently
    try:
        def _dmi(key: str) -> str:
            r = subprocess.run(
                ["dmidecode", "-s", key],
                capture_output=True, text=True
            )
            return r.stdout.strip() if r.returncode == 0 else ""

        for attr, key in (
            ("bios_vendor",  "bios-vendor"),
            ("bios_version", "bios-version"),
            ("bios_date",    "bios-release-date"),
            ("board_name",   "baseboard-product-name"),
        ):
            val = _dmi(key)
            if val:  # only store non-empty values
                info[attr] = val
    except Exception:
        pass

    # Boot mode
    try:
        info["boot_mode"] = "UEFI" if os.path.exists("/sys/firmware/efi") else "Legacy BIOS"
    except Exception:
        pass

    # Secure boot
    try:
        r = subprocess.run(["mokutil", "--sb-state"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            info["secure_boot"] = r.stdout.strip()
    except Exception:
        pass

    # IBM POWER firmware via lsmcode
    # lsmcode is often in /usr/sbin which may not be in a normal user's $PATH
    _lsmcode_candidates = ["lsmcode", "/usr/sbin/lsmcode", "/sbin/lsmcode"]
    for cmd in _lsmcode_candidates:
        try:
            r = subprocess.run([cmd], capture_output=True, text=True)
            out = r.stdout.strip()
            if out:
                # "Version of System Firmware is FW1120.00 (RB1120_139) ..."
                m = re.search(r"is\s+(\S+)", out)
                if m:
                    info["bios_version"] = m.group(1)
                    info["bios_vendor"]  = "IBM POWER Firmware"
                info["firmware_raw"] = out
                break  # found and parsed — stop trying
        except FileNotFoundError:
            continue
        except Exception:
            break

    return info


def _windows() -> dict:
    info = {}
    try:
        out = subprocess.run(
            ["powershell", "-Command",
             "Get-WmiObject -Class Win32_BIOS | Select-Object Manufacturer,SMBIOSBIOSVersion,ReleaseDate | ConvertTo-Json"],
            capture_output=True, text=True
        ).stdout
        data = json.loads(out)
        info["bios_vendor"]  = data.get("Manufacturer", "")
        info["bios_version"] = data.get("SMBIOSBIOSVersion", "")
        info["bios_date"]    = data.get("ReleaseDate", "")
    except Exception:
        pass
    return info
