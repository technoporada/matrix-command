"""MatrixCommand - Network Recon Service"""

import asyncio
import socket
import ssl
import time
import json
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config import Config


class NetworkRecon:
    def __init__(self):
        self.timeout = Config.REQUEST_TIMEOUT
        self.tech_signatures = self._load_tech_signatures()

    def _load_tech_signatures(self) -> List[Dict]:
        return [
            {"name": "WordPress", "pattern": "wp-content|wp-includes", "category": "CMS"},
            {"name": "Joomla", "pattern": "joomla", "category": "CMS"},
            {"name": "Drupal", "pattern": "drupal", "category": "CMS"},
            {"name": "React", "pattern": "react|_next|reactroot", "category": "Framework"},
            {"name": "Vue.js", "pattern": "vue\\.js|vue\\.min\\.js", "category": "Framework"},
            {"name": "Angular", "pattern": "angular|ng-version", "category": "Framework"},
            {"name": "jQuery", "pattern": "jquery", "category": "Library"},
            {"name": "Bootstrap", "pattern": "bootstrap", "category": "CSS"},
            {"name": "Tailwind", "pattern": "tailwindcss", "category": "CSS"},
            {"name": "nginx", "pattern": "nginx", "category": "Server"},
            {"name": "Apache", "pattern": "apache", "category": "Server"},
            {"name": "IIS", "pattern": "iis|asp\\.net", "category": "Server"},
            {"name": "Cloudflare", "pattern": "cloudflare", "category": "CDN"},
            {"name": "Laravel", "pattern": "laravel", "category": "PHP"},
            {"name": "Django", "pattern": "django", "category": "Python"},
            {"name": "Flask", "pattern": "flask", "category": "Python"},
            {"name": "Express", "pattern": "express|connect\\.sess", "category": "Node"},
            {"name": "Shopify", "pattern": "shopify|myshopify", "category": "Ecommerce"},
            {"name": "WooCommerce", "pattern": "woocommerce", "category": "Ecommerce"},
            {"name": "Stripe", "pattern": "stripe", "category": "Payment"},
            {"name": "PayPal", "pattern": "paypal", "category": "Payment"},
            {"name": "Google Analytics", "pattern": "google-analytics|ga\\.js|gtag", "category": "Analytics"},
            {"name": "Hotjar", "pattern": "hotjar", "category": "Analytics"},
            {"name": "Sentry", "pattern": "sentry", "category": "ErrorTracking"},
        ]

    async def port_scan(self, target: str, ports: List[int] = None) -> Dict:
        if ports is None:
            ports = Config.PORT_SCAN_DEFAULT

        results = {"target": target, "open": [], "closed": [], "filtered": []}
        start = time.monotonic()

        async def check_port(port: int):
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(target, port),
                    timeout=2.0
                )
                writer.close()
                await writer.wait_closed()
                results["open"].append(port)
            except (ConnectionRefusedError, OSError):
                results["closed"].append(port)
            except (asyncio.TimeoutError, ConnectionError):
                results["filtered"].append(port)

        await asyncio.gather(*[check_port(p) for p in ports])
        results["duration_ms"] = int((time.monotonic() - start) * 1000)
        results["total"] = len(ports)
        results["stats"] = {
            "open": len(results["open"]),
            "closed": len(results["closed"]),
            "filtered": len(results["filtered"]),
        }
        return results

    async def whois_lookup(self, domain: str) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"https://rdap.org/domain/{domain}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "domain": domain,
                        "registrar": self._extract_rdap_field(data, "registrar"),
                        "created": self._extract_rdap_field(data, "created"),
                        "expires": self._extract_rdap_field(data, "expires"),
                        "nameservers": self._extract_rdap_nameservers(data),
                        "status": self._extract_rdap_status(data),
                        "raw": data,
                    }
        except Exception:
            pass

        return {"domain": domain, "error": "WHOIS lookup failed"}

    def _extract_rdap_field(self, data: Dict, field: str) -> str:
        events = data.get("events", [])
        for event in events:
            if event.get("eventAction") == field:
                return event.get("eventDate", "Unknown")
        return "Unknown"

    def _extract_rdap_nameservers(self, data: Dict) -> List[str]:
        ns = []
        for item in data.get("nameservers", []):
            name = item.get("ldhName", "")
            if name:
                ns.append(name.lower())
        return ns

    def _extract_rdap_status(self, data: Dict) -> List[str]:
        return data.get("status", [])

    async def geoip_lookup(self, ip: str) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"http://ip-api.com/json/{ip}")
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "ip": ip,
                        "country": data.get("country"),
                        "country_code": data.get("countryCode"),
                        "region": data.get("regionName"),
                        "city": data.get("city"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "isp": data.get("isp"),
                        "org": data.get("org"),
                        "as": data.get("as"),
                        "query": data.get("query"),
                    }
        except Exception:
            pass

        return {"ip": ip, "error": "GeoIP lookup failed"}

    async def dns_lookup(self, domain: str) -> Dict:
        results = {"domain": domain, "records": {}}

        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
            try:
                loop = asyncio.get_event_loop()
                if rtype == "A":
                    addrs = await loop.run_in_executor(None, socket.getaddrinfo, domain, None)
                    results["records"]["A"] = list(set(addr[4][0] for addr in addrs))
                elif rtype == "AAAA":
                    addrs = await loop.run_in_executor(
                        None, socket.getaddrinfo, domain, None, socket.AF_INET6
                    )
                    results["records"]["AAAA"] = list(set(addr[4][0] for addr in addrs))
            except Exception:
                results["records"][rtype] = []

        return results

    async def ssl_check(self, domain: str) -> Dict:
        try:
            loop = asyncio.get_event_loop()

            def _get_cert():
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with socket.create_connection((domain, 443), timeout=5) as sock:
                    with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert(binary_form=True)
                        return cert

            cert_der = await loop.run_in_executor(None, _get_cert)

            cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
            return {
                "domain": domain,
                "valid": True,
                "cert_pem": cert_pem[:200] + "...",
            }
        except Exception as e:
            return {"domain": domain, "valid": False, "error": str(e)}

    async def web_scraper(self, url: str) -> Dict:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": Config.USER_AGENT},
            ) as client:
                resp = await client.get(url)
                soup = BeautifulSoup(resp.text, "html.parser")

                title = soup.title.string.strip() if soup.title and soup.title.string else ""
                meta_desc = ""
                meta_tag = soup.find("meta", attrs={"name": "description"})
                if meta_tag:
                    meta_desc = meta_tag.get("content", "")

                headings = []
                for tag in ["h1", "h2", "h3"]:
                    for h in soup.find_all(tag):
                        text = h.get_text(strip=True)
                        if text:
                            headings.append({"tag": tag.upper(), "text": text[:200]})

                links = []
                for a in soup.find_all("a", href=True)[:50]:
                    text = a.get_text(strip=True)[:100]
                    href = a["href"]
                    if text and href:
                        links.append({"text": text, "href": href})

                emails = set()
                import re
                for match in re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resp.text):
                    emails.add(match)

                tech = self._detect_technologies(resp.text, dict(resp.headers))

                return {
                    "url": url,
                    "status": resp.status_code,
                    "title": title,
                    "description": meta_desc,
                    "headings": headings,
                    "links": links,
                    "emails": list(emails)[:20],
                    "technologies": tech,
                    "content_length": len(resp.text),
                }
        except Exception as e:
            return {"url": url, "error": str(e)}

    def _detect_technologies(self, html: str, headers: Dict) -> List[Dict]:
        found = []
        import re

        for sig in self.tech_signatures:
            if re.search(sig["pattern"], html, re.IGNORECASE):
                found.append({"name": sig["name"], "category": sig["category"]})

        server = headers.get("server", "")
        if server:
            found.append({"name": server.split("/")[0], "category": "Server"})

        powered_by = headers.get("x-powered-by", "")
        if powered_by:
            found.append({"name": powered_by, "category": "Runtime"})

        seen = set()
        unique = []
        for t in found:
            if t["name"] not in seen:
                seen.add(t["name"])
                unique.append(t)

        return unique

    async def full_recon(self, target: str) -> Dict:
        start = time.monotonic()
        hostname = target
        if "://" in target:
            hostname = urlparse(target).hostname

        results = {"target": target, "scans": {}}

        scans = [
            ("port_scan", self.port_scan(hostname)),
            ("dns", self.dns_lookup(hostname)),
            ("ssl", self.ssl_check(hostname)),
        ]

        ip = None
        try:
            ip = socket.gethostbyname(hostname)
            scans.append(("geoip", self.geoip_lookup(ip)))
        except Exception:
            pass

        if "://" in target:
            scans.append(("web", self.web_scraper(target)))

        for name, coro in scans:
            try:
                results["scans"][name] = await coro
            except Exception as e:
                results["scans"][name] = {"error": str(e)}

        results["duration_ms"] = int((time.monotonic() - start) * 1000)
        return results
