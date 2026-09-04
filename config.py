"""MatrixCommand - Konfiguracja"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

class Config:
    BASE_DIR = BASE_DIR
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/matrixcommand.db")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8080"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    USER_AGENT = "MatrixCommand/2.0"
    REQUEST_TIMEOUT = 10
    MAX_REDIRECTS = 5

    SCRAPING_INTERVAL = 300
    MAX_HISTORY = 1000

    FREE_GAMES_SOURCES = {
        "steam": "https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&maxprice=free&ndl=1",
        "epic": "https://store.epicgames.com/en-US/free-games",
        "gog": "https://www.gog.com/games/ajax/filtered?mediaType=game&price=free",
        "reddit": "https://www.reddit.com/r/GameDeals/search.json?q=free&restrict_sr=on&sort=new&t=week&limit=25",
    }

    PRIVACY_TRACKERS = [
        "google-analytics.com", "googletagmanager.com", "googlesyndication.com",
        "doubleclick.net", "facebook.com/tr", "facebook.net",
        "amazon-adsystem.com", "analytics.twitter.com", "ads.twitter.com",
        "hotjar.com", "sentry.io", "mixpanel.com", "segment.com",
        "amplitude.com", "heap.io", "fullstory.com", "mouseflow.com",
        "crazyegg.com", "optimizely.com", "vwo.com",
    ]

    SECURITY_HEADERS = [
        "strict-transport-security", "content-security-policy",
        "x-content-type-options", "x-frame-options", "x-xss-protection",
        "referrer-policy", "permissions-policy",
    ]

    PORT_SCAN_DEFAULT = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995,
                         1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 8888, 9200, 27017]
