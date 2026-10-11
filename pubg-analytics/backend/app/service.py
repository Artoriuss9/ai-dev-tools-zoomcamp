import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .analytics import calculate_insights, calculate_summary
from .exceptions import InvalidPUBGDataError
from .models import Match, PlayerMatch
from .pubg_client import PUBGClient
from .repository import PlayerRepository
from .schemas import (
    AnalyzeResponse,
    InsightsResponse,
    MapPerformanceResponse,
    MapStats,
    MatchResponse,
    PlayerResponse,
    SeasonComparisonResponse,
    SeasonSummaryResponse,
    SummaryResponse,
    TrendResponse,
)
from .constants import display_map_name, display_mode_name

logger = logging.getLogger(__name__)


class AnalysisService:
    MAX_MATCHES = 10

    def __init__(self, client: PUBGClient, db: Session, mode: str):
        self.client = client
        self.db = db
        self.mode = mode

    async def analyze(self, nickname: str, mode: str | None = None) -> AnalyzeResponse:
        selected_mode = mode or self.mode
        api_player = await self.client.find_player(nickname)
        api_season = await self.client.get_current_season_player(api_player.player_id, selected_mode)

        unique_match_ids = list(dict.fromkeys(api_season.match_ids))
        selected_ids: list[str] = []
        match_data = []
        for match_id in unique_match_ids:
            try:
                data = await self.client.get_match(match_id, api_player.player_id)
            except InvalidPUBGDataError:
                logger.exception("Invalid match payload for %s", match_id)
                raise
            if data.game_mode == selected_mode:
                selected_ids.append(match_id)
                match_data.append(data)
                if len(match_data) == self.MAX_MATCHES:
                    break

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
        summary = calculate_summary(rows) if rows else None
        insights = calculate_insights(rows) if rows else None
        season_stats = api_season.stats
        season_summary = None
        if season_stats is not None:
            season_summary = SeasonSummaryResponse(
                season_id=api_season.season_id,
                mode=selected_mode,
                matches=season_stats.matches,
                wins=season_stats.wins,
                win_rate=round(season_stats.wins / season_stats.matches * 100, 2)
                if season_stats.matches
                else 0,
                top_10_rate=round(season_stats.top_10s / season_stats.matches * 100, 2)
                if season_stats.matches
                else 0,
                total_kills=season_stats.kills,
                kills_per_match=round(season_stats.kills / season_stats.matches, 2)
                if season_stats.matches
                else 0,
                damage_per_match=round(season_stats.damage / season_stats.matches, 2)
                if season_stats.matches
                else 0,
                avg_survival_time=round(season_stats.survival_time / season_stats.matches / 60, 2)
                if season_stats.matches
                else 0,
                total_assists=season_stats.assists,
            )
        season_comparison = None
        if summary is not None and season_summary is not None:
            season_comparison = SeasonComparisonResponse(
                recent_matches=summary.matches,
                season_kills_per_match=season_summary.kills_per_match,
                recent_kills_per_match=summary.kills_per_match,
                kills_delta_percent=round(
                    (summary.kills_per_match / season_summary.kills_per_match - 1) * 100,
                    2,
                )
                if season_summary.kills_per_match
                else None,
                season_damage_per_match=season_summary.damage_per_match,
                recent_damage_per_match=summary.avg_damage,
                damage_delta_percent=round(
                    (summary.avg_damage / season_summary.damage_per_match - 1) * 100,
                    2,
                )
                if season_summary.damage_per_match
                else None,
            )
        fetched_at = datetime.now(timezone.utc)

        return AnalyzeResponse(
            player=PlayerResponse(nickname=player.nickname, player_id=player.player_id),
            summary=SummaryResponse(**summary.__dict__) if summary else None,
            insights=InsightsResponse(
                headline=insights.headline,
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
                season_comparison=season_comparison,
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
            ) if insights else None,
            season_summary=season_summary,
            mode=selected_mode,
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
