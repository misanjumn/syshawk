"""🦅 SysHawk CLI — entry point."""

import argparse
import json
import re
import time

from rich.console import Console

from syshawk import __version__
from syshawk.collectors import cpu, disk, memory, network, os_info, gpu, block_devices, firmware

console = Console()


# ── helpers ───────────────────────────────────────────────────────────────────

def _gb(val) -> str:
    return f"{val:.1f} GB" if val is not None else "N/A"


def _pct_color(percent: float) -> str:
    """Return a rich color tag based on usage threshold."""
    if percent >= 80:
        return "bold red"
    elif percent >= 50:
        return "bold yellow"
    return "bold green"


def _pct(percent: float) -> str:
    color = _pct_color(percent)
    return f"[{color}]{percent}%[/]"


def _filter_interfaces(interfaces: list) -> list:
    """Keep only interfaces that have an actual IPv4 address."""
    result = [iface for iface in interfaces if iface.get("ipv4")]
    return result or interfaces  # fallback: show all if everything got filtered


# ── section renderers ─────────────────────────────────────────────────────────

# All labels are left-padded to _LW chars so the " : " separator stays in one column.
# "  " prefix + _LW chars + " : " = value starts at column 2 + 10 + 3 = 15
_LW = 10
_CONT = " " * (2 + _LW + 3)  # continuation indent = "  " + label + " : " = 15 chars


def _label(name: str) -> str:
    return f"  [bold cyan]{name:<{_LW}}[/] : "


def _sublabel(name: str) -> str:
    """Sub-field aligned under the interface name (same indent as _CONT)."""
    return f"{_CONT}{name:<7}  "


def _render_os(data: dict, fw: dict | None = None) -> None:
    console.print(f"{_label('OS')}{data.get('os_name', data.get('system', 'Unknown'))}"
                  f"  [dim]({data['system']} {data['kernel']})[/]")
    console.print(f"{_label('Kernel')}{data['kernel']}")
    console.print(f"{_label('Hostname')}{data['hostname']}")
    console.print(f"{_label('Arch')}{data['machine']}")
    console.print(f"{_label('Uptime')}{data['uptime_human']}")
    console.print(f"{_label('Python')}{data['python']}")
    if fw:
        if fw.get("bios_version"):
            console.print(f"{_label('BIOS')}[dim]{fw.get('bios_vendor', '')}[/]  {fw['bios_version']}"
                          + (f"  [dim]{fw['bios_date']}[/]" if fw.get("bios_date") else ""))
        if fw.get("boot_mode"):
            console.print(f"{_label('Boot Mode')}{fw['boot_mode']}")
        if fw.get("secure_boot"):
            console.print(f"{_label('SecureBoot')}{fw['secure_boot']}")
        if fw.get("firmware_raw"):
            m = re.search(r"(\S+\s+\([^)]+\))", fw["firmware_raw"])
            short = m.group(1) if m else fw["firmware_raw"]
            console.print(f"{_label('FW Detail')}[dim]{short}[/]")


def _render_cpu(data: dict) -> None:
    temp = f"  · {data['temp_celsius']}°C" if data.get("temp_celsius") else ""
    freq = f"  · {data['freq_mhz']} MHz" if data.get("freq_mhz") else ""
    console.print(f"{_label('CPU')}{data['brand']}{freq}{temp}")
    console.print(f"{_label('Cores')}{data['cores_physical']}P / {data['cores_logical']}L")
    if data.get("topology"):
        console.print(f"{_label('Topology')}{data['topology']}")
    console.print(f"{_label('Usage')}{_pct(data['usage_percent'])}")


def _render_memory(data: dict) -> None:
    console.print(f"{_label('Memory')}{_gb(data['used_gb'])} / {_gb(data['total_gb'])}  {_pct(data['percent'])}")
    if data["swap_total_gb"] > 0:
        console.print(f"{_label('Swap')}{_gb(data['swap_used_gb'])} / {_gb(data['swap_total_gb'])}  {_pct(data['swap_percent'])}")


def _render_disk(partitions: list) -> None:
    _skip_prefixes = ("/System/Volumes/VM", "/System/Volumes/Preboot",
                      "/System/Volumes/Update", "/System/Volumes/xarts",
                      "/System/Volumes/iSCPreboot", "/System/Volumes/Hardware")
    visible = [p for p in partitions if not any(p["mountpoint"].startswith(s) for s in _skip_prefixes)]
    for i, part in enumerate(visible):
        label = _label("Disk") if i == 0 else _CONT
        console.print(f"{label}[magenta]{part['mountpoint']:<28}[/]"
                      f"  {_gb(part['used_gb'])} / {_gb(part['total_gb'])}"
                      f"  {_pct(part['percent'])}")


