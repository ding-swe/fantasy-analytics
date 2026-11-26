const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface YahooGameLogTeam {
  team_key: string;
  team_name: string;
  players: { player_key: string; name: string; nba_player_id: number | null }[];
}

interface YahooGameLogRosters {
  default_team_key: string | null;
  teams: YahooGameLogTeam[];
}

export async function fetchYahooGameLogRosters(signal: AbortSignal): Promise<YahooGameLogRosters> {
  const response = await fetch(API_BASE_URL + '/api/yahoo/game-log-rosters', { signal });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || 'Could not load Yahoo rosters.');
  }
  return response.json();
}
