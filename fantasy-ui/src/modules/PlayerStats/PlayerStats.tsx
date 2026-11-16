import React, { useCallback, useEffect, useState } from 'react';
import {
  PlayerAverageStats,
  PlayerWeeklySummary
} from './PlayerGameLog';
import PlayerTable from './PlayerTable';
import WeeklyCategoryCard, { WeeklyCategoryIncrease } from './WeeklyCategoryCard';
import WeeklyFantasyCard from './WeeklyFantasyCard';
import {
  CurrentRoster,
  fetchManagerRoster,
  fetchRosterManagers,
  RosterManager
} from '../../services/rosterApi';
import './PlayerStats.css';

export default function PlayerStats() {
  const [managers, setManagers] = useState<RosterManager[]>([]);
  const [selectedManagerId, setSelectedManagerId] = useState<number | null>(null);
  const [roster, setRoster] = useState<CurrentRoster | null>(null);
  const [rosterError, setRosterError] = useState<string | null>(null);
  const [rosterLoading, setRosterLoading] = useState(true);
  const [managersLoading, setManagersLoading] = useState(true);
  const [averagesByPlayer, setAveragesByPlayer] = useState<
    Record<number, PlayerAverageStats>
  >({});
  const [weeklyFantasyByPlayer, setWeeklyFantasyByPlayer] = useState<
    Record<number, PlayerWeeklySummary>
  >({});

  useEffect(() => {
    let cancelled = false;

    fetchRosterManagers()
      .then((data) => {
        if (!cancelled) {
          setManagers(data.managers);
          const defaultManagerId =
            data.defaultManagerId ?? data.managers[0]?.managerId ?? null;
          setSelectedManagerId(defaultManagerId);
          setManagersLoading(false);
          if (defaultManagerId === null) {
            setRosterError('No fantasy managers are configured yet.');
            setRosterLoading(false);
          }
        }
      })
      .catch((error: Error) => {
        if (!cancelled) {
          setRosterError(error.message);
          setManagersLoading(false);
          setRosterLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (selectedManagerId === null) return;

    let cancelled = false;
    setRosterLoading(true);
    setRosterError(null);
    setRoster(null);
    setAveragesByPlayer({});
    setWeeklyFantasyByPlayer({});

    fetchManagerRoster(selectedManagerId)
      .then((data) => {
        if (!cancelled) {
          setRoster(data);
          setRosterLoading(false);
        }
      })
      .catch((error: Error) => {
        if (!cancelled) {
          setRosterError(error.message);
          setRosterLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedManagerId]);

  const handleAveragesChange = useCallback(
    (
      playerId: number,
      averages: PlayerAverageStats,
      weeklySummary: PlayerWeeklySummary
    ) => {
      setAveragesByPlayer((previous) => ({
        ...previous,
        [playerId]: averages
      }));
      setWeeklyFantasyByPlayer((previous) => ({
        ...previous,
        [playerId]: weeklySummary
      }));
    },
    []
  );

  return (
    <main className="player-stats-page">
      <header className="player-stats-heading">
        <h1>Player game logs</h1>
        <p>
          {roster ? `${roster.teamName} · ` : ''}Most recent games · current season
        </p>
        <div className="player-stats-manager-selector">
          <label htmlFor="manager-select">Manager</label>
          <div className="player-stats-manager-select-wrap">
            <select
              id="manager-select"
              value={selectedManagerId ?? ''}
              disabled={managersLoading || managers.length === 0}
              onChange={(event) => setSelectedManagerId(Number(event.target.value))}
            >
              {managersLoading && <option value="">Loading managers…</option>}
              {managers.map((manager) => (
                <option key={manager.managerId} value={manager.managerId}>
                  {manager.managerName}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {roster && (() => {
        const rosterPlayers = [
          ...roster.corePlayers,
          ...roster.streamSlotCandidates
        ];
        const uniquePlayerIds = [...new Set(rosterPlayers.map((player) => player.playerId))];
        const loaded = uniquePlayerIds.every((playerId) =>
          Object.prototype.hasOwnProperty.call(weeklyFantasyByPlayer, playerId)
        );
        const totals = uniquePlayerIds.reduce(
          (sum, playerId) => {
            const weekly = weeklyFantasyByPlayer[playerId];
            if (weekly) {
              sum.current += weekly.fantasyPoints.current;
              sum.previous += weekly.fantasyPoints.previous;
            }
            return sum;
          },
          { current: 0, previous: 0 }
        );
        const categoryIncrease = loaded
          ? findBiggestWeeklyCategoryIncrease(
              uniquePlayerIds
                .map((playerId) => weeklyFantasyByPlayer[playerId])
                .filter((weekly): weekly is PlayerWeeklySummary => Boolean(weekly))
            )
          : null;

        return (
          <div className="weekly-summary-cards">
            <WeeklyFantasyCard
              current={totals.current}
              previous={totals.previous}
              loading={!loaded || rosterLoading}
            />
            <WeeklyCategoryCard increase={categoryIncrease} loading={!loaded || rosterLoading} />
          </div>
        );
      })()}

      {rosterLoading && <p className="player-stats-message">Loading roster…</p>}
      {rosterError && (
        <p className="player-stats-message error" role="alert">
          {rosterError}
        </p>
      )}
      {roster && (
        <>
          <section aria-labelledby="core-roster-heading">
            <h2 className="player-stats-section-heading" id="core-roster-heading">
              Roster
            </h2>
            <PlayerTable
              players={roster.corePlayers}
              averagesByPlayer={averagesByPlayer}
              onAveragesChange={handleAveragesChange}
            />
          </section>

          <section aria-labelledby="stream-slot-heading">
            <h2 className="player-stats-section-heading" id="stream-slot-heading">
              Stream slot candidates
            </h2>
            <p className="player-stats-section-description">
              {roster.streamSlotCandidates.length > 0
                ? `Candidates for ${roster.streamingSlots} streaming spot${
                    roster.streamingSlots === 1 ? '' : 's'
                  }.`
                : `${roster.streamingSlots} open streaming spot${
                    roster.streamingSlots === 1 ? '' : 's'
                  }.`}
            </p>
            {roster.streamSlotCandidates.length > 0 ? (
              <PlayerTable
                players={roster.streamSlotCandidates}
                averagesByPlayer={averagesByPlayer}
                onAveragesChange={handleAveragesChange}
              />
            ) : (
              <div className="player-stats-open-stream-slot">
                No player assigned yet
              </div>
            )}
          </section>
        </>
      )}
    </main>
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
