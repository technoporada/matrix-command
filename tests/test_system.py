"""Tests for System Info Service"""

import pytest
from services.system import SystemInfo


@pytest.fixture
def sysinfo():
    return SystemInfo()


def test_get_snapshot(sysinfo):
    snapshot = sysinfo.get_snapshot()
    assert "cpu" in snapshot
    assert "memory" in snapshot
    assert "disk" in snapshot
    assert "network" in snapshot
    assert "system" in snapshot
    assert "connections" in snapshot
    assert "top_processes" in snapshot

    assert 0 <= snapshot["cpu"]["percent"] <= 100
    assert 0 <= snapshot["memory"]["percent"] <= 100
    assert 0 <= snapshot["disk"]["percent"] <= 100
    assert snapshot["cpu"]["cores"] > 0
    assert snapshot["memory"]["total_gb"] > 0
    assert snapshot["disk"]["total_gb"] > 0


def test_get_network_interfaces(sysinfo):
    interfaces = sysinfo.get_network_interfaces()
    assert isinstance(interfaces, list)
    for iface in interfaces:
        assert "name" in iface
        assert "addresses" in iface


def test_hostname(sysinfo):
    import socket
    assert sysinfo.hostname == socket.gethostname()
