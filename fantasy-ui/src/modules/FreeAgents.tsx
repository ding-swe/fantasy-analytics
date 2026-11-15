import React, { useCallback, useEffect, useState } from 'react';
import PlayerTable from './PlayerStats/PlayerTable';
import { PlayerAverageStats } from './PlayerStats/PlayerGameLog';
import { fetchFreeAgents, FreeAgentList } from '../services/freeAgentsApi';
import './PlayerStats/PlayerStats.css';

const emptyAverages = (fantasyPoints: number): PlayerAverageStats => ({
  minutes: null,
  fieldGoalsMade: null,
  fieldGoalsAttempted: null,
  freeThrowsMade: null,
  freeThrowsAttempted: null,
  points: null,
  rebounds: null,
  assists: null,
  steals: null,
  blocks: null,
  turnovers: null,
  threePointersMade: null,
  fantasyPoints
});

export default function FreeAgents() {
  const [data, setData] = useState<FreeAgentList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [averagesByPlayer, setAveragesByPlayer] = useState<
    Record<number, PlayerAverageStats>
  >({});

  useEffect(() => {
    let cancelled = false;

    fetchFreeAgents()
      .then((freeAgentList) => {
        if (cancelled) return;
        setData(freeAgentList);
        setAveragesByPlayer(
          Object.fromEntries(
            freeAgentList.players.map((player) => [
              player.playerId,
              emptyAverages(player.averageFantasyPoints)
            ])
          )
        );
        setLoading(false);
      })
      .catch((requestError: Error) => {
        if (!cancelled) {
          setError(requestError.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

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
        <h1>Free agents</h1>
        <p>
          Top 20 unrostered players · ranked by average fantasy points over the
          last 7 games
        </p>
      </header>

      {loading && <p className="player-stats-message">Loading free agents…</p>}
      {error && (
        <p className="player-stats-message error" role="alert">
          {error}
        </p>
      )}
      {!loading && !error && data?.players.length === 0 && (
        <p className="player-stats-message">
          No free-agent game data is available for {data.season} yet.
        </p>
      )}
      {!loading && !error && data && data.players.length > 0 && (
        <PlayerTable
          players={data.players}
          averagesByPlayer={averagesByPlayer}
          onAveragesChange={handleAveragesChange}
        />
      )}
    </main>
  );
}
