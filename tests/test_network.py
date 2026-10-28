import sys
import os
import socket
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from types import SimpleNamespace

import services.network as network_service
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
async def test_web_scraper_blocks_non_http_and_private_urls(network, monkeypatch):
    monkeypatch.setattr(network_service, "_is_public_host", lambda host: False)

    class UnexpectedClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("blocked URL must not be fetched")

    monkeypatch.setattr(network_service.httpx, "AsyncClient", UnexpectedClient)

    for url in ("file:///etc/passwd", "http://127.0.0.1/"):
        result = await network.web_scraper(url)
        assert result["error"] == "blocked: non-public host"


@pytest.mark.asyncio
async def test_web_scraper_blocks_private_redirect(network, monkeypatch):
    monkeypatch.setattr(
        network_service,
        "_is_public_host",
        lambda host: host == "public.example",
    )
    fetched_urls = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            fetched_urls.append(url)
            return SimpleNamespace(
                status_code=302,
                headers={"location": "http://127.0.0.1/"},
            )

    monkeypatch.setattr(network_service.httpx, "AsyncClient", FakeClient)

    result = await network.web_scraper("https://public.example/")

    assert result["error"] == "blocked: redirect to non-public host"
    assert fetched_urls == ["https://public.example/"]


@pytest.mark.asyncio
async def test_web_scraper_returns_parsed_response(network, monkeypatch):
    monkeypatch.setattr(network_service, "_is_public_host", lambda host: True)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return SimpleNamespace(
                status_code=200,
                headers={"server": "nginx"},
                text="<html><title>Example</title><h1>Welcome</h1></html>",
            )

    monkeypatch.setattr(network_service.httpx, "AsyncClient", FakeClient)

    result = await network.web_scraper("https://public.example/")

    assert result["status"] == 200
    assert result["title"] == "Example"
    assert result["headings"] == [{"tag": "H1", "text": "Welcome"}]
