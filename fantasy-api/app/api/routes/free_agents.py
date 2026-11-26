from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.free_agents import FreeAgentListResponse
from app.services.free_agents import get_free_agents

router = APIRouter(prefix="/api/free-agents", tags=["free agents"])


@router.get("", response_model=FreeAgentListResponse)
def read_free_agents(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> FreeAgentListResponse:
    try:
        result = get_free_agents(limit, db)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="The local stats database is unavailable. Please try again.",
        ) from error

    if result is None:
        raise HTTPException(status_code=404, detail="Import the Yahoo league rosters to see unrostered players.")
    return result
