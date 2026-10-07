from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.pubg_client import APIPlayer, APIMatchParticipant
from backend.app.service import AnalysisService


@pytest.fixture(autouse=True)
def prevent_default_database_initialization(monkeypatch):
    monkeypatch.setattr("backend.app.main.init_db", lambda: None)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as session:
        yield session
    engine.dispose()


class FakePUBGClient:
    def __init__(self, player: APIPlayer, matches: list[APIMatchParticipant]):
        self.player = player
        self.matches = {item.match_id: item for item in matches}

    async def find_player(self, nickname: str) -> APIPlayer:
        return self.player

    async def get_match(self, match_id: str, player_id: str) -> APIMatchParticipant:
        return self.matches[match_id]


@pytest.fixture
def sample_player() -> APIPlayer:
    return APIPlayer(player_id="account.test", nickname="TestPlayer", match_ids=["m3", "m2", "m1"])


@pytest.fixture
def sample_matches() -> list[APIMatchParticipant]:
    from datetime import datetime, timezone

    return [
        APIMatchParticipant("m1", "Baltic_Main", "solo-fpp", datetime(2026, 9, 1, tzinfo=timezone.utc), 1, 5, 1, 500, 1500),
        APIMatchParticipant("m2", "Desert_Main", "solo-fpp", datetime(2026, 9, 2, tzinfo=timezone.utc), 8, 2, 0, 250, 900),
        APIMatchParticipant("m3", "Baltic_Main", "squad-fpp", datetime(2026, 9, 3, tzinfo=timezone.utc), 2, 7, 2, 900, 2000),
    ]
