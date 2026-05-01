import { openDB } from 'idb';

const DB_NAME = 'medical-offline-db';
const STORE_NAME = 'medical-requests';
const DB_VERSION = 1;

// ── Open / initialise DB ──────────────────────────────────
function getDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, {
          keyPath: 'localId',
          autoIncrement: true,
        });
        store.createIndex('syncStatus', 'syncStatus'); // 'pending' | 'synced' | 'failed'
        store.createIndex('timestamp', 'timestamp');
      }
    },
  });
}

// ── Save a new request (always offline-first) ─────────────
export async function saveRequest(data) {
  const db = await getDB();
  const record = {
    ...data,
    syncStatus: 'pending',
    timestamp: new Date().toISOString(),
  };
  const localId = await db.add(STORE_NAME, record);
  return { ...record, localId };
}

// ── Get all pending (unsynced) requests ───────────────────
export async function getPendingRequests() {
  const db = await getDB();
  return db.getAllFromIndex(STORE_NAME, 'syncStatus', 'pending');
}

// ── Mark a request as synced ──────────────────────────────
export async function markSynced(localId) {
  const db = await getDB();
  const tx = db.transaction(STORE_NAME, 'readwrite');
  const record = await tx.store.get(localId);
  if (record) {
    record.syncStatus = 'synced';
    await tx.store.put(record);
  }
  await tx.done;
}

// ── Mark a request as failed (optional, for error tracking) ─
export async function markFailed(localId) {
  const db = await getDB();
  const tx = db.transaction(STORE_NAME, 'readwrite');
  const record = await tx.store.get(localId);
  if (record) {
    record.syncStatus = 'failed';
    await tx.store.put(record);
  }
  await tx.done;
}

// ── Get all requests (for history/audit view) ─────────────
export async function getAllRequests() {
  const db = await getDB();
  return db.getAll(STORE_NAME);
}

// ── Count pending requests ────────────────────────────────
export async function countPending() {
  const pending = await getPendingRequests();
  return pending.length;
}