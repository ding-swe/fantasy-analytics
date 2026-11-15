from nba_api.stats.endpoints import PlayerGameLogs


def fetch_player_game_logs(
    player_id: int,
    season: str,
    limit: int,
) -> list[dict[str, object]]:
    response = PlayerGameLogs(
        player_id_nullable=player_id,
        season_nullable=season,
        season_type_nullable="Regular Season",
        last_n_games_nullable=limit,
        timeout=20,
    )
    return response.player_game_logs.get_data_frame().to_dict(orient="records")
