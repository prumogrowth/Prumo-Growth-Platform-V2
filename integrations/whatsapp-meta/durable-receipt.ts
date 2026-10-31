/**
 * WA-01B — Legacy shape-only receipt review, permanently fail-closed.
 *
 * Earlier code emitted {status:200,action:'ACK'} after checking counters and
 * a caller-supplied "COMMITTED". This is NOT cryptographic or S0 persistence
 * evidence and cannot establish HTTP authority. Keeping the old function
 * name avoids an unsafe, silent replacement in legacy callers.
 *
 * This module must never emit HTTP status/action, perform network/storage,
 * authorize a reply to Meta, or infer a human/commercial decision.
 */

export type AckDecision=Readonly<{
  decision:'DENIED_NO_HTTP_AUTHORITY';
  reason:'UNTRUSTED_RECEIPT_PROVENANCE';
  ack_allowed:false;
  http_ack_allowed:false;
  http_response_authorized:false;
  production_authorized:false;
  commit_verified:false;
  durable_receipt_verified:false;
}>;

/** Historical proposed metadata, NOT a signed receipt and NOT S0 authority. */
export type DurableBatchReceipt=Readonly<{
  outcome:'ACCEPTED_DURABLE'|'ALREADY_ACCEPTED'|'QUARANTINED_DURABLE';
  commit_state:'COMMITTED';
  total:number;
  accepted:number;
  duplicates:number;
  quarantined:number;
}>;

const DENIED:AckDecision=Object.freeze({
  decision:'DENIED_NO_HTTP_AUTHORITY',
  reason:'UNTRUSTED_RECEIPT_PROVENANCE',
  ack_allowed:false,
  http_ack_allowed:false,
  http_response_authorized:false,
  production_authorized:false,
  commit_verified:false,
  durable_receipt_verified:false,
});

/**
 * A counter-shaped or self-asserted COMMITTED object has zero HTTP authority.
 * Ignore the entire object (including getters and Proxies) so no attacker
 * input can promote a synthetic receipt into an ACK. Only a separately
 * ratified, authenticated S0 service/transport contract could do that,
 * and that integration does not exist in this function.
 */
export function decideBatchAck(
  _expectedItems:number,
  _untrustedShape:unknown,
):AckDecision{
  return DENIED;
}
