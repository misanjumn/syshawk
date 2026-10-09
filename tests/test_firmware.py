"""Tests for firmware collector."""

from syshawk.collectors import firmware


def test_collect_returns_dict():
    data = firmware.collect()
    assert isinstance(data, dict)


def test_no_exception_on_collect():
    """collect() must never raise — it catches all errors internally."""
    try:
        firmware.collect()
    except Exception as exc:
        assert False, f"firmware.collect() raised unexpectedly: {exc}"


def test_known_keys_are_strings_when_present():
    data = firmware.collect()
    for key in ("bios_version", "bios_vendor", "bios_date", "boot_mode", "secure_boot"):
        if key in data:
            assert isinstance(data[key], str), f"Key '{key}' should be a string"
