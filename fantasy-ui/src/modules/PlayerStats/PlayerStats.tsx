import React, { useCallback, useEffect, useState } from 'react';
import {
  PlayerAverageStats,
  PlayerWeeklySummary
} from './PlayerGameLog';
import PlayerTable, { PlayerTableItem } from './PlayerTable';
import WeeklyCategoryCard, { WeeklyCategoryIncrease } from './WeeklyCategoryCard';
import WeeklyFantasyCard from './WeeklyFantasyCard';
import { fetchYahooGameLogRosters, YahooGameLogTeam } from '../../services/yahooGameLogApi';
import './PlayerStats.css';

const TEAM_PREFERENCE = 'basketbase:game-log-team';

export default function PlayerStats() {
  const [teams, setTeams] = useState<YahooGameLogTeam[]>([]);
  const [selectedTeamKey, setSelectedTeamKey] = useState(
    () => window.localStorage.getItem(TEAM_PREFERENCE) || ''
  );
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const refreshRosters = () => setRefresh((previous) => previous + 1);
    window.addEventListener('basketbase:yahoo-rosters-synced', refreshRosters);
    return () => window.removeEventListener('basketbase:yahoo-rosters-synced', refreshRosters);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setError('');
    fetchYahooGameLogRosters(controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        setTeams(data.teams);
        setSelectedTeamKey((previous) =>
          data.teams.some((team) => team.team_key === previous)
            ? previous
            : data.default_team_key || data.teams[0]?.team_key || ''
        );
      })
      .catch((failure: Error) => {
        if (!controller.signal.aborted) setError(failure.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [refresh]);

  const team = teams.find((entry) => entry.team_key === selectedTeamKey);

  return (
    <main className="player-stats-page">
      <header className="player-stats-heading">
        <h1>Player game logs</h1>
        <p>{team ? team.team_name + ' · ' : ''}Most recent games · current season</p>
        <div className="player-stats-manager-selector">
          <label htmlFor="roster-team-select">Team</label>
          <div className="player-stats-manager-select-wrap">
            <select
              id="roster-team-select"
              value={selectedTeamKey}
              disabled={loading || teams.length === 0}
              onChange={(event) => {
                const teamKey = event.target.value;
                window.localStorage.setItem(TEAM_PREFERENCE, teamKey);
                setSelectedTeamKey(teamKey);
              }}
            >
              {!team && <option value="">{loading ? 'Loading teams…' : 'No Yahoo teams'}</option>}
              {teams.map((entry) => (
                <option key={entry.team_key} value={entry.team_key}>{entry.team_name}</option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {loading && <p className="player-stats-message" role="status">Loading Yahoo rosters…</p>}
      {error && <p className="player-stats-message error" role="alert">{error}</p>}
      {team && <RosterGameLogs key={team.team_key} team={team} />}
    </main>
  );
}

function RosterGameLogs({ team }: { team: YahooGameLogTeam }) {
  const [averagesByPlayer, setAveragesByPlayer] = useState<
    Record<number, PlayerAverageStats>
  >({});
  const [weeklyByPlayer, setWeeklyByPlayer] = useState<
    Record<number, PlayerWeeklySummary>
  >({});

  const handleAveragesChange = useCallback(
    (playerId: number, averages: PlayerAverageStats, weekly: PlayerWeeklySummary) => {
      setAveragesByPlayer((previous) => ({ ...previous, [playerId]: averages }));
      setWeeklyByPlayer((previous) => ({ ...previous, [playerId]: weekly }));
    },
    []
  );

  const players: PlayerTableItem[] = team.players.map((player) => ({
    playerId: player.nba_player_id,
    rosterKey: player.player_key,
    name: player.name
  }));
  const ids = Array.from(new Set(players.flatMap((player) =>
    player.playerId === null ? [] : [player.playerId]
  )));
  const weekly = ids.map((id) => weeklyByPlayer[id]).filter(Boolean);
  const loaded = weekly.length === ids.length;
  const totals = weekly.reduce(
    (sum, entry) => ({
      current: sum.current + entry.fantasyPoints.current,
      previous: sum.previous + entry.fantasyPoints.previous
    }),
    { current: 0, previous: 0 }
  );

  return (
    <>
      {ids.length > 0 && (
        <div className="weekly-summary-cards">
          <WeeklyFantasyCard current={totals.current} previous={totals.previous} loading={!loaded} />
          <WeeklyCategoryCard
            increase={loaded ? findBiggestWeeklyCategoryIncrease(weekly) : null}
            loading={!loaded}
          />
        </div>
      )}
      <section aria-labelledby="game-log-roster-heading">
        <h2 className="player-stats-section-heading" id="game-log-roster-heading">Roster</h2>
        {players.length ? (
          <PlayerTable
            players={players}
            averagesByPlayer={averagesByPlayer}
            onAveragesChange={handleAveragesChange}
          />
        ) : (
          <p className="player-stats-message">No rostered players.</p>
        )}
      </section>
    </>
  );
}

function findBiggestWeeklyCategoryIncrease(
  players: PlayerWeeklySummary[]
): WeeklyCategoryIncrease | null {
  const sum = (
    period: 'currentWeek' | 'previousWeek',
    key: keyof PlayerWeeklySummary['currentWeek']
  ) =>
    players.reduce((total, player) => {
      const value = player[period][key];
      return total + (typeof value === 'number' ? value : 0);
    }, 0);

  const shootingPercentage = (
    period: 'currentWeek' | 'previousWeek',
    madeKey: 'field_goals_made' | 'free_throws_made',
    attemptedKey: 'field_goals_attempted' | 'free_throws_attempted'
  ) => {
    const attempted = sum(period, attemptedKey);
    return attempted > 0 ? sum(period, madeKey) / attempted : null;
  };

  const categories: {
    label: string;
    current: number | null;
    previous: number | null;
  }[] = [
    {
      label: 'MIN',
      current: sum('currentWeek', 'minutes'),
      previous: sum('previousWeek', 'minutes')
    },
    {
      label: 'FG%',
      current: shootingPercentage('currentWeek', 'field_goals_made', 'field_goals_attempted'),
      previous: shootingPercentage('previousWeek', 'field_goals_made', 'field_goals_attempted')
    },
    {
      label: 'FT%',
      current: shootingPercentage('currentWeek', 'free_throws_made', 'free_throws_attempted'),
      previous: shootingPercentage('previousWeek', 'free_throws_made', 'free_throws_attempted')
    },
    ...([
      ['3PM', 'three_pointers_made'],
      ['PTS', 'points'],
      ['REB', 'rebounds'],
      ['AST', 'assists'],
      ['STL', 'steals'],
      ['BLK', 'blocks'],
      ['TO', 'turnovers'],
      ['Fantasy', 'nba_fantasy_points']
    ] as const).map(([label, key]) => ({
      label,
      current: sum('currentWeek', key),
      previous: sum('previousWeek', key)
    }))
  ];

  return categories.reduce<WeeklyCategoryIncrease | null>((best, category) => {
    if (
      category.current === null ||
      category.previous === null ||
      category.previous <= 0 ||
      category.current <= category.previous
    ) {
      return best;
    }

    const percentIncrease = (category.current - category.previous) / category.previous;
    return !best || percentIncrease > best.percentIncrease
      ? { label: category.label, percentIncrease }
      : best;
  }, null);
}
