"""Tests for Database"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Scan, FreeGame, PrivacyEvent, SystemSnapshot


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_scan(db_session):
    scan = Scan(scan_type="port_scan", target="127.0.0.1", results="test", duration_ms=100)
    db_session.add(scan)
    db_session.commit()

    result = db_session.query(Scan).first()
    assert result.scan_type == "port_scan"
    assert result.target == "127.0.0.1"


def test_create_free_game(db_session):
    game = FreeGame(title="Test Game", url="https://example.com", source="Steam", platform="PC")
    db_session.add(game)
    db_session.commit()

    result = db_session.query(FreeGame).first()
    assert result.title == "Test Game"
    assert result.is_active is True


def test_create_privacy_event(db_session):
    event = PrivacyEvent(url="https://example.com", tracker="google-analytics.com", category="analytics")
    db_session.add(event)
    db_session.commit()

    result = db_session.query(PrivacyEvent).first()
    assert result.tracker == "google-analytics.com"


def test_create_system_snapshot(db_session):
    snapshot = SystemSnapshot(cpu_percent=50.0, memory_percent=60.0, disk_percent=70.0)
    db_session.add(snapshot)
    db_session.commit()

    result = db_session.query(SystemSnapshot).first()
    assert result.cpu_percent == 50.0
