# 🦅 SysHawk

> A cross-platform CLI for system diagnostics - snapshot your OS, CPU, memory, disk, network, firmware and block devices in one command.

[![PyPI version](https://badge.fury.io/py/syshawk.svg)](https://pypi.org/project/syshawk/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🦅 SysHawk - fast, sharp, cross-platform system diagnostics.

---

## Install

```bash
pip3 install syshawk
```

---

## Usage

Both **flag style** and **subcommand style** work identically:

```bash
# Full system snapshot (default)
syshawk

# Individual sections - flag style
syshawk --os
syshawk --cpu
syshawk --memory
syshawk --disk
syshawk --blocks
syshawk --firmware
syshawk --network
syshawk --gpu

# Individual sections - subcommand style
syshawk os
syshawk cpu
syshawk memory
syshawk disk
syshawk blocks
syshawk firmware
syshawk network
syshawk gpu

# Machine-readable JSON
syshawk --json
syshawk json

# Live refresh (like top)
syshawk --watch
syshawk --watch --interval 5
syshawk watch

# CPU flame graph → opens in browser
syshawk --flamegraph
syshawk --flamegraph --duration 10
syshawk --flamegraph --out my-flame.html
syshawk flamegraph

# Full HTML system report → opens in browser
syshawk --report
syshawk --report --out system-report.html
syshawk report

# Version
syshawk --version
```

---

## Example output

```
🦅 SysHawk v0.1.0 - system diagnostics

  OS         : macOS 26.5.2  (Darwin 25.5.0)
  Kernel     : 25.5.0
  Hostname   : Misbahs-MacBook-Pro.local
  Arch       : arm64
  Uptime     : 22d 19h 43m
  Python     : 3.13.4
  Boot Mode  : UEFI
  SecureBoot : Full Security

  CPU        : Apple M3 Pro  · 4056 MHz
  Cores      : 12P / 12L
  Topology   : 1 socket · 12 cores · 12 logical CPUs
  Usage      : 35.0%

  Memory     : 10.9 GB / 36.0 GB  82.1%
  Swap       : 27.3 GB / 28.0 GB  97.6%

  Disk       : /                             11.7 GB / 926.4 GB  1.7%
               /System/Volumes/Data          179.4 GB / 926.4 GB  20.5%
               /Volumes/OpenVPN Connect      0.2 GB / 0.2 GB  98.8%

  Blocks     : disk0         931.8 GB    GUID_partition_scheme    SSD
                 └─ disk0s1       500.0 MB    Apple_APFS_ISC      SSD
                 └─ disk0s2       926.4 GB    Apple_APFS          SSD
                 └─ disk0s3       5.0 GB      Apple_APFS_Recovery SSD
               disk1         500.0 MB    Apple_APFS_Container     SSD
               disk2         5.0 GB      Apple_APFS_Container     SSD
               disk3         926.4 GB    Apple_APFS_Container     SSD
               disk4         255.3 MB    GUID_partition_scheme    SSD
                 └─ disk4s1       255.2 MB    Apple_HFS           SSD  → /Volumes/OpenVPN Connect

  Network    : en0       192.168.0.9         255.255.255.0  up
               MAC      f6:ec:25:3d:4b:c6
               Gateway  192.168.0.1
               DNS      192.168.0.1
  Throughput : ↑ 0.01 MB/s   ↓ 0.01 MB/s
```

---

## Features

| Feature | Command |
|---|---|
| System snapshot | `syshawk` |
| OS info + firmware | `syshawk os` or `syshawk --os` |
| CPU info + topology | `syshawk cpu` or `syshawk --cpu` |
| Memory + swap | `syshawk memory` or `syshawk --memory` |
| Mounted disk partitions | `syshawk disk` or `syshawk --disk` |
| Block devices tree | `syshawk blocks` or `syshawk --blocks` |
| Firmware / BIOS / UEFI | `syshawk firmware` or `syshawk --firmware` |
| Network interfaces | `syshawk network` or `syshawk --network` |
| GPU info (NVIDIA) | `syshawk gpu` or `syshawk --gpu` |
| JSON output | `syshawk --json` |
| Live watch mode | `syshawk --watch` |
| CPU flame graph (HTML) | `syshawk --flamegraph` |
| Full HTML report | `syshawk --report` |

---

## Dependencies

- [`psutil`](https://github.com/giampaolo/psutil) - CPU, memory, disk, network
- [`py-cpuinfo`](https://github.com/workhorsy/py-cpuinfo) - detailed CPU brand & arch
- [`rich`](https://github.com/Textualize/rich) - pretty terminal output
- [`jinja2`](https://jinja.palletsprojects.com/) - HTML report templating
- [`distro`](https://github.com/python-distro/distro) *(Linux only)* - OS release name

Optional:
- [`gputil`](https://github.com/anderskm/gputil) - NVIDIA GPU stats (`pip3 install syshawk[gpu]`)

---

## Platform support

| Platform | OS | CPU | Memory | Disk | Blocks | Firmware | Network | GPU |
|---|---|---|---|---|---|---|---|---|
| macOS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅* |
| Linux (x86_64) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅† | ✅ | ✅* |
| Linux (ppc64le) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅‡ | ✅ | - |
| Windows | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅* |

\* Requires `pip3 install syshawk[gpu]` and an NVIDIA GPU  
† Requires `dmidecode` (needs sudo on most distros); Boot Mode via `/sys/firmware/efi`  
‡ IBM POWER firmware via `lsmcode` (available on SLES/ppc64le)

---

## Development

```bash
git clone https://github.com/misanjumn/syshawk
cd syshawk
pip3 install -e ".[dev]"
pytest
```

---

## Author

**Misbah Anjum N**
- GitHub: [@misanjumn](https://github.com/misanjumn)
- PyPI: [syshawk](https://pypi.org/project/syshawk/)

---

## AI Assistance

This project was developed with the assistance of an AI coding tool.

## License

MIT © Misbah Anjum N
