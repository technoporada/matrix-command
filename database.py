"""MatrixCommand - Baza danych"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True)
    scan_type = Column(String(50), nullable=False, index=True)
    target = Column(String(500), nullable=False)
    results = Column(Text)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    duration_ms = Column(Integer)


class FreeGame(Base):
    __tablename__ = "free_games"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    source = Column(String(50), nullable=False, index=True)
    platform = Column(String(100))
    ends_at = Column(DateTime)
    image_url = Column(String(1000))
    is_active = Column(Boolean, default=True, index=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class PrivacyEvent(Base):
    __tablename__ = "privacy_events"

    id = Column(Integer, primary_key=True)
    url = Column(String(1000), nullable=False)
    tracker = Column(String(200), nullable=False)
    category = Column(String(50))
    blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemSnapshot(Base):
    __tablename__ = "system_snapshots"

    id = Column(Integer, primary_key=True)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)
    network_sent = Column(Integer)
    network_recv = Column(Integer)
    active_connections = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_session(self):
        return self.SessionLocal()
