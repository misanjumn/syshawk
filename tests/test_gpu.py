"""Tests for gpu collector."""

from syshawk.collectors import gpu


def test_collect_returns_list():
    data = gpu.collect()
    assert isinstance(data, list)


def test_no_exception_on_collect():
    """collect() must never raise — GPUtil is optional."""
    try:
        gpu.collect()
    except Exception as exc:
        assert False, f"gpu.collect() raised unexpectedly: {exc}"


def test_gpu_entries_have_required_keys():
    data = gpu.collect()
    for g in data:
        for key in ("name", "load_percent", "memory_used_mb", "memory_total_mb"):
            assert key in g, f"Missing key '{key}' in GPU entry: {g}"
