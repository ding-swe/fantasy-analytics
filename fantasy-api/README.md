# Fantasy Analytics API

The backend API uses FastAPI and Python. The React UI lives in `../fantasy-ui`.

## Requirements

- Python 3.10 or newer

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

The first endpoint is `GET /api/players/{player_id}/games?limit=7`. It defaults to the current NBA season and returns up to seven recent regular-season games. For example, `GET /api/players/1630581/games?limit=7` returns Josh Giddey's player name, season, and game rows.

## Run the UI

In a second terminal, run the React app:

```powershell
cd ..\fantasy-ui
npm start
```

The UI calls `http://localhost:8000` by default. Set `REACT_APP_API_URL` before starting the UI to use a different API address.
