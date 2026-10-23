// E04 synthetic Meta receipt normalizer. Pure: no I/O, no state writes.
// This does NOT ratify S0/Meta contracts or authorize C09/status mutations.
const statusTypes = new Set(['api_accepted', 'queued', 'unknown', 'sent', 'definitive_failed']);
const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const validId = x => typeof x === 'string' && /^[A-Za-z0-9_.:-]{1,100}$/.test(x);
const record = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const strict = (x, keys) => record(x) && Object.keys(x).every(k => keys.includes(k));
const error = status => ({ status });
const validInstant = x => typeof x === 'string' && /(Z|[+-]\d\d:\d\d)$/.test(x) && Number.isFinite(Date.parse(x));

/**
 * Scope and booleans below must originate from a trusted synthetic S0 fixture.
 * No data in this function should ever be interpreted as a signed Meta receipt.
 */
export function summarizeTransportEvidence(scope, events) {
  if (!record(scope) || scope.authenticated !== true || scope.authorized !== true || scope.tenantAllowed !== true) return error('DENIED');
  if (!validId(scope.storeId) || !validId(scope.caseId) || !validId(scope.chainId) || !Array.isArray(events)) return error('INVALID_INPUT');
  const ids = new Map();
  const sequences = new Map();
  for (const e of events) {
    if (!strict(e, ['eventId', 'storeId', 'caseId', 'chainId', 'attemptId', 'sequence', 'at', 'status', 'verified', 'isFinal'])) return error('INVALID_INPUT');
    if (![e.eventId, e.storeId, e.caseId, e.chainId, e.attemptId].every(validId) ||
        e.storeId !== scope.storeId || e.caseId !== scope.caseId || e.chainId !== scope.chainId ||
        !Number.isSafeInteger(e.sequence) || e.sequence < 0 || !validInstant(e.at) ||
        !statusTypes.has(e.status) || typeof e.verified !== 'boolean' || typeof e.isFinal !== 'boolean' ||
        (e.status !== 'sent' && e.isFinal)) return error('INVALID_INPUT');
    const identity = JSON.stringify(e);
    if (ids.has(e.eventId)) {
      if (ids.get(e.eventId) !== identity) return error('REVIEW_REQUIRED');
      continue; // exact transport webhook retry
    }
    if (sequences.has(e.sequence)) return error('REVIEW_REQUIRED');
    ids.set(e.eventId, identity);
    sequences.set(e.sequence, e);
  }
  const ordered = [...sequences.values()].sort((a, b) => a.sequence - b.sequence);
  const terminalByAttempt = new Map();
  let consecutiveDefinitiveFailures = 0;
  let verifiedFinalSentAt = null;
  let uncertainProof = false;
  for (const e of ordered) {
    if (e.status !== 'sent' && e.status !== 'definitive_failed') continue;
    if (!e.verified) { uncertainProof = true; continue; }
    const previous = terminalByAttempt.get(e.attemptId);
    if (previous && previous !== e.status) return error('REVIEW_REQUIRED');
    if (previous) continue; // same attempt cannot be counted twice
    terminalByAttempt.set(e.attemptId, e.status);
    if (e.status === 'sent') {
      consecutiveDefinitiveFailures = 0;
      if (e.isFinal) verifiedFinalSentAt = e.at;
    } else {
      consecutiveDefinitiveFailures++;
    }
  }
  if (uncertainProof) return error('REVIEW_REQUIRED'); // don't infer failure chain across unknown delivery
  return {
    status: 'EVIDENCE_ONLY',
    verifiedFinalSentAt,
    consecutiveDefinitiveFailures,
    twoFailureReviewCandidate: consecutiveDefinitiveFailures >= 2,
    uniqueEventCount: ordered.length,
    // No lost/sent-to-customer/commercial mutation is possible from this return.
  };
}
