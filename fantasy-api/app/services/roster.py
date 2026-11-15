from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FantasyLeague, FantasyManager, FantasyRosterEntry, Player
from app.schemas.roster import (
    CurrentRosterResponse,
    RosterManagerListResponse,
    RosterManagerOption,
    RosterPlayer,
)


def get_roster_managers(db: Session) -> RosterManagerListResponse:
    managers = db.scalars(
        select(FantasyManager)
        .join(FantasyLeague, FantasyLeague.id == FantasyManager.league_id)
        .order_by(FantasyLeague.name, FantasyManager.team_name)
    ).all()
    return RosterManagerListResponse(
        managers=[
            RosterManagerOption(
                manager_id=manager.id,
                manager_name=manager.manager_name,
                team_name=manager.team_name,
                is_primary=manager.is_primary,
            )
            for manager in managers
        ],
        default_manager_id=next(
            (manager.id for manager in managers if manager.is_primary), None
        ),
    )


def get_current_roster(db: Session) -> CurrentRosterResponse | None:
    manager_id = db.scalar(
        select(FantasyManager.id).where(FantasyManager.is_primary.is_(True)).limit(1)
    )
    if manager_id is None:
        return None
    return get_manager_roster(manager_id, db)


def get_manager_roster(
    manager_id: int, db: Session
) -> CurrentRosterResponse | None:
    manager_row = db.execute(
        select(FantasyManager, FantasyLeague)
        .join(FantasyLeague, FantasyLeague.id == FantasyManager.league_id)
        .where(FantasyManager.id == manager_id)
        .limit(1)
    ).first()
    if manager_row is None:
        return None

    manager, _league = manager_row
    entries = db.execute(
        select(FantasyRosterEntry.roster_group, Player.id, Player.full_name)
        .join(Player, Player.id == FantasyRosterEntry.player_id)
        .where(FantasyRosterEntry.manager_id == manager.id)
        .order_by(FantasyRosterEntry.sort_order, Player.full_name)
    ).all()

    core_players = [
        RosterPlayer(player_id=player_id, name=full_name)
        for group, player_id, full_name in entries
        if group == "core"
    ]
    stream_slot_candidates = [
        RosterPlayer(player_id=player_id, name=full_name)
        for group, player_id, full_name in entries
        if group == "stream_candidate"
    ]

    return CurrentRosterResponse(
        manager_id=manager.id,
        manager_name=manager.manager_name,
        team_name=manager.team_name,
        streaming_slots=manager.streaming_slots,
        core_players=core_players,
        stream_slot_candidates=stream_slot_candidates,
    )
