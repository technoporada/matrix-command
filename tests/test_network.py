"""Tests for Network Recon Service"""

import pytest
import asyncio
from services.network import NetworkRecon


@pytest.fixture
def network():
    return NetworkRecon()


def test_load_tech_signatures(network):
    sigs = network._load_tech_signatures()
    assert len(sigs) > 0
    assert any(s["name"] == "WordPress" for s in sigs)


def test_detect_technologies(network):
    html = '<html><script src="jquery.min.js"></script></html>'
    tech = network._detect_technologies(html, {"server": "nginx"})
    names = [t["name"] for t in tech]
    assert "jQuery" in names
    assert "nginx" in names


@pytest.mark.asyncio
async def test_port_scan_localhost(network):
    results = await network.port_scan("127.0.0.1", [22])
    assert "open" in results
    assert "closed" in results
    assert "filtered" in results
    assert "duration_ms" in results


@pytest.mark.asyncio
async def test_dns_lookup(network):
    results = await network.dns_lookup("localhost")
    assert results["domain"] == "localhost"
    assert "records" in results
