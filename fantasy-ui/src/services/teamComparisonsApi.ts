const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ApiTeamComparison {
  manager_id: number;
  manager_name: string;
  team_name: string;
  core_player_count: number;
  minutes: number;
  field_goals_made: number;
  field_goals_attempted: number;
  free_throws_made: number;
  free_throws_attempted: number;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  three_pointers_made: number;
  fantasy_points: number;
  current_week_fantasy_points: number;
  previous_week_fantasy_points: number;
}

interface ApiTeamComparisonResponse {
  season: string;
  teams: ApiTeamComparison[];
}

export interface TeamComparison {
  managerId: number;
  managerName: string;
  teamName: string;
  corePlayerCount: number;
  minutes: number;
  fieldGoalsMade: number;
  fieldGoalsAttempted: number;
  freeThrowsMade: number;
  freeThrowsAttempted: number;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  threePointersMade: number;
  fantasyPoints: number;
  currentWeekFantasyPoints: number;
  previousWeekFantasyPoints: number;
}

export interface TeamComparisonData {
  season: string;
  teams: TeamComparison[];
}

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || 'Could not load team comparisons.');
  }
  return response.json();
}

export async function fetchTeamComparisons(): Promise<TeamComparisonData> {
  const response = await fetch(`${API_BASE_URL}/api/team-comparisons`);
  const data = await readResponse<ApiTeamComparisonResponse>(response);

  return {
    season: data.season,
    teams: data.teams.map((team) => ({
      managerId: team.manager_id,
      managerName: team.manager_name,
      teamName: team.team_name,
      corePlayerCount: team.core_player_count,
      minutes: team.minutes,
      fieldGoalsMade: team.field_goals_made,
      fieldGoalsAttempted: team.field_goals_attempted,
      freeThrowsMade: team.free_throws_made,
      freeThrowsAttempted: team.free_throws_attempted,
      points: team.points,
      rebounds: team.rebounds,
      assists: team.assists,
      steals: team.steals,
      blocks: team.blocks,
      turnovers: team.turnovers,
      threePointersMade: team.three_pointers_made,
      fantasyPoints: team.fantasy_points,
      currentWeekFantasyPoints: team.current_week_fantasy_points,
      previousWeekFantasyPoints: team.previous_week_fantasy_points
    }))
  };
}
