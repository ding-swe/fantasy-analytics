from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Game,
    Player,
    PlayerGameStats,
)
from app.schemas.free_agents import FreeAgentListResponse, FreeAgentPlayer
from app.services.yahoo_game_logs import rostered_nba_ids
from app.services.yahoo_rosters import get_latest_snapshot


GAMES_TO_AVERAGE = 7


def current_nba_season(today: date | None = None) -> str:
    today = today or date.today()
    start_year = today.year if today.month >= 10 else today.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def get_free_agents(limit: int, db: Session) -> FreeAgentListResponse | None:
    season = current_nba_season()
    snapshot = get_latest_snapshot(db)
    if snapshot is None:
        return None
    rostered_ids = rostered_nba_ids(db, snapshot)

    ranked_games = (
        select(
            PlayerGameStats.player_id.label("player_id"),
            PlayerGameStats.nba_fantasy_points.label("fantasy_points"),
            func.row_number()
            .over(
                partition_by=PlayerGameStats.player_id,
                order_by=(Game.game_date.desc(), Game.id.desc()),
            )
            .label("game_rank"),
        )
        .join(Game, Game.id == PlayerGameStats.game_id)
        .where(Game.season == season)
    ).subquery()

    recent_averages = (
        select(
            ranked_games.c.player_id,
            func.avg(ranked_games.c.fantasy_points).label("average_fantasy_points"),
            func.count(ranked_games.c.fantasy_points).label("games_played"),
        )
        .where(ranked_games.c.game_rank <= GAMES_TO_AVERAGE)
        .group_by(ranked_games.c.player_id)
        .having(func.count(ranked_games.c.fantasy_points) > 0)
    ).subquery()

    rows = db.execute(
        select(
            Player.id,
            Player.full_name,
            recent_averages.c.average_fantasy_points,
            recent_averages.c.games_played,
        )
        .join(recent_averages, recent_averages.c.player_id == Player.id)
        .where(Player.id.not_in(rostered_ids))
        .order_by(
            recent_averages.c.average_fantasy_points.desc(), Player.full_name.asc()
        )
        .limit(limit)
    ).all()

    return FreeAgentListResponse(
        season=season,
        games_considered=GAMES_TO_AVERAGE,
        players=[
            FreeAgentPlayer(
                player_id=player_id,
                name=full_name,
                average_fantasy_points=float(average_fantasy_points),
                games_played=games_played,
            )
            for player_id, full_name, average_fantasy_points, games_played in rows
        ],
    )
