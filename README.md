# MatrixCommand

Unified security/privacy dashboard with network recon, privacy monitoring, and free games aggregation.

## Features

- **Network Recon:** Port scan, WHOIS, GeoIP, DNS, SSL, web scraper
- **Privacy Monitor:** Track security headers, detect trackers, privacy scoring
- **Free Games:** Aggregates free games from Steam, Epic, GOG, Reddit
- **System Info:** CPU, RAM, disk, network, processes
- **Dark Theme:** Matrix-inspired UI with 3D progress bars

## Installation

```bash
# na tej maszynie pip dziala tylko w venv (PEP 668):
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# lokalnie gotowe .venv (odtworzone 2026-08-11)
```

## Usage

```bash
source .venv/bin/activate
python app.py
# or
uvicorn app:app --host 127.0.0.1 --port 8080
```

Then open http://127.0.0.1:8080

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/network/port-scan?target=` | GET | Port scan |
| `/api/network/whois?target=` | GET | WHOIS lookup |
| `/api/network/geoip?ip=` | GET | GeoIP lookup |
| `/api/network/dns?domain=` | GET | DNS lookup |
| `/api/network/ssl?domain=` | GET | SSL check |
| `/api/network/scraper?url=` | GET | Web scraper |
| `/api/network/full-recon?target=` | GET | Full recon |
| `/api/privacy/scan?url=` | GET | Privacy scan |
| `/api/system/snapshot` | GET | System snapshot |
| `/api/system/interfaces` | GET | Network interfaces |
| `/api/games/free?refresh=` | GET | Free games |
| `/api/history` | GET | Scan history |
| `/api/stats` | GET | Statistics |

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- BeautifulSoup4 + httpx
- psutil
- Leaflet.js (maps)
- Vanilla JS/CSS