def _render_network(interfaces: list, thru: dict) -> None:
    visible = _filter_interfaces(interfaces)
    for i, iface in enumerate(visible):
        label = _label("Network") if i == 0 else "               "
        status = "[bold green]up[/]" if iface["is_up"] else "[bold red]down[/]"
        ip = iface.get("ipv4") or iface.get("ipv6") or "no IP"
        netmask = f"  {iface['netmask']}" if iface.get("netmask") else ""
        console.print(f"{label}[bold]{iface['name']:<8}[/]  {ip:<18}{netmask}  {status}")
        if iface.get("mac"):
            console.print(_sublabel("MAC") + iface["mac"])
        if iface.get("gateway"):
            console.print(_sublabel("Gateway") + iface["gateway"])
        if iface.get("dns"):
            console.print(_sublabel("DNS") + ", ".join(iface["dns"]))
        if i < len(visible) - 1:
            console.print()
    if thru:
        console.print(f"{_label('Throughput')}[green]↑ {thru['sent_mbps']} MB/s[/]   [cyan]↓ {thru['recv_mbps']} MB/s[/]")


def _render_block_devices(devices: list) -> None:
    if not devices:
        return
    for i, dev in enumerate(devices):
        label = _label("Blocks") if i == 0 else _CONT
        prefix = "  " * dev["depth"]
        tree   = "└─ " if dev["depth"] > 0 else ""
        model  = f"  [dim]{dev['model']}[/]" if dev.get("model") else ""
        fstype = dev.get("fstype") or ""
        mount  = f"  [dim]→ {dev['mountpoint']}[/]" if dev.get("mountpoint") else ""
        kind   = "HDD" if dev.get("rotational") else "SSD"
        console.print(f"{label}{prefix}{tree}[bold]{dev['name']:<12}[/]"
                      f"  {dev['size']:<10}  {fstype:<28}  {kind}{model}{mount}")


def _render_firmware(data: dict) -> None:
    if not data:
        return
    if data.get("bios_version"):
        console.print(f"{_label('BIOS')}[dim]{data.get('bios_vendor', '')}[/]  {data['bios_version']}"
                      + (f"  [dim]{data['bios_date']}[/]" if data.get("bios_date") else ""))
    if data.get("smc_version"):
        console.print(f"{_label('SMC')}{data['smc_version']}")
    if data.get("boot_mode"):
        console.print(f"{_label('Boot Mode')}{data['boot_mode']}")
    if data.get("secure_boot"):
        console.print(f"{_label('SecureBoot')}{data['secure_boot']}")
    if data.get("board_name"):
        console.print(f"{_label('Board')}{data['board_name']}")
    if data.get("firmware_raw"):
        # Trim to first parenthesised block to avoid long line wrap
        # e.g. "...FW1120.00 (RB1120_139) (t) ..." → "FW1120.00 (RB1120_139)"
        raw = data["firmware_raw"]
        m = re.search(r"(\S+\s+\([^)]+\))", raw)
        short = m.group(1) if m else raw
        console.print(f"{_label('FW Detail')}[dim]{short}[/]")


def _render_gpu(gpus: list) -> None:
    for i, g in enumerate(gpus):
        label = _label(f"GPU {i + 1}") if len(gpus) > 1 else _label("GPU")
        temp = f"  · {g['temp_celsius']}°C" if g.get("temp_celsius") else ""
        console.print(f"{label}{g['name']}{temp}")
        console.print(f"{_label('Load')}{_pct(g['load_percent'])}  {g['memory_used_mb']} / {g['memory_total_mb']} MB VRAM")


# ── snapshot ──────────────────────────────────────────────────────────────────

def _snapshot(sections: list[str] | None = None) -> dict:
    """Collect all data and return as a dict."""
    all_sections = sections or ["os", "cpu", "memory", "disk", "blocks", "firmware", "network", "gpu"]
    data = {}
    if "os" in all_sections:
        data["os"] = os_info.collect()
    if "cpu" in all_sections:
        data["cpu"] = cpu.collect()
    if "memory" in all_sections:
        data["memory"] = memory.collect()
    if "disk" in all_sections:
        data["disk"] = disk.collect()
    if "blocks" in all_sections:
        data["blocks"] = block_devices.collect()
    if "firmware" in all_sections:
        data["firmware"] = firmware.collect()
    if "network" in all_sections:
        data["network"] = network.collect()
        data["throughput"] = network.throughput(interval=0.5)
    if "gpu" in all_sections:
        data["gpu"] = gpu.collect()
    return data


def _print_snapshot(data: dict) -> None:
    console.print()
    console.print(f"[bold white]🦅 SysHawk[/] [dim]v{__version__} — system diagnostics[/]")
    console.print()

    if "os" in data:
        _render_os(data["os"], data.get("firmware"))
        console.print()
    if "cpu" in data:
        _render_cpu(data["cpu"])
        console.print()
    if "memory" in data:
        _render_memory(data["memory"])
        console.print()
    if "disk" in data:
        _render_disk(data["disk"])
        console.print()
    if "blocks" in data and data["blocks"]:
        _render_block_devices(data["blocks"])
        console.print()
    if "firmware" in data and data["firmware"] and "os" not in data:
        _render_firmware(data["firmware"])
        console.print()
    if "network" in data:
        _render_network(data["network"], data.get("throughput"))
        console.print()
    if "gpu" in data and data["gpu"]:
        _render_gpu(data["gpu"])
        console.print()


