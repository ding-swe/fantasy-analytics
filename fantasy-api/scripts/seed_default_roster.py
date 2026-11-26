"""Seed the local fantasy league and classify each team's bottom two players as stream candidates."""

from collections import defaultdict
from typing import Any
import unicodedata
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_session_factory
from app.db.models import (
    FantasyLeague,
    FantasyManager,
    FantasyRosterEntry,
    Game,
    Player,
    PlayerGameStats,
)
from app.services.free_agents import GAMES_TO_AVERAGE, current_nba_season


ROSTER_NAME_ALIASES = {
    "Nemias Queta": "Neemias Queta",
    "Scotty Barnes": "Scottie Barnes",
    "Dennis Jenkins": "Daniss Jenkins",
    "Jalen Brown": "Jaylen Brown",
    "Sandro Mamukalashvili": "Sandro Mamukelashvili",
    "AJ Dybonsta": "AJ Dybantsa",
    "Nikola Jokic": "Nikola Jokić",
    "Kon Knupple": "Kon Knueppel",
    "Steph Curry": "Stephen Curry",
    "Jimmy Butler": "Jimmy Butler III",
    "Colin Murray-Boyles": "Collin Murray-Boyles",
    "Adeemara": "Aday Mara",
    "Nikhil Alexander-Walker": "Nickeil Alexander-Walker",
    "Norm Powell": "Norman Powell",
    "Darius Acuff": "Darius Acuff Jr.",
    "Derek Queen": "Derik Queen",
    "Luka Doncic": "Luka Dončić",
    "Cedric Howard": "Cedric Coward",
    "Brandon Podziemski": "Brandin Podziemski",
    "Vijay Edgecomb": "VJ Edgecombe",
    "Brayden Buryes": "Brayden Burries",
    "Kaihson George": "Kyshawn George",
    "Nick Claxton": "Nic Claxton",
    "Peyton Pritchard": "Payton Pritchard",
    "Darren Peterson": "Darryn Peterson",
    "Cam Boozer": "Cameron Boozer",
}

# Brandon Ingram is on Kyle's roster but has no player row or game logs in the
# local current-season import yet. Keep his known NBA ID so the roster is complete.
PLAYER_ID_OVERRIDES = {
    "Brandon Ingram": 1627742,
    "Jimmy Butler III": 202710,
}

