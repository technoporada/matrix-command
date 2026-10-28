# MatrixCommand

[![CI](https://github.com/technoporada/matrix-command/actions/workflows/ci.yml/badge.svg)](https://github.com/technoporada/matrix-command/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

**Security recon dashboard — network scanning, privacy monitoring, free games aggregation.**

Matrix-inspired dark UI with real-time scanning, Leaflet maps, and 3D progress bars.

> **Keywords:** `security-dashboard` `network-recon` `privacy-monitor` `port-scanner` `whois` `geoip` `free-games` `fastapi` `python` `osint`

---

## Features

| Module | What it does |
|--------|-------------|
| **Network Recon** | Port scan, WHOIS, GeoIP, DNS, SSL cert check, web scraper, tech detection |
| **Privacy Monitor** | Security headers, tracker detection, privacy scoring |
| **Free Games** | Aggregates free games from Steam, Epic, GOG, Reddit |
| **System Info** | CPU, RAM, disk, network interfaces, processes |
| **Scan History** | SQLite-backed history of all scans |
| **Dark Theme** | Matrix-inspired UI with animated effects |

## Quick Start

```bash
git clone https://github.com/technoporada/matrix-command.git
cd matrix-command

# Create venv (PEP 668)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run
python app.py
# → http://127.0.0.1:8080
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/network/port-scan?target=` | GET | Port scan (top 100 ports) |
| `/api/network/whois?target=` | GET | WHOIS lookup |
| `/api/network/geoip?ip=` | GET | GeoIP + map coordinates |
| `/api/network/dns?domain=` | GET | DNS records (A, AAAA, MX, NS, TXT) |
| `/api/network/ssl?domain=` | GET | SSL certificate info |
| `/api/network/scraper?url=` | GET | Web scraper + tech detection |
| `/api/network/full-recon?target=` | GET | All-in-one recon |
| `/api/privacy/scan?url=` | GET | Privacy analysis + scoring |
| `/api/system/snapshot` | GET | System metrics |
| `/api/system/interfaces` | GET | Network interfaces |
| `/api/games/free?refresh=` | GET | Free games aggregator |
| `/api/history` | GET | Scan history |
| `/api/stats` | GET | Dashboard statistics |

## Tech Stack

```
Backend:   FastAPI + Uvicorn + SQLAlchemy
Scraping:  httpx + BeautifulSoup4 + lxml
System:    psutil
Frontend:  Vanilla JS + CSS + Leaflet.js
Database:  SQLite
```

## Testing

```bash
pytest tests/ -v
```

## Project Structure

```
matrix-command/
├── app.py              # FastAPI application + routes
├── config.py           # Configuration
├── database.py         # SQLAlchemy models + manager
├── services/
│   ├── network.py      # Port scan, WHOIS, GeoIP, DNS, SSL, scraper
│   ├── privacy.py      # Security headers, tracker detection
│   └── system.py       # System metrics
├── scrapers/
│   └── free_games.py   # Steam, Epic, GOG, Reddit
├── static/
│   ├── index.html      # Dashboard UI
│   ├── app.js          # Frontend logic
│   └── style.css       # Matrix theme
├── tests/              # Unit tests
└── requirements.txt
```

## License

MIT

## Author

**technoporada** — [github.com/technoporada](https://github.com/technoporada)
