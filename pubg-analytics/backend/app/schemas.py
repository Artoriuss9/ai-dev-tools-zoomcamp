from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)

    @field_validator("nickname")
    @classmethod
    def nickname_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("nickname must not be blank")
        return value


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class PlayerResponse(BaseModel):
    nickname: str
    player_id: str


class SummaryResponse(BaseModel):
    matches: int
    wins: int
    win_rate: float
    avg_placement: float
    avg_kills: float
    kills_per_death: float
    kills_per_match: float
    avg_damage: float
    avg_assists: float
    avg_survival_time: float


class MatchResponse(BaseModel):
    match_id: str
    played_at: datetime
    map: str
    mode: str
    placement: int
    kills: int
    assists: int
    damage: float
    survival_time: float


class TrendResponse(BaseModel):
    recent_matches: int
    previous_matches: int
    placement_delta: float
    kills_delta: float
    damage_delta: float
    survival_delta: float
    early: "TrendStats"
    recent: "TrendStats"


class TrendStats(BaseModel):
    kills_per_match: float
    avg_damage: float


class MapStats(BaseModel):
    kills_per_match: float
    win_rate: float
    avg_damage: float


class MapPerformanceResponse(BaseModel):
    map_name: str
    matches: int
    avg_placement: float
    avg_kills: float
    avg_damage: float


class InsightsResponse(BaseModel):
    headline: str
    profile: str
    strengths: list[str]
    weaknesses: list[str]
    next_match_goals: list[str]
    early_death_rate: float
    top_10_rate: float
    kill_rate: float
    trend: TrendResponse
    map_performance: list[MapPerformanceResponse]
    by_map: dict[str, MapStats]
    advice: str


class AnalyzeResponse(BaseModel):
    player: PlayerResponse
    summary: SummaryResponse
    matches: list[MatchResponse]
    insights: InsightsResponse
    analyzed_count: int
    requested_count: int = 10
    updated_at: datetime
    data_source: str = "PUBG API"


class HealthResponse(BaseModel):
    status: str
