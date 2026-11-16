from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import FantasyLeague, FantasyManager, FantasyRosterEntry, Game, PlayerGameStats
from app.schemas.team_comparisons import TeamComparison, TeamComparisonResponse
from app.services.free_agents import GAMES_TO_AVERAGE, current_nba_season

RECENT_DAYS = 21
STAT_COLUMNS = (
    "minutes",
    "field_goals_made",
    "field_goals_attempted",
    "free_throws_made",
    "free_throws_attempted",
    "points",
    "rebounds",
    "assists",
    "steals",
    "blocks",
    "turnovers",
    "three_pointers_made",
    "nba_fantasy_points",
)


def get_team_comparisons(db: Session) -> TeamComparisonResponse:
    season = current_nba_season()
    recent_cutoff = date.today() - timedelta(days=RECENT_DAYS)
    ranked_games = (
        select(
            PlayerGameStats.player_id.label("player_id"),
            Game.game_date.label("game_date"),
            *[
                getattr(PlayerGameStats, column).label(column)
                for column in STAT_COLUMNS
            ],
            func.row_number()
            .over(
                partition_by=PlayerGameStats.player_id,
                order_by=(Game.game_date.desc(), Game.id.desc()),
            )
            .label("game_rank"),
        )
        .join(Game, Game.id == PlayerGameStats.game_id)
        .where(Game.season == season, Game.game_date >= recent_cutoff)
    ).subquery()

    player_averages = (
        select(
            ranked_games.c.player_id,
            *[
                func.avg(getattr(ranked_games.c, column)).label(column)
                for column in STAT_COLUMNS
            ],
        )
        .where(ranked_games.c.game_rank <= GAMES_TO_AVERAGE)
        .group_by(ranked_games.c.player_id)
    ).subquery()

    teams = db.execute(
        select(
            FantasyManager.id,
            FantasyManager.manager_name,
            FantasyManager.team_name,
            func.count(FantasyRosterEntry.player_id).label("core_player_count"),
            *[
                func.coalesce(func.sum(getattr(player_averages.c, column)), 0).label(
                    column
                )
                for column in STAT_COLUMNS
            ],
        )
        .join(FantasyLeague, FantasyLeague.id == FantasyManager.league_id)
        .outerjoin(
            FantasyRosterEntry,
            (FantasyRosterEntry.manager_id == FantasyManager.id)
            & (FantasyRosterEntry.roster_group == "core"),
        )
        .outerjoin(
            player_averages,
            player_averages.c.player_id == FantasyRosterEntry.player_id,
        )
        .group_by(FantasyManager.id)
        .order_by(FantasyManager.team_name)
    ).all()

    return TeamComparisonResponse(
        season=season,
        games_considered=GAMES_TO_AVERAGE,
        recent_days=RECENT_DAYS,
        teams=[
            TeamComparison(
                manager_id=row.id,
                manager_name=row.manager_name,
                team_name=row.team_name,
                core_player_count=row.core_player_count,
                **{
                    field: float(getattr(row, field) or 0)
                    for field in STAT_COLUMNS
                    if field != "nba_fantasy_points"
                },
                fantasy_points=float(row.nba_fantasy_points or 0),
            )
            for row in teams
        ],
    )
