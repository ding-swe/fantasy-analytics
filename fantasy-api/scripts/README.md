# Offline data scripts

Scripts in this folder are manual tools. They are not imported by FastAPI and do not run when the app starts.

## Player game history backfill

`backfill_player_games.py` is a manual first iteration for loading NBA game rows into the local PostgreSQL database. By default it fetches the current regular season and prints a summary without writing to the database. Add `--apply` to enable database upserts. It is not imported by FastAPI and is never run when the app starts.

Run it from `fantasy-api`:

```powershell
.venv\Scripts\python.exe .\scripts\backfill_player_games.py --season 2026-27
```

After reviewing the preview, run with `--apply` to write the data. Optional `--date-from MM/DD/YYYY` and `--date-to MM/DD/YYYY` arguments restrict the query window.

The database key for a stat line is `(player_id, game_id)`, so repeating a season or date-range import updates existing rows instead of duplicating them. The script records progress in `sync_runs` and advances the completed-through date only after a successful commit.
