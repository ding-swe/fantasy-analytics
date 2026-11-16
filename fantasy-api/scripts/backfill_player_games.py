"""Offline NBA game-log importer using the shared sync service."""

import argparse
from datetime import date, datetime

from app.db.database import get_session_factory
from app.services.nba_sync import (
    create_sync_run,
    current_nba_season,
    fetch_rows,
    fetch_inactive_players,
    map_rows,
    run_sync_run,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch NBA player logs; writes require --apply."
    )
    parser.add_argument("--season", default=current_nba_season())
    parser.add_argument("--date-from", help="Inclusive start date (MM/DD/YYYY).")
    parser.add_argument("--date-to", help="Inclusive end date (MM/DD/YYYY).")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upsert fetched rows into PostgreSQL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    date_from = datetime.strptime(args.date_from, "%m/%d/%Y").date() if args.date_from else None
    date_to = datetime.strptime(args.date_to, "%m/%d/%Y").date() if args.date_to else date.today()
    if date_from and date_from > date_to:
        raise SystemExit("--date-from must be on or before --date-to")

    print(f"Fetching {args.season} regular-season player logs from NBA Stats...")
    if not args.apply:
        rows = fetch_rows(args.season, date_from, date_to)
        _players, games, _stats = map_rows(rows, args.season)
        inactive_by_game = fetch_inactive_players([game["id"] for game in games])
        players, games, stats = map_rows(rows, args.season, inactive_by_game)
        dates = [game["game_date"] for game in games]
        date_range = f"{min(dates)} through {max(dates)}" if dates else "no games returned"
        print(
            f"Fetched {len(rows)} rows: {len(players)} players, {len(games)} games, "
            f"{len(stats)} unique player-game lines ({date_range})."
        )
        print("Read-only preview; nothing was written. Pass --apply to upsert these rows.")
        return

    with get_session_factory()() as session:
        sync_run = create_sync_run(session, args.season, date_from, date_to)
        sync_run_id = sync_run.id
    stored = run_sync_run(sync_run_id, args.season, date_from, date_to)
    print(f"Database sync succeeded; upserted {stored} player-game lines.")


if __name__ == "__main__":
    main()
