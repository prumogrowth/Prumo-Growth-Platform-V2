import test from 'node:test';
import assert from 'node:assert/strict';
import { summarizeTransportEvidence as reduce } from '../transport-evidence.mjs';
const ctx = () => ({ authenticated: true, authorized: true, tenantAllowed: true, storeId: 'A', caseId: 'K1', chainId: 'C1' });
const ev = (n, status, attemptId = 'A' + n, extra = {}) => ({
  eventId: 'e' + n, storeId: 'A', caseId: 'K1', chainId: 'C1', attemptId,
  sequence: n, at: '2026-11-01T' + String(n).padStart(2, '0') + ':00:00Z',
  status, verified: true, isFinal: false, ...extra,
});
const must = (events, status, tweak = {}) => assert.equal(reduce({ ...ctx(), ...tweak }, events).status, status);

test('empty evidence has no send or losses', () => assert.deepEqual(reduce(ctx(), []), {status: 'EVIDENCE_ONLY', verifiedFinalSentAt: null, consecutiveDefinitiveFailures: 0, twoFailureReviewCandidate: false, uniqueEventCount: 0}));
test('accepted+queued+unknown are not sent', () => {
  const r = reduce(ctx(), [ev(1, 'api_accepted'), ev(2, 'queued'), ev(3, 'unknown')]);
  assert.equal(r.verifiedFinalSentAt, null); assert.equal(r.consecutiveDefinitiveFailures, 0);
});
test('verified final sent captures final timestamp', () => assert.equal(reduce(ctx(), [ev(1, 'sent', 'A1', {isFinal: true})]).verifiedFinalSentAt, '2026-11-01T01:00:00Z'));
test('ordinary sent does not set final marker', () => assert.equal(reduce(ctx(), [ev(1, 'sent')]).verifiedFinalSentAt, null));
test('one definitive failure is not 2', () => assert.equal(reduce(ctx(), [ev(1, 'definitive_failed')]).twoFailureReviewCandidate, false));
test('two distinct consecutive failures only suggest review', () => {
  const r = reduce(ctx(), [ev(1, 'definitive_failed'), ev(2, 'definitive_failed')]);
  assert.equal(r.twoFailureReviewCandidate, true); assert.equal(r.consecutiveDefinitiveFailures, 2); assert.equal('commercialStatus' in r, false);
});
test('verified sent between failures resets counter', () => {
  const r = reduce(ctx(), [ev(1, 'definitive_failed'), ev(2, 'sent'), ev(3, 'definitive_failed')]);
  assert.equal(r.consecutiveDefinitiveFailures, 1); assert.equal(r.twoFailureReviewCandidate, false);
});
test('unknown does not convert into definitive failure', () => assert.equal(reduce(ctx(), [ev(1, 'definitive_failed'), ev(2, 'unknown')]).consecutiveDefinitiveFailures, 1));
test('out-of-order input normalized by S0 sequence', () => {
  const r = reduce(ctx(), [ev(3, 'definitive_failed'), ev(1, 'definitive_failed'), ev(2, 'sent')]);
  assert.equal(r.consecutiveDefinitiveFailures, 1); assert.equal(r.twoFailureReviewCandidate, false);
});
test('duplicate exact webhook event ignored', () => {
  const one = ev(1, 'definitive_failed'); const r = reduce(ctx(), [one, one, {...one}]);
  assert.equal(r.uniqueEventCount, 1); assert.equal(r.consecutiveDefinitiveFailures, 1);
});
test('duplicate terminal status on same attempt counted once', () => {
  const r = reduce(ctx(), [ev(1, 'definitive_failed', 'A1'), ev(2, 'definitive_failed', 'A1')]);
  assert.equal(r.consecutiveDefinitiveFailures, 1);
});
test('contradictory sent and failed on same attempt goes to review', () => must([ev(1, 'sent', 'A1'), ev(2, 'definitive_failed', 'A1')], 'REVIEW_REQUIRED'));
test('conflicting payload for one event ID goes to review', () => must([ev(1, 'sent'), {...ev(1, 'sent'), status: 'queued'}], 'REVIEW_REQUIRED'));
test('colliding sequence for different events goes to review', () => must([ev(1, 'sent'), {...ev(2, 'sent'), sequence: 1}], 'REVIEW_REQUIRED'));
test('unverified sent quarantines failure chain', () => must([ev(1, 'definitive_failed'), ev(2, 'sent', 'A2', {verified: false}), ev(3, 'definitive_failed')], 'REVIEW_REQUIRED'));
test('unverified definitive fail quarantines', () => must([ev(1, 'definitive_failed', 'A1', {verified: false})], 'REVIEW_REQUIRED'));
test('revoked authorization precedes malformed input', () => must([{invalid: true}], 'DENIED', {authorized: false}));
test('tenant authorization must be explicit', () => must([], 'DENIED', {tenantAllowed: undefined}));
test('cross-store event rejected', () => must([ev(1, 'sent', 'A1', {storeId: 'B'})], 'INVALID_INPUT'));
test('cross-case event rejected', () => must([ev(1, 'sent', 'A1', {caseId: 'K2'})], 'INVALID_INPUT'));
test('cross-chain event rejected', () => must([ev(1, 'sent', 'A1', {chainId: 'C2'})], 'INVALID_INPUT'));
test('unlisted event status rejected', () => must([ev(1, 'delivered')], 'INVALID_INPUT'));
test('unverified API accepted carries no delivery proof', () => assert.equal(reduce(ctx(), [ev(1, 'api_accepted', 'A1', {verified: false})]).verifiedFinalSentAt, null));
test('cannot mark queued event as final', () => must([ev(1, 'queued', 'A1', {isFinal: true})], 'INVALID_INPUT'));
test('unknown keys rejected', () => must([ev(1, 'sent', 'A1', {commercialStatus: 'perdido'})], 'INVALID_INPUT'));
test('final verified sent then failure remains a source date not C09 action', () => {
  const r = reduce(ctx(), [ev(1, 'sent', 'A1', {isFinal:true}), ev(2, 'definitive_failed', 'A2')]);
  assert.equal(r.verifiedFinalSentAt, '2026-11-01T01:00:00Z'); assert.equal('c09Status' in r, false);
});
test('final sent replay does not change date', () => {
  const e = ev(1, 'sent', 'A1', {isFinal: true}); assert.equal(reduce(ctx(), [e, e]).verifiedFinalSentAt, e.at);
});
test('final sent status requires independent verified receipt', () => must([ev(1, 'sent', 'A1', {isFinal: true, verified: false})], 'REVIEW_REQUIRED'));

test('131049 is quarantined rather than counted as technical loss', () => must([ev(1, 'definitive_failed', 'A1', {errorCode: 131049})], 'META_ECOSYSTEM_REVIEW'));
test('two 131049 events never produce technical loss candidate', () => must([ev(1, 'definitive_failed', 'A1', {errorCode: 131049}), ev(2, 'definitive_failed', 'A2', {errorCode: 131049})], 'META_ECOSYSTEM_REVIEW'));
test('unknown provider error remains review pending Meta decision', () => must([ev(1, 'definitive_failed', 'A1', {errorCode: 131026})], 'REVIEW_REQUIRED'));
test('provider error cannot masquerade as sent receipt', () => must([ev(1, 'sent', 'A1', {errorCode: 131049})], 'INVALID_INPUT'));
test('provider error without verification is quarantined', () => must([ev(1, 'definitive_failed', 'A1', {errorCode: 131049, verified: false})], 'REVIEW_REQUIRED'));
