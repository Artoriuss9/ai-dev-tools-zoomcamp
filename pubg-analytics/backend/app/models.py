from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    player_matches: Mapped[list["PlayerMatch"]] = relationship(back_populates="player", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    map_name: Mapped[str] = mapped_column(String(128), nullable=False)
    game_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    player_matches: Mapped[list["PlayerMatch"]] = relationship(back_populates="match", cascade="all, delete-orphan")


class PlayerMatch(Base):
    __tablename__ = "player_matches"
    __table_args__ = (UniqueConstraint("player_id", "match_id", name="uq_player_match"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False, index=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False, index=True)
    placement: Mapped[int] = mapped_column(Integer, nullable=False)
    kills: Mapped[int] = mapped_column(Integer, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, nullable=False)
    damage: Mapped[float] = mapped_column(Float, nullable=False)
    survival_time: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    player: Mapped[Player] = relationship(back_populates="player_matches")
    match: Mapped[Match] = relationship(back_populates="player_matches")
