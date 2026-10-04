import os
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Integer, String, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class TeamRecord(Base):
    __tablename__ = 'teams'

    short: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(60))
    color: Mapped[str] = mapped_column(String(7))
    mark: Mapped[str] = mapped_column(String(1))
    standings: Mapped['StandingRecord | None'] = relationship(back_populates='team', uselist=False)


class GameRecord(Base):
    __tablename__ = 'games'

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    date_key: Mapped[str] = mapped_column(String(20), index=True)
    away_short: Mapped[str] = mapped_column(ForeignKey('teams.short'))
    home_short: Mapped[str] = mapped_column(ForeignKey('teams.short'))
    status: Mapped[str] = mapped_column(String(20))
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(String(100))
    venue: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[str] = mapped_column(String(30))
    updated_at: Mapped[str] = mapped_column(String(40))
    away: Mapped[TeamRecord] = relationship(foreign_keys=[away_short])
    home: Mapped[TeamRecord] = relationship(foreign_keys=[home_short])


class StandingRecord(Base):
    __tablename__ = 'standings'

    team_short: Mapped[str] = mapped_column(ForeignKey('teams.short'), primary_key=True)
    gp: Mapped[int] = mapped_column(Integer)
    wins: Mapped[int] = mapped_column(Integer)
    losses: Mapped[int] = mapped_column(Integer)
    otl: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    differential: Mapped[int] = mapped_column(Integer)
    team: Mapped[TeamRecord] = relationship(back_populates='standings')


def create_database(url: str | None = None) -> tuple[Engine, sessionmaker[Session]]:
    database_url = url or os.getenv('DATABASE_URL', 'sqlite:///./ice_now.db')
    connect_args = {'check_same_thread': False} if database_url.startswith('sqlite') else {}
    engine_args = {'connect_args': connect_args}
    if database_url == 'sqlite://':
        engine_args['poolclass'] = StaticPool
    engine = create_engine(database_url, **engine_args)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)


def seed_database(session_factory: sessionmaker[Session], games: dict, teams: dict, standings: list) -> None:
    with session_factory.begin() as session:
        if session.scalar(select(TeamRecord.short).limit(1)):
            return
        for record in teams.values():
            session.add(TeamRecord(short=record.short, name=record.name, city=record.city, color=record.color, mark=record.mark))
        for date_key, date_games in games.items():
            for game in date_games:
                session.add(GameRecord(id=game.id, date_key=date_key, away_short=game.away.short, home_short=game.home.short, status=game.status, away_score=game.awayScore, home_score=game.homeScore, detail=game.detail, venue=game.venue, start_time=game.startTime, updated_at=game.updatedAt))
        for standing in standings:
            session.add(StandingRecord(team_short=standing.team.short, gp=standing.gp, wins=standing.w, losses=standing.l, otl=standing.otl, points=standing.points, differential=standing.differential))


def utc_now() -> datetime:
    return datetime.now(UTC)