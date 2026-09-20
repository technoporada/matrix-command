import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def test_detect_no_tech(network):
    html = '<html><body>nothing</body></html>'
    tech = network._detect_technologies(html, {})
    assert isinstance(tech, list)


def test_tech_signatures_categories(network):
    sigs = network._load_tech_signatures()
    categories = set(s["category"] for s in sigs)
    assert "CMS" in categories
    assert "Framework" in categories
    assert "Server" in categories
