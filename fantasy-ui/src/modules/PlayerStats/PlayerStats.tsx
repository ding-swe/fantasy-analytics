import React, { useCallback, useEffect, useState } from 'react';
import PlayerGameLog, { PlayerAverageStats } from './PlayerGameLog';
import {
  CurrentRoster,
  fetchManagerRoster,
  fetchRosterManagers,
  RosterManager,
  RosterPlayer
} from '../../services/rosterApi';
import './PlayerStats.css';

type SortKey = 'name' | keyof PlayerAverageStats;

interface AverageColumn {
  label: string;
  sortKey: SortKey;
  sortDescription?: string;
}

interface SortState {
  key: SortKey;
  direction: 'asc' | 'desc';
}

const averageColumns: AverageColumn[] = [
  { label: 'Player', sortKey: 'name' },
  { label: 'MIN', sortKey: 'minutes' },
  {
    label: 'FGM / FGA',
    sortKey: 'fieldGoalsMade',
    sortDescription: 'Sort by average field goals made'
  },
  {
    label: 'FTM / FTA',
    sortKey: 'freeThrowsMade',
    sortDescription: 'Sort by average free throws made'
  },
  { label: 'PTS', sortKey: 'points' },
  { label: 'REB', sortKey: 'rebounds' },
  { label: 'AST', sortKey: 'assists' },
  { label: 'STL', sortKey: 'steals' },
  { label: 'BLK', sortKey: 'blocks' },
  { label: 'TO', sortKey: 'turnovers' },
  { label: '3PM', sortKey: 'threePointersMade' },
  { label: 'Fantasy', sortKey: 'fantasyPoints' }
];

function PlayerRows({
  players,
  averagesByPlayer,
  onAveragesChange
}: {
  players: RosterPlayer[];
  averagesByPlayer: Record<number, PlayerAverageStats>;
  onAveragesChange: (playerId: number, averages: PlayerAverageStats) => void;
}) {
  const [sort, setSort] = useState<SortState>({
    key: 'fantasyPoints',
    direction: 'desc'
  });

  const handleSort = (key: SortKey) => {
    setSort((previous) => ({
      key,
      direction:
        previous.key === key
          ? previous.direction === 'asc'
            ? 'desc'
            : 'asc'
          : key === 'name'
          ? 'asc'
          : 'desc'
    }));
  };

  const sortedPlayers = players
    .map((player, originalIndex) => ({ player, originalIndex }))
    .sort((left, right) => {
      const leftValue =
        sort.key === 'name'
          ? left.player.name.toLocaleLowerCase()
          : averagesByPlayer[left.player.playerId]?.[sort.key] ?? null;
      const rightValue =
        sort.key === 'name'
          ? right.player.name.toLocaleLowerCase()
          : averagesByPlayer[right.player.playerId]?.[sort.key] ?? null;

      if (leftValue === null && rightValue === null) {
        return left.originalIndex - right.originalIndex;
      }
      if (leftValue === null) return 1;
      if (rightValue === null) return -1;

      const comparison =
        typeof leftValue === 'string' && typeof rightValue === 'string'
          ? leftValue.localeCompare(rightValue)
          : Number(leftValue) - Number(rightValue);

      if (comparison === 0) return left.originalIndex - right.originalIndex;
      return sort.direction === 'asc' ? comparison : -comparison;
    });

  return (
    <div className="player-stats-roster-grid">
      <div className="player-stats-column-headings">
        {averageColumns.map(({ label, sortKey, sortDescription }) => {
          const isActive = sort.key === sortKey;
          const direction = sort.direction === 'asc' ? '▲' : '▼';

          return (
            <span key={sortKey}>
              <button
                type="button"
                className="player-stats-sort-button"
                aria-pressed={isActive}
                title={sortDescription || `Sort by ${label}`}
                onClick={() => handleSort(sortKey)}
              >
                {label}
                <span aria-hidden="true">{isActive ? direction : '↕'}</span>
              </button>
            </span>
          );
        })}
      </div>
      {sortedPlayers.map(({ player }) => (
        <PlayerGameLog
          key={player.playerId}
          playerId={player.playerId}
          name={player.name}
          onAveragesChange={onAveragesChange}
        />
      ))}
    </div>
  );
}

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
    (playerId: number, averages: PlayerAverageStats) => {
      setAveragesByPlayer((previous) => ({
        ...previous,
        [playerId]: averages
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
            <PlayerRows
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
              <PlayerRows
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
