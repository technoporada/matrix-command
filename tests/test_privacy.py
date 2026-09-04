"""Tests for Privacy Monitor Service"""

import pytest
from services.privacy import PrivacyMonitor


@pytest.fixture
def monitor():
    return PrivacyMonitor()


def test_header_severity(monitor):
    assert monitor._header_severity("strict-transport-security") == "critical"
    assert monitor._header_severity("x-content-type-options") == "high"
    assert monitor._header_severity("x-xss-protection") == "medium"
    assert monitor._header_severity("custom-header") == "low"


def test_check_security_headers(monitor):
    headers = {
        "strict-transport-security": "max-age=31536000",
        "content-type": "text/html",
    }
    result = monitor._check_security_headers(headers)
    assert result["strict-transport-security"]["present"] is True
    assert result["content-security-policy"]["present"] is False


def test_detect_trackers(monitor):
    html = '<script src="https://google-analytics.com/analytics.js"></script>'
    trackers = monitor._detect_trackers(html)
    assert any(t["domain"] == "google-analytics.com" for t in trackers)


def test_calculate_score(monitor):
    results = {
        "security_headers": {"hsts": {"present": True}, "csp": {"present": False, "severity": "critical"}},
        "trackers": [{"domain": "test"}],
        "third_party": ["a.com", "b.com"],
    }
    score = monitor._calculate_score(results)
    assert score < 100
    assert score > 0
