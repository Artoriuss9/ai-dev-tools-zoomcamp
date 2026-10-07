from unittest.mock import AsyncMock, patch

import httpx
import pytest

from backend.app.exceptions import PlayerNotFoundError, RateLimitedError
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
