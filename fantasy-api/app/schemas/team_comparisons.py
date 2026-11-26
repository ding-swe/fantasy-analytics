from datetime import date

from pydantic import BaseModel


class ScoringCategory(BaseModel):
    stat_id: str
    name: str
    label: str
    counts_toward_result: bool
    higher_is_better: bool


class MatchupTeam(BaseModel):
    team_key: str
    team_name: str
    manager_name: str | None
    is_my_team: bool
    points: str | None
    stats: dict[str, str]


class YahooMatchup(BaseModel):
    status: str
    week_start: date | None
    week_end: date | None
    winner_team_key: str | None
    is_tied: bool
    category_winners: dict[str, str | None]
    teams: list[MatchupTeam]


class TeamComparisonResponse(BaseModel):
    league_name: str
    scoring_type: str
    start_week: int
    current_week: int
    week: int
    categories: list[ScoringCategory]
    matchups: list[YahooMatchup]
