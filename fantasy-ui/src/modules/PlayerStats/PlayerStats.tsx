import React, { useEffect, useState } from 'react';
import {
  fetchPlayerGames,
  PlayerGameLogResponse,
} from '../../services/playerStatsApi';
import './PlayerStats.css';

const PLAYER_ID = 1628378;

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
                  <td>{game.game_date}</td>
                  <td>{game.matchup}</td>
                  <td>{game.result || '—'}</td>
                  <td>{game.minutes ?? '—'}</td>
                  <td>{game.points ?? '—'}</td>
                  <td>{game.rebounds ?? '—'}</td>
                  <td>{game.assists ?? '—'}</td>
                  <td>{game.steals ?? '—'}</td>
                  <td>{game.blocks ?? '—'}</td>
                  <td>{game.turnovers ?? '—'}</td>
                  <td>{game.three_pointers_made ?? '—'}</td>
                  <td>{game.fantasy_points ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
