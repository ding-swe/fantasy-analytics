"""Fetch and optionally store the current NBA regular-season player game logs.

Run from ``fantasy-api``. By default this only fetches data and prints a summary.
Pass ``--apply`` to upsert the results into the local PostgreSQL database.
This manual script is not run by FastAPI or when the app starts.
"""

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal
import math
import re
from typing import Any

from nba_api.stats.endpoints import PlayerGameLogs
from sqlalchemy.dialects.postgresql import insert

from app.db.database import get_session_factory
from app.db.models import Game, Player, PlayerGameStats, SyncRun


BATCH_SIZE = 500
MATCHUP_PATTERN = re.compile(r"^([A-Z]{2,3})\s+(?:@|vs\.)\s+([A-Z]{2,3})$")


def opponent_abbreviation(matchup: Any, team_abbreviation: Any) -> str | None:
    matchup = clean_value(matchup)
    team_abbreviation = clean_value(team_abbreviation)
    if not matchup or not team_abbreviation:
        return None

    match = MATCHUP_PATTERN.fullmatch(str(matchup).strip())
    if match is None:
        return None

    first_team, second_team = match.groups()
    team_abbreviation = str(team_abbreviation).strip().upper()
    if team_abbreviation == first_team:
        return second_team
    if team_abbreviation == second_team:
        return first_team
    return None


def current_nba_season(today: date | None = None) -> str:
    today = today or date.today()
    start_year = today.year if today.month >= 10 else today.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def clean_value(value: Any) -> Any:
    """Convert pandas/numpy scalar values and NaNs to database-friendly values."""
    if hasattr(value, "item"):
        value = value.item()
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def integer_value(value: Any) -> int | None:
    value = clean_value(value)
    return None if value is None else int(value)


def decimal_value(value: Any) -> Decimal | None:
    value = clean_value(value)
    return None if value is None else Decimal(str(value))


def game_date_value(value: Any) -> date:
    value = clean_value(value)
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch current-season player game logs; writes require --apply."
    )
    parser.add_argument(
        "--season",
        default=current_nba_season(),
        help="NBA season (default: current season, e.g. 2026-27).",
    )
    parser.add_argument(
        "--date-from",
        help="Optional inclusive start date in MM/DD/YYYY format.",
    )
    parser.add_argument(
        "--date-to",
        help="Optional inclusive end date in MM/DD/YYYY format.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upsert the fetched rows into PostgreSQL. Without this flag, no DB writes occur.",
    )
    return parser.parse_args()


def fetch_rows(season: str, date_from: str | None, date_to: str | None) -> list[dict[str, Any]]:
    response = PlayerGameLogs(
        season_nullable=season,
        season_type_nullable="Regular Season",
        date_from_nullable=date_from or "",
        date_to_nullable=date_to or "",
        timeout=30,
    )
    return response.player_game_logs.get_data_frame().to_dict(orient="records")


