import React, { useEffect, useMemo, useState } from 'react';
import {
  fetchTeamComparisons,
  TeamComparison,
  TeamComparisonData
} from '../../services/teamComparisonsApi';
import { fetchRosterManagers, RosterManager } from '../../services/rosterApi';
import TeamComparisonRow, { TeamStatTones } from './TeamComparisonRow';
import './TeamComparisons.css';

type SortKey =
  | 'teamName'
  | 'minutes'
  | 'fieldGoalsMade'
  | 'freeThrowsMade'
  | 'points'
  | 'rebounds'
  | 'assists'
  | 'steals'
  | 'blocks'
  | 'turnovers'
  | 'threePointersMade'
  | 'fantasyPoints';

const columns: { label: string; key: SortKey }[] = [
  { label: 'Team', key: 'teamName' },
  { label: 'MIN', key: 'minutes' },
  { label: 'FGM / FGA', key: 'fieldGoalsMade' },
  { label: 'FTM / FTA', key: 'freeThrowsMade' },
  { label: 'PTS', key: 'points' },
  { label: 'REB', key: 'rebounds' },
  { label: 'AST', key: 'assists' },
  { label: 'STL', key: 'steals' },
  { label: 'BLK', key: 'blocks' },
  { label: 'TO', key: 'turnovers' },
  { label: '3PM', key: 'threePointersMade' },
  { label: 'Fantasy', key: 'fantasyPoints' }
];

interface Category {
  label: string;
  key: keyof TeamComparison;
  higherIsBetter: boolean;
  measure: (team: TeamComparison) => number;
}

const categories: Category[] = [
  {
    label: 'FG%',
    key: 'fieldGoalsMade',
    higherIsBetter: true,
    measure: (team) =>
      team.fieldGoalsAttempted > 0
        ? team.fieldGoalsMade / team.fieldGoalsAttempted
        : 0
  },
  {
    label: 'FT%',
    key: 'freeThrowsMade',
    higherIsBetter: true,
    measure: (team) =>
      team.freeThrowsAttempted > 0
        ? team.freeThrowsMade / team.freeThrowsAttempted
        : 0
  },
  { label: 'MIN', key: 'minutes', higherIsBetter: true, measure: (team) => team.minutes },
  { label: '3PM', key: 'threePointersMade', higherIsBetter: true, measure: (team) => team.threePointersMade },
  { label: 'PTS', key: 'points', higherIsBetter: true, measure: (team) => team.points },
  { label: 'REB', key: 'rebounds', higherIsBetter: true, measure: (team) => team.rebounds },
  { label: 'AST', key: 'assists', higherIsBetter: true, measure: (team) => team.assists },
  { label: 'STL', key: 'steals', higherIsBetter: true, measure: (team) => team.steals },
  { label: 'BLK', key: 'blocks', higherIsBetter: true, measure: (team) => team.blocks },
  { label: 'TO', key: 'turnovers', higherIsBetter: false, measure: (team) => team.turnovers },
  { label: 'Fantasy', key: 'fantasyPoints', higherIsBetter: true, measure: (team) => team.fantasyPoints }
];

