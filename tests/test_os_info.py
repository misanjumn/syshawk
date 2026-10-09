"""Tests for os_info collector."""

from syshawk.collectors import os_info


def test_collect_returns_required_keys():
    data = os_info.collect()
    for key in ("system", "hostname", "kernel", "machine", "uptime_seconds", "uptime_human", "os_name"):
        assert key in data, f"Missing key: {key}"


def test_uptime_is_positive():
    data = os_info.collect()
    assert data["uptime_seconds"] > 0


def test_hostname_is_string():
    data = os_info.collect()
    assert isinstance(data["hostname"], str)
    assert len(data["hostname"]) > 0
