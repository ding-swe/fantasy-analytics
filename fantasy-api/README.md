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

- `app/data/nba_stats_client.py` calls the NBA stats endpoint through `nba_api`.
- `app/services/player_stats.py` maps the source fields into our response shape.
- `app/api/routes/player_stats.py` exposes the result over HTTP.
- `app/schemas/player_stats.py` defines the JSON response contract.

## Local PostgreSQL database

1. Install PostgreSQL and create a local database and application user. Keep the application user's password out of source control.
2. Copy `.env.example` to `.env` and set `DATABASE_URL` to the local connection string.
3. Install the backend dependencies with `python -m pip install -e .`.
4. Create the initial tables with `python -m app.db.init_db`.

The initial schema stores players, games, per-player game statistics, and sync run history. The database is the durable source; averages can be calculated from the game rows. The initialization command creates missing tables and does not delete existing data.

The PostgreSQL service stores its data on disk in the data directory selected during installation. Stopping the service does not delete the database. Back up data with a PostgreSQL dump rather than copying the live data directory while the service is running.

The first endpoint is `GET /api/players/{player_id}/games?limit=7`. It defaults to the current NBA season and returns up to seven recent regular-season games. For example, `GET /api/players/1630581/games?limit=7` returns Josh Giddey's player name, season, and game rows.

## Run the UI

In a second terminal, run the React app:

```powershell
cd ..\fantasy-ui
npm start
```

The UI calls `http://localhost:8000` by default. Set `REACT_APP_API_URL` before starting the UI to use a different API address.
