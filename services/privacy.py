"""MatrixCommand - Privacy Monitor Service"""

import re
from typing import Dict, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config import Config


class PrivacyMonitor:
    def __init__(self):
        self.trackers = Config.PRIVACY_TRACKERS
        self.security_headers = Config.SECURITY_HEADERS

    async def scan_url(self, url: str) -> Dict:
        results = {
            "url": url,
            "trackers": [],
            "third_party": [],
            "cookies": [],
            "security_headers": {},
            "privacy_score": 100,
            "recommendations": [],
        }

        try:
            async with httpx.AsyncClient(
                timeout=Config.REQUEST_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": Config.USER_AGENT},
            ) as client:
                resp = await client.get(url)

                results["security_headers"] = self._check_security_headers(dict(resp.headers))
                results["cookies"] = self._parse_cookies(resp.cookies)
                results["trackers"] = self._detect_trackers(resp.text)
                results["third_party"] = self._detect_third_party(resp.text, url)

                results["privacy_score"] = self._calculate_score(results)
                results["recommendations"] = self._generate_recommendations(results)
        except Exception as e:
            results["error"] = str(e)

        return results

    def _check_security_headers(self, headers: Dict) -> Dict:
        found = {}
        for header in self.security_headers:
            value = headers.get(header)
            if value:
                found[header] = {"present": True, "value": value[:200]}
            else:
                found[header] = {"present": False, "severity": self._header_severity(header)}
        return found

    def _header_severity(self, header: str) -> str:
        critical = ["strict-transport-security", "content-security-policy"]
        high = ["x-content-type-options", "x-frame-options"]
        medium = ["x-xss-protection", "referrer-policy"]

        if header in critical:
            return "critical"
        elif header in high:
            return "high"
        elif header in medium:
            return "medium"
        return "low"

    def _parse_cookies(self, cookies: httpx.Cookies) -> List[Dict]:
        result = []
        for name, value in cookies.items():
            result.append({
                "name": name,
                "httponly": "httponly" in str(cookies).lower(),
                "secure": "secure" in str(cookies).lower(),
            })
        return result

    def _detect_trackers(self, html: str) -> List[Dict]:
        found = []
        for tracker in self.trackers:
            if tracker in html:
                found.append({
                    "domain": tracker,
                    "category": self._tracker_category(tracker),
                    "risk": self._tracker_risk(tracker),
                })
        return found

    def _detect_third_party(self, html: str, base_url: str) -> List[str]:
        base_domain = urlparse(base_url).hostname
        third_party = set()

        for match in re.findall(r'(?:src|href|action)="([^"]+)"', html):
            try:
                parsed = urlparse(match)
                if parsed.hostname and parsed.hostname != base_domain:
                    third_party.add(parsed.hostname)
            except Exception:
                pass

        return list(third_party)[:50]

    def _tracker_category(self, tracker: str) -> str:
        analytics = ["google-analytics", "googletagmanager", "hotjar", "mixpanel",
                     "segment.com", "amplitude", "heap.io", "fullstory"]
        ads = ["googlesyndication", "doubleclick", "amazon-adsystem",
               "analytics.twitter", "ads.twitter"]
        social = ["facebook.com", "facebook.net"]

        for a in analytics:
            if a in tracker:
                return "analytics"
        for a in ads:
            if a in tracker:
                return "advertising"
        for s in social:
            if s in tracker:
                return "social"
        return "other"

    def _tracker_risk(self, tracker: str) -> str:
        high_risk = ["facebook", "google-analytics", "hotjar", "fullstory", "mouseflow"]
        for h in high_risk:
            if h in tracker:
                return "high"
        return "medium"

    def _calculate_score(self, results: Dict) -> int:
        score = 100

        for header_info in results["security_headers"].values():
            if not header_info.get("present"):
                severity = header_info.get("severity", "low")
                if severity == "critical":
                    score -= 15
                elif severity == "high":
                    score -= 10
                elif severity == "medium":
                    score -= 5

        score -= len(results["trackers"]) * 3
        score -= len(results["third_party"]) * 1

        return max(0, score)

    def _generate_recommendations(self, results: Dict) -> List[str]:
        recs = []

        for header, info in results["security_headers"].items():
            if not info.get("present"):
                recs.append(f"Add header: {header}")

        if results["trackers"]:
            tracker_count = len(results["trackers"])
            recs.append(f"Block {tracker_count} tracker(s) to improve privacy")

        if len(results["third_party"]) > 5:
            recs.append(f"Reduce third-party requests ({len(results['third_party'])} found)")

        return recs[:10]
