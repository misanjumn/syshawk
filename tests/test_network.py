"""Tests for network collector."""

from syshawk.collectors import network


def test_collect_returns_list():
    data = network.collect()
    assert isinstance(data, list)


def test_interface_has_required_keys():
    data = network.collect()
    for iface in data:
        for key in ("name", "ipv4", "ipv6", "mac", "is_up"):
            assert key in iface, f"Missing key: {key}"


def test_throughput_returns_dict():
    thru = network.throughput(interval=0.2)
    for key in ("sent_mbps", "recv_mbps", "total_sent_gb", "total_recv_gb"):
        assert key in thru, f"Missing key: {key}"
