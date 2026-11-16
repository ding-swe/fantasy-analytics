from pydantic import BaseModel


class PlayerGameLog(BaseModel):
    game_id: str
    game_date: str
    matchup: str
    opponent_team_abbreviation: str | None
    result: str | None
    minutes: str | int | float | None
    field_goals_made: int | float | None
    field_goals_attempted: int | float | None
    free_throws_made: int | float | None
    free_throws_attempted: int | float | None
    points: int | float | None
    rebounds: int | float | None
    assists: int | float | None
    steals: int | float | None
    blocks: int | float | None
    turnovers: int | float | None
    three_pointers_made: int | float | None
    fantasy_points: int | float | None


class PlayerWeeklyStats(BaseModel):
    games_played: int
    minutes: float | None
    field_goals_made: float | None
    field_goals_attempted: float | None
    free_throws_made: float | None
    free_throws_attempted: float | None
    points: float | None
    rebounds: float | None
    assists: float | None
    steals: float | None
    blocks: float | None
    turnovers: float | None
    three_pointers_made: float | None
    nba_fantasy_points: float | None


class PlayerGameLogResponse(BaseModel):
    player_id: int
    player_name: str | None
    season: str
    games: list[PlayerGameLog]
    current_week: PlayerWeeklyStats
    previous_week: PlayerWeeklyStats
