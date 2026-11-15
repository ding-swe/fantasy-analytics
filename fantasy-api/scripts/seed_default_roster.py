"""Seed the prototype league and its initial managers into PostgreSQL."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_session_factory
from app.db.models import FantasyLeague, FantasyManager, FantasyRosterEntry, Player


ROSTERS = [
    {
        "manager_name": "Me",
        "team_name": "My Team",
        "is_primary": True,
        "streaming_slots": 1,
        "core": [
            (1630581, "Josh Giddey"),
            (1628384, "OG Anunoby"),
            (1631095, "Jabari Smith Jr."),
            (1641705, "Victor Wembanyama"),
            (203497, "Rudy Gobert"),
            (1642847, "Jeremiah Fears"),
            (202331, "Paul George"),
            (1629027, "Trae Young"),
            (1626164, "Devin Booker"),
            (1628401, "Derrick White"),
            (1630188, "Jalen Smith"),
        ],
        "stream_candidates": [
            (201950, "Jrue Holiday"),
            (1642258, "Zaccharie Risacher"),
        ],
    },
    {
        "manager_name": "Nancy",
        "team_name": "Nancy's Team",
        "is_primary": False,
        "streaming_slots": 1,
        "core": [
            (203954, "Joel Embiid"),
            (1629630, "Ja Morant"),
            (1630530, "Trey Murphy III"),
            (203507, "Giannis Antetokounmpo"),
            (1642865, "Yaxel Lendeborg"),
            (1642276, "Kel'el Ware"),
            (1630700, "Dyson Daniels"),
            (1642846, "Ace Bailey"),
            (1642264, "Stephon Castle"),
            (1642843, "Cooper Flagg"),
            (203468, "CJ McCollum"),
            (1630578, "Alperen Sengun"),
        ],
        "stream_candidates": [],
    },
]


def seed_manager(session: Session, league: FantasyLeague, roster: dict[str, Any]) -> None:
    manager = session.scalar(
        select(FantasyManager).where(
            FantasyManager.league_id == league.id,
            FantasyManager.team_name == roster["team_name"],
        )
    )
    if manager is None:
        manager = FantasyManager(
            league_id=league.id,
            manager_name=roster["manager_name"],
            team_name=roster["team_name"],
            is_primary=roster["is_primary"],
            streaming_slots=roster["streaming_slots"],
        )
        session.add(manager)
        session.flush()
    else:
        manager.manager_name = roster["manager_name"]
        manager.is_primary = roster["is_primary"]
        manager.streaming_slots = roster["streaming_slots"]

    for roster_group, field in (
        ("core", "core"),
        ("stream_candidate", "stream_candidates"),
    ):
        for sort_order, (player_id, player_name) in enumerate(roster[field]):
            player = session.get(Player, player_id)
            if player is None:
                session.add(Player(id=player_id, full_name=player_name))
                session.flush()

            entry = session.get(FantasyRosterEntry, (manager.id, player_id))
            if entry is None:
                entry = FantasyRosterEntry(
                    manager_id=manager.id,
                    player_id=player_id,
                    roster_group=roster_group,
                    sort_order=sort_order,
                )
                session.add(entry)
            else:
                entry.roster_group = roster_group
                entry.sort_order = sort_order


def main() -> None:
    with get_session_factory()() as session:
        league = session.scalar(
            select(FantasyLeague).where(FantasyLeague.slug == "local-fantasy-league")
        )
        if league is None:
            league = FantasyLeague(slug="local-fantasy-league", name="Fantasy League")
            session.add(league)
            session.flush()

        for roster in ROSTERS:
            seed_manager(session, league, roster)

        session.commit()
        for roster in ROSTERS:
            print(
                f"Seeded {roster['manager_name']}: {len(roster['core'])} players, "
                f"{roster['streaming_slots']} streaming spot(s), "
                f"{len(roster['stream_candidates'])} candidates."
            )


if __name__ == "__main__":
    main()
