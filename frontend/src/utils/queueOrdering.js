const SEVERITY_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

export function compareQueuedPatients(first, second) {
  const severity = (SEVERITY_ORDER[first.severity] ?? 3) - (SEVERITY_ORDER[second.severity] ?? 3);
  if (severity) return severity;
  // Equal-severity patients are shown in arrival order, including older records.
  const arrival = (patient) => Date.parse(patient.submittedAt || patient.submitted_at || '') || 0;
  return arrival(first) - arrival(second) || String(first.id || '').localeCompare(String(second.id || ''));
}
