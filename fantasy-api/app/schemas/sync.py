from datetime import date, datetime

from pydantic import BaseModel


class SyncRunStatus(BaseModel):
    id: int
    status: str
    season: str | None
    date_from: date | None
    date_to: date | None
    started_at: datetime
    completed_at: datetime | None
    completed_through_date: date | None
    records_processed: int
    error_message: str | None
    yahoo_status: str | None = None
    yahoo_error_message: str | None = None
