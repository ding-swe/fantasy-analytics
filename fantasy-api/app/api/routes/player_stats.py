from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas.player_stats import PlayerGameLogResponse
from app.services.player_stats import get_player_game_log

router = APIRouter(prefix="/api/players", tags=["player stats"])


def current_nba_season() -> str:
    year = date.today().year
    season_start = year if date.today().month >= 10 else year - 1
    return f"{season_start}-{str(season_start + 1)[-2:]}"


@router.get("/{player_id}/games", response_model=PlayerGameLogResponse)
def read_player_games(
    player_id: int,
    season: str | None = None,
    limit: int = Query(default=7, ge=1, le=20),
) -> PlayerGameLogResponse:
    selected_season = season or current_nba_season()

    try:
        return get_player_game_log(player_id, selected_season, limit)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="The NBA stats source could not be reached. Please try again.",
        ) from error
