const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface SyncRunStatus {
  id: number;
  status: 'running' | 'succeeded' | 'failed';
  season: string | null;
  date_from: string | null;
  date_to: string | null;
  started_at: string;
  completed_at: string | null;
  completed_through_date: string | null;
  records_processed: number;
  error_message: string | null;
}

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || 'Could not sync NBA game data.');
  }
  return response.json();
}

export async function fetchLatestSync(): Promise<SyncRunStatus | null> {
  const response = await fetch(`${API_BASE_URL}/api/sync/latest`);
  return readResponse<SyncRunStatus | null>(response);
}

export async function startSync(): Promise<SyncRunStatus> {
  const response = await fetch(`${API_BASE_URL}/api/sync`, { method: 'POST' });
  return readResponse<SyncRunStatus>(response);
}

export async function fetchSyncStatus(id: number): Promise<SyncRunStatus> {
  const response = await fetch(`${API_BASE_URL}/api/sync/${id}`);
  return readResponse<SyncRunStatus>(response);
}
