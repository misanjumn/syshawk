"""Collect network interface and throughput information."""

import platform
import subprocess
import time
import psutil


def collect() -> list[dict]:
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    gateways = _gateways()
    dns_servers = _dns()
    interfaces = []

    for iface, addr_list in addrs.items():
        if iface == "lo" or iface.startswith("lo"):
            continue

        ipv4_addr = next((a for a in addr_list if a.family.name == "AF_INET"), None)
        ipv6 = next((a.address for a in addr_list if a.family.name == "AF_INET6"), None)
        mac = next((a.address for a in addr_list if a.family.name in ("AF_LINK", "AF_PACKET")), None)

        stat = stats.get(iface)
        is_up = stat.isup if stat else False

        interfaces.append({
            "name": iface,
            "ipv4": ipv4_addr.address if ipv4_addr else None,
            "netmask": ipv4_addr.netmask if ipv4_addr else None,
            "ipv6": ipv6,
            "mac": mac,
            "is_up": is_up,
            "speed_mbps": stat.speed if stat else None,
            "gateway": gateways.get(iface) or gateways.get("default"),
            "dns": dns_servers,
        })

    return interfaces


def _gateways() -> dict[str, str]:
    """Return a dict of {iface: gateway_ip} plus a 'default' key."""
    result = {}
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.run(
                ["netstat", "-rn", "-f", "inet"], capture_output=True, text=True
            ).stdout
            for line in out.splitlines():
                parts = line.split()
                # only take lines where gateway is a real IP, not link#N
                if len(parts) >= 4 and parts[0] == "default" and not parts[1].startswith("link#"):
                    result["default"] = parts[1]
                    result[parts[3]] = parts[1]  # iface → gateway (col 4 on macOS)
        elif system == "Linux":
            out = subprocess.run(["ip", "route"], capture_output=True, text=True).stdout
            for line in out.splitlines():
                parts = line.split()
                if parts and parts[0] == "default" and "via" in parts:
                    via_idx = parts.index("via")
                    result["default"] = parts[via_idx + 1]
                    if "dev" in parts:
                        dev_idx = parts.index("dev")
                        result[parts[dev_idx + 1]] = parts[via_idx + 1]
        elif system == "Windows":
            out = subprocess.run(
                ["powershell", "-Command",
                 "(Get-NetRoute -DestinationPrefix '0.0.0.0/0').NextHop"],
                capture_output=True, text=True
            ).stdout.strip()
            if out:
                result["default"] = out.splitlines()[0]
    except Exception:
        pass
    return result


def _dns() -> list[str]:
    """Return list of DNS server IPs."""
    system = platform.system()
    servers = []
    try:
        if system in ("Darwin", "Linux"):
            with open("/etc/resolv.conf") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) >= 2:
                            servers.append(parts[1])
        elif system == "Windows":
            out = subprocess.run(
                ["powershell", "-Command",
                 "(Get-DnsClientServerAddress -AddressFamily IPv4).ServerAddresses"],
                capture_output=True, text=True
            ).stdout.strip()
            servers = [s for s in out.splitlines() if s]
    except Exception:
        pass
    return servers[:3]  # cap at 3


def throughput(interval: float = 1.0) -> dict:
    """Sample network throughput over `interval` seconds."""
    before = psutil.net_io_counters()
    time.sleep(interval)
    after = psutil.net_io_counters()

    sent = (after.bytes_sent - before.bytes_sent) / interval
    recv = (after.bytes_recv - before.bytes_recv) / interval

    return {
        "sent_mbps": round(sent / (1024 ** 2), 2),
        "recv_mbps": round(recv / (1024 ** 2), 2),
        "total_sent_gb": round(after.bytes_sent / (1024 ** 3), 2),
        "total_recv_gb": round(after.bytes_recv / (1024 ** 3), 2),
    }
