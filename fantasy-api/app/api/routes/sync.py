from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import SyncRun
from app.schemas.sync import SyncRunStatus
from app.services.free_agents import current_nba_season
from app.services.nba_sync import create_sync_run, next_sync_window, run_sync_run
from app.services.yahoo_sync import refresh_rosters_for_run

router = APIRouter(prefix="/api/sync", tags=["data sync"])


def to_status(run: SyncRun) -> SyncRunStatus:
    return SyncRunStatus(
        id=run.id,
        status=run.status,
        season=run.season,
        date_from=run.date_from,
        date_to=run.date_to,
        started_at=run.started_at,
        completed_at=run.completed_at,
        completed_through_date=run.completed_through_date,
        records_processed=run.records_processed,
        error_message=run.error_message,
        yahoo_status=run.yahoo_status,
        yahoo_error_message=run.yahoo_error_message,
    )


def run_app_sync(run_id: int, season: str, date_from: date | None, date_to: date) -> None:
    try:
        refresh_rosters_for_run(run_id)
    finally:
        run_sync_run(run_id, season, date_from, date_to)


@router.post("", response_model=SyncRunStatus, status_code=status.HTTP_202_ACCEPTED)
def start_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SyncRunStatus:
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('basketbase:app-sync', 0))"))
    now = datetime.now(timezone.utc)
    active_run = db.scalar(
        select(SyncRun)
        .where(SyncRun.status == "running")
        .order_by(SyncRun.started_at.desc())
        .limit(1)
    )
    if active_run is not None:
        started_at = active_run.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if started_at > now - timedelta(hours=3):
            return to_status(active_run)
        active_run.status = "failed"
        active_run.completed_at = now
        active_run.error_message = "Marked failed because the sync exceeded three hours."
        if active_run.yahoo_status == "running":
            active_run.yahoo_status = "failed"
            active_run.yahoo_error_message = "The previous sync timed out."
        db.flush()

    season = current_nba_season()
    date_from, date_to = next_sync_window(db, season)
    run = create_sync_run(db, season, date_from, date_to, include_yahoo=True)
    background_tasks.add_task(run_app_sync, run.id, season, date_from, date_to)
    return to_status(run)


@router.get("/latest", response_model=SyncRunStatus | None)
def read_latest_sync(db: Session = Depends(get_db)) -> SyncRunStatus | None:
    run = db.scalar(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(1))
    return to_status(run) if run is not None else None


@router.get("/{sync_run_id}", response_model=SyncRunStatus)
def read_sync_status(
    sync_run_id: int,
    db: Session = Depends(get_db),
) -> SyncRunStatus:
    run = db.get(SyncRun, sync_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Sync run not found.")
    return to_status(run)
