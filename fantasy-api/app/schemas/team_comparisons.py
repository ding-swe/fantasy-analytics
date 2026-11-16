from pydantic import BaseModel


class TeamComparison(BaseModel):
    manager_id: int
    manager_name: str
    team_name: str
    core_player_count: int
    minutes: float
    field_goals_made: float
    field_goals_attempted: float
    free_throws_made: float
    free_throws_attempted: float
    points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    turnovers: float
    three_pointers_made: float
    fantasy_points: float
    current_week_fantasy_points: float
    previous_week_fantasy_points: float


class TeamComparisonResponse(BaseModel):
    season: str
    teams: list[TeamComparison]
