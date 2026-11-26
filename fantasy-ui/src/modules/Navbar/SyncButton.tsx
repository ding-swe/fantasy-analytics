import React, { useEffect, useState } from 'react';
import {
  fetchLatestSync,
  fetchSyncStatus,
  startSync,
  SyncRunStatus
} from '../../services/syncApi';

export default function SyncButton() {
  const [sync, setSync] = useState<SyncRunStatus | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchLatestSync()
      .then((latest) => {
        if (!cancelled && latest?.status === 'running') setSync(latest);
      })
      .catch((error: Error) => {
        if (!cancelled) setRequestError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const runningSyncId = sync?.status === 'running' ? sync.id : null;

  useEffect(() => {
    if (runningSyncId === null) return;
    let yahooNotified = false;
    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const latest = await fetchSyncStatus(runningSyncId);
        if (cancelled) return;
        setRequestError(null);
        setSync(latest);
        if (
          !yahooNotified &&
          (latest.yahoo_status === 'succeeded' || latest.yahoo_status === 'unchanged')
        ) {
          yahooNotified = true;
          window.dispatchEvent(new Event('basketbase:yahoo-rosters-synced'));
        }
        if (latest.status === 'succeeded') {
          window.dispatchEvent(new Event('basketbase:sync-complete'));
        } else if (latest.status === 'running') {
          timeout = setTimeout(poll, 2000);
        }
      } catch (error) {
        if (!cancelled) {
          setRequestError((error as Error).message);
          timeout = setTimeout(poll, 5000);
        }
      }
    };

    timeout = setTimeout(poll, 1200);
    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [runningSyncId]);

  const handleClick = async () => {
    setRequestError(null);
    setStarting(true);
    try {
      const started = await startSync();
      setSync(started);
    } catch (error) {
      setRequestError((error as Error).message);
    } finally {
      setStarting(false);
    }
  };

  const running = starting || sync?.status === 'running';
  const yahooFailed = sync?.yahoo_status === 'failed' || sync?.yahoo_status === 'needs_authorization';
  const yahooSynced = sync?.yahoo_status === 'succeeded' || sync?.yahoo_status === 'unchanged';
  const nbaSynced = sync?.status === 'succeeded';
  const complete = !running && !requestError && nbaSynced && !yahooFailed;
  const failed = !running && Boolean(requestError || sync?.status === 'failed' || yahooFailed);
  let label = 'Sync';
  if (running) label = yahooSynced ? 'Yahoo synced · NBA syncing' : 'Syncing';
  else if (complete) label = 'Sync Complete';
  else if (requestError) label = 'Sync Failed';
  else if (sync?.yahoo_status === 'needs_authorization') label = 'Yahoo sign-in needed';
  else if (nbaSynced && yahooFailed) label = 'NBA synced · Yahoo failed';
  else if (yahooSynced && sync?.status === 'failed') label = 'Yahoo synced · NBA failed';
  else if (failed) label = 'Sync Failed';

  const details = [
    requestError,
    sync?.error_message ? 'NBA: ' + sync.error_message : null,
    sync?.yahoo_error_message ? 'Yahoo: ' + sync.yahoo_error_message : null
  ].filter(Boolean).join(' ');

  return (
    <button
      type="button"
      className={`sync-button${running ? ' syncing' : ''}${
        complete ? ' complete' : ''
      }${failed ? ' failed' : ''}`}
      onClick={handleClick}
      disabled={running}
      title={details || 'Sync Yahoo rosters and NBA game data'}
      aria-live="polite"
    >
      {running && <span className="sync-spinner" aria-hidden="true" />}
      {label}
    </button>
  );
}
