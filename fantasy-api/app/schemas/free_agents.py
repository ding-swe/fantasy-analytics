from pydantic import BaseModel


class FreeAgentPlayer(BaseModel):
    player_id: int
    name: str
    average_fantasy_points: float
    games_played: int


class FreeAgentListResponse(BaseModel):
    season: str
    games_considered: int
    players: list[FreeAgentPlayer]
