from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.yahoo_game_logs import YahooGameLogRosters, to_game_log_rosters
from app.services.yahoo_rosters import YahooRosterSnapshot, get_latest_snapshot


router = APIRouter(prefix="/api/yahoo", tags=["yahoo fantasy"])


@router.get("/teams")
def read_yahoo_teams(db: Session = Depends(get_db)) -> YahooRosterSnapshot:
    try:
        snapshot = get_latest_snapshot(db)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not load Yahoo rosters from PostgreSQL.",
        ) from None
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="Import the Yahoo league rosters, then reload this page.",
        )
    return snapshot


@router.get("/game-log-rosters")
def read_yahoo_game_log_rosters(db: Session = Depends(get_db)) -> YahooGameLogRosters:
    snapshot = read_yahoo_teams(db)
    try:
        return to_game_log_rosters(db, snapshot)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not match Yahoo roster players to the local NBA database.",
        ) from None
