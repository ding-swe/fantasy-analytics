export interface FreeAgentPlayer {
  playerId: number;
  name: string;
  averageFantasyPoints: number;
  gamesPlayed: number;
}

export interface FreeAgentList {
  season: string;
  gamesConsidered: number;
  players: FreeAgentPlayer[];
}

interface ApiFreeAgentPlayer {
  player_id: number;
  name: string;
  average_fantasy_points: number;
  games_played: number;
}

interface ApiFreeAgentList {
  season: string;
  games_considered: number;
  players: ApiFreeAgentPlayer[];
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function fetchFreeAgents(limit = 20): Promise<FreeAgentList> {
  const response = await fetch(`${API_BASE_URL}/api/free-agents?limit=${limit}`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || 'Could not load free agents.');
  }

  const data: ApiFreeAgentList = await response.json();
  return {
    season: data.season,
    gamesConsidered: data.games_considered,
    players: data.players.map((player) => ({
      playerId: player.player_id,
      name: player.name,
      averageFantasyPoints: player.average_fantasy_points,
      gamesPlayed: player.games_played
    }))
  };
}
