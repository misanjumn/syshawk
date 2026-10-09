"""Tests for block_devices collector."""

from syshawk.collectors import block_devices


def test_collect_returns_list():
    data = block_devices.collect()
    assert isinstance(data, list)


def test_each_device_has_required_keys():
    data = block_devices.collect()
    for dev in data:
        for key in ("name", "size", "depth"):
            assert key in dev, f"Missing key '{key}' in device: {dev}"


def test_depth_is_non_negative():
    data = block_devices.collect()
    for dev in data:
        assert dev["depth"] >= 0
