import { getPendingRequests, markSynced, markFailed } from './db';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export async function syncPendingRequests() {
  const pending = await getPendingRequests();

  if (pending.length === 0) {
    return { synced: 0, failed: 0, total: 0 };
  }

  let synced = 0;
  let failed = 0;

  for (const request of pending) {
    try {
      const response = await fetch(`${API_BASE}/api/medical-requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (response.ok) {
        await markSynced(request.localId);
        synced++;
      } else {
        await markFailed(request.localId);
        failed++;
      }
    } catch {
      // Network error — leave as pending to retry later
      console.warn(`Could not sync request ${request.localId}, will retry`);
    }
  }

  return { synced, failed, total: pending.length };
}