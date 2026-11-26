"""Fetch a complete Yahoo league roster and save its membership to PostgreSQL."""

import argparse
import getpass
import re
import warnings
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree

import requests
from dotenv import dotenv_values
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_session_factory
from app.services.yahoo_rosters import YahooRosterImport, save_snapshot


OAUTH_URL = "https://api.login.yahoo.com/oauth2/"
FANTASY_URL = "https://fantasysports.yahooapis.com/fantasy/v2/"
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def authorize() -> str:
    settings = dotenv_values(ENV_FILE, interpolate=False)
    client_id = settings.get("YAHOO_CLIENT_ID")
    client_secret = settings.get("YAHOO_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("Fill in YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET in fantasy-api/.env.")

    auth_url = OAUTH_URL + "request_auth?" + urlencode({
        "client_id": client_id,
        "redirect_uri": "oob",
        "response_type": "code",
        "scope": "fspt-r",
    })
    if not webbrowser.open(auth_url):
        print("Open this Yahoo authorization URL in your browser:", auth_url)
    print("Approve Yahoo access, then return to this terminal.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        code = getpass.getpass("Yahoo authorization code (hidden): ").strip()
    if not code:
        raise SystemExit("No Yahoo authorization code was entered.")

    response = requests.post(
        OAUTH_URL + "get_token",
        auth=(client_id, client_secret),
        data={"grant_type": "authorization_code", "redirect_uri": "oob", "code": code},
        timeout=30,
        allow_redirects=False,
    )
    if response.status_code != 200:
        raise SystemExit(f"Yahoo OAuth token exchange returned HTTP {response.status_code}.")
    return response.json()["access_token"]


def parse_rosters(content: bytes, league_key: str) -> YahooRosterImport:
    league = ElementTree.fromstring(content).find("{*}league")
    if league is None or league.findtext("{*}league_key") != league_key:
        raise SystemExit("Yahoo did not return the requested league.")

    teams = []
    for team in league.findall("{*}teams/{*}team"):
        roster = team.find("{*}roster/{*}players")
        if roster is None:
            raise SystemExit("Yahoo returned a team without its roster. Nothing was saved.")
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("league_key", help="Yahoo league key, such as 123.l.456789.")
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.l\.\d+", args.league_key):
        parser.error("Enter a Yahoo league key in GAME.l.LEAGUE format.")

    token = authorize()
    response = requests.get(
        FANTASY_URL + f"league/{args.league_key}/teams/roster",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
        allow_redirects=False,
    )
    if response.status_code != 200:
        raise SystemExit(f"Yahoo Fantasy API returned HTTP {response.status_code}. Nothing was saved.")
    snapshot = parse_rosters(response.content, args.league_key)
    with get_session_factory().begin() as db:
        inserted = save_snapshot(db, snapshot)
    if inserted:
        print(f"Saved rosters for {len(snapshot.teams)} teams to PostgreSQL.")
    else:
        print("The roster membership is already saved. No new snapshot was created.")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, ElementTree.ParseError, ValidationError,
            ValueError, KeyError, getpass.GetPassWarning, EOFError):
        raise SystemExit("Could not read a complete Yahoo roster response. Nothing was saved.") from None
    except (SQLAlchemyError, RuntimeError, ImportError):
        raise SystemExit("Could not save to PostgreSQL. Check that it is running and the API database is initialized.") from None
