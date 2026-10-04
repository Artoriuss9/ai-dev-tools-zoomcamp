from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app('sqlite://'))


def test_scoreboard_returns_games_and_standings_for_supported_date():
    response = client.get('/api/scoreboard/today')

    assert response.status_code == 200
    payload = response.json()
    assert payload['dateKey'] == 'today'
    assert len(payload['games']) == 5
    assert payload['games'][0]['status'] == 'live'
    assert payload['standings'][0]['team']['short'] == 'TOR'
    assert payload['fetchedAt']


def test_scoreboard_returns_games_for_tomorrow_from_database():
    response = client.get('/api/scoreboard/tomorrow')

    assert response.status_code == 200
    assert response.json()['games'][0]['id'] == 'm1'


def test_database_seed_is_idempotent():
    app = create_app('sqlite://')
    first = TestClient(app).get('/api/scoreboard/today').json()
    second = TestClient(app).get('/api/scoreboard/today').json()

    assert len(first['games']) == len(second['games']) == 5
    assert len(first['standings']) == len(second['standings']) == 8


def test_scoreboard_rejects_invalid_date_key():
    response = client.get('/api/scoreboard/next-season')

    assert response.status_code == 422
