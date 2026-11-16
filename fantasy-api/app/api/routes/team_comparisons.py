from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.team_comparisons import TeamComparisonResponse
from app.services.team_comparisons import get_team_comparisons

router = APIRouter(prefix="/api/team-comparisons", tags=["team comparisons"])


@router.get("", response_model=TeamComparisonResponse)
def read_team_comparisons(
    db: Session = Depends(get_db),
) -> TeamComparisonResponse:
    try:
        return get_team_comparisons(db)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="The local stats database is unavailable. Please try again.",
        ) from error
