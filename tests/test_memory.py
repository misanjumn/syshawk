"""Tests for memory collector."""

from syshawk.collectors import memory


def test_collect_returns_required_keys():
    data = memory.collect()
    for key in ("total_gb", "used_gb", "available_gb", "percent", "swap_total_gb", "swap_used_gb", "swap_percent"):
        assert key in data, f"Missing key: {key}"


def test_total_is_positive():
    data = memory.collect()
    assert data["total_gb"] > 0


def test_percent_in_range():
    data = memory.collect()
    assert 0.0 <= data["percent"] <= 100.0
    assert 0.0 <= data["swap_percent"] <= 100.0


def test_used_lte_total():
    data = memory.collect()
    assert data["used_gb"] <= data["total_gb"]
