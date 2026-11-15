import React, { useEffect, useState } from 'react';
import {
  fetchPlayerGames,
  PlayerGameLogResponse,
} from '../../services/playerStatsApi';
import './PlayerStats.css';

const PLAYER_ID = 1628378;

function formatNumber(value: number | string | null): string {
  if (value === null || value === '') return '—';

  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(1) : String(value);
}

function formatMadeAttempted(
  made: number | null,
  attempted: number | null
): string {
  if (made === null || attempted === null) return '—';
  return `${made}/${attempted}`;
}

function formatDate(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return value;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  let suffix = 'th';
  if (day % 100 < 11 || day % 100 > 13) {
    if (day % 10 === 1) suffix = 'st';
    else if (day % 10 === 2) suffix = 'nd';
    else if (day % 10 === 3) suffix = 'rd';
  }
  const monthName = new Date(year, month - 1, day).toLocaleString('en-US', {
    month: 'long',
  });

  return `${monthName} ${day}${suffix}, ${year}`;
}

export default function PlayerStats() {
  const [data, setData] = useState<PlayerGameLogResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlayerGames(PLAYER_ID)
      .then(setData)
      .catch((requestError: Error) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="player-stats-page">
      <header className="player-stats-heading">
        <p className="player-stats-eyebrow">NBA player data</p>
        <h1>{data?.player_name || 'Player game log'}</h1>
        <p>Most recent games · {data?.season || 'current season'}</p>
      </header>

      {loading && <p role="status">Loading player stats…</p>}
      {error && <p className="player-stats-message error" role="alert">{error}</p>}
      {!loading && !error && data?.games.length === 0 && (
        <p className="player-stats-message">No games were returned for this player yet.</p>
      )}

      {!loading && !error && data && data.games.length > 0 && (
        <div className="player-stats-table-wrap">
          <table className="player-stats-table">
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Matchup</th>
                <th scope="col">Result</th>
                <th scope="col">MIN</th>
                <th scope="col">FGM / FGA</th>
                <th scope="col">FTM / FTA</th>
                <th scope="col">PTS</th>
                <th scope="col">REB</th>
                <th scope="col">AST</th>
                <th scope="col">STL</th>
                <th scope="col">BLK</th>
                <th scope="col">TO</th>
                <th scope="col">3PM</th>
                <th scope="col">Fantasy</th>
              </tr>
            </thead>
            <tbody>
              {data.games.map((game) => (
                <tr key={game.game_id}>
                  <td>{formatDate(game.game_date)}</td>
                  <td>{game.matchup}</td>
                  <td>{game.result || '—'}</td>
                  <td>{formatNumber(game.minutes)}</td>
                  <td>
                    {formatMadeAttempted(
                      game.field_goals_made,
                      game.field_goals_attempted
                    )}
                  </td>
                  <td>
                    {formatMadeAttempted(
                      game.free_throws_made,
                      game.free_throws_attempted
                    )}
                  </td>
                  <td>{formatNumber(game.points)}</td>
                  <td>{formatNumber(game.rebounds)}</td>
                  <td>{formatNumber(game.assists)}</td>
                  <td>{formatNumber(game.steals)}</td>
                  <td>{formatNumber(game.blocks)}</td>
                  <td>{formatNumber(game.turnovers)}</td>
                  <td>{formatNumber(game.three_pointers_made)}</td>
                  <td>{formatNumber(game.fantasy_points)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
