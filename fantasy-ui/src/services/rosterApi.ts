const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ApiRosterPlayer {
  player_id: number;
  name: string;
}

interface ApiRosterManager {
  manager_id: number;
  manager_name: string;
  team_name: string;
  is_primary: boolean;
}

interface ApiManagerList {
  managers: ApiRosterManager[];
  default_manager_id: number | null;
}

interface ApiManagerRoster extends ApiRosterManager {
  streaming_slots: number;
  core_players: ApiRosterPlayer[];
  stream_slot_candidates: ApiRosterPlayer[];
}

export interface RosterPlayer {
  playerId: number;
  name: string;
}

export interface RosterManager {
  managerId: number;
  managerName: string;
  teamName: string;
  isPrimary: boolean;
}

export interface CurrentRoster extends RosterManager {
  streamingSlots: number;
  corePlayers: RosterPlayer[];
  streamSlotCandidates: RosterPlayer[];
}

export interface RosterManagerList {
  managers: RosterManager[];
  defaultManagerId: number | null;
}

function mapManager(manager: ApiRosterManager): RosterManager {
  return {
    managerId: manager.manager_id,
    managerName: manager.manager_name,
    teamName: manager.team_name,
    isPrimary: manager.is_primary
  };
}

function mapPlayers(players: ApiRosterPlayer[]): RosterPlayer[] {
  return players.map((player) => ({
    playerId: player.player_id,
    name: player.name
  }));
}

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || 'Could not load fantasy league data.');
  }
  return response.json();
}

export async function fetchRosterManagers(): Promise<RosterManagerList> {
  const response = await fetch(`${API_BASE_URL}/api/rosters`);
  const data = await readResponse<ApiManagerList>(response);
  return {
    managers: data.managers.map(mapManager),
    defaultManagerId: data.default_manager_id
  };
}

export async function fetchManagerRoster(
  managerId: number
): Promise<CurrentRoster> {
  const response = await fetch(`${API_BASE_URL}/api/rosters/${managerId}`);
  const roster = await readResponse<ApiManagerRoster>(response);
  return {
    ...mapManager(roster),
    streamingSlots: roster.streaming_slots,
    corePlayers: mapPlayers(roster.core_players),
    streamSlotCandidates: mapPlayers(roster.stream_slot_candidates)
  };
}
