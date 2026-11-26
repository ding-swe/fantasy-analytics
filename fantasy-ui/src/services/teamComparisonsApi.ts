const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface ScoringCategory {
  stat_id: string;
  name: string;
  label: string;
  counts_toward_result: boolean;
  higher_is_better: boolean;
}

export interface YahooMatchup {
  status: string;
  week_start: string | null;
  week_end: string | null;
  winner_team_key: string | null;
  is_tied: boolean;
  category_winners: Record<string, string | null>;
  teams: {
    team_key: string;
    team_name: string;
    manager_name: string | null;
    is_my_team: boolean;
    points: string | null;
    stats: Record<string, string>;
  }[];
}

export interface TeamComparisonData {
  league_name: string;
  scoring_type: string;
  start_week: number;
  current_week: number;
  week: number;
  categories: ScoringCategory[];
  matchups: YahooMatchup[];
}

export async function fetchTeamComparisons(
  week: number | null,
  signal: AbortSignal
): Promise<TeamComparisonData> {
  const query = week === null ? '' : '?week=' + week;
  const response = await fetch(API_BASE_URL + '/api/team-comparisons' + query, { signal });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || 'Could not load Yahoo matchup scores.');
  }
  return response.json();
}

export interface ComparisonValue {
  display: string;
  sortValue: number | null;
  strengthValue: number | null;
}

export interface ComparisonColumn {
  key: string;
  label: string;
  higherIsBetter: boolean;
  highlight: boolean;
  wide?: boolean;
}

export interface ComparisonTeam {
  teamKey: string;
  teamName: string;
  managerName: string | null;
  opponentName: string | null;
  isMyTeam: boolean;
  values: Record<string, ComparisonValue>;
}

const categoryOrder = [
  'minutes', 'field-goals', 'free-throws', '10', '12', '15', '16', '17', '18', '19'
];

function numeric(value: string | null | undefined): number | null {
  if (!value || !value.trim()) return null;
  const result = Number(value.replace(/,/g, ''));
  return Number.isFinite(result) ? result : null;
}

export function comparisonTable(data: TeamComparisonData): {
  columns: ComparisonColumn[];
  teams: ComparisonTeam[];
} {
  const sourceCategories = new Map(data.categories.map((category) => [category.stat_id, category]));
  const shooting = new Map([
    ['5', { key: 'field-goals', label: 'FGM / FGA', totals: '9004003' }],
    ['8', { key: 'free-throws', label: 'FTM / FTA', totals: '9007006' }]
  ]);
  const combinedStats = new Set(['9004003', '9007006']);
  const columns = data.categories
    .filter((category) => !combinedStats.has(category.stat_id) || !data.categories.some(
      (entry) => shooting.get(entry.stat_id)?.totals === category.stat_id
    ))
    .map((category) => {
      const pair = shooting.get(category.stat_id);
      const hasTotals = pair && sourceCategories.has(pair.totals);
      const minutes = category.label.toUpperCase() === 'MIN';
      return {
        key: minutes ? 'minutes' : pair?.key || category.stat_id,
        label: hasTotals ? pair.label : category.stat_id === '17' ? 'STL' :
          category.stat_id === '10' ? '3PM' : category.label,
        higherIsBetter: category.higher_is_better,
        highlight: category.counts_toward_result,
        wide: Boolean(hasTotals),
        statId: category.stat_id,
        totalsId: hasTotals ? pair.totals : null
      };
    });
  const order = (key: string) => {
    const index = categoryOrder.indexOf(key);
    return index < 0 ? categoryOrder.length : index;
  };
  columns.sort((left, right) => order(left.key) - order(right.key));

  const pointsLeague = data.scoring_type === 'headpoint';
  const resultColumn: ComparisonColumn = pointsLeague
    ? { key: 'result', label: 'Fantasy', higherIsBetter: true, highlight: true }
    : { key: 'result', label: 'W–L–T', higherIsBetter: true, highlight: false, wide: true };
  const scoredStats = data.categories.filter((category) => category.counts_toward_result);
  const teams = data.matchups.flatMap((matchup) => {
    const winners = scoredStats
      .filter((category) => category.stat_id in matchup.category_winners)
      .map((category) => matchup.category_winners[category.stat_id]);
    return matchup.teams.map((team) => {
      const values: Record<string, ComparisonValue> = {};
      for (const column of columns) {
        const score = team.stats[column.statId];
        const totals = column.totalsId ? team.stats[column.totalsId] : undefined;
        values[column.key] = {
          display: totals?.replace('/', ' / ') || score || '—',
          sortValue: numeric(totals?.split('/')[0] ?? score),
          strengthValue: numeric(score)
        };
      }
      const wins = winners.filter((winner) => winner === team.team_key).length;
      const ties = winners.filter((winner) => winner === null).length;
      const losses = winners.length - wins - ties;
      values.result = pointsLeague
        ? { display: team.points || '—', sortValue: numeric(team.points), strengthValue: numeric(team.points) }
        : {
            display: winners.length ? [wins, losses, ties].join('–') : '—',
            sortValue: winners.length ? wins + ties / (scoredStats.length + 1) : null,
            strengthValue: null
          };
      return {
        teamKey: team.team_key,
        teamName: team.team_name,
        managerName: team.manager_name,
        opponentName: matchup.teams.find((opponent) => opponent.team_key !== team.team_key)?.team_name || null,
        isMyTeam: team.is_my_team,
        values
      };
    });
  });
  return { columns: [...columns, resultColumn], teams };
}
