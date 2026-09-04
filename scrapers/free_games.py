"""MatrixCommand - Free Games Scraper"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from config import Config


class FreeGamesScraper:
    def __init__(self):
        self.timeout = Config.REQUEST_TIMEOUT
        self.headers = {
            "User-Agent": Config.USER_AGENT,
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def scrape_all(self) -> List[Dict]:
        results = []
        scrapers = [
            ("Steam", self._scrape_steam),
            ("Epic", self._scrape_epic),
            ("GOG", self._scrape_gog),
            ("Reddit", self._scrape_reddit),
        ]

        for name, scraper in scrapers:
            try:
                games = await scraper()
                results.extend(games)
            except Exception as e:
                pass

        return results

    async def _scrape_steam(self) -> List[Dict]:
        games = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                resp = await client.get(Config.FREE_GAMES_SOURCES["steam"])
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")

                    for item in soup.select("a.search_result_row")[:20]:
                        title_el = item.select_one(".title")
                        price_el = item.select_one(".discount_final_price")

                        if title_el and price_el:
                            price_text = price_el.get_text(strip=True)
                            if "Free" in price_text or "0,00" in price_text or "$0" in price_text:
                                games.append({
                                    "title": title_el.get_text(strip=True),
                                    "url": item.get("href", ""),
                                    "source": "Steam",
                                    "platform": "PC",
                                    "price": "Free",
                                    "ends_at": None,
                                })
        except Exception:
            pass

        return games

    async def _scrape_epic(self) -> List[Dict]:
        games = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                resp = await client.get(Config.FREE_GAMES_SOURCES["epic"])
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")

                    for item in soup.select("[data-component='DiscoverOffer']"):
                        title = item.select_one("span")
                        if title:
                            games.append({
                                "title": title.get_text(strip=True),
                                "url": Config.FREE_GAMES_SOURCES["epic"],
                                "source": "Epic",
                                "platform": "PC",
                                "price": "Free",
                                "ends_at": None,
                            })
        except Exception:
            pass

        return games

    async def _scrape_gog(self) -> List[Dict]:
        games = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                resp = await client.get(Config.FREE_GAMES_SOURCES["gog"])
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get("products", [])

                    for product in products[:20]:
                        title = product.get("title", "")
                        price = product.get("price", {})

                        if price.get("isFree", False) or price.get("finalAmount", 1) == 0:
                            slug = product.get("slug", "")
                            games.append({
                                "title": title,
                                "url": f"https://www.gog.com/game/{slug}" if slug else "",
                                "source": "GOG",
                                "platform": "PC",
                                "price": "Free",
                                "ends_at": None,
                            })
        except Exception:
            pass

        return games

    async def _scrape_reddit(self) -> List[Dict]:
        games = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                resp = await client.get(Config.FREE_GAMES_SOURCES["reddit"])
                if resp.status_code == 200:
                    data = resp.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts[:25]:
                        post_data = post.get("data", {})
                        title = post_data.get("title", "")
                        url = post_data.get("url", "")
                        permalink = post_data.get("permalink", "")

                        if any(kw in title.lower() for kw in ["free", "100%", "gratis"]):
                            games.append({
                                "title": title,
                                "url": f"https://reddit.com{permalink}" if permalink else url,
                                "source": "Reddit",
                                "platform": "Multi",
                                "price": "Free",
                                "ends_at": None,
                            })
        except Exception:
            pass

        return games
