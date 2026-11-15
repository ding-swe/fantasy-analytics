export interface PlayerGame {
  game_id: string;
  game_date: string;
  matchup: string;
  result: string | null;
  minutes: string | number | null;
  field_goals_made: number | null;
  field_goals_attempted: number | null;
  free_throws_made: number | null;
  free_throws_attempted: number | null;
  points: number | null;
  rebounds: number | null;
  assists: number | null;
  steals: number | null;
  blocks: number | null;
  turnovers: number | null;
  three_pointers_made: number | null;
  fantasy_points: number | null;
}

export interface PlayerGameLogResponse {
  player_id: number;
  player_name: string | null;
  season: string;
  games: PlayerGame[];
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function fetchPlayerGames(
  playerId: number,
  limit = 7
): Promise<PlayerGameLogResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/players/${playerId}/games?limit=${limit}`
  );

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || 'Could not load player stats.');
  }

  return response.json();
}
