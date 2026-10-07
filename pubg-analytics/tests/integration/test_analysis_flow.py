import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app, get_analysis_service, settings
from backend.app.models import PlayerMatch
from backend.app.service import AnalysisService
from tests.conftest import FakePUBGClient


@pytest.mark.integration
def test_analyze_request_persists_data_and_returns_frontend_contract(
    db, sample_player, sample_matches, monkeypatch
):
    fake_client = FakePUBGClient(sample_player, sample_matches)
    service = AnalysisService(client=fake_client, db=db, mode="solo-fpp")
    overrides_before = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_analysis_service] = lambda: service
    monkeypatch.setattr(settings, "pubg_api_key", "test-key")

    try:
        with TestClient(app) as client:
            response = client.post("/analyze", json={"nickname": "TestPlayer"})
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides_before)

    assert response.status_code == 200
    payload = response.json()
    assert payload["player"]["nickname"] == "TestPlayer"
    assert payload["analyzed_count"] == 2
    assert len(payload["matches"]) == 2
    assert payload["summary"]["matches"] == 2
    assert payload["insights"]["trend"]["recent_matches"] == 1
    assert db.query(PlayerMatch).count() == 2


def test_checked_in_openapi_contract_matches_fastapi():
    contract_path = Path(__file__).resolve().parents[2] / "openapi.yaml"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract == app.openapi()
