import json
import re
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

import keyring
import requests
from dotenv import dotenv_values
from keyring.errors import KeyringError
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_session_factory
from app.db.models import SyncRun
from app.services.yahoo_rosters import YahooRosterImport, save_snapshot


OAUTH_URL = "https://api.login.yahoo.com/oauth2/"
FANTASY_URL = "https://fantasysports.yahooapis.com/fantasy/v2/"
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
KEYRING_SERVICE = "Basketbase Yahoo Fantasy"
AUTHORIZE_HINT = "Run the Yahoo roster importer once to authorize Sync."


class YahooSyncError(Exception):
    pass


class YahooAuthorizationRequired(YahooSyncError):
    pass


def yahoo_credentials() -> tuple[str, str]:
    settings = dotenv_values(ENV_FILE, interpolate=False)
    client_id = settings.get("YAHOO_CLIENT_ID")
    client_secret = settings.get("YAHOO_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise YahooAuthorizationRequired("Set the Yahoo client ID and secret in the backend .env first.")
    return client_id, client_secret


def lock_yahoo_authorization(db: Session) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('basketbase:yahoo-sync', 0))"))


def store_authorization(client_id: str, league_key: str, refresh_token: str) -> None:
    try:
        keyring.set_password(
            KEYRING_SERVICE, client_id,
            json.dumps({"league_key": league_key, "refresh_token": refresh_token}),
        )
    except KeyringError:
        raise YahooSyncError("Could not write Yahoo authorization to the system credential store.") from None


def read_authorization(client_id: str) -> tuple[str, str]:
    try:
        saved = keyring.get_password(KEYRING_SERVICE, client_id)
    except KeyringError:
        raise YahooSyncError("Could not read the system credential store for Yahoo Sync.") from None
    if saved:
        try:
            data = json.loads(saved)
            league_key, refresh_token = data["league_key"], data["refresh_token"]
            if re.fullmatch(r"\d+\.l\.\d+", league_key) and isinstance(refresh_token, str) and refresh_token:
                return league_key, refresh_token
        except (KeyError, TypeError, ValueError):
            pass
    raise YahooAuthorizationRequired(AUTHORIZE_HINT)


def request_tokens(credentials: tuple[str, str], grant_type: str, **grant) -> tuple[str, str | None]:
    try:
        response = requests.post(
            OAUTH_URL + "get_token",
            auth=credentials,
            data={"grant_type": grant_type, "redirect_uri": "oob", **grant},
            timeout=30,
            allow_redirects=False,
        )
        if response.status_code != 200:
            try:
                error = response.json().get("error")
            except (AttributeError, ValueError):
                error = None
            if grant_type == "refresh_token" and error in ("invalid_grant", "invalid_client"):
                raise YahooAuthorizationRequired(f"Yahoo authorization expired or changed. {AUTHORIZE_HINT}")
            if error == "invalid_grant":
                raise YahooSyncError(
                    "Yahoo OAuth rejected the authorization code (invalid_grant). "
                    "Run the importer again and use the new code from Yahoo."
                )
            if error == "invalid_client":
                raise YahooSyncError("Yahoo OAuth rejected the client credentials (invalid_client).")
            known_errors = ("invalid_request", "invalid_scope", "unauthorized_client", "unsupported_grant_type")
            detail = f" ({error})" if error in known_errors else ""
            raise YahooSyncError(f"Yahoo OAuth returned HTTP {response.status_code}{detail}.")
        payload = response.json()
        access_token, refresh_token = payload["access_token"], payload.get("refresh_token")
        if not isinstance(access_token, str) or not access_token:
            raise YahooSyncError("Yahoo did not return an access token.")
        if refresh_token is not None and (not isinstance(refresh_token, str) or not refresh_token):
            raise YahooSyncError("Yahoo returned an invalid refresh token.")
        return access_token, refresh_token
    except (requests.RequestException, ValueError, TypeError, KeyError):
        raise YahooSyncError("Could not complete Yahoo OAuth.") from None


def parse_rosters(content: bytes, league_key: str) -> YahooRosterImport:
    league = ElementTree.fromstring(content).find("{*}league")
    if league is None or league.findtext("{*}league_key") != league_key:
        raise YahooSyncError("Yahoo did not return the requested league.")

    teams = []
    for team in league.findall("{*}teams/{*}team"):
        roster = team.find("{*}roster/{*}players")
        if roster is None:
            raise YahooSyncError("Yahoo returned a team without its roster. Nothing was saved.")
        teams.append({
            "team_key": team.findtext("{*}team_key", ""),
            "team_name": team.findtext("{*}name", ""),
            "players": [
                {
                    "player_key": player.findtext("{*}player_key", ""),
                    "name": player.findtext("{*}name/{*}full", ""),
                }
                for player in roster.findall("{*}player")
            ],
        })
    return YahooRosterImport.model_validate({
        "league_key": league_key,
        "league_name": league.findtext("{*}name", ""),
        "captured_at": datetime.now(timezone.utc),
        "expected_team_count": league.findtext("{*}num_teams"),
        "teams": teams,
    })


def fetch_rosters(league_key: str, access_token: str) -> YahooRosterImport:
    try:
        response = requests.get(
            FANTASY_URL + f"league/{league_key}/teams/roster",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
            allow_redirects=False,
        )
        if response.status_code != 200:
            raise YahooSyncError(f"Yahoo Fantasy API returned HTTP {response.status_code}. Nothing was saved.")
        return parse_rosters(response.content, league_key)
    except requests.RequestException:
        raise YahooSyncError("Could not reach the Yahoo Fantasy API.") from None
    except (ElementTree.ParseError, ValidationError):
        raise YahooSyncError("Yahoo returned an incomplete league roster. Nothing was saved.") from None


def refresh_rosters_for_run(run_id: int) -> None:
    factory = get_session_factory()
    try:
        with factory.begin() as db:
            lock_yahoo_authorization(db)
            credentials = yahoo_credentials()
            league_key, refresh_token = read_authorization(credentials[0])
            access_token, rotated_token = request_tokens(
                credentials, "refresh_token", refresh_token=refresh_token
            )
            if rotated_token and rotated_token != refresh_token:
                store_authorization(credentials[0], league_key, rotated_token)
            snapshot = fetch_rosters(league_key, access_token)
            saved = save_snapshot(db, snapshot)
            run = db.get(SyncRun, run_id)
            if run is not None:
                run.yahoo_status = "succeeded" if saved else "unchanged"
        return
    except YahooAuthorizationRequired as error:
        status, message = "needs_authorization", str(error)
    except YahooSyncError as error:
        status, message = "failed", str(error)
    except SQLAlchemyError:
        status, message = "failed", "Could not save Yahoo rosters to PostgreSQL."

    with factory.begin() as db:
        run = db.get(SyncRun, run_id)
        if run is not None:
            run.yahoo_status = status
            run.yahoo_error_message = message
