import sys
import os
import socket
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
import httpx
from services.network import NetworkRecon, _prepare_public_request


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


def test_prepare_public_request_pins_resolved_address(monkeypatch):
    def getaddrinfo(host, port, type):
        assert host == "example.com"
        assert port == 443
        assert type == socket.SOCK_STREAM
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", port))
        ]

    monkeypatch.setattr("services.network.socket.getaddrinfo", getaddrinfo)

    prepared = _prepare_public_request("https://example.com/path?q=1")

    assert prepared == (
        "https://8.8.8.8/path?q=1",
        "example.com",
        "example.com",
    )


def test_prepare_public_request_rejects_unsafe_urls(monkeypatch):
    assert _prepare_public_request("http://127.0.0.1/") is None
    assert _prepare_public_request("file:///etc/passwd") is None
    assert _prepare_public_request("https://[invalid/") is None

    monkeypatch.setattr(
        "services.network.socket.getaddrinfo",
        lambda host, port, type: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
        ],
    )
    assert _prepare_public_request("https://example.com/") is None


@pytest.mark.asyncio
async def test_web_scraper_sends_pinned_request(monkeypatch):
    sent_requests = []

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def build_request(self, method, url, headers):
            return httpx.Request(method, url, headers=headers)

        async def send(self, request):
            sent_requests.append(request)
            return httpx.Response(200, text="<title>Example</title>", request=request)

    monkeypatch.setattr(
        "services.network._prepare_public_request",
        lambda url: ("https://8.8.8.8/path", "example.com", "example.com"),
    )
    monkeypatch.setattr("services.network.httpx.AsyncClient", FakeClient)

    result = await NetworkRecon().web_scraper("https://example.com/path")

    assert result["title"] == "Example"
    assert str(sent_requests[0].url) == "https://8.8.8.8/path"
    assert sent_requests[0].headers["host"] == "example.com"
    assert sent_requests[0].extensions["sni_hostname"] == "example.com"
