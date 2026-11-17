from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import FantasyLeague, FantasyManager, FantasyRosterEntry
from app.schemas.team_comparisons import TeamComparison, TeamComparisonResponse
from app.services.free_agents import current_nba_season
from app.services.weekly_stats import get_weekly_player_averages

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
    weekly_by_player = get_weekly_player_averages(db, season)
    weekly_points_by_manager: dict[int, dict[str, float]] = {}
    core_entries = db.execute(
        select(FantasyRosterEntry.manager_id, FantasyRosterEntry.player_id).where(
            FantasyRosterEntry.roster_group == "core"
        )
    ).all()
    for manager_id, player_id in core_entries:
        weekly = weekly_by_player.get(player_id, {})
        points = weekly_points_by_manager.setdefault(
            manager_id, {"current_week": 0.0, "previous_week": 0.0}
        )
        points["current_week"] += float(
            (weekly.get("current_week") or {}).get("nba_fantasy_points") or 0
        )
        points["previous_week"] += float(
            (weekly.get("previous_week") or {}).get("nba_fantasy_points") or 0
        )

    weekly_totals: dict[int, dict[str, float]] = {}
    for manager_id, player_id in core_entries:
        current = weekly_by_player.get(player_id, {}).get("current_week") or {}
        totals = weekly_totals.setdefault(
            manager_id, {column: 0.0 for column in STAT_COLUMNS}
        )
        for column in STAT_COLUMNS:
            totals[column] += float(current.get(column) or 0)

    managers = db.execute(
        select(
            FantasyManager.id,
            FantasyManager.manager_name,
            FantasyManager.team_name,
            func.count(FantasyRosterEntry.player_id).label("core_player_count"),
        )
        .join(FantasyLeague, FantasyLeague.id == FantasyManager.league_id)
        .outerjoin(
            FantasyRosterEntry,
            (FantasyRosterEntry.manager_id == FantasyManager.id)
            & (FantasyRosterEntry.roster_group == "core"),
        )
        .group_by(FantasyManager.id)
        .order_by(FantasyManager.team_name)
    ).all()

    return TeamComparisonResponse(
        season=season,
        teams=[
            TeamComparison(
                manager_id=row.id,
                manager_name=row.manager_name,
                team_name=row.team_name,
                core_player_count=row.core_player_count,
                **{
                    field: weekly_totals.get(row.id, {}).get(field, 0.0)
                    for field in STAT_COLUMNS
                    if field != "nba_fantasy_points"
                },
                fantasy_points=weekly_totals.get(row.id, {}).get(
                    "nba_fantasy_points", 0.0
                ),
                current_week_fantasy_points=weekly_points_by_manager.get(
                    row.id, {}
                ).get("current_week", 0.0),
                previous_week_fantasy_points=weekly_points_by_manager.get(
                    row.id, {}
                ).get("previous_week", 0.0),
            )
            for row in managers
        ],
    )