def map_rows(
    rows: list[dict[str, Any]], season: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    players_by_id: dict[int, dict[str, Any]] = {}
    games_by_id: dict[str, dict[str, Any]] = {}
    stats_by_player_game: dict[tuple[int, str], dict[str, Any]] = {}

    for row in rows:
        player_id = integer_value(row.get("PLAYER_ID"))
        if player_id is None:
            continue

        game_id_value = clean_value(row.get("GAME_ID"))
        game_date = game_date_value(row.get("GAME_DATE"))
        if game_id_value is None:
            continue
        game_id = str(game_id_value)

        player_name = clean_value(row.get("PLAYER_NAME"))
        if not player_name:
            continue
        players_by_id[player_id] = {
            "id": player_id,
            "full_name": str(player_name),
        }

        games_by_id[game_id] = {
            "id": game_id,
            "season": str(clean_value(row.get("SEASON_YEAR")) or season),
            "game_date": game_date,
        }

        team_abbreviation = clean_value(row.get("TEAM_ABBREVIATION"))
        matchup = clean_value(row.get("MATCHUP"))
        stat_row = {
            "player_id": player_id,
            "game_id": game_id,
            "team_id": integer_value(row.get("TEAM_ID")),
            "team_abbreviation": team_abbreviation,
            "matchup": matchup,
            "opponent_team_abbreviation": opponent_abbreviation(
                matchup, team_abbreviation
            ),
            "result": clean_value(row.get("WL")),
            "minutes": decimal_value(row.get("MIN")),
            "field_goals_made": integer_value(row.get("FGM")),
            "field_goals_attempted": integer_value(row.get("FGA")),
            "three_pointers_made": integer_value(row.get("FG3M")),
            "free_throws_made": integer_value(row.get("FTM")),
            "free_throws_attempted": integer_value(row.get("FTA")),
            "offensive_rebounds": integer_value(row.get("OREB")),
            "defensive_rebounds": integer_value(row.get("DREB")),
            "rebounds": integer_value(row.get("REB")),
            "assists": integer_value(row.get("AST")),
            "steals": integer_value(row.get("STL")),
            "blocks": integer_value(row.get("BLK")),
            "turnovers": integer_value(row.get("TOV")),
            "points": integer_value(row.get("PTS")),
            "nba_fantasy_points": decimal_value(row.get("NBA_FANTASY_PTS")),
        }
        stats_by_player_game[(player_id, game_id)] = stat_row

    return (
        list(players_by_id.values()),
        list(games_by_id.values()),
        list(stats_by_player_game.values()),
    )


def upsert_batches(session: Any, model: Any, rows: list[dict[str, Any]], keys: list[str]) -> None:
    if not rows:
        return

    table = model.__table__
    update_columns = [
        column.name
        for column in table.columns
        if column.name not in keys and not column.primary_key
    ]

    for offset in range(0, len(rows), BATCH_SIZE):
        batch = rows[offset : offset + BATCH_SIZE]
        statement = insert(table).values(batch)
        statement = statement.on_conflict_do_update(
            index_elements=keys,
            set_={column: getattr(statement.excluded, column) for column in update_columns},
        )
        session.execute(statement)


def write_rows(
    players: list[dict[str, Any]],
    games: list[dict[str, Any]],
    stats: list[dict[str, Any]],
) -> int:
    session_factory = get_session_factory()
    started_at = datetime.now(timezone.utc)

    with session_factory() as session:
        sync_run = SyncRun(status="running", started_at=started_at)
        session.add(sync_run)
        session.commit()
        sync_run_id = sync_run.id

    try:
        with session_factory() as session:
            upsert_batches(session, Player, players, ["id"])
            upsert_batches(session, Game, games, ["id"])
            upsert_batches(session, PlayerGameStats, stats, ["player_id", "game_id"])

            latest_game_date = max((game["game_date"] for game in games), default=None)
            sync_run = session.get(SyncRun, sync_run_id)
            sync_run.status = "succeeded"
            sync_run.completed_at = datetime.now(timezone.utc)
            sync_run.completed_through_date = latest_game_date
            sync_run.records_processed = len(stats)
            session.commit()
        return len(stats)
    except Exception as error:
        with session_factory() as session:
            sync_run = session.get(SyncRun, sync_run_id)
            if sync_run is not None:
                sync_run.status = "failed"
                sync_run.completed_at = datetime.now(timezone.utc)
                sync_run.records_processed = 0
                sync_run.error_message = str(error)[:2000]
                session.commit()
        raise


def main() -> None:
    args = parse_args()
    parsed_from = datetime.strptime(args.date_from, "%m/%d/%Y") if args.date_from else None
    parsed_to = datetime.strptime(args.date_to, "%m/%d/%Y") if args.date_to else None
    if parsed_from and parsed_to and parsed_from > parsed_to:
        raise SystemExit("--date-from must be on or before --date-to")

    print(f"Fetching {args.season} regular-season player logs from NBA Stats...")
    rows = fetch_rows(args.season, args.date_from, args.date_to)
    players, games, stats = map_rows(rows, args.season)

    dates = [game["game_date"] for game in games]
    date_range = f"{min(dates)} through {max(dates)}" if dates else "no games returned"
    print(
        f"Fetched {len(rows)} rows: {len(players)} players, {len(games)} games, "
        f"{len(stats)} unique player-game lines ({date_range})."
    )

    if not args.apply:
        print("Read-only preview; nothing was written. Pass --apply to upsert these rows.")
        return
    if not rows:
        raise SystemExit("No rows returned; refusing to record an empty database sync.")

    stored_rows = write_rows(players, games, stats)
    print(f"Database sync succeeded; upserted {stored_rows} player-game lines.")


if __name__ == "__main__":
    main()
