import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .analytics import calculate_insights, calculate_summary
from .exceptions import InvalidPUBGDataError
from .models import Match, PlayerMatch
from .pubg_client import PUBGClient
from .repository import PlayerRepository
from .schemas import AnalyzeResponse, InsightsResponse, MapPerformanceResponse, MapStats, MatchResponse, PlayerResponse, SummaryResponse, TrendResponse
from .constants import display_map_name, display_mode_name

logger = logging.getLogger(__name__)


class AnalysisService:
    MAX_MATCHES = 10

    def __init__(self, client: PUBGClient, db: Session, mode: str):
        self.client = client
        self.db = db
        self.mode = mode

    async def analyze(self, nickname: str) -> AnalyzeResponse:
        api_player = await self.client.find_player(nickname)

        unique_match_ids = list(dict.fromkeys(api_player.match_ids))
        selected_ids: list[str] = []
        match_data = []
        for match_id in unique_match_ids:
            # The player endpoint returns recent match references; mode is known on each match.
            try:
                data = await self.client.get_match(match_id, api_player.player_id)
            except InvalidPUBGDataError:
                logger.exception("Invalid match payload for %s", match_id)
                raise
            if data.game_mode == self.mode:
                selected_ids.append(match_id)
                match_data.append(data)
                if len(match_data) == self.MAX_MATCHES:
                    break

        if not match_data:
            raise InvalidPUBGDataError(f"No matches found for configured mode {self.mode}")

        # All external calls succeeded; save everything atomically.
        repo = PlayerRepository(self.db)
        player = repo.upsert_player(api_player)
        for data in match_data:
            repo.upsert_match(data)
            repo.upsert_player_match(player.player_id, data.match_id, data)
        self.db.commit()

        stmt = (
            select(PlayerMatch)
            .where(PlayerMatch.player_id == player.player_id, PlayerMatch.match_id.in_(selected_ids))
            .join(PlayerMatch.match)
        )
        rows = list(self.db.scalars(stmt).all())
        rows.sort(key=lambda row: row.match.played_at, reverse=True)
        summary = calculate_summary(rows)
        insights = calculate_insights(rows)
        fetched_at = datetime.now(timezone.utc)

        return AnalyzeResponse(
            player=PlayerResponse(nickname=player.nickname, player_id=player.player_id),
            summary=SummaryResponse(**summary.__dict__),
            insights=InsightsResponse(
                headline=insights.headline,
                profile=insights.profile,
                strengths=insights.strengths,
                weaknesses=insights.weaknesses,
                next_match_goals=insights.next_match_goals,
                early_death_rate=insights.early_death_rate,
                top_10_rate=insights.top_10_rate,
                kill_rate=insights.kill_rate,
                trend=TrendResponse(
                    recent_matches=insights.trend.recent_matches,
                    previous_matches=insights.trend.previous_matches,
                    placement_delta=insights.trend.placement_delta,
                    kills_delta=insights.trend.kills_delta,
                    damage_delta=insights.trend.damage_delta,
                    survival_delta=insights.trend.survival_delta,
                    early=insights.trend.early.__dict__,
                    recent=insights.trend.recent.__dict__,
                ),
                map_performance=[
                    MapPerformanceResponse(
                        map_name=display_map_name(item.map_name),
                        matches=item.matches,
                        avg_placement=item.avg_placement,
                        avg_kills=item.avg_kills,
                        avg_damage=item.avg_damage,
                    )
                    for item in insights.map_performance
                ],
                by_map={
                    display_map_name(map_name): MapStats(**stats.__dict__)
                    for map_name, stats in insights.by_map.items()
                },
                advice=insights.advice,
            ),
            matches=[
                MatchResponse(
                    match_id=row.match.match_id,
                    played_at=row.match.played_at,
                    map=display_map_name(row.match.map_name),
                    mode=display_mode_name(row.match.game_mode),
                    placement=row.placement,
                    kills=row.kills,
                    assists=row.assists,
                    damage=round(row.damage, 2),
                    survival_time=round(row.survival_time / 60, 2),
                )
                for row in rows
            ],
            analyzed_count=len(rows),
            updated_at=fetched_at,
        )
