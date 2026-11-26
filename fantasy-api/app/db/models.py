from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
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
    opponent_team_abbreviation: Mapped[str | None] = mapped_column(
        String(5), index=True
    )
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
    season: Mapped[str | None] = mapped_column(String(7))
    date_from: Mapped[date | None] = mapped_column(Date)
    date_to: Mapped[date | None] = mapped_column(Date)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_through_date: Mapped[date | None] = mapped_column(Date)
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(String(2000))
    yahoo_status: Mapped[str | None] = mapped_column(String(24))
    yahoo_error_message: Mapped[str | None] = mapped_column(String(2000))


class FantasyLeague(Base):
    __tablename__ = "fantasy_leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)


class FantasyManager(Base):
    """A manager's team in one fantasy league (not an app login account)."""

    __tablename__ = "fantasy_managers"
    __table_args__ = (
        UniqueConstraint("league_id", "team_name", name="uq_fantasy_manager_league_team"),
        Index(
            "uq_fantasy_managers_primary",
            "is_primary",
            unique=True,
            postgresql_where=text("is_primary IS TRUE"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_leagues.id"), nullable=False, index=True
    )
    manager_name: Mapped[str] = mapped_column(String(120), nullable=False)
    team_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    streaming_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class FantasyRosterEntry(Base):
    __tablename__ = "fantasy_roster_entries"
    __table_args__ = (
        Index("ix_fantasy_roster_entries_manager_order", "manager_id", "sort_order"),
        Index("ix_fantasy_roster_entries_player_id", "player_id"),
    )

    manager_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_managers.id"), primary_key=True
    )
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    roster_group: Mapped[str] = mapped_column(String(30), nullable=False, default="core")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)




class YahooTeamRosterSnapshot(Base):
    __tablename__ = "yahoo_team_roster_snapshots"
    __table_args__ = (
        Index("ix_yahoo_roster_league_capture", "league_key", "captured_at"),
        Index("ix_yahoo_roster_captured_at", "captured_at"),
    )

    snapshot_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    team_key: Mapped[str] = mapped_column(Text, primary_key=True)
    league_key: Mapped[str] = mapped_column(Text, nullable=False)
    league_name: Mapped[str] = mapped_column(Text, nullable=False)
    team_name: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lineup_date: Mapped[date | None] = mapped_column(Date)
    details_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    players: Mapped[list[dict[str, str | None]]] = mapped_column(JSONB, nullable=False)
