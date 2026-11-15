from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
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
    db: Session = Depends(get_db),
) -> PlayerGameLogResponse:
    selected_season = season or current_nba_season()

    try:
        return get_player_game_log(player_id, selected_season, limit, db)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="The local stats database is unavailable. Please try again.",
        ) from error
