# Fantasy Analytics API

The backend API uses FastAPI and Python. The React UI lives in `../fantasy-ui`.

## Requirements

- Python 3.10 or newer
- PostgreSQL 16 or newer

## Run locally

From this directory, create and activate a virtual environment, then install the project:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
fastapi dev app/main.py
```

The API is available at <http://127.0.0.1:8000>. Interactive API docs are at <http://127.0.0.1:8000/docs>.

## Data path

- `app/services/player_stats.py` queries the local PostgreSQL database and maps rows into our response shape.
- `app/api/routes/player_stats.py` exposes the result over HTTP.
- `app/schemas/player_stats.py` defines the JSON response contract.
- `scripts/backfill_player_games.py` is the manual NBA stats importer; the API does not call NBA stats directly.

## Local PostgreSQL database

1. Install PostgreSQL and create a local database and application user. Keep the application user's password out of source control.
2. Copy `.env.example` to `.env` and set `DATABASE_URL` to the local connection string.
3. Install the backend dependencies with `python -m pip install -e .`.
4. Create the initial tables with `python -m app.db.init_db`.
5. Seed the prototype league's initial managers and rosters with `python .\scripts\seed_default_roster.py`.

The schema stores NBA players, games, per-player game statistics, sync history, fantasy leagues, managers, streaming-slot counts, and roster entries. Player-game rows keep the original matchup and a separately indexed opponent team abbreviation for opponent-based analysis. Database initialization backfills the opponent abbreviation from existing matchup values, and future imports populate it as each row is stored. The database is the durable source; averages can be calculated from the game rows. The initialization command creates missing tables and applies small additive schema updates. The seed script sets up a local example league and is safe to rerun.

The PostgreSQL service stores its data on disk in the data directory selected during installation. Stopping the service does not delete the database. Back up data with a PostgreSQL dump rather than copying the live data directory while the service is running.

`GET /api/players/{player_id}/games?limit=7` reads up to seven recent games from PostgreSQL for the current season. `GET /api/rosters/current` returns the primary fantasy manager's core roster and stream-slot candidates. NBA stats are imported separately with `scripts/backfill_player_games.py`; the API does not call NBA stats directly.

## Run the UI

In a second terminal, run the React app:

```powershell
cd ..\fantasy-ui
npm start
```

The UI calls `http://localhost:8000` by default. Set `REACT_APP_API_URL` before starting the UI to use a different API address.
