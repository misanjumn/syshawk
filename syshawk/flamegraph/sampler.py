"""Sample CPU stack traces using psutil over a given duration."""

import collections
import time
import psutil


def sample(duration: int = 5, hz: int = 100) -> dict[str, int]:
    """
    Sample all running processes every (1/hz) seconds for `duration` seconds.
    Returns a dict mapping semicolon-joined stack strings to hit counts
    (folded stacks format, compatible with flamegraph renderers).
    """
    stacks: dict[str, int] = collections.defaultdict(int)
    interval = 1.0 / hz
    end = time.time() + duration

    while time.time() < end:
        for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
            try:
                name = proc.info["name"] or "unknown"
                cpu = proc.info["cpu_percent"] or 0
                if cpu <= 0:
                    continue
                # build a simple 2-level stack: process name → cpu%
                # For a real deep stack you'd need py-spy; this gives process-level granularity
                key = f"root;{name}"
                stacks[key] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(interval)

    return dict(stacks)
