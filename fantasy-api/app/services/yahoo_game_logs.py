import os
import unicodedata
from collections import defaultdict

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Player
from app.services.yahoo_rosters import YahooRosterPlayer, YahooRosterSnapshot


class YahooGameLogPlayer(YahooRosterPlayer):
    nba_player_id: int | None


class YahooGameLogTeam(BaseModel):
    team_key: str
    team_name: str
    players: list[YahooGameLogPlayer]


class YahooGameLogRosters(BaseModel):
    default_team_key: str | None
    teams: list[YahooGameLogTeam]


def normalize_player_name(name: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", name).casefold()
        if character.isalnum()
    )


def to_game_log_rosters(db: Session, snapshot: YahooRosterSnapshot) -> YahooGameLogRosters:
    ids_by_name: dict[str, set[int]] = defaultdict(set)
    for player_id, name in db.execute(select(Player.id, Player.full_name)):
        ids_by_name[normalize_player_name(name)].add(player_id)

    teams = []
    for team in snapshot.teams:
        players = []
        for player in team.players:
            matches = ids_by_name.get(normalize_player_name(player.name), set())
            players.append(YahooGameLogPlayer(
                **player.model_dump(),
                nba_player_id=next(iter(matches)) if len(matches) == 1 else None,
            ))
        teams.append(YahooGameLogTeam(
            team_key=team.team_key, team_name=team.team_name, players=players,
        ))

    configured_team = os.getenv("YAHOO_MY_TEAM_KEY")
    default_team = next(
        (team.team_key for team in teams if team.team_key == configured_team),
        None,
    )
    return YahooGameLogRosters(default_team_key=default_team, teams=teams)
