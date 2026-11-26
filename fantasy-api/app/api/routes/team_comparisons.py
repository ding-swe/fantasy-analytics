from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.team_comparisons import TeamComparisonResponse
from app.services.team_comparisons import MatchupWeekUnavailable, get_team_comparisons
from app.services.yahoo_sync import YahooAuthorizationRequired, YahooSyncError


router = APIRouter(prefix="/api/team-comparisons", tags=["team comparisons"])


@router.get("", response_model=TeamComparisonResponse)
def read_team_comparisons(
    week: int | None = Query(default=None, ge=1, le=53),
    db: Session = Depends(get_db),
) -> TeamComparisonResponse:
    try:
        return get_team_comparisons(db, week)
    except MatchupWeekUnavailable as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except YahooAuthorizationRequired as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except YahooSyncError as error:
        raise HTTPException(status_code=502, detail=str(error)) from None
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="The local database is unavailable. Please try again.",
        ) from None
