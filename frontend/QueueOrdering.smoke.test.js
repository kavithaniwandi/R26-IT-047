import assert from 'node:assert/strict';
import { compareQueuedPatients } from './src/utils/queueOrdering.js';

const patients = [
  { id: 'low-later', severity: 'LOW', submittedAt: '2026-10-18T10:00:00Z', should_queue: false },
  { id: 'medium', severity: 'MEDIUM' },
  { id: 'critical', severity: 'CRITICAL' },
  { id: 'low-first', severity: 'LOW', submitted_at: '2026-10-18T09:00:00Z' },
  { id: 'high', severity: 'HIGH' },
];
assert.deepEqual([...patients].sort(compareQueuedPatients).map((p) => p.id),
  ['critical', 'high', 'medium', 'low-first', 'low-later']);
assert.equal(patients.length, 5);
assert.equal(compareQueuedPatients({ id: 'same', severity: 'LOW' }, { id: 'same', severity: 'LOW' }), 0);
console.log('PASS every patient retained, severity ordering and equal-severity arrival order');
