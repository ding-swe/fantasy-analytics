from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Game, PlayerGameStats

WEEKLY_STAT_COLUMNS = (
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


def week_date_ranges(today: date | None = None) -> tuple[date, date, date, date]:
    today = today or date.today()
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)
    last_sunday = this_monday - timedelta(days=1)
    return this_monday, today, last_monday, last_sunday


def get_weekly_player_averages(
    db: Session,
    season: str,
    player_ids: Iterable[int] | None = None,
    today: date | None = None,
) -> dict[int, dict[str, dict[str, float | int | None]]]:
    this_monday, current_end, last_monday, last_sunday = week_date_ranges(today)
    player_id_set = set(player_ids) if player_ids is not None else None
    result: dict[int, dict[str, dict[str, float | int | None]]] = {}
    if player_id_set is not None:
        for player_id in player_id_set:
            result[player_id] = {
                "current_week": {"games_played": 0, **{column: None for column in WEEKLY_STAT_COLUMNS}},
                "previous_week": {"games_played": 0, **{column: None for column in WEEKLY_STAT_COLUMNS}},
            }

    query = (
        select(
            PlayerGameStats.player_id,
            Game.game_date,
            *[getattr(PlayerGameStats, column) for column in WEEKLY_STAT_COLUMNS],
        )
        .join(Game, Game.id == PlayerGameStats.game_id)
        .where(
            Game.season == season,
            Game.game_date >= last_monday,
            Game.game_date <= current_end,
        )
    )
    if player_id_set is not None:
        if not player_id_set:
            return result
        query = query.where(PlayerGameStats.player_id.in_(player_id_set))

    accumulators: dict[int, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: {"current_week": defaultdict(list), "previous_week": defaultdict(list)}
    )
    games_by_player_period: dict[int, dict[str, int]] = defaultdict(
        lambda: {"current_week": 0, "previous_week": 0}
    )

    for row in db.execute(query):
        player_id, game_date, *values = row
        period = "current_week" if game_date >= this_monday else "previous_week"
        games_by_player_period[player_id][period] += 1
        for column, value in zip(WEEKLY_STAT_COLUMNS, values):
            if value is not None:
                accumulators[player_id][period][column].append(float(value))

    for player_id, periods in games_by_player_period.items():
        result.setdefault(player_id, {})
        for period in ("current_week", "previous_week"):
            stats = {
                "games_played": periods[period],
                **{
                    column: (
                        sum(values) / len(values)
                        if (values := accumulators[player_id][period][column])
                        else None
                    )
                    for column in WEEKLY_STAT_COLUMNS
                },
            }
            result[player_id][period] = stats

    return result
