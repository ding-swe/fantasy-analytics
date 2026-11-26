import React, { useEffect, useState } from 'react';
import './YahooTeams.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface YahooRosterSnapshot {
  league_name: string;
  captured_at: string;
  teams: {
    team_name: string;
    team_key: string;
    players: { player_key: string; name: string }[];
  }[];
}

export default function YahooTeams() {
  const [snapshot, setSnapshot] = useState<YahooRosterSnapshot | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    async function loadRosters() {
      try {
        const response = await fetch(API_BASE_URL + '/api/yahoo/teams', {
          signal: controller.signal
        });
        if (!response.ok) {
          const body = await response.json().catch(() => null);
          throw new Error(body?.detail || 'Could not load Yahoo teams.');
        }
        const data: YahooRosterSnapshot = await response.json();
        if (!controller.signal.aborted) setSnapshot(data);
      } catch (error) {
        if (!controller.signal.aborted) {
          setError(error instanceof Error ? error.message : 'Could not load Yahoo teams.');
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void loadRosters();
    return () => controller.abort();
  }, [refresh]);

  return (
    <main className="yahoo-teams">
      <header className="yahoo-teams-heading">
        <div>
          <h1>{snapshot?.league_name || 'Yahoo Teams'}</h1>
          {snapshot && (
            <p>
              {snapshot.teams.length} teams · Snapshot captured{' '}
              <time dateTime={snapshot.captured_at}>
                {new Date(snapshot.captured_at).toLocaleString()}
              </time>
            </p>
          )}
        </div>
        <button type="button" onClick={() => setRefresh((value) => value + 1)} disabled={loading}>
          Reload rosters
        </button>
      </header>
      {loading && <p role="status">Loading Yahoo rosters…</p>}
      {error && <p role="alert">{error}</p>}
      {snapshot && (
        <div className="yahoo-team-grid">
          {snapshot.teams.map((team) => (
            <section className="yahoo-team-card" key={team.team_key}>
              <h2>{team.team_name}</h2>
              {team.players.length ? (
                <ul aria-label={team.team_name + ' roster'}>
                  {team.players.map((player) => (
                    <li key={player.player_key}>{player.name}</li>
                  ))}
                </ul>
              ) : (
                <p>No rostered players.</p>
              )}
            </section>
          ))}
        </div>
      )}
      <footer>
        <a href="https://basketball.fantasysports.yahoo.com/">Fantasy data provided by Yahoo Fantasy</a>
      </footer>
    </main>
  );
}