# ── watch mode ────────────────────────────────────────────────────────────────

def _watch(interval: int) -> None:
    console.print(f"[dim]🦅 SysHawk — live  (Ctrl+C to quit, refreshing every {interval}s)[/]")
    try:
        while True:
            data = _snapshot(["cpu", "memory", "network"])
            console.clear()
            console.print(f"[dim]🦅 SysHawk — live  (Ctrl+C to quit, refreshing every {interval}s)[/]\n")
            _render_cpu(data["cpu"])
            console.print()
            _render_memory(data["memory"])
            console.print()
            _render_network(data["network"], data.get("throughput"))
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped.[/]")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="syshawk",
        description="🦅 SysHawk — cross-platform system diagnostics CLI",
    )

    # ── subcommands (positional) ───────────────────────────────────────────
    parser.add_argument("command", nargs="?", default=None,
                        metavar="COMMAND",
                        help="report | flamegraph | watch | json | os | cpu | memory | disk | blocks | firmware | network | gpu")

    # section filters
    parser.add_argument("--os",       action="store_true", help="Show OS info only")
    parser.add_argument("--cpu",      action="store_true", help="Show CPU info only")
    parser.add_argument("--memory",   action="store_true", help="Show memory info only")
    parser.add_argument("--disk",     action="store_true", help="Show disk info only")
    parser.add_argument("--blocks",   action="store_true", help="Show block devices only")
    parser.add_argument("--firmware", action="store_true", help="Show firmware/BIOS info only")
    parser.add_argument("--network",  action="store_true", help="Show network info only")
    parser.add_argument("--gpu",      action="store_true", help="Show GPU info only")

    # output modes
    parser.add_argument("--json",     action="store_true", help="Output as JSON")
    parser.add_argument("--watch",    action="store_true", help="Live refresh mode")
    parser.add_argument("--interval", type=int, default=2, metavar="S",
                        help="Refresh interval for watch (default: 2s)")

    # flamegraph
    parser.add_argument("--flamegraph", action="store_true", help="Generate CPU flame graph")
    parser.add_argument("--duration",   type=int, default=5, metavar="S",
                        help="Sampling duration for flamegraph (default: 5s)")
    parser.add_argument("--out", metavar="FILE", help="Save flamegraph / report to file")

    # report
    parser.add_argument("--report", action="store_true", help="Generate full HTML report")

    parser.add_argument("--version", action="version", version=f"syshawk {__version__}")

    args = parser.parse_args()

    # merge subcommand + flag styles so both work
    do_report     = args.report     or args.command == "report"
    do_flamegraph = args.flamegraph or args.command == "flamegraph"
    do_watch      = args.watch      or args.command == "watch"
    do_json       = args.json       or args.command == "json"

    # section subcommands: "syshawk cpu" == "syshawk --cpu"
    _section_names = {"os", "cpu", "memory", "disk", "blocks", "firmware", "network", "gpu"}
    section_flags = {"os": args.os, "cpu": args.cpu, "memory": args.memory,
                     "disk": args.disk, "blocks": args.blocks, "firmware": args.firmware,
                     "network": args.network, "gpu": args.gpu}
    active = [k for k, v in section_flags.items() if v]
    if args.command in _section_names:
        active = [args.command]
    # firmware is always bundled with os since they display together
    if "os" in active and "firmware" not in active:
        active.append("firmware")
    sections = active if active else None  # None = all

    # route to feature
    if do_flamegraph:
        from syshawk.flamegraph.sampler import sample
        from syshawk.flamegraph.renderer import render_html
        console.print(f"[dim]Sampling CPU for {args.duration}s…[/]")
        stacks = sample(args.duration)
        out = args.out or "syshawk-flamegraph.html"
        render_html(stacks, out)
        console.print(f"[green]✓[/] Flame graph saved → [bold]{out}[/]")
        _open_browser(out)
        return

    if do_report:
        from syshawk.report.builder import build_report
        console.print("[dim]Collecting system data…[/]")
        data = _snapshot()
        out = args.out or "syshawk-report.html"
        build_report(data, out)
        console.print(f"[green]✓[/] Report saved → [bold]{out}[/]")
        _open_browser(out)
        return

    if do_watch:
        _watch(args.interval)
        return

    # default: snapshot
    data = _snapshot(sections)

    if do_json:
        print(json.dumps(data, indent=2))
        return

    _print_snapshot(data)


def _open_browser(path: str) -> None:
    import os
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(path)}")
