from pydantic import BaseModel


class RosterPlayer(BaseModel):
    player_id: int
    name: str


class CurrentRosterResponse(BaseModel):
    manager_id: int
    manager_name: str
    team_name: str
    streaming_slots: int
    core_players: list[RosterPlayer]
    stream_slot_candidates: list[RosterPlayer]


class RosterManagerOption(BaseModel):
    manager_id: int
    manager_name: str
    team_name: str
    is_primary: bool


class RosterManagerListResponse(BaseModel):
    managers: list[RosterManagerOption]
    default_manager_id: int | None
