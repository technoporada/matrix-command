import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from services.system import SystemInfo


def test_system_info_init():
    info = SystemInfo()
    assert info is not None


def test_get_snapshot():
    info = SystemInfo()
    snapshot = info.get_snapshot()
    assert "cpu" in snapshot
    assert "memory" in snapshot
    assert "disk" in snapshot
    assert "network" in snapshot


def test_cpu_info():
    info = SystemInfo()
    snapshot = info.get_snapshot()
    cpu = snapshot["cpu"]
    assert "percent" in cpu
    assert "cores" in cpu
    assert "freq" in cpu
    assert 0 <= cpu["percent"] <= 100


def test_memory_info():
    info = SystemInfo()
    snapshot = info.get_snapshot()
    mem = snapshot["memory"]
    assert "total_gb" in mem
    assert "used_gb" in mem
    assert "percent" in mem
    assert mem["total_gb"] > 0
    assert 0 <= mem["percent"] <= 100


def test_disk_info():
    info = SystemInfo()
    snapshot = info.get_snapshot()
    disk = snapshot["disk"]
    assert "total_gb" in disk
    assert "used_gb" in disk
    assert "percent" in disk
    assert disk["total_gb"] > 0


def test_network_info():
    info = SystemInfo()
    snapshot = info.get_snapshot()
    net = snapshot["network"]
    assert "sent_mb" in net
    assert "recv_mb" in net