ROSTERS = [
    {
        "manager_name": "Me",
        "team_name": "My Team",
        "is_primary": True,
        "players": [
            "Josh Giddey",
            "OG Anunoby",
            "Jabari Smith Jr.",
            "Victor Wembanyama",
            "Rudy Gobert",
            "Jeremiah Fears",
            "Paul George",
            "Trae Young",
            "Devin Booker",
            "Derrick White",
            "Jalen Smith",
            "Aaron Wiggins",
            "Jimmy Butler",
            "Jrue Holiday",
            "Zaccharie Risacher",
        ],
        "stream_candidates": ["Jrue Holiday", "Zaccharie Risacher"],
    },
    {
        "manager_name": "Nancy",
        "team_name": "Nancy's Team",
        "is_primary": False,
        "players": [
            "Joel Embiid",
            "Ja Morant",
            "Trey Murphy III",
            "Giannis Antetokounmpo",
            "Yaxel Lendeborg",
            "Kel'el Ware",
            "Dyson Daniels",
            "Ace Bailey",
            "Stephon Castle",
            "Cooper Flagg",
            "CJ McCollum",
            "Alperen Sengun",
            "Nolan Traore",
            "Santi Aldama",
            "Kelly Oubre Jr.",
        ],
        "stream_candidates": ["Nolan Traore", "Santi Aldama", "Kelly Oubre Jr."],
    },
    {
        "manager_name": "Mike",
        "team_name": "Fahhhbonis",
        "is_primary": False,
        "players": [
            "De'Aaron Fox",
            "Donovan Mitchell",
            "Kyrie Irving",
            "Grayson Allen",
            "Jaime Jaquez Jr.",
            "Cameron Johnson",
            "Day'Ron Sharpe",
            "Domantas Sabonis",
            "Jaden McDaniels",
            "Ajay Mitchell",
            "Pelle Larsson",
            "Christian Braun",
            "Wendell Carter Jr.",
            "Lauri Markkanen",
            "Anthony Edwards",
            "Dejounte Murray",
        ],
    },
    {
        "manager_name": "Sonia",
        "team_name": "Sonia's Superb Team",
        "is_primary": False,
        "players": [
            "Coby White",
            "Tyler Herro",
            "Shai Gilgeous-Alexander",
            "Ausar Thompson",
            "Saddiq Bey",
            "Anthony Davis",
            "Moussa Diabate",
            "Brook Lopez",
            "Immanuel Quickley",
            "Nemias Queta",
            "Ayo Dosunmu",
            "Jamal Murray",
            "Donovan Clingan",
            "Michael Porter Jr.",
            "Evan Mobley",
        ],
    },
    {
        "manager_name": "Kyle",
        "team_name": "Ky Jerome",
        "is_primary": False,
        "players": [
            "Davion Mitchell",
            "Keyonte George",
            "RJ Barrett",
            "Jalen Johnson",
            "Julius Randle",
            "Aaron Gordon",
            "P.J. Washington",
            "Mo Bamba",
            "Pascal Siakam",
            "Ty Jerome",
            "Bam Adebayo",
            "Anthony Black",
            "Deni Avdija",
            "Caleb Wilson",
            "Brandon Ingram",
            "Scotty Barnes",
        ],
    },
    {
        "manager_name": "Claudia",
        "team_name": "Clau Jerome",
        "is_primary": False,
        "players": [
            "Dennis Jenkins",
            "Andrew Nembhard",
            "Damian Lillard",
            "Jalen Brown",
            "Naz Reid",
            "Toumani Camara",
            "Isaiah Hartenstein",
            "Sandro Mamukalashvili",
            "AJ Dybonsta",
            "Fred VanVleet",
            "Nikola Jokic",
            "Duncan Robinson",
            "Paul Reed",
            "Austin Reaves",
            "Kon Knupple",
            "Steph Curry",
        ],
    },
    {
        "manager_name": "Jeff",
        "team_name": "Jeffrey's Cool Team",
        "is_primary": False,
        "players": [
            "Jared McCain",
            "Nikhil Alexander-Walker",
            "Matisse Thybulle",
            "Josh Hart",
            "Jayson Tatum",
            "Colin Murray-Boyles",
            "Adeemara",
            "Karl-Anthony Towns",
            "Walker Kessler",
            "Darius Garland",
            "Franz Wagner",
            "Norm Powell",
            "Yves Missi",
            "James Harden",
        ],
    },
    {
        "manager_name": "Karyn",
        "team_name": "Karyn's Notable Team",
        "is_primary": False,
        "players": [
            "Darius Acuff",
            "Amen Thompson",
            "Jalen Brunson",
            "Brandon Miller",
            "Derek Queen",
            "Zion Williamson",
            "Jaren Jackson Jr.",
            "Alex Sarr",
            "Brandon Podziemski",
            "Luka Doncic",
            "Cedric Howard",
            "Moritz Wagner",
            "Jarrett Allen",
            "Paolo Banchero",
        ],
    },
    {
        "manager_name": "Mary",
        "team_name": "Dabonis",
        "is_primary": False,
        "players": [
            "Vijay Edgecomb",
            "Brayden Buryes",
            "Tyrese Maxey",
            "Zach LaVine",
            "Kaihson George",
            "Desmond Bane",
            "Nick Claxton",
            "Precious Achiuwa",
            "Dylan Harper",
            "Jakob Poeltl",
            "Jonathan Kuminga",
            "Isaiah Stewart",
            "John Collins",
            "Tyrese Haliburton",
            "Chet Holmgren",
            "Kawhi Leonard",
        ],
    },
    {
        "manager_name": "Clement",
        "team_name": "Clement's Cool Team",
        "is_primary": False,
        "players": [
            "Peyton Pritchard",
            "Jalen Suggs",
            "LaMelo Ball",
            "Kevin Durant",
            "Miles Bridges",
            "LeBron James",
            "Jalen Duren",
            "Onyeka Okongwu",
            "Jalen Green",
            "Darren Peterson",
            "Cade Cunningham",
            "Cam Boozer",
            "Matas Buzelis",
        ],
    },
]


def normalize_player_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    unaccented = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]", "", unaccented.casefold())


def resolve_players(session: Session) -> dict[str, Player]:
    players = session.scalars(select(Player)).all()
    players_by_name: dict[str, list[Player]] = defaultdict(list)
    players_by_id = {player.id: player for player in players}
    for player in players:
        canonical_name = ROSTER_NAME_ALIASES.get(player.full_name, player.full_name)
        players_by_name[normalize_player_name(canonical_name)].append(player)

    resolved: dict[str, Player] = {}
    requested_names = {
        ROSTER_NAME_ALIASES.get(name, name)
        for roster in ROSTERS
        for name in roster["players"]
    }
    for name in sorted(requested_names):
        normalized = normalize_player_name(name)
        matches = players_by_name.get(normalized, [])
        if len(matches) == 1:
            resolved[name] = matches[0]
            continue
        if len(matches) > 1:
            raise ValueError(f"Multiple player records match {name!r}.")

        player_id = PLAYER_ID_OVERRIDES.get(name)
        if player_id is None:
            raise ValueError(f"No NBA player record found for {name!r}.")
        player = players_by_id.get(player_id)
        if player is not None and normalize_player_name(player.full_name) != normalized:
            raise ValueError(
                f"Player ID {player_id} is already assigned to {player.full_name!r}."
            )
        if player is None:
            player = Player(id=player_id, full_name=name)
            session.add(player)
            session.flush()
            players_by_id[player_id] = player
            players_by_name[normalized].append(player)
        resolved[name] = player

    return resolved


