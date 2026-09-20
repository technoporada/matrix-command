import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from config import Config


def test_config_has_timeout():
    assert hasattr(Config, 'REQUEST_TIMEOUT')
    assert Config.REQUEST_TIMEOUT > 0


def test_config_has_database():
    assert hasattr(Config, 'DATABASE_URL')
    assert 'sqlite' in Config.DATABASE_URL


def test_config_has_game_sources():
    assert hasattr(Config, 'FREE_GAMES_SOURCES')
    assert isinstance(Config.FREE_GAMES_SOURCES, dict)
    assert len(Config.FREE_GAMES_SOURCES) >= 3


def test_user_agent():
    assert hasattr(Config, 'USER_AGENT')
    assert len(Config.USER_AGENT) > 0
