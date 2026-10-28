import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
import ssl
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


@pytest.mark.asyncio
async def test_ssl_check_requires_tls_12(network, monkeypatch):
    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def getpeercert(self, binary_form):
            return b"certificate"

    class FakeContext:
        def wrap_socket(self, sock, server_hostname):
            return FakeSocket()

    context = FakeContext()
    monkeypatch.setattr("services.network.ssl.create_default_context", lambda: context)
    monkeypatch.setattr(
        "services.network.socket.create_connection", lambda *args, **kwargs: FakeSocket()
    )
    monkeypatch.setattr("services.network.ssl.DER_cert_to_PEM_cert", lambda cert: "certificate")

    await network.ssl_check("example.com")

    assert context.minimum_version == ssl.TLSVersion.TLSv1_2
