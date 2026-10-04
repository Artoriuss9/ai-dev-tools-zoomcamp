from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

GameStatus = Literal["scheduled", "live", "final", "postponed", "canceled"]


class Team(BaseModel):
    name: str
    short: str
    city: str
    color: str
    mark: str


class Game(BaseModel):
    id: str
    away: Team
    home: Team
    status: GameStatus
    awayScore: int | None = None
    homeScore: int | None = None
    detail: str
    venue: str
    startTime: str
    updatedAt: str


class Standing(BaseModel):
    team: Team
    gp: int = Field(ge=0)
    w: int = Field(ge=0)
    l: int = Field(ge=0)
    otl: int = Field(ge=0)
    points: int = Field(ge=0)
    differential: int


class ScoreboardResponse(BaseModel):
    dateKey: str
    games: list[Game]
    standings: list[Standing]
    fetchedAt: datetime
