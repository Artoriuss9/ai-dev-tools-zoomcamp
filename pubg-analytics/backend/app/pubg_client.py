import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from .exceptions import (
    InvalidPUBGDataError,
    PlayerNotFoundError,
    PUBGAPIError,
    PUBGAPIUnavailableError,
    RateLimitedError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class APIPlayer:
    player_id: str
    nickname: str
    match_ids: list[str]


@dataclass(frozen=True)
class APIMatchParticipant:
    match_id: str
    map_name: str
    game_mode: str
    played_at: datetime
    placement: int
    kills: int
    assists: int
    damage: float
    survival_time: float


class PUBGClient:
    def __init__(self, api_key: str, platform: str, base_url: str, timeout: float = 10.0):
        self.api_key = api_key
        self.platform = platform
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json",
        }

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/shards/{self.platform}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
                response = await client.get(url, params=params)
        except httpx.TimeoutException as exc:
            logger.exception("PUBG API timeout: %s", path)
            raise PUBGAPIUnavailableError("PUBG API request timed out") from exc
        except httpx.RequestError as exc:
            logger.exception("PUBG API request failed: %s", path)
            raise PUBGAPIUnavailableError("PUBG API is unavailable") from exc

        if response.status_code == 404:
            raise PlayerNotFoundError("Player not found")
        if response.status_code == 429:
            raise RateLimitedError("PUBG API rate limit reached")
        if 500 <= response.status_code <= 599:
            raise PUBGAPIUnavailableError("PUBG API is temporarily unavailable")
        if response.status_code >= 400:
            logger.error("PUBG API error %s for %s: %s", response.status_code, path, response.text[:500])
            raise PUBGAPIError(f"PUBG API returned HTTP {response.status_code}")

        try:
            return response.json()
        except ValueError as exc:
            raise PUBGAPIError("PUBG API returned invalid JSON") from exc

    async def find_player(self, nickname: str) -> APIPlayer:
        payload = await self._get("players", {"filter[playerNames]": nickname})
        data = payload.get("data") or []
        if not data:
            raise PlayerNotFoundError("Player not found")
        item = data[0]
        player_id = item.get("id")
        attrs = item.get("attributes") or {}
        returned_nickname = attrs.get("name") or nickname
        match_ids = [m.get("id") for m in ((item.get("relationships") or {}).get("matches") or {}).get("data", []) if m.get("id")]
        if not player_id:
            raise InvalidPUBGDataError("PUBG player response is missing player id")
        return APIPlayer(player_id=player_id, nickname=returned_nickname, match_ids=match_ids)

    async def get_match(self, match_id: str, player_id: str) -> APIMatchParticipant:
        payload = await self._get(f"matches/{quote(match_id, safe='')}")
        data = payload.get("data") or {}
        attrs = data.get("attributes") or {}
        map_name = attrs.get("mapName")
        game_mode = attrs.get("gameMode")
        created_at = attrs.get("createdAt")
        played_at = self._parse_datetime(created_at)

        included = payload.get("included") or []
        participant = None
        for item in included:
            if item.get("type") != "participant":
                continue
            stats = (item.get("attributes") or {}).get("stats") or {}
            candidate_player_id = stats.get("playerId")
            rel_player = ((item.get("relationships") or {}).get("player") or {}).get("data") or {}
            if candidate_player_id == player_id or rel_player.get("id") == player_id:
                participant = stats
                break

        if not participant:
            raise InvalidPUBGDataError(f"No participant stats for player {player_id} in match {match_id}")

        required = {
            "winPlace": participant.get("winPlace"),
            "kills": participant.get("kills"),
            "assists": participant.get("assists"),
            "damageDealt": participant.get("damageDealt"),
            "timeSurvived": participant.get("timeSurvived"),
        }
        if map_name is None or game_mode is None or played_at is None or any(v is None for v in required.values()):
            raise InvalidPUBGDataError(f"Incomplete match data for {match_id}")

        return APIMatchParticipant(
            match_id=match_id,
            map_name=str(map_name),
            game_mode=str(game_mode),
            played_at=played_at,
            placement=int(participant["winPlace"]),
            kills=int(participant["kills"]),
            assists=int(participant["assists"]),
            damage=float(participant["damageDealt"]),
            survival_time=float(participant["timeSurvived"]),
        )

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            logger.warning("Invalid PUBG datetime: %s", value)
            return None
