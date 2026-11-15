from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # NBA player ID
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # NBA game ID
    season: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    game_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)


class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "game_id", name="uq_player_game_stats_player_game"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False, index=True)
    team_id: Mapped[int | None] = mapped_column(Integer)
    team_abbreviation: Mapped[str | None] = mapped_column(String(5))
    matchup: Mapped[str | None] = mapped_column(String(20))
    result: Mapped[str | None] = mapped_column(String(1))
    minutes: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    field_goals_made: Mapped[int | None] = mapped_column(Integer)
    field_goals_attempted: Mapped[int | None] = mapped_column(Integer)
    three_pointers_made: Mapped[int | None] = mapped_column(Integer)
    free_throws_made: Mapped[int | None] = mapped_column(Integer)
    free_throws_attempted: Mapped[int | None] = mapped_column(Integer)
    offensive_rebounds: Mapped[int | None] = mapped_column(Integer)
    defensive_rebounds: Mapped[int | None] = mapped_column(Integer)
    rebounds: Mapped[int | None] = mapped_column(Integer)
    assists: Mapped[int | None] = mapped_column(Integer)
    steals: Mapped[int | None] = mapped_column(Integer)
    blocks: Mapped[int | None] = mapped_column(Integer)
    turnovers: Mapped[int | None] = mapped_column(Integer)
    points: Mapped[int | None] = mapped_column(Integer)
    nba_fantasy_points: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_through_date: Mapped[date | None] = mapped_column(Date)
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(String(2000))
