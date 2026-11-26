from sqlalchemy import text

from app.db.base import Base
from app.db.database import get_engine
from app.db import models  # noqa: F401 - registers model tables on Base.metadata


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE fantasy_managers "
                "ADD COLUMN IF NOT EXISTS streaming_slots INTEGER NOT NULL DEFAULT 1"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE player_game_stats "
                "ADD COLUMN IF NOT EXISTS opponent_team_abbreviation VARCHAR(5)"
            )
        )
        connection.execute(text("ALTER TABLE sync_runs ADD COLUMN IF NOT EXISTS season VARCHAR(7)"))
        connection.execute(text("ALTER TABLE sync_runs ADD COLUMN IF NOT EXISTS date_from DATE"))
        connection.execute(text("ALTER TABLE sync_runs ADD COLUMN IF NOT EXISTS date_to DATE"))
        connection.execute(text("ALTER TABLE sync_runs ADD COLUMN IF NOT EXISTS yahoo_status VARCHAR(24)"))
        connection.execute(text("ALTER TABLE sync_runs ADD COLUMN IF NOT EXISTS yahoo_error_message VARCHAR(2000)"))
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_fantasy_roster_entries_player_id "
                "ON fantasy_roster_entries (player_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_player_game_stats_opponent_team_abbreviation "
                "ON player_game_stats (opponent_team_abbreviation)"
            )
        )
        connection.execute(
            text(
                """
                UPDATE player_game_stats AS stats
                SET opponent_team_abbreviation = CASE
                    WHEN stats.team_abbreviation = parts.matchup_parts[1]
                        THEN parts.matchup_parts[3]
                    WHEN stats.team_abbreviation = parts.matchup_parts[3]
                        THEN parts.matchup_parts[1]
                END
                FROM (
                    SELECT id, regexp_match(
                        matchup,
                        '^([A-Z]{2,3})[[:space:]]+(@|vs\\.)[[:space:]]+([A-Z]{2,3})$'
                    ) AS matchup_parts
                    FROM player_game_stats
                    WHERE opponent_team_abbreviation IS NULL
                      AND matchup IS NOT NULL
                ) AS parts
                WHERE stats.id = parts.id
                  AND parts.matchup_parts IS NOT NULL
                """
            )
        )
    print("Database tables are ready.")


if __name__ == "__main__":
    main()
