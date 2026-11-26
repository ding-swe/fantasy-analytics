import React, { useEffect, useMemo, useState } from 'react';
import {
  comparisonTable,
  fetchTeamComparisons,
  TeamComparisonData
} from '../../services/teamComparisonsApi';
import TeamComparisonRow, { TeamStatTones } from './TeamComparisonRow';
import './TeamComparisons.css';

const STRENGTH_THRESHOLD = 5;

export default function TeamComparisons() {
  const [data, setData] = useState<TeamComparisonData | null>(null);
  const [week, setWeek] = useState<number | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [selectedTeamKey, setSelectedTeamKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('result');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    if (week !== null) return;
    const refreshScores = () => setRefresh((previous) => previous + 1);
    window.addEventListener('basketbase:yahoo-rosters-synced', refreshScores);
    return () => window.removeEventListener('basketbase:yahoo-rosters-synced', refreshScores);
  }, [week]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    fetchTeamComparisons(week, controller.signal)
      .then((next) => {
        if (!controller.signal.aborted) setData(next);
      })
      .catch((failure: Error) => {
        if (!controller.signal.aborted) setError(failure.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [week, refresh]);

  const { teams, columns } = useMemo(
    () => data ? comparisonTable(data) : { teams: [], columns: [] },
    [data]
  );
  const selectedTeam = teams.find((team) => team.teamKey === selectedTeamKey)
    ?? teams.find((team) => team.isMyTeam) ?? teams[0];

  const sortedTeams = useMemo(() => [...teams].sort((left, right) => {
    const leftValue = sortKey === 'team' ? left.teamName : left.values[sortKey]?.sortValue;
    const rightValue = sortKey === 'team' ? right.teamName : right.values[sortKey]?.sortValue;

    if (leftValue == null) return rightValue == null ? left.teamName.localeCompare(right.teamName) : 1;
    if (rightValue == null) return -1;
    const comparison = typeof leftValue === 'string' && typeof rightValue === 'string'
      ? leftValue.localeCompare(rightValue)
      : Number(leftValue) - Number(rightValue);
    return (sortDirection === 'asc' ? comparison : -comparison)
      || left.teamName.localeCompare(right.teamName);
  }), [teams, sortKey, sortDirection]);

  const selectedStrengths = columns.filter((column) => {
    const selectedValue = selectedTeam?.values[column.key]?.strengthValue;
    if (!column.highlight || selectedValue == null) return false;
    const teamsBeaten = teams.filter((team) => {
      const value = team.values[column.key]?.strengthValue;
      return value != null && (column.higherIsBetter ? selectedValue > value : selectedValue < value);
    }).length;
    return teamsBeaten >= STRENGTH_THRESHOLD;
  });

  const tonesByTeam: Record<string, TeamStatTones> = {};
  for (const column of columns) {
    if (!column.highlight) continue;
    const values = teams.flatMap((team) => {
      const value = team.values[column.key]?.strengthValue;
      return value == null ? [] : [value];
    });
    if (values.length < 2) continue;
    const best = column.higherIsBetter ? Math.max(...values) : Math.min(...values);
    const worst = column.higherIsBetter ? Math.min(...values) : Math.max(...values);
    if (best === worst) continue;

    for (const team of teams) {
      const value = team.values[column.key]?.strengthValue;
      if (value == null) continue;
      const selectedStrength = team.teamKey === selectedTeam?.teamKey &&
        selectedStrengths.some((strength) => strength.key === column.key);
      const tone = value === best ? 'best' : value === worst ? 'worst' :
        selectedStrength ? 'strength' : undefined;
      if (tone) {
        tonesByTeam[team.teamKey] = { ...tonesByTeam[team.teamKey], [column.key]: tone };
      }
    }
  }

  const handleSort = (key: string) => {
    if (key === sortKey) {
      setSortDirection((direction) => direction === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection(key === 'team' ? 'asc' : 'desc');
    }
  };

  const historicalWeeks = data ? Array.from(
    { length: data.current_week - data.start_week },
    (_, index) => data.current_week - index - 1
  ) : [];
  const headers = [{ key: 'team', label: 'Team' }, ...columns];
  const gridColumns = [
    'minmax(230px, 2.1fr)',
    ...columns.map((column) => column.wide ? 'minmax(94px, 1fr)' : 'minmax(64px, 0.8fr)')
  ].join(' ');
  const finished = data?.matchups.length && data.matchups.every((matchup) => matchup.status === 'postevent');
  const ready = data && !loading && !error;

  return (
    <main className="team-comparisons-page">
      <header className="team-comparisons-heading">
        <h1>Team Comparisons</h1>
        <p>
          {data ? data.league_name + ' · Week ' + data.week + (finished ? ' · Final' : '') :
            'Yahoo matchup totals'}
        </p>
        <div className="team-comparisons-controls">
          <div className="team-comparisons-manager-selector">
            <label htmlFor="team-comparisons-manager">Manager</label>
            <div className="team-comparisons-select-wrap">
              <select
                id="team-comparisons-manager"
                value={selectedTeam?.teamKey ?? ''}
                disabled={loading || !teams.length}
                onChange={(event) => setSelectedTeamKey(event.target.value)}
              >
                {teams.map((team) => (
                  <option key={team.teamKey} value={team.teamKey}>{team.managerName || team.teamName}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="team-comparisons-manager-selector">
            <label htmlFor="matchup-week">Matchup week</label>
            <div className="team-comparisons-select-wrap">
              <select
                id="matchup-week"
                value={week ?? ''}
                disabled={!data}
                onChange={(event) => setWeek(event.target.value === '' ? null : Number(event.target.value))}
              >
                <option value="">{data ? 'Current week (' + data.current_week + ')' : 'Current week'}</option>
                {historicalWeeks.map((entry) => <option key={entry} value={entry}>Week {entry}</option>)}
              </select>
            </div>
          </div>
          <div className="team-comparisons-strengths" aria-live="polite">
            <span className="team-comparisons-strengths-label">Strengths · ahead of 5+ teams</span>
            <div className="team-comparisons-strength-list">
              {selectedStrengths.length ? selectedStrengths.map((column) => (
                <span className="team-comparisons-strength-chip" key={column.key}>
                  {column.key === 'field-goals' ? 'FG%' : column.key === 'free-throws' ? 'FT%' : column.label}
                </span>
              )) : <span className="team-comparisons-no-strengths">No categories currently meet this threshold</span>}
            </div>
          </div>
        </div>
      </header>

      {loading && <p className="player-stats-message" role="status">Loading team comparisons…</p>}
      {error && <p className="player-stats-message error" role="alert">{error}</p>}
      {ready && !teams.length && <p>Yahoo has no matchups for week {data.week}.</p>}
      {ready && teams.length > 0 && (
        <section
          className="team-comparison-table"
          role="table"
          aria-label="Yahoo weekly team stat totals"
          style={{ '--yahoo-team-columns': gridColumns } as React.CSSProperties}
        >
          <div className="team-comparison-header" role="row">
            {headers.map(({ label, key }) => {
              const active = sortKey === key;
              return (
                <span key={key} role="columnheader">
                  <button type="button" aria-pressed={active} title={'Sort by ' + label} onClick={() => handleSort(key)}>
                    {label}
                    <span aria-hidden="true">{active ? (sortDirection === 'asc' ? '▲' : '▼') : '↕'}</span>
                  </button>
                </span>
              );
            })}
          </div>
          {sortedTeams.map((team, index) => (
            <TeamComparisonRow key={team.teamKey} team={team} columns={columns} rank={index + 1}
              tones={tonesByTeam[team.teamKey] || {}} />
          ))}
        </section>
      )}
      <footer className="team-comparisons-attribution">
        <a href="https://basketball.fantasysports.yahoo.com/">Fantasy data provided by Yahoo Fantasy</a>
      </footer>
    </main>
  );
}
