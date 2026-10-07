from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Match, Player, PlayerMatch
from .pubg_client import APIPlayer, APIMatchParticipant


class PlayerRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_player(self, api_player: APIPlayer) -> Player:
        player = self.db.get(Player, api_player.player_id)
        now = datetime.now(timezone.utc)
        if player is None:
            player = Player(player_id=api_player.player_id, nickname=api_player.nickname, created_at=now, updated_at=now)
            self.db.add(player)
        else:
            player.nickname = api_player.nickname
            player.updated_at = now
        self.db.flush()
        return player

    def upsert_match(self, match_data: APIMatchParticipant) -> Match:
        match = self.db.get(Match, match_data.match_id)
        now = datetime.now(timezone.utc)
        if match is None:
            match = Match(
                match_id=match_data.match_id,
                map_name=match_data.map_name,
                game_mode=match_data.game_mode,
                played_at=match_data.played_at,
                created_at=now,
                updated_at=now,
            )
            self.db.add(match)
        else:
            match.map_name = match_data.map_name
            match.game_mode = match_data.game_mode
            match.played_at = match_data.played_at
            match.updated_at = now
        self.db.flush()
        return match

    def upsert_player_match(self, player_id: str, match_id: str, match_data: APIMatchParticipant) -> PlayerMatch:
        stmt = select(PlayerMatch).where(PlayerMatch.player_id == player_id, PlayerMatch.match_id == match_id)
        player_match = self.db.scalar(stmt)
        now = datetime.now(timezone.utc)
        if player_match is None:
            player_match = PlayerMatch(
                player_id=player_id,
                match_id=match_id,
                placement=match_data.placement,
                kills=match_data.kills,
                assists=match_data.assists,
                damage=match_data.damage,
                survival_time=match_data.survival_time,
                created_at=now,
                updated_at=now,
            )
            self.db.add(player_match)
        else:
            player_match.placement = match_data.placement
            player_match.kills = match_data.kills
            player_match.assists = match_data.assists
            player_match.damage = match_data.damage
            player_match.survival_time = match_data.survival_time
            player_match.updated_at = now
        self.db.flush()
        return player_match
