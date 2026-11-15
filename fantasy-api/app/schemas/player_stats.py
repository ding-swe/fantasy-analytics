from pydantic import BaseModel


class PlayerGameLog(BaseModel):
    game_id: str
    game_date: str
    matchup: str
    result: str | None
    minutes: str | int | float | None
    points: int | float | None
    rebounds: int | float | None
    assists: int | float | None
    steals: int | float | None
    blocks: int | float | None
    turnovers: int | float | None
    three_pointers_made: int | float | None
    fantasy_points: int | float | None


class PlayerGameLogResponse(BaseModel):
    player_id: int
    player_name: str | None
    season: str
    games: list[PlayerGameLog]
