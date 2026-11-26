from datetime import date
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, Field, model_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import YahooTeamRosterSnapshot


class YahooRosterPlayer(BaseModel):
    player_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    lineup_slot: str | None = None
    injury_status: str | None = None
    added_at: AwareDatetime | None = None


class YahooTeam(BaseModel):
    team_key: str = Field(min_length=1)
    team_name: str = Field(min_length=1)
    lineup_date: date | None = None
    players: list[YahooRosterPlayer]


class YahooRosterSnapshot(BaseModel):
    league_key: str = Field(pattern=r"^\d+\.l\.\d+$")
    league_name: str = Field(min_length=1)
    captured_at: AwareDatetime
    teams: list[YahooTeam] = Field(min_length=1)


class YahooRosterImport(YahooRosterSnapshot):
    expected_team_count: int = Field(gt=0)
    recent_adds_complete: bool = False

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


def latest_snapshot_rows(db: Session, league_key: str | None) -> list[YahooTeamRosterSnapshot]:
    latest_id = select(YahooTeamRosterSnapshot.snapshot_id)
    if league_key is not None:
        latest_id = latest_id.where(YahooTeamRosterSnapshot.league_key == league_key)
    latest_id = latest_id.order_by(
        YahooTeamRosterSnapshot.captured_at.desc(),
        YahooTeamRosterSnapshot.snapshot_id.desc(),
    ).limit(1)
    return list(db.scalars(
        select(YahooTeamRosterSnapshot)
        .where(YahooTeamRosterSnapshot.snapshot_id == latest_id.scalar_subquery())
        .order_by(YahooTeamRosterSnapshot.team_key)
    ))


def get_latest_snapshot(db: Session, league_key: str | None = None) -> YahooRosterSnapshot | None:
    rows = latest_snapshot_rows(db, league_key)
    if not rows:
        return None

    first = rows[0]
    return YahooRosterSnapshot(
        league_key=first.league_key,
        league_name=first.league_name,
        captured_at=first.captured_at,
        teams=[YahooTeam.model_validate(row, from_attributes=True) for row in rows],
    )


def save_snapshot(db: Session, snapshot: YahooRosterImport) -> bool:
    # Serialize comparison and insertion for imports of the same league.
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:league_key, 0))"),
        {"league_key": snapshot.league_key},
    )
    latest = latest_snapshot_rows(db, snapshot.league_key)
    previous_by_team = {row.team_key: row for row in latest}
    if latest and snapshot.captured_at <= (latest[0].details_fetched_at or latest[0].captured_at):
        return False

    same_membership = {
        team.team_key: {player.player_key for player in team.players}
        for team in snapshot.teams
    } == {
        row.team_key: {player["player_key"] for player in row.players}
        for row in latest
    }

    snapshot_id = uuid4()
    for team in snapshot.teams:
        previous = previous_by_team.get(team.team_key)
        players = [player.model_dump(mode="json") for player in team.players]
        if previous is not None and not snapshot.recent_adds_complete:
            known_adds = {player["player_key"]: player.get("added_at") for player in previous.players}
            for player in players:
                if player["added_at"] is None:
                    player["added_at"] = known_adds.get(player["player_key"])

        if same_membership:
            previous.league_name = snapshot.league_name
            previous.team_name = team.team_name
            previous.lineup_date = team.lineup_date
            previous.details_fetched_at = snapshot.captured_at
            previous.players = players
        else:
            db.add(YahooTeamRosterSnapshot(
                snapshot_id=snapshot_id,
                league_key=snapshot.league_key,
                league_name=snapshot.league_name,
                captured_at=snapshot.captured_at,
                team_key=team.team_key,
                team_name=team.team_name,
                lineup_date=team.lineup_date,
                details_fetched_at=snapshot.captured_at,
                players=players,
            ))
    return not same_membership
