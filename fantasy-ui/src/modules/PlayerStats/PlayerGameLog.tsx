import React, { useEffect, useState } from 'react';
import {
  fetchPlayerGames,
  PlayerGame,
  PlayerGameLogResponse
} from '../../services/playerStatsApi';
import './PlayerStats.css';

export interface PlayerAverageStats {
  minutes: number | null;
  fieldGoalsMade: number | null;
  fieldGoalsAttempted: number | null;
  freeThrowsMade: number | null;
  freeThrowsAttempted: number | null;
  points: number | null;
  rebounds: number | null;
  assists: number | null;
  steals: number | null;
  blocks: number | null;
  turnovers: number | null;
  threePointersMade: number | null;
  fantasyPoints: number | null;
}

interface PlayerGameLogProps {
  playerId: number;
  name: string;
  onAveragesChange: (playerId: number, averages: PlayerAverageStats) => void;
}

interface PlayerLoadState {
  data: PlayerGameLogResponse | null;
  error: string | null;
  loading: boolean;
}

function formatNumber(value: number | string | null): string {
  if (value === null || value === '') return '—';

  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(1) : String(value);
}

function average(
  games: PlayerGame[],
  getValue: (game: PlayerGame) => number | string | null
): number | null {
  const values = games
    .map(getValue)
    .filter((value): value is number | string => value !== null && value !== '')
    .map(Number)
    .filter(Number.isFinite);

  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function formatDate(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return value;

  const month = Number(match[2]);
  const day = Number(match[3]);
  let suffix = 'th';
  if (day % 100 < 11 || day % 100 > 13) {
    if (day % 10 === 1) suffix = 'st';
    else if (day % 10 === 2) suffix = 'nd';
    else if (day % 10 === 3) suffix = 'rd';
  }
  const monthName = new Date(2000, month - 1, day).toLocaleString('en-US', {
    month: 'long'
  });

  return `${monthName} ${day}${suffix}`;
}

function opponentAbbreviation(game: PlayerGame): string | null {
  if (game.opponent_team_abbreviation) return game.opponent_team_abbreviation;

  const match = /^([A-Z]{2,3})\s+(?:@|vs\.)\s+([A-Z]{2,3})$/.exec(
    game.matchup.trim()
  );
  return match?.[2] || null;
}

function calculateAverages(games: PlayerGame[]): PlayerAverageStats {
  return {
    minutes: average(games, (game) => game.minutes),
    fieldGoalsMade: average(games, (game) => game.field_goals_made),
    fieldGoalsAttempted: average(games, (game) => game.field_goals_attempted),
    freeThrowsMade: average(games, (game) => game.free_throws_made),
    freeThrowsAttempted: average(games, (game) => game.free_throws_attempted),
    points: average(games, (game) => game.points),
    rebounds: average(games, (game) => game.rebounds),
    assists: average(games, (game) => game.assists),
    steals: average(games, (game) => game.steals),
    blocks: average(games, (game) => game.blocks),
    turnovers: average(games, (game) => game.turnovers),
    threePointersMade: average(games, (game) => game.three_pointers_made),
    fantasyPoints: average(games, (game) => game.fantasy_points)
  };
}

function ComparedNumber({
  value,
  averageValue,
  inverse = false,
  integer = false
}: {
  value: number | string | null;
  averageValue: number | null;
  inverse?: boolean;
  integer?: boolean;
}) {
  const numericValue = value === null || value === '' ? null : Number(value);
  let comparisonClass = '';

  if (
    numericValue !== null &&
    Number.isFinite(numericValue) &&
    averageValue !== null &&
    averageValue > 0
  ) {
    if (numericValue <= averageValue * 0.8) {
      comparisonClass = inverse ? 'above-average' : 'below-average';
    } else if (numericValue >= averageValue * 1.2) {
      comparisonClass = inverse ? 'below-average' : 'above-average';
    }
  }

  const displayValue =
    integer && numericValue !== null && Number.isFinite(numericValue)
      ? String(numericValue)
      : formatNumber(value);

  return <strong className={comparisonClass}>{displayValue}</strong>;
}

function ComparedPercentage({
  made,
  attempted,
  averageMade,
  averageAttempted
}: {
  made: number | string | null;
  attempted: number | string | null;
  averageMade: number | null;
  averageAttempted: number | null;
}) {
  const madeValue = made === null || made === '' ? null : Number(made);
  const attemptedValue =
    attempted === null || attempted === '' ? null : Number(attempted);
  const averagePercentage =
    averageMade !== null && averageAttempted !== null && averageAttempted > 0
      ? averageMade / averageAttempted
      : null;
  const percentage =
    madeValue !== null && attemptedValue !== null && attemptedValue > 0
      ? madeValue / attemptedValue
      : null;

  let comparisonClass = '';
  if (
    percentage !== null &&
    Number.isFinite(percentage) &&
    averagePercentage !== null &&
    averagePercentage > 0
  ) {
    if (percentage <= averagePercentage * 0.8) {
      comparisonClass = 'below-average';
    } else if (percentage >= averagePercentage * 1.2) {
      comparisonClass = 'above-average';
    }
  }

  return (
    <strong className={comparisonClass}>
      {madeValue !== null && Number.isFinite(madeValue)
        ? String(madeValue)
        : formatNumber(made)}
      /
      {attemptedValue !== null && Number.isFinite(attemptedValue)
        ? String(attemptedValue)
        : formatNumber(attempted)}
    </strong>
  );
}

function AverageStat({ label, value }: { label: string; value: string }) {
  return (
    <span className="player-stats-average-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </span>
  );
}

function PlayerGameRows({
  games,
  averages,
  playerName
}: {
  games: PlayerGame[];
  averages: PlayerAverageStats;
  playerName: string;
}) {
  return (
    <div
      className="player-stats-game-rows"
      role="table"
      aria-label={`${playerName} recent games`}
    >
      {games.map((game) => {
        const opponent = opponentAbbreviation(game);
        return (
          <div className="player-stats-game-row" role="row" key={game.game_id}>
            <span
              className="player-stats-game-context"
              role="cell"
              aria-label={`${formatDate(game.game_date)}, vs ${
                opponent || 'unknown opponent'
              }, ${game.result || 'no result'}`}
            >
              <span>{formatDate(game.game_date)}</span>
              <span>
                vs {opponent || '—'}{' '}
                <span className="player-stats-result">{game.result}</span>
              </span>
            </span>
            <span
              role="cell"
              aria-label={`Minutes: ${formatNumber(game.minutes)}`}
            >
              <ComparedNumber
                value={game.minutes}
                averageValue={averages.minutes}
              />
            </span>
            <span
              role="cell"
              aria-label={`Field goals made and attempted: ${game.field_goals_made}/${game.field_goals_attempted}`}
            >
              <ComparedPercentage
                made={game.field_goals_made}
                attempted={game.field_goals_attempted}
                averageMade={averages.fieldGoalsMade}
                averageAttempted={averages.fieldGoalsAttempted}
              />
            </span>
            <span
              role="cell"
              aria-label={`Free throws made and attempted: ${game.free_throws_made}/${game.free_throws_attempted}`}
            >
              <ComparedPercentage
                made={game.free_throws_made}
                attempted={game.free_throws_attempted}
                averageMade={averages.freeThrowsMade}
                averageAttempted={averages.freeThrowsAttempted}
              />
            </span>
            <span
              role="cell"
              aria-label={`Points: ${formatNumber(game.points)}`}
            >
              <ComparedNumber
                value={game.points}
                averageValue={averages.points}
              />
            </span>
            <span
              role="cell"
              aria-label={`Rebounds: ${formatNumber(game.rebounds)}`}
            >
              <ComparedNumber
                value={game.rebounds}
                averageValue={averages.rebounds}
              />
            </span>
            <span
              role="cell"
              aria-label={`Assists: ${formatNumber(game.assists)}`}
            >
              <ComparedNumber
                value={game.assists}
                averageValue={averages.assists}
              />
            </span>
            <span
              role="cell"
              aria-label={`Steals: ${formatNumber(game.steals)}`}
            >
              <ComparedNumber
                value={game.steals}
                averageValue={averages.steals}
              />
            </span>
            <span
              role="cell"
              aria-label={`Blocks: ${formatNumber(game.blocks)}`}
            >
              <ComparedNumber
                value={game.blocks}
                averageValue={averages.blocks}
              />
            </span>
            <span
              role="cell"
              aria-label={`Turnovers: ${formatNumber(game.turnovers)}`}
            >
              <ComparedNumber
                value={game.turnovers}
                averageValue={averages.turnovers}
                inverse
              />
            </span>
            <span
              role="cell"
              aria-label={`Three pointers made: ${formatNumber(
                game.three_pointers_made
              )}`}
            >
              <ComparedNumber
                value={game.three_pointers_made}
                averageValue={averages.threePointersMade}
              />
            </span>
            <span
              role="cell"
              aria-label={`Fantasy points: ${formatNumber(
                game.fantasy_points
              )}`}
            >
              <ComparedNumber
                value={game.fantasy_points}
                averageValue={averages.fantasyPoints}
              />
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function PlayerGameLog({
  playerId,
  name,
  onAveragesChange
}: PlayerGameLogProps) {
  const [refreshKey, setRefreshKey] = useState(0);
  const [state, setState] = useState<PlayerLoadState>({
    data: null,
    error: null,
    loading: true
  });

  useEffect(() => {
    const refresh = () => setRefreshKey((current) => current + 1);
    window.addEventListener('basketbase:sync-complete', refresh);
    return () => window.removeEventListener('basketbase:sync-complete', refresh);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setState((previous) => ({ ...previous, loading: true, error: null }));

    fetchPlayerGames(playerId)
      .then((data) => {
        if (cancelled) return;
        onAveragesChange(playerId, calculateAverages(data.games));
        setState({ data, error: null, loading: false });
      })
      .catch((requestError: Error) => {
        if (!cancelled) {
          setState({ data: null, error: requestError.message, loading: false });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [playerId, onAveragesChange, refreshKey]);

  const games = state.data?.games || [];
  const averages = calculateAverages(games);
  const getAverage = (getValue: (game: PlayerGame) => number | string | null) =>
    state.loading ? '…' : formatNumber(average(games, getValue));
  const getAverageAttempts = (
    made: (game: PlayerGame) => number | null,
    attempted: (game: PlayerGame) => number | null
  ) => `${getAverage(made)} / ${getAverage(attempted)}`;

  return (
    <details className="player-stats-player">
      <summary className="player-stats-player-summary">
        <span className="player-stats-player-identity">
          <strong className="player-stats-player-name">
            {state.data?.player_name || name}
          </strong>
        </span>

        <span className="player-stats-average-grid">
          <AverageStat label="MIN" value={getAverage((game) => game.minutes)} />
          <AverageStat
            label="FGM / FGA"
            value={getAverageAttempts(
              (game) => game.field_goals_made,
              (game) => game.field_goals_attempted
            )}
          />
          <AverageStat
            label="FTM / FTA"
            value={getAverageAttempts(
              (game) => game.free_throws_made,
              (game) => game.free_throws_attempted
            )}
          />
          <AverageStat label="PTS" value={getAverage((game) => game.points)} />
          <AverageStat
            label="REB"
            value={getAverage((game) => game.rebounds)}
          />
          <AverageStat label="AST" value={getAverage((game) => game.assists)} />
          <AverageStat label="STL" value={getAverage((game) => game.steals)} />
          <AverageStat label="BLK" value={getAverage((game) => game.blocks)} />
          <AverageStat
            label="TO"
            value={getAverage((game) => game.turnovers)}
          />
          <AverageStat
            label="3PM"
            value={getAverage((game) => game.three_pointers_made)}
          />
          <AverageStat
            label="Fantasy"
            value={getAverage((game) => game.fantasy_points)}
          />
        </span>
      </summary>

      <div className="player-stats-player-details">
        {state.loading && <p role="status">Loading games…</p>}
        {state.error && (
          <p className="player-stats-message error" role="alert">
            {state.error}
          </p>
        )}
        {!state.loading && !state.error && games.length === 0 && (
          <p className="player-stats-message">No games returned yet.</p>
        )}
        {!state.loading && !state.error && games.length > 0 && (
          <PlayerGameRows
            games={games}
            averages={averages}
            playerName={state.data?.player_name || name}
          />
        )}
      </div>
    </details>
  );
}
