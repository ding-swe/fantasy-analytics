import React, { useState } from 'react';
import PlayerGameLog, {
  PlayerAverageStats,
  PlayerWeeklySummary
} from './PlayerGameLog';

export interface PlayerTableItem {
  playerId: number;
  name: string;
}

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

export default function PlayerTable({
  players,
  averagesByPlayer,
  onAveragesChange,
  trendScope = 'all'
}: {
  players: PlayerTableItem[];
  averagesByPlayer: Record<number, PlayerAverageStats>;
  onAveragesChange: (
    playerId: number,
    averages: PlayerAverageStats,
    weeklySummary: PlayerWeeklySummary
  ) => void;
  trendScope?: 'all' | 'fantasy';
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
          trendScope={trendScope}
        />
      ))}
    </div>
  );
}
