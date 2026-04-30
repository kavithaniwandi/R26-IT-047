import { useState, useEffect, useCallback } from 'react';
import { syncPendingRequests } from '../services/syncService';
import { countPending } from '../services/db';

export function useNetworkStatus() {
  const [isOnline, setIsOnline]         = useState(navigator.onLine);
  const [isSyncing, setIsSyncing]       = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastSynced, setLastSynced]     = useState(null);

  // Refresh the pending count from IndexedDB
  const refreshPendingCount = useCallback(async () => {
    const count = await countPending();
    setPendingCount(count);
  }, []);

  // Run sync and update state
  const runSync = useCallback(async () => {
    if (!navigator.onLine) return;
    setIsSyncing(true);
    try {
      const result = await syncPendingRequests();
      if (result.synced > 0) {
        setLastSynced(new Date());
      }
      await refreshPendingCount();
    } finally {
      setIsSyncing(false);
    }
  }, [refreshPendingCount]);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      runSync();               // auto-sync when connection returns
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial count + sync attempt on mount
    refreshPendingCount();
    runSync();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [runSync, refreshPendingCount]);

  return { isOnline, isSyncing, pendingCount, lastSynced, runSync, refreshPendingCount };
}