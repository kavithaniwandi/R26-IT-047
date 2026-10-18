export const SESSION_KEY = 'severityQueueSession';
export const STORAGE_KEY = 'priorityApplications';

export function readTriageSession() {
  const raw = localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  const session = JSON.parse(raw);
  if (!session?.session_id || !session?.camp || !Array.isArray(session.mos)) {
    throw new Error('The active session is invalid. Return to camp setup.');
  }
  return session;
}

export const pendingPatientKey = (sessionId, patientId) => `pendingTriagePatient:${sessionId}${patientId ? `:${patientId}` : ''}`;

export function readPendingPatients(sessionId) {
  const prefix = pendingPatientKey(sessionId);
  return Object.keys(localStorage)
    .filter((key) => key === prefix || key.startsWith(`${prefix}:`))
    .map((key) => JSON.parse(localStorage.getItem(key)))
    .filter((entry) => entry?.session_id === sessionId && entry?.id);
}

// Older versions displayed local-only records as saved. Keep those recoverable
// instead of discarding them when replacing the queue with server data.
export function recoverLocalPatients(session, confirmed = []) {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  let cached;
  try { cached = JSON.parse(raw); } catch { return; }
  if (!Array.isArray(cached)) return;
  for (const patient of cached) {
    const belongs = patient.session_id === session.session_id ||
      (!patient.session_id && patient.camp?.id === session.camp.id);
    if (!belongs || !patient.id || confirmed.some((p) => p.id === patient.id)) continue;
    const entry = { ...patient, session_id: session.session_id };
    localStorage.setItem(pendingPatientKey(session.session_id, entry.id), JSON.stringify(entry));
  }
}

export function cacheSessionPatients(session, patients) {
  const raw = localStorage.getItem(STORAGE_KEY);
  let cached;
  try {
    cached = JSON.parse(raw || '[]');
    if (!Array.isArray(cached)) throw new Error('Invalid cache format');
  } catch {
    // Preserve unreadable legacy data before rebuilding the disposable cache.
    localStorage.setItem(`${STORAGE_KEY}:unreadable`, raw || '');
    cached = [];
    console.warn('[triage] Unreadable patient cache preserved; rebuilding from server.');
  }
  const otherSessions = cached.filter((p) => p.session_id
    ? p.session_id !== session.session_id
    : p.camp?.id !== session.camp.id);
  const next = [...patients, ...otherSessions];
  if (next.length) localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  else localStorage.removeItem(STORAGE_KEY);
}

export async function loadSessionPatients(api, sessionId) {
  const patients = [];
  let total;
  do {
    const page = await api.getTriagePatients({ session_id: sessionId, skip: patients.length, limit: 500 });
    if (!Array.isArray(page?.patients) || !Number.isInteger(page.total)) {
      throw new Error('The server returned an invalid patient list.');
    }
    total = page.total;
    if (!page.patients.length && patients.length < total) {
      throw new Error('The patient list is incomplete. Please refresh.');
    }
    patients.push(...page.patients);
  } while (patients.length < total);
  return patients;
}
