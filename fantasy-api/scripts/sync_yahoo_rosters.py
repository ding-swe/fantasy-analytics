"""Authorize Yahoo roster Sync and save the first league snapshot."""

import argparse
import getpass
import re
import warnings
import webbrowser
from urllib.parse import urlencode

from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_session_factory
from app.services.yahoo_rosters import save_snapshot
from app.services.yahoo_sync import (
    OAUTH_URL,
    YahooSyncError,
    fetch_rosters,
    lock_yahoo_authorization,
    request_tokens,
    store_authorization,
    yahoo_credentials,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("league_key", help="Yahoo league key, such as 123.l.456789.")
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.l\.\d+", args.league_key):
        parser.error("Enter a Yahoo league key in GAME.l.LEAGUE format.")

    credentials = yahoo_credentials()
    auth_url = OAUTH_URL + "request_auth?" + urlencode({
        "client_id": credentials[0],
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

    with get_session_factory().begin() as db:
        lock_yahoo_authorization(db)
        access_token, refresh_token = request_tokens(credentials, "authorization_code", code=code)
        if not refresh_token:
            raise YahooSyncError("Yahoo did not issue a refresh token. Reauthorize to enable Sync.")
        snapshot = fetch_rosters(args.league_key, access_token)
        store_authorization(credentials[0], args.league_key, refresh_token)
        inserted = save_snapshot(db, snapshot)

    if inserted:
        print(f"Saved rosters for {len(snapshot.teams)} teams to PostgreSQL.")
    else:
        print("The roster membership is already saved.")
    print("Yahoo authorization saved in the system credential store. The app's Sync button can now refresh rosters.")


if __name__ == "__main__":
    try:
        main()
    except YahooSyncError as error:
        raise SystemExit(str(error)) from None
    except (getpass.GetPassWarning, EOFError):
        raise SystemExit("Enter the Yahoo code in an interactive terminal.") from None
    except (SQLAlchemyError, RuntimeError, ImportError):
        raise SystemExit("Could not save to PostgreSQL. Check that it is running and initialized.") from None