def get_recent_fantasy_averages(session: Session) -> dict[int, float | None]:
    season = current_nba_season()
    recent_points: dict[int, list[float | None]] = defaultdict(list)
    rows = session.execute(
        select(
            PlayerGameStats.player_id,
            PlayerGameStats.nba_fantasy_points,
        )
        .join(Game, Game.id == PlayerGameStats.game_id)
        .where(Game.season == season)
        .order_by(
            PlayerGameStats.player_id,
            Game.game_date.desc(),
            Game.id.desc(),
        )
    ).all()

    for player_id, fantasy_points in rows:
        player_games = recent_points[player_id]
        if len(player_games) < GAMES_TO_AVERAGE:
            player_games.append(
                float(fantasy_points) if fantasy_points is not None else None
            )

    return {
        player_id: (
            sum(value for value in points if value is not None)
            / sum(value is not None for value in points)
            if any(value is not None for value in points)
            else None
        )
        for player_id, points in recent_points.items()
    }


def classify_roster(
    roster: dict[str, Any],
    resolved_players: dict[str, Player],
    averages: dict[int, float | None],
) -> tuple[list[tuple[Player, str]], list[tuple[Player, str, float | None]]]:
    roster_players = [
        (
            resolved_players[ROSTER_NAME_ALIASES.get(name, name)],
            name,
        )
        for name in roster["players"]
    ]
    ranked = sorted(
        roster_players,
        key=lambda item: (
            averages.get(item[0].id) is not None,
            averages.get(item[0].id)
            if averages.get(item[0].id) is not None
            else float("-inf"),
            item[1].casefold(),
        ),
    )
    explicit_candidates = roster.get("stream_candidates")
    if explicit_candidates is not None:
        candidate_names = {
            normalize_player_name(ROSTER_NAME_ALIASES.get(name, name))
            for name in explicit_candidates
        }
        roster_names = {normalize_player_name(name) for _, name in roster_players}
        missing_candidates = candidate_names - roster_names
        if missing_candidates:
            raise ValueError(
                f"Stream candidates are not on {roster['team_name']}: "
                f"{', '.join(sorted(missing_candidates))}"
            )
        candidate_ids = {
            player.id
            for player, name in roster_players
            if normalize_player_name(name) in candidate_names
        }
    else:
        candidate_ids = {player.id for player, _ in ranked[:2]}
    assignments = [
        (
            player,
            "stream_candidate" if player.id in candidate_ids else "core",
        )
        for player, _ in roster_players
    ]
    candidates = [
        (player, name, averages.get(player.id))
        for player, name in roster_players
        if player.id in candidate_ids
    ]
    return assignments, candidates


def seed_manager(
    session: Session,
    league: FantasyLeague,
    roster: dict[str, Any],
    assignments: list[tuple[Player, str]],
) -> None:
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
            streaming_slots=1,
        )
        session.add(manager)
        session.flush()
    else:
        manager.manager_name = roster["manager_name"]
        manager.is_primary = roster["is_primary"]
        manager.streaming_slots = 1

    desired_player_ids = {player.id for player, _ in assignments}
    existing_entries = session.scalars(
        select(FantasyRosterEntry).where(
            FantasyRosterEntry.manager_id == manager.id
        )
    ).all()
    for entry in existing_entries:
        if entry.player_id not in desired_player_ids:
            session.delete(entry)

    for sort_order, (player, roster_group) in enumerate(assignments):
        entry = session.get(FantasyRosterEntry, (manager.id, player.id))
        if entry is None:
            entry = FantasyRosterEntry(
                manager_id=manager.id,
                player_id=player.id,
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

        resolved_players = resolve_players(session)
        averages = get_recent_fantasy_averages(session)
        reports = []
        for roster in ROSTERS:
            assignments, candidates = classify_roster(
                roster, resolved_players, averages
            )
            seed_manager(session, league, roster, assignments)
            reports.append((roster, assignments, candidates))

        session.commit()

    season = current_nba_season()
    for roster, assignments, candidates in reports:
        core_count = sum(group == "core" for _, group in assignments)
        candidate_names = ", ".join(
            f"{name} ({average:.1f})" if average is not None else f"{name} (no games)"
        for _, name, average in candidates
        )
        print(
            f"Seeded {roster['team_name']}: {core_count} core, "
            f"{len(candidates)} stream candidates using {season} last-"
            f"{GAMES_TO_AVERAGE}-game fantasy averages: {candidate_names}."
        )


if __name__ == "__main__":
    main()
