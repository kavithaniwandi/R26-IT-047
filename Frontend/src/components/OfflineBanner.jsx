import { useNetworkStatus } from '../hooks/useNetworkStatus';

export default function OfflineBanner() {
  const { isOnline, isSyncing, pendingCount, lastSynced, runSync } = useNetworkStatus();

  if (isOnline && pendingCount === 0 && !isSyncing) return null; // nothing to show

  return (
    <div style={{
      padding: '10px 16px',
      marginBottom: '16px',
      borderRadius: '6px',
      fontSize: '14px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: isOnline ? '#d1ecf1' : '#fff3cd',
      border: `1px solid ${isOnline ? '#bee5eb' : '#ffeeba'}`,
      color: isOnline ? '#0c5460' : '#856404',
    }}>
      <span>
        {!isOnline && `🔴 Offline — ${pendingCount} request(s) queued locally`}
        {isOnline && isSyncing && `🔄 Syncing ${pendingCount} pending request(s)...`}
        {isOnline && !isSyncing && pendingCount > 0 &&
          `🟡 ${pendingCount} request(s) pending sync`}
      </span>

      {isOnline && !isSyncing && pendingCount > 0 && (
        <button
          onClick={runSync}
          style={{
            marginLeft: '12px',
            padding: '4px 10px',
            fontSize: '13px',
            cursor: 'pointer',
            borderRadius: '4px',
            border: '1px solid #0c5460',
            background: 'transparent',
          }}
        >
          Sync Now
        </button>
      )}

      {lastSynced && (
        <span style={{ fontSize: '12px', opacity: 0.7, marginLeft: '12px' }}>
          Last synced: {lastSynced.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}