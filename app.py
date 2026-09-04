"""MatrixCommand - Unified Security Dashboard"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import Config
from database import DatabaseManager, Scan, FreeGame, PrivacyEvent, SystemSnapshot
from services.network import NetworkRecon
from services.privacy import PrivacyMonitor
from services.system import SystemInfo
from scrapers.free_games import FreeGamesScraper

db = DatabaseManager(Config.DATABASE_URL)
network = NetworkRecon()
privacy = PrivacyMonitor()
system_info = SystemInfo()
games_scraper = FreeGamesScraper()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="MatrixCommand",
    description="Unified Security Dashboard",
    version="2.0",
    lifespan=lifespan,
)


@app.get("/api/network/port-scan")
async def port_scan(target: str, ports: Optional[str] = None):
    port_list = None
    if ports:
        port_list = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()]

    results = await network.port_scan(target, port_list)

    db_session = db.get_session()
    try:
        scan = Scan(
            scan_type="port_scan",
            target=target,
            results=str(results["stats"]),
            duration_ms=results.get("duration_ms"),
        )
        db_session.add(scan)
        db_session.commit()
    finally:
        db_session.close()

    return results


@app.get("/api/network/whois")
async def whois_lookup(target: str):
    return await network.whois_lookup(target)


@app.get("/api/network/geoip")
async def geoip_lookup(ip: str):
    return await network.geoip_lookup(ip)


@app.get("/api/network/dns")
async def dns_lookup(domain: str):
    return await network.dns_lookup(domain)


@app.get("/api/network/ssl")
async def ssl_check(domain: str):
    return await network.ssl_check(domain)


@app.get("/api/network/scraper")
async def web_scraper(url: str):
    return await network.web_scraper(url)


@app.get("/api/network/full-recon")
async def full_recon(target: str):
    return await network.full_recon(target)


@app.get("/api/privacy/scan")
async def privacy_scan(url: str):
    results = await privacy.scan_url(url)

    db_session = db.get_session()
    try:
        for tracker in results.get("trackers", []):
            event = PrivacyEvent(
                url=url,
                tracker=tracker.get("domain", ""),
                category=tracker.get("category", ""),
                blocked=False,
            )
            db_session.add(event)
        db_session.commit()
    finally:
        db_session.close()

    return results


@app.get("/api/system/snapshot")
async def system_snapshot():
    snapshot = system_info.get_snapshot()

    db_session = db.get_session()
    try:
        db_snapshot = SystemSnapshot(
            cpu_percent=snapshot["cpu"]["percent"],
            memory_percent=snapshot["memory"]["percent"],
            disk_percent=snapshot["disk"]["percent"],
            network_sent=snapshot["network"]["sent_mb"],
            network_recv=snapshot["network"]["recv_mb"],
            active_connections=len(snapshot["connections"]),
        )
        db_session.add(db_snapshot)
        db_session.commit()
    finally:
        db_session.close()

    return snapshot


@app.get("/api/system/interfaces")
async def network_interfaces():
    return system_info.get_network_interfaces()


@app.get("/api/games/free")
async def free_games(refresh: bool = False):
    if not refresh:
        db_session = db.get_session()
        try:
            from sqlalchemy import desc
            cached = db_session.query(FreeGame).filter(
                FreeGame.is_active == True
            ).order_by(desc(FreeGame.first_seen)).limit(50).all()

            if cached:
                return [ {
                    "id": g.id,
                    "title": g.title,
                    "url": g.url,
                    "source": g.source,
                    "platform": g.platform,
                    "ends_at": g.ends_at.isoformat() if g.ends_at else None,
                    "first_seen": g.first_seen.isoformat(),
                } for g in cached ]
        finally:
            db_session.close()

    games = await games_scraper.scrape_all()

    db_session = db.get_session()
    try:
        for game in games:
            existing = db_session.query(FreeGame).filter(
                FreeGame.title == game["title"],
                FreeGame.source == game["source"],
            ).first()

            if existing:
                existing.last_seen = datetime.now(timezone.utc)
                existing.is_active = True
            else:
                new_game = FreeGame(
                    title=game["title"],
                    url=game["url"],
                    source=game["source"],
                    platform=game.get("platform", ""),
                    ends_at=datetime.fromisoformat(game["ends_at"]) if game.get("ends_at") else None,
                )
                db_session.add(new_game)

        db_session.commit()
    finally:
        db_session.close()

    return games


@app.get("/api/history")
async def history(scan_type: Optional[str] = None, limit: int = 50):
    db_session = db.get_session()
    try:
        query = db_session.query(Scan)
        if scan_type:
            query = query.filter(Scan.scan_type == scan_type)
        scans = query.order_by(Scan.created_at.desc()).limit(limit).all()

        return [{
            "id": s.id,
            "scan_type": s.scan_type,
            "target": s.target,
            "results": s.results,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "duration_ms": s.duration_ms,
        } for s in scans]
    finally:
        db_session.close()


@app.get("/api/stats")
async def stats():
    db_session = db.get_session()
    try:
        return {
            "total_scans": db_session.query(Scan).count(),
            "active_games": db_session.query(FreeGame).filter(FreeGame.is_active == True).count(),
            "privacy_events": db_session.query(PrivacyEvent).count(),
            "system_snapshots": db_session.query(SystemSnapshot).count(),
        }
    finally:
        db_session.close()


@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Config.BASE_DIR / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>MatrixCommand</h1><p>Frontend not found</p>")


app.mount("/static", StaticFiles(directory=str(Config.BASE_DIR / "static")), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT, reload=Config.DEBUG)
