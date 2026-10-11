from unittest.mock import AsyncMock, patch

import httpx
import pytest

from backend.app.exceptions import (
    InvalidPUBGDataError,
    PlayerNotFoundError,
    PUBGAPIError,
    RateLimitedError,
)
from backend.app.pubg_client import PUBGClient


def response(status, json_data):
    return httpx.Response(status, json=json_data, request=httpx.Request("GET", "https://api.pubg.com"))


@pytest.mark.asyncio
async def test_find_player_parses_player_and_match_ids():
    payload = {
        "data": [{
            "type": "player",
            "id": "account.1",
            "attributes": {"name": "Test"},
            "relationships": {"matches": {"data": [{"type": "match", "id": "m1"}, {"type": "match", "id": "m2"}]}}
        }]
    }
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=response(200, payload))
    with patch("httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value = mock
        client = PUBGClient("key", "steam", "https://api.pubg.com")
        player = await client.find_player("Test")
    assert player.player_id == "account.1"
    assert player.match_ids == ["m1", "m2"]


@pytest.mark.asyncio
async def test_find_player_maps_404():
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=response(404, {"errors": []}))
    with patch("httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value = mock
        client = PUBGClient("key", "steam", "https://api.pubg.com")
        with pytest.raises(PlayerNotFoundError):
            await client.find_player("missing")


@pytest.mark.asyncio
async def test_find_player_maps_429():
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=response(429, {"errors": []}))
    with patch("httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value = mock
        client = PUBGClient("key", "steam", "https://api.pubg.com")
        with pytest.raises(RateLimitedError):
            await client.find_player("busy")


@pytest.mark.asyncio
async def test_get_current_season_player_parses_stats_and_mode_matches():
    client = PUBGClient("key", "steam", "https://season.api")
    client._current_seasons.pop((client.base_url, client.platform), None)

    client._get = AsyncMock(side_effect=[
        {"data": [
            {"id": "old-season", "attributes": {"isCurrentSeason": False}},
            {"id": "current-season", "attributes": {"isCurrentSeason": True}},
        ]},
        {
            "data": {
                "attributes": {
                    "gameModeStats": {
                        "duo-fpp": {
                            "roundsPlayed": 12,
                            "wins": 2,
                            "top10s": 7,
                            "kills": 18,
                            "damageDealt": 3200.5,
                            "timeSurvived": 9000,
                            "assists": 8,
                        }
                    }
                },
                "relationships": {
                    "matchesDuoFPP": {
                        "data": [{"id": "duo-1"}, {"id": "duo-2"}]
                    }
                },
            }
        },
    ])

    season = await client.get_current_season_player("account.1", "duo-fpp")

    assert season.season_id == "current-season"
    assert season.match_ids == ["duo-1", "duo-2"]
    assert season.stats is not None
    assert season.stats.matches == 12
    assert season.stats.wins == 2
    assert season.stats.damage == 3200.5
    assert [call.args[0] for call in client._get.await_args_list] == [
        "seasons",
        "players/account.1/seasons/current-season",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mode", "relationship"),
    [
        ("solo", "matchesSolo"),
        ("duo", "matchesDuo"),
        ("squad", "matchesSquad"),
    ],
)
async def test_get_current_season_player_supports_tpp_modes(mode, relationship):
    client = PUBGClient("key", "steam", "https://tpp-season.api")
    client._current_seasons[(client.base_url, client.platform)] = (
        float("inf"),
        "current-season",
    )
    client._get = AsyncMock(return_value={
        "data": {
            "attributes": {
                "gameModeStats": {
                    mode: {
                        "roundsPlayed": 3,
                        "wins": 0,
                        "top10s": 1,
                        "kills": 4,
                        "damageDealt": 500,
                        "timeSurvived": 1000,
                        "assists": 0,
                    }
                }
            },
            "relationships": {relationship: {"data": [{"id": f"{mode}-match"}]}},
        }
    })

    season = await client.get_current_season_player("account.1", mode)

    assert season.match_ids == [f"{mode}-match"]
    assert season.stats is not None
    assert season.stats.matches == 3


@pytest.mark.asyncio
async def test_get_current_season_player_rejects_malformed_season_stats():
    client = PUBGClient("key", "steam", "https://season-invalid.api")
    client._current_seasons[(client.base_url, client.platform)] = (
        float("inf"),
        "current-season",
    )

    client._get = AsyncMock(return_value={
        "data": {
            "attributes": {"gameModeStats": {"solo-fpp": {"roundsPlayed": "invalid"}}},
            "relationships": {},
        }
    })

    with pytest.raises(InvalidPUBGDataError, match="roundsPlayed"):
        await client.get_current_season_player("account.1", "solo-fpp")


@pytest.mark.asyncio
async def test_non_player_404_is_not_reported_as_player_not_found():
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=response(404, {"errors": []}))
    with patch("httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value = mock
        client = PUBGClient("key", "steam", "https://api.pubg.com")
        with pytest.raises(PUBGAPIError, match="resource was not found"):
            await client.get_match("missing-match", "account.1")


@pytest.mark.asyncio
async def test_get_match_parses_death_type():
    payload = {
        "data": {
            "attributes": {
                "mapName": "Baltic_Main",
                "gameMode": "solo-fpp",
                "createdAt": "2026-09-01T12:00:00Z",
            }
        },
        "included": [{
            "type": "participant",
            "attributes": {
                "stats": {
                    "playerId": "account.1",
                    "winPlace": 1,
                    "kills": 4,
                    "assists": 0,
                    "damageDealt": 500,
                    "timeSurvived": 1200,
                    "deathType": "alive",
                }
            },
        }],
    }
    client = PUBGClient("key", "steam", "https://api.pubg.com")
    client._get = AsyncMock(return_value=payload)

    match = await client.get_match("match-1", "account.1")

    assert match.death_type == "alive"
