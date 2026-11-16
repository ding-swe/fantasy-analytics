"""Shared NBA game-log sync used by the API and offline importer."""

from datetime import date, datetime, timezone
from decimal import Decimal
import math
import re
import time
from typing import Any

from nba_api.stats.endpoints import BoxScoreSummaryV3, PlayerGameLogs
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.database import get_session_factory
from app.db.models import Game, Player, PlayerGameStats, SyncRun

BATCH_SIZE = 500
MATCHUP_PATTERN = re.compile(r"^([A-Z]{2,3})\s+(?:@|vs\.)\s+([A-Z]{2,3})$")
MAX_FETCH_ATTEMPTS = 4
BOX_SCORE_REQUEST_DELAY_SECONDS = 0.7


def current_nba_season(today: date | None = None) -> str:
    today = today or date.today()
    start_year = today.year if today.month >= 10 else today.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def season_start_date(season: str) -> date:
    return date(int(season[:4]), 10, 1)


def next_sync_window(db: Session, season: str, today: date | None = None):
    today = today or date.today()
    last_successful_date = db.scalar(
        select(SyncRun.completed_through_date)
        .where(
            SyncRun.status == "succeeded",
            SyncRun.completed_through_date.is_not(None),
        )
        .order_by(SyncRun.completed_at.desc(), SyncRun.id.desc())
        .limit(1)
    )
    start = season_start_date(season)
    if last_successful_date is not None and start <= last_successful_date <= today:
        return last_successful_date, today
    return None, today


def create_sync_run(db: Session, season: str, date_from: date | None, date_to: date) -> SyncRun:
    sync_run = SyncRun(
        status="running",
        season=season,
        date_from=date_from,
        date_to=date_to,
        started_at=datetime.now(timezone.utc),
        records_processed=0,
    )
    db.add(sync_run)
    db.commit()
    db.refresh(sync_run)
    return sync_run


def clean_value(value: Any) -> Any:
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


def fetch_rows(
    season: str, date_from: date | None = None, date_to: date | None = None
) -> list[dict[str, Any]]:
    start_text = date_from.strftime("%m/%d/%Y") if date_from else ""
    end_text = date_to.strftime("%m/%d/%Y") if date_to else ""
    last_error = None
    for attempt in range(MAX_FETCH_ATTEMPTS):
        try:
            response = PlayerGameLogs(
                season_nullable=season,
                season_type_nullable="Regular Season",
                date_from_nullable=start_text,
                date_to_nullable=end_text,
                timeout=60,
            )
            return response.player_game_logs.get_data_frame().to_dict(orient="records")
        except Exception as error:
            last_error = error
            if attempt + 1 < MAX_FETCH_ATTEMPTS:
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError(
        f"NBA Stats request failed after {MAX_FETCH_ATTEMPTS} attempts: {last_error}"
    ) from last_error


