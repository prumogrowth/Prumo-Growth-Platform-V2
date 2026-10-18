import { test } from 'node:test';
import assert from 'node:assert/strict';
import { decideBatchAck } from './durable-receipt.ts';

const committed = (overrides: Record<string, unknown> = {}) => ({
  outcome: 'ACCEPTED_DURABLE', commit_state: 'COMMITTED',
  total: 4, accepted: 4, duplicates: 0, quarantined: 0, ...overrides,
});
const ack = { status: 200, action: 'ACK', reason: 'ALL_ITEMS_DURABLE' };

test('WA-ACK-01: one committed 2+2 aggregate permits ACK', () => {
  assert.deepEqual(decideBatchAck(4, committed()), ack);
});
test('WA-ACK-02: complete mixed accepted and duplicates permits ACK', () => {
  assert.deepEqual(decideBatchAck(4, committed({ accepted: 2, duplicates: 2 })), ack);
});
test('WA-ACK-03: all compatible duplicates permit ACK', () => {
  assert.deepEqual(decideBatchAck(4, committed({
    outcome: 'ALREADY_ACCEPTED', accepted: 0, duplicates: 4,
  })), ack);
});
test('WA-ACK-04: no commit never permits 200', () => {
  assert.equal(decideBatchAck(4, committed({ commit_state: 'ROLLED_BACK' })).status, 503);
  assert.equal(decideBatchAck(4, { outcome: 'RETRYABLE_STORAGE_FAILURE' }).status, 503);
});
test('WA-ACK-05: partial commit accounting never permits 200', () => {
  assert.deepEqual(decideBatchAck(4, committed({ accepted: 3 })), {
    status: 503, action: 'RETRY', reason: 'INCOMPLETE_BATCH',
  });
  assert.equal(decideBatchAck(4, committed({ total: 3, accepted: 3 })).status, 503);
});
test('WA-ACK-06: quarantine withholds ACK until policy approval', () => {
  assert.deepEqual(decideBatchAck(4, committed({
    outcome: 'QUARANTINED_DURABLE', accepted: 3, quarantined: 1,
  })), { status: 503, action: 'RETRY', reason: 'QUARANTINE_POLICY_PENDING' });
  assert.equal(decideBatchAck(4, committed({ accepted: 3, quarantined: 1 })).status, 503);
});
test('WA-ACK-07: rejects inconsistent outcome labels', () => {
  assert.equal(decideBatchAck(4, committed({ outcome: 'ALREADY_ACCEPTED' })).status, 503);
  assert.equal(decideBatchAck(4, committed({ accepted: 0, duplicates: 4 })).status, 503);
  assert.equal(decideBatchAck(4, committed({ outcome: 'UNKNOWN' })).status, 503);
});
test('WA-ACK-08: rejects missing, null, and arbitrary receipts', () => {
  for (const receipt of [null, undefined, [], {}, 'COMMITTED', false]) {
    assert.equal(decideBatchAck(4, receipt).status, 503);
  }
});
test('WA-ACK-09: invalid event count and negative/decimal counters fail closed', () => {
  for (const expected of [0, -1, NaN, Infinity, 1.5]) {
    assert.equal(decideBatchAck(expected, committed()).status, 503);
  }
  for (const accepted of [-1, 1.5, '4', Number.MAX_SAFE_INTEGER + 1]) {
    assert.equal(decideBatchAck(4, committed({ accepted })).status, 503);
  }
});
test('WA-ACK-10: unsupported batch receipt cannot be mistaken for S0/029 ACK', () => {
  const s029 = { outcome: 'ACCEPTED_DURABLE', accepted: 4, duplicates: 0,
    concessionaria_id: 'fixture_uuid' };
  assert.equal(decideBatchAck(4, s029).status, 503);
});