export default function TeamComparisons() {
  const [data, setData] = useState<TeamComparisonData | null>(null);
  const [managers, setManagers] = useState<RosterManager[]>([]);
  const [selectedManagerId, setSelectedManagerId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>('fantasyPoints');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchTeamComparisons(), fetchRosterManagers()])
      .then(([result, rosterManagers]) => {
        if (!cancelled) {
          setData(result);
          setManagers(rosterManagers.managers);
          const primaryManagerId =
            rosterManagers.managers.find((manager) => manager.isPrimary)?.managerId;
          setSelectedManagerId(
            primaryManagerId ?? result.teams[0]?.managerId ?? null
          );
        }
      })
      .catch((requestError: Error) => {
        if (!cancelled) setError(requestError.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const sortedTeams = useMemo(() => {
    if (!data) return [];
    return [...data.teams].sort((left, right) => {
      const leftValue = left[sortKey];
      const rightValue = right[sortKey];
      const comparison =
        typeof leftValue === 'string' && typeof rightValue === 'string'
          ? leftValue.localeCompare(rightValue)
          : Number(leftValue) - Number(rightValue);
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [data, sortDirection, sortKey]);

  const selectedTeam =
    data?.teams.find((team) => team.managerId === selectedManagerId) ?? null;
  const selectedStrengths = selectedTeam
    ? categories.filter((category) => {
        const selectedValue = category.measure(selectedTeam);
        const teamsBeaten = data!.teams.filter((team) => {
          if (team.managerId === selectedTeam.managerId) return false;
          const otherValue = category.measure(team);
          return category.higherIsBetter
            ? selectedValue > otherValue
            : selectedValue < otherValue;
        }).length;
        return teamsBeaten >= 5;
      })
    : [];

  const tonesByManager = useMemo(() => {
    const result: Record<number, TeamStatTones> = {};
    if (!data) return result;

    for (const category of categories) {
      const values = data.teams.map((team) => category.measure(team));
      const best = category.higherIsBetter
        ? Math.max(...values)
        : Math.min(...values);
      const worst = category.higherIsBetter
        ? Math.min(...values)
        : Math.max(...values);

      if (best === worst) continue;
      for (const team of data.teams) {
        const value = category.measure(team);
        if (value === best) {
          result[team.managerId] = {
            ...result[team.managerId],
            [category.key]: 'best'
          };
        } else if (value === worst) {
          result[team.managerId] = {
            ...result[team.managerId],
            [category.key]: 'worst'
          };
        } else if (
          team.managerId === selectedManagerId &&
          selectedStrengths.some((strength) => strength.key === category.key)
        ) {
          result[team.managerId] = {
            ...result[team.managerId],
            [category.key]: 'strength'
          };
        }
      }
    }

    return result;
  }, [data, selectedManagerId, selectedStrengths]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection((direction) => (direction === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDirection(key === 'teamName' ? 'asc' : 'desc');
    }
  };

  return (
    <main className="team-comparisons-page">
      <header className="team-comparisons-heading">
        <h1>Team Comparisons</h1>
        <p>
          {data
            ? `${data.season} · summed core-player averages from up to ${data.gamesConsidered} games in the last ${data.recentDays} days`
            : 'Comparing recent team production'}
        </p>
        <div className="team-comparisons-controls">
          <div className="team-comparisons-manager-selector">
            <label htmlFor="team-comparisons-manager">Manager</label>
            <div className="team-comparisons-select-wrap">
              <select
                id="team-comparisons-manager"
                value={selectedManagerId ?? ''}
                disabled={loading || managers.length === 0}
                onChange={(event) => setSelectedManagerId(Number(event.target.value))}
              >
                {managers.map((manager) => (
                  <option key={manager.managerId} value={manager.managerId}>
                    {manager.managerName}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="team-comparisons-strengths" aria-live="polite">
            <span className="team-comparisons-strengths-label">
              Strengths · better than 4+ teams
            </span>
            <div className="team-comparisons-strength-list">
              {selectedStrengths.length > 0 ? (
                selectedStrengths.map((category) => (
                  <span className="team-comparisons-strength-chip" key={category.label}>
                    {category.label}
                  </span>
                ))
              ) : (
                <span className="team-comparisons-no-strengths">
                  No categories currently meet this threshold
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {loading && <p className="player-stats-message">Loading team comparisons…</p>}
      {error && (
        <p className="player-stats-message error" role="alert">
          {error}
        </p>
      )}
      {data && (
        <section
          className="team-comparison-table"
          role="table"
          aria-label="Fantasy team recent stat totals"
        >
          <div className="team-comparison-header" role="row">
            {columns.map(({ label, key }) => {
              const active = sortKey === key;
              return (
                <span key={key} role="columnheader">
                  <button
                    type="button"
                    aria-pressed={active}
                    title={`Sort by ${label}`}
                    onClick={() => handleSort(key)}
                  >
                    {label}
                    <span aria-hidden="true">
                      {active ? (sortDirection === 'asc' ? '▲' : '▼') : '↕'}
                    </span>
                  </button>
                </span>
              );
            })}
          </div>
          {sortedTeams.map((team: TeamComparison, index) => (
            <TeamComparisonRow
              key={team.managerId}
              team={team}
              rank={index + 1}
              tones={tonesByManager[team.managerId] || {}}
            />
          ))}
        </section>
      )}
    </main>
  );
}
