from backend.app.exceptions import PlayerNotFoundError
from backend.app.database import get_db
from backend.app.main import app, settings
from backend.app.main import get_analysis_service
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError


class StubService:
    async def analyze(self, nickname: str):
        raise PlayerNotFoundError("Player not found")


def test_health():
    settings.pubg_api_key = "test-key"
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_reports_deployed_commit(monkeypatch):
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abc123")
    with TestClient(app) as client:
        response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"commit_sha": "abc123"}


def test_ready():
    settings.pubg_api_key = "test-key"
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_database_failure():
    class BrokenSession:
        def execute(self, statement):
            raise OperationalError("SELECT 1", {}, Exception("database unavailable"))

    settings.pubg_api_key = "test-key"
    app.dependency_overrides[get_db] = lambda: BrokenSession()
    try:
        with TestClient(app) as client:
            response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_analyze_invalid_nickname():
    settings.pubg_api_key = "test-key"
    with TestClient(app) as client:
        response = client.post("/analyze", json={"nickname": ""})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_player_not_found():
    settings.pubg_api_key = "test-key"
    app.dependency_overrides[get_analysis_service] = lambda: StubService()
    try:
        with TestClient(app) as client:
            response = client.post("/analyze", json={"nickname": "missing"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "PLAYER_NOT_FOUND", "message": "Player not found"}}
