import React, { useCallback, useEffect, useState } from 'react';
import { PlayerAverageStats } from './PlayerGameLog';
import PlayerTable from './PlayerTable';
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
