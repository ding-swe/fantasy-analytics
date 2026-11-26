from dataclasses import dataclass
from threading import Lock
from time import monotonic
from xml.etree import ElementTree

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SyncRun
from app.schemas.team_comparisons import (
    MatchupTeam,
    ScoringCategory,
    TeamComparisonResponse,
    YahooMatchup,
)
from app.services.yahoo_sync import (
    FANTASY_URL,
    YahooSyncError,
    read_authorization,
    refresh_yahoo_access,
    yahoo_credentials,
)


CACHE_TTL_SECONDS = 30 * 60


@dataclass(frozen=True)
class CachedScoreboard:
    expires_at: float
    sync_revision: int | None
    scoreboard: TeamComparisonResponse


_scoreboard_cache: dict[tuple[str, str, int | None], CachedScoreboard] = {}
_cache_lock = Lock()


class MatchupWeekUnavailable(Exception):
    pass


def parse_scoreboard(
    content: bytes, league_key: str, requested_week: int | None = None
) -> TeamComparisonResponse:
    league = ElementTree.fromstring(content).find("{*}league")
    if league is None or league.findtext("{*}league_key") != league_key:
        raise YahooSyncError("Yahoo did not return the requested league.")

    start_week = int(league.findtext("{*}start_week", "0"))
    current_week = int(league.findtext("{*}current_week", "0"))
    if requested_week is not None and not start_week <= requested_week <= current_week:
        raise MatchupWeekUnavailable("Choose a week from the start of the league through the current week.")

    board = league.find("{*}scoreboard")
    if board is None:
        raise YahooSyncError("Yahoo did not return a league scoreboard.")
    week = int(board.findtext("{*}week", "0"))
    if not start_week <= week <= current_week or (requested_week is not None and week != requested_week):
        raise YahooSyncError("Yahoo returned a different matchup week than requested.")

    categories = [
        ScoringCategory(
            stat_id=stat.findtext("{*}stat_id", ""),
            name=stat.findtext("{*}name", ""),
            label=stat.findtext("{*}display_name") or stat.findtext("{*}name", ""),
            counts_toward_result=stat.findtext("{*}is_only_display_stat") != "1",
            higher_is_better=stat.findtext("{*}sort_order") != "0",
        )
        for stat in league.findall("{*}settings/{*}stat_categories/{*}stats/{*}stat")
        if stat.findtext("{*}enabled") == "1" and stat.findtext("{*}stat_id")
    ]

    matchups = []
    for match in board.findall("{*}matchups/{*}matchup"):
        teams = []
        for team in match.findall("{*}teams/{*}team"):
            team_key = team.findtext("{*}team_key", "")
            if not team_key:
                raise YahooSyncError("Yahoo returned a matchup team without its team key.")
            stats = {}
            for stat in team.findall("{*}team_stats/{*}stats/{*}stat"):
                stat_id, value = stat.findtext("{*}stat_id"), stat.findtext("{*}value")
                if stat_id and value:
                    stats[stat_id] = value
            teams.append(MatchupTeam(
                team_key=team_key,
                team_name=team.findtext("{*}name") or team_key,
                manager_name=team.findtext("{*}managers/{*}manager/{*}nickname") or None,
                is_my_team=team.findtext("{*}is_owned_by_current_login") == "1",
                points=team.findtext("{*}team_points/{*}total") or None,
                stats=stats,
            ))
        if not teams:
            continue

        winners = {}
        team_keys = {team.team_key for team in teams}
        for stat in match.findall("{*}stat_winners/{*}stat_winner"):
            stat_id, winner = stat.findtext("{*}stat_id"), stat.findtext("{*}winner_team_key")
            if stat_id and winner in team_keys:
                winners[stat_id] = winner
            elif stat_id and stat.findtext("{*}is_tied") == "1":
                winners[stat_id] = None

        matchups.append(YahooMatchup(
            status=match.findtext("{*}status", ""),
            week_start=match.findtext("{*}week_start") or None,
            week_end=match.findtext("{*}week_end") or None,
            winner_team_key=match.findtext("{*}winner_team_key") or None,
            is_tied=match.findtext("{*}is_tied") == "1",
            category_winners=winners,
            teams=teams,
        ))

    return TeamComparisonResponse(
        league_name=league.findtext("{*}name") or league_key,
        scoring_type=league.findtext("{*}scoring_type", ""),
        start_week=start_week,
        current_week=current_week,
        week=week,
        categories=categories,
        matchups=matchups,
    )


def get_team_comparisons(db: Session, week: int | None = None) -> TeamComparisonResponse:
    client_id, _ = yahoo_credentials()
    league_key, _ = read_authorization(client_id)
    key = (client_id, league_key, week)
    sync_revision = None
    if week is None:
        # The next request after Yahoo Sync should refresh the live scoreboard.
        with db.begin():
            sync_revision = db.scalar(
                select(SyncRun.id)
                .where(SyncRun.yahoo_status.in_(("succeeded", "unchanged")))
                .order_by(SyncRun.id.desc())
                .limit(1)
            )

    with _cache_lock:
        now = monotonic()
        cached = _scoreboard_cache.get(key)
        if cached and cached.expires_at > now and cached.sync_revision == sync_revision:
            return cached.scoreboard

        scoreboard = fetch_scoreboard(db, league_key, week)
        for stale_key in [
            entry_key for entry_key, entry in _scoreboard_cache.items()
            if entry.expires_at <= now
        ]:
            del _scoreboard_cache[stale_key]
        _scoreboard_cache[key] = CachedScoreboard(
            expires_at=monotonic() + CACHE_TTL_SECONDS,
            sync_revision=sync_revision,
            scoreboard=scoreboard,
        )
        return scoreboard


def fetch_scoreboard(db: Session, expected_league: str, week: int | None) -> TeamComparisonResponse:
    # Hold the database lock only through OAuth refresh and credential rotation.
    with db.begin():
        league_key, access_token = refresh_yahoo_access(db)
    if league_key != expected_league:
        raise YahooSyncError("Yahoo authorization changed. Reload Team Comparisons.")
    path = f"league/{league_key};out=settings,scoreboard"
    if week is not None:
        path = f"league/{league_key};out=settings/scoreboard;week={week}"
    try:
        response = requests.get(
            FANTASY_URL + path,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise YahooSyncError("Could not reach Yahoo's matchup scoreboard.") from None
    if week is not None and response.status_code in (400, 404):
        raise MatchupWeekUnavailable("Yahoo has no scoreboard for that week.")
    if response.status_code != 200:
        raise YahooSyncError(f"Yahoo's matchup scoreboard returned HTTP {response.status_code}.")
    try:
        return parse_scoreboard(response.content, league_key, week)
    except (ElementTree.ParseError, ValueError):
        raise YahooSyncError("Yahoo returned an unreadable matchup scoreboard.") from None
