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

  useEffect(() => {
    if (!sync || sync.status !== 'running') return;
    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const latest = await fetchSyncStatus(sync.id);
        if (cancelled) return;
        setSync(latest);
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
  }, [sync?.id, sync?.status]);

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
  const complete =
    !running && requestError === null && sync?.status === 'succeeded';
  const failed = !running && (sync?.status === 'failed' || requestError !== null);
  const label = running
    ? 'Syncing'
    : complete
    ? 'Sync Complete'
    : failed
    ? 'Sync Failed'
    : 'Sync';

  return (
    <button
      type="button"
      className={`sync-button${running ? ' syncing' : ''}${
        complete ? ' complete' : ''
      }${failed ? ' failed' : ''}`}
      onClick={handleClick}
      disabled={running}
      title={requestError || (sync?.error_message ?? 'Sync NBA data to today')}
      aria-live="polite"
    >
      {running && <span className="sync-spinner" aria-hidden="true" />}
      {label}
    </button>
  );
}
