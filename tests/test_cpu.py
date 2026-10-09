"""Tests for cpu collector."""

from syshawk.collectors import cpu


def test_collect_returns_required_keys():
    data = cpu.collect()
    for key in ("brand", "arch", "cores_physical", "cores_logical", "usage_percent"):
        assert key in data, f"Missing key: {key}"


def test_cores_are_positive():
    data = cpu.collect()
    assert data["cores_physical"] >= 1
    assert data["cores_logical"] >= 1


def test_usage_in_range():
    data = cpu.collect()
    assert 0.0 <= data["usage_percent"] <= 100.0


def test_topology_key_present():
    data = cpu.collect()
    assert "topology" in data


def test_topology_is_str_or_none():
    data = cpu.collect()
    assert data["topology"] is None or isinstance(data["topology"], str)
