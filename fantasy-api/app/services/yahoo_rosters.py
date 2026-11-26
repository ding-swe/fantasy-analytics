from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, Field, model_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import YahooTeamRosterSnapshot


class YahooRosterPlayer(BaseModel):
    player_key: str = Field(min_length=1)
    name: str = Field(min_length=1)


class YahooTeam(BaseModel):
    team_key: str = Field(min_length=1)
    team_name: str = Field(min_length=1)
    players: list[YahooRosterPlayer]


class YahooRosterSnapshot(BaseModel):
    league_key: str = Field(pattern=r"^\d+\.l\.\d+$")
    league_name: str = Field(min_length=1)
    captured_at: AwareDatetime
    teams: list[YahooTeam] = Field(min_length=1)


class YahooRosterImport(YahooRosterSnapshot):
    expected_team_count: int = Field(gt=0)

    @model_validator(mode="after")
    def check_complete_league(self):
        team_keys = {team.team_key for team in self.teams}
        if len(self.teams) != self.expected_team_count or len(team_keys) != len(self.teams):
            raise ValueError("Yahoo did not return the complete set of unique league teams.")
        for team in self.teams:
            if not team.team_key.startswith(f"{self.league_key}.t."):
                raise ValueError("Yahoo returned a team from a different league.")
            if len({player.player_key for player in team.players}) != len(team.players):
                raise ValueError("Yahoo returned duplicate players on a team.")
        return self


def get_latest_snapshot(db: Session, league_key: str | None = None) -> YahooRosterSnapshot | None:
    latest_id = select(YahooTeamRosterSnapshot.snapshot_id)
    if league_key is not None:
        latest_id = latest_id.where(YahooTeamRosterSnapshot.league_key == league_key)
    latest_id = latest_id.order_by(
        YahooTeamRosterSnapshot.captured_at.desc(),
        YahooTeamRosterSnapshot.snapshot_id.desc(),
    ).limit(1)
    rows = db.scalars(
        select(YahooTeamRosterSnapshot)
        .where(YahooTeamRosterSnapshot.snapshot_id == latest_id.scalar_subquery())
        .order_by(YahooTeamRosterSnapshot.team_key)
    ).all()
    if not rows:
        return None

    first = rows[0]
    return YahooRosterSnapshot(
        league_key=first.league_key,
        league_name=first.league_name,
        captured_at=first.captured_at,
        teams=[YahooTeam.model_validate(row, from_attributes=True) for row in rows],
    )


def roster_membership(snapshot: YahooRosterSnapshot) -> dict[str, set[str]]:
    return {
        team.team_key: {player.player_key for player in team.players}
        for team in snapshot.teams
    }


def save_snapshot(db: Session, snapshot: YahooRosterImport) -> bool:
    # Serialize comparison and insertion for imports of the same league.
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:league_key, 0))"),
        {"league_key": snapshot.league_key},
    )
    latest = get_latest_snapshot(db, snapshot.league_key)
    if latest is not None and (
        snapshot.captured_at <= latest.captured_at
        or roster_membership(snapshot) == roster_membership(latest)
    ):
        return False

    snapshot_id = uuid4()
    db.add_all([
        YahooTeamRosterSnapshot(
            snapshot_id=snapshot_id,
            league_key=snapshot.league_key,
            league_name=snapshot.league_name,
            captured_at=snapshot.captured_at,
            team_key=team.team_key,
            team_name=team.team_name,
            players=[player.model_dump() for player in team.players],
        )
        for team in snapshot.teams
    ])
    return True
