from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Game, Player, PlayerGameStats
from app.schemas.player_stats import (
    PlayerGameLog,
    PlayerGameLogResponse,
    PlayerWeeklyStats,
)
from app.services.weekly_stats import get_weekly_player_averages


def get_player_game_log(
    player_id: int,
    season: str,
    limit: int,
    db: Session,
) -> PlayerGameLogResponse:
    rows = db.execute(
        select(PlayerGameStats, Game, Player)
        .join(Game, Game.id == PlayerGameStats.game_id)
        .join(Player, Player.id == PlayerGameStats.player_id)
        .where(PlayerGameStats.player_id == player_id, Game.season == season)
        .order_by(Game.game_date.desc(), Game.id.desc())
        .limit(limit)
    ).all()

    player_name = (
        rows[0][2].full_name
        if rows
        else db.scalar(select(Player.full_name).where(Player.id == player_id))
    )
    games = [
        PlayerGameLog(
            game_id=game.id,
            game_date=game.game_date.isoformat(),
            matchup=stats.matchup or "",
            opponent_team_abbreviation=stats.opponent_team_abbreviation,
            result=stats.result,
            minutes=float(stats.minutes) if stats.minutes is not None else None,
            field_goals_made=stats.field_goals_made,
            field_goals_attempted=stats.field_goals_attempted,
            free_throws_made=stats.free_throws_made,
            free_throws_attempted=stats.free_throws_attempted,
            points=stats.points,
            rebounds=stats.rebounds,
            assists=stats.assists,
            steals=stats.steals,
            blocks=stats.blocks,
            turnovers=stats.turnovers,
            three_pointers_made=stats.three_pointers_made,
            fantasy_points=(
                float(stats.nba_fantasy_points)
                if stats.nba_fantasy_points is not None
                else None
            ),
        )
        for stats, game, _player in rows
    ]
    weekly = get_weekly_player_averages(db, season, [player_id])[player_id]

    return PlayerGameLogResponse(
        player_id=player_id,
        player_name=player_name,
        season=season,
        games=games,
        current_week=PlayerWeeklyStats(**weekly["current_week"]),
        previous_week=PlayerWeeklyStats(**weekly["previous_week"]),
    )
