from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.roster import (
    CurrentRosterResponse,
    RosterManagerListResponse,
)
from app.services.roster import get_current_roster, get_manager_roster, get_roster_managers

router = APIRouter(prefix="/api/rosters", tags=["fantasy rosters"])


@router.get("", response_model=RosterManagerListResponse)
def read_roster_managers(db: Session = Depends(get_db)) -> RosterManagerListResponse:
    try:
        return get_roster_managers(db)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="The local stats database is unavailable. Please try again.",
        ) from error


@router.get("/current", response_model=CurrentRosterResponse)
def read_current_roster(db: Session = Depends(get_db)) -> CurrentRosterResponse:
    try:
        roster = get_current_roster(db)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="The local stats database is unavailable. Please try again.",
        ) from error

    if roster is None:
        raise HTTPException(status_code=404, detail="No primary fantasy roster is configured.")
    return roster


@router.get("/{manager_id}", response_model=CurrentRosterResponse)
def read_manager_roster(
    manager_id: int, db: Session = Depends(get_db)
) -> CurrentRosterResponse:
    try:
        roster = get_manager_roster(manager_id, db)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="The local stats database is unavailable. Please try again.",
        ) from error

    if roster is None:
        raise HTTPException(status_code=404, detail="Fantasy manager not found.")
    return roster