def fetch_inactive_players(game_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    inactive_by_game: dict[str, list[dict[str, Any]]] = {}
    for index, game_id in enumerate(dict.fromkeys(game_ids)):
        if index:
            time.sleep(BOX_SCORE_REQUEST_DELAY_SECONDS)
        last_error = None
        for attempt in range(MAX_FETCH_ATTEMPTS):
            try:
                summary = BoxScoreSummaryV3(game_id=game_id, timeout=60)
                inactive_by_game[game_id] = (
                    summary.inactive_players.get_data_frame().to_dict(orient="records")
                )
                break
            except Exception as error:
                last_error = error
                if attempt + 1 < MAX_FETCH_ATTEMPTS:
                    time.sleep(2 ** (attempt + 1))
        else:
            raise RuntimeError(
                f"NBA Stats inactive-player request failed for game {game_id}: {last_error}"
            ) from last_error
    return inactive_by_game


def map_rows(
    rows: list[dict[str, Any]],
    season: str,
    inactive_by_game: dict[str, list[dict[str, Any]]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    players_by_id: dict[int, dict[str, Any]] = {}
    games_by_id: dict[str, dict[str, Any]] = {}
    stats_by_player_game: dict[tuple[int, str], dict[str, Any]] = {}
    team_context_by_game: dict[str, dict[int, dict[str, Any]]] = {}
    for row in rows:
        player_id = integer_value(row.get("PLAYER_ID"))
        game_id_value = clean_value(row.get("GAME_ID"))
        player_name = clean_value(row.get("PLAYER_NAME"))
        if player_id is None or game_id_value is None or not player_name:
            continue
        game_id = str(game_id_value)
        game_date = game_date_value(row.get("GAME_DATE"))
        players_by_id[player_id] = {"id": player_id, "full_name": str(player_name)}
        games_by_id[game_id] = {
            "id": game_id,
            "season": str(clean_value(row.get("SEASON_YEAR")) or season),
            "game_date": game_date,
        }
        team_abbreviation = clean_value(row.get("TEAM_ABBREVIATION"))
        matchup = clean_value(row.get("MATCHUP"))
        team_id = integer_value(row.get("TEAM_ID"))
        if team_id is not None:
            team_context_by_game.setdefault(game_id, {})[team_id] = {
                "team_abbreviation": team_abbreviation,
                "matchup": matchup,
                "result": clean_value(row.get("WL")),
            }
        stats_by_player_game[(player_id, game_id)] = {
            "player_id": player_id,
            "game_id": game_id,
            "team_id": team_id,
            "team_abbreviation": team_abbreviation,
            "matchup": matchup,
            "opponent_team_abbreviation": opponent_abbreviation(matchup, team_abbreviation),
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

    for game_id, inactive_rows in (inactive_by_game or {}).items():
        team_context = team_context_by_game.get(game_id, {})
        for inactive in inactive_rows:
            player_id = integer_value(inactive.get("personId") or inactive.get("PLAYER_ID"))
            team_id = integer_value(inactive.get("teamId") or inactive.get("TEAM_ID"))
            if player_id is None or team_id is None:
                continue
            key = (player_id, game_id)
            if key in stats_by_player_game or game_id not in games_by_id:
                continue
            player_name = " ".join(
                part
                for part in (
                    str(clean_value(inactive.get("firstName") or inactive.get("FIRST_NAME")) or "").strip(),
                    str(clean_value(inactive.get("familyName") or inactive.get("LAST_NAME")) or "").strip(),
                )
                if part
            )
            if not player_name:
                continue
            players_by_id.setdefault(
                player_id, {"id": player_id, "full_name": player_name}
            )
            context = team_context.get(team_id)
            if context is None:
                continue
            matchup = context["matchup"]
            abbreviation = context["team_abbreviation"]
            stats_by_player_game[key] = {
                "player_id": player_id,
                "game_id": game_id,
                "team_id": team_id,
                "team_abbreviation": abbreviation,
                "matchup": matchup,
                "opponent_team_abbreviation": opponent_abbreviation(matchup, abbreviation),
                "result": context["result"],
                "minutes": Decimal("0"),
                "field_goals_made": 0,
                "field_goals_attempted": 0,
                "three_pointers_made": 0,
                "free_throws_made": 0,
                "free_throws_attempted": 0,
                "offensive_rebounds": 0,
                "defensive_rebounds": 0,
                "rebounds": 0,
                "assists": 0,
                "steals": 0,
                "blocks": 0,
                "turnovers": 0,
                "points": 0,
                "nba_fantasy_points": Decimal("0"),
            }
    return list(players_by_id.values()), list(games_by_id.values()), list(stats_by_player_game.values())


def upsert_batches(session: Session, model: Any, rows: list[dict[str, Any]], keys: list[str]) -> None:
    for offset in range(0, len(rows), BATCH_SIZE):
        batch = rows[offset : offset + BATCH_SIZE]
        statement = insert(model.__table__).values(batch)
        update_columns = [
            column.name
            for column in model.__table__.columns
            if column.name not in keys and not column.primary_key
        ]
        session.execute(
            statement.on_conflict_do_update(
                index_elements=keys,
                set_={column: getattr(statement.excluded, column) for column in update_columns},
            )
        )


def run_sync_run(
    sync_run_id: int,
    season: str,
    date_from: date | None,
    date_to: date,
) -> int:
    factory = get_session_factory()
    try:
        rows = fetch_rows(season, date_from, date_to)
        _players, games, _stats = map_rows(rows, season)
        inactive_by_game = fetch_inactive_players([game["id"] for game in games])
        players, games, stats = map_rows(rows, season, inactive_by_game)
        with factory() as session:
            upsert_batches(session, Player, players, ["id"])
            upsert_batches(session, Game, games, ["id"])
            upsert_batches(session, PlayerGameStats, stats, ["player_id", "game_id"])
            sync_run = session.get(SyncRun, sync_run_id)
            if sync_run is None:
                raise RuntimeError(f"Sync run {sync_run_id} disappeared before completion.")
            sync_run.status = "succeeded"
            sync_run.completed_at = datetime.now(timezone.utc)
            sync_run.completed_through_date = date_to
            sync_run.records_processed = len(stats)
            session.commit()
        return len(stats)
    except Exception as error:
        with factory() as session:
            sync_run = session.get(SyncRun, sync_run_id)
            if sync_run is not None:
                sync_run.status = "failed"
                sync_run.completed_at = datetime.now(timezone.utc)
                sync_run.records_processed = 0
                sync_run.error_message = str(error)[:2000]
                session.commit()
        raise
