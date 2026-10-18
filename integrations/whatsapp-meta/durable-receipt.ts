/**
 * WA-01B candidate: fail-closed decision at the boundary between the public
 * Meta webhook and a FUTURE trusted, atomic S0 batch persistence service.
 *
 * This module does not make an HTTP response and does not prove a database
 * commit itself. Never accept a receipt from Meta or an untrusted client.
 * No storage, queues, network calls, tenant resolution or commercial rules.
 */

export type AckDecision =
  | { readonly status: 200; readonly action: 'ACK'; readonly reason: 'ALL_ITEMS_DURABLE' }
  | {
      readonly status: 503;
      readonly action: 'RETRY';
      readonly reason:
        | 'INVALID_RECEIPT'
        | 'COMMIT_UNCONFIRMED'
        | 'INCOMPLETE_BATCH'
        | 'QUARANTINE_POLICY_PENDING';
    };

/**
 * Proposed result from an authenticated INTERNAL batch service, not from
 * S0/029 as presently implemented. S0 must attest a transaction committed,
 * all items retained for replay, and channel/tenant binding verified.
 */
export type DurableBatchReceipt = {
  readonly outcome: 'ACCEPTED_DURABLE' | 'ALREADY_ACCEPTED' | 'QUARANTINED_DURABLE';
  readonly commit_state: 'COMMITTED';
  readonly total: number;
  readonly accepted: number;
  readonly duplicates: number;
  readonly quarantined: number;
};

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function count(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}
const retry = (reason: Extract<AckDecision, { action: 'RETRY' }>['reason']): AckDecision => ({
  status: 503,
  action: 'RETRY',
  reason,
});

/**
 * All events in ONE Meta POST must be committed or safely decided together.
 * Quarantine acknowledgment is deliberately withheld until the separate
 * security/retention/replay policy (DEC-WA-06) is approved.
 *
 * The future trusted port must NEVER issue COMMITTED for a metadata-only
 * record lacking a protected replayable payload reference.
 */
export function decideBatchAck(expectedItems: number, untrustedShape: unknown): AckDecision {
  if (!Number.isSafeInteger(expectedItems) || expectedItems <= 0 || !record(untrustedShape)) {
    return retry('INVALID_RECEIPT');
  }
  const r = untrustedShape;
  if (!count(r.total) || !count(r.accepted) || !count(r.duplicates) || !count(r.quarantined) ||
      !['ACCEPTED_DURABLE', 'ALREADY_ACCEPTED', 'QUARANTINED_DURABLE'].includes(String(r.outcome))) {
    return retry('INVALID_RECEIPT');
  }
  if (r.commit_state !== 'COMMITTED') return retry('COMMIT_UNCONFIRMED');
  if (r.total !== expectedItems || r.accepted + r.duplicates + r.quarantined !== r.total) {
    return retry('INCOMPLETE_BATCH');
  }
  if (r.quarantined > 0 || r.outcome === 'QUARANTINED_DURABLE') {
    return retry('QUARANTINE_POLICY_PENDING');
  }
  if (r.outcome === 'ALREADY_ACCEPTED' && r.accepted !== 0) {
    return retry('INVALID_RECEIPT');
  }
  if (r.outcome === 'ACCEPTED_DURABLE' && r.accepted === 0) {
    return retry('INVALID_RECEIPT');
  }
  return { status: 200, action: 'ACK', reason: 'ALL_ITEMS_DURABLE' };
}
