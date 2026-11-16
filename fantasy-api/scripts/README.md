# Offline data scripts

Scripts in this folder are manual tools. They are not imported by FastAPI and do not run when the app starts.

## Player game history backfill

`backfill_player_games.py` is the offline path for loading NBA game rows into the local PostgreSQL database. It shares fetching, inactive-player enrichment, and upsert logic with the `/api/sync` route. By default it fetches NBA data and prints a summary without writing to the database. Add `--apply` to enable database upserts.

Run it from `fantasy-api`:

```powershell
.venv\Scripts\python.exe .\scripts\backfill_player_games.py --season 2026-27
```

After reviewing the preview, run with `--apply` to write the data. Optional `--date-from MM/DD/YYYY` and `--date-to MM/DD/YYYY` arguments restrict the query window.

The database key for a stat line is `(player_id, game_id)`, so repeating a season or date-range import updates existing rows instead of duplicating them. The sync checks each returned game's inactive-player list and stores a zero-stat line for inactive players. It records date range and progress in `sync_runs` and advances the completed-through date only after a successful commit. A full-season run makes one box-score summary request per game, with retry delays if NBA Stats throttles or errors.
