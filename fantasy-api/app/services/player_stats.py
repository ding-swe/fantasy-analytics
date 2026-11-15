import math
from typing import Any

from app.data.nba_stats_client import fetch_player_game_logs
from app.schemas.player_stats import PlayerGameLog, PlayerGameLogResponse


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def get_player_game_log(
    player_id: int,
    season: str,
    limit: int,
) -> PlayerGameLogResponse:
    rows = fetch_player_game_logs(player_id, season, limit)
    games = [
        PlayerGameLog(
            game_id=str(row.get("GAME_ID", "")),
            game_date=str(row.get("GAME_DATE", "")),
            matchup=str(row.get("MATCHUP", "")),
            result=_json_value(row.get("WL")),
            minutes=_json_value(row.get("MIN")),
            points=_json_value(row.get("PTS")),
            rebounds=_json_value(row.get("REB")),
            assists=_json_value(row.get("AST")),
            steals=_json_value(row.get("STL")),
            blocks=_json_value(row.get("BLK")),
            turnovers=_json_value(row.get("TOV")),
            three_pointers_made=_json_value(row.get("FG3M")),
            fantasy_points=_json_value(row.get("NBA_FANTASY_PTS")),
        )
        for row in rows
    ]
    player_name = str(rows[0].get("PLAYER_NAME", "")) if rows else None

    return PlayerGameLogResponse(
        player_id=player_id,
        player_name=player_name,
        season=season,
        games=games,
    )
