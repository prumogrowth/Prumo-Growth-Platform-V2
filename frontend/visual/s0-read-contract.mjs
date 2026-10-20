/** FV-S0-UQ-01 — CANDIDATE ONLY. No transport, authentication or server permission.
 * Follows proposed UQ01–UQ09 read families in document 40, and DOES NOT
 * implement the backend authorization decided by S0/S1.
 * This is a defensive UI boundary for future pre-minimized server projections.
 */

export const S0_READ_PROPOSAL_VERSION = 's0-ui-read-proposal/0.1';

export const PROPOSED_UQ_FAMILIES = Object.freeze([
  'UQ01', 'UQ02', 'UQ03', 'UQ04', 'UQ05',
  'UQ06', 'UQ07', 'UQ08', 'UQ09'
]);

const rejected = Object.freeze({
  accepted: false,
  code: 'UNTRUSTED_READ_PROJECTION',
  records: Object.freeze([]),
  nextCursor: null,
  sourceVersion: null
});

const isRecord = value => value !== null && typeof value === 'object' &&
  !Array.isArray(value) &&
  (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
const nonEmpty = value => typeof value === 'string' && value.trim().length > 0;

/**
 * Checks a candidate read envelope against the authenticated context EXPECTED
 * by the caller. The context MUST originate from a trusted backend; merely
 * matching scope_ref/actor_id strings is NOT authorization or a security proof.
 *
 * Invalid/stale/denied/malformed input returns the same empty result, without
 * echoing raw records, sensitive values, IDs, or denial details.
 */
export function stageProposedS0ReadEnvelope(response, expected) {
  if (!isRecord(expected) || !isRecord(response)) return rejected;
  if (!PROPOSED_UQ_FAMILIES.includes(expected.query_id)) return rejected;
  for (const key of [
    'query_version', 'request_id', 'correlation_id', 'actor_id',
    'scope_ref', 'returned_projection'
  ]) {
    if (!nonEmpty(expected[key]) || response[key] !== expected[key]) return rejected;
  }
  if (response.query_id !== expected.query_id ||
      response.schema_version !== S0_READ_PROPOSAL_VERSION ||
      response.leitura_minimizada !== true ||
      !nonEmpty(response.source_of_truth_version) ||
      !nonEmpty(response.as_of)) return rejected;
  if (!isRecord(response.outcome) || response.outcome.status !== 'APPLIED' ||
      response.outcome.reason_code != null) return rejected;
  if (!Array.isArray(response.records) ||
      !response.records.every(isRecord)) return rejected;
  if (response.next_cursor != null && !nonEmpty(response.next_cursor)) return rejected;

  // Data must already be minimized by S0; this boundary does NOT redact D3/D4.
  // Copy to avoid sharing mutable arrays/records with the envelope producer.
  try {
    const records = structuredClone(response.records);
    return Object.freeze({
      accepted: true,
      code: 'ACCEPTED_FOR_VISUALIZATION',
      records: Object.freeze(records),
      nextCursor: response.next_cursor ?? null,
      sourceVersion: response.source_of_truth_version
    });
  } catch {
    return rejected;
  }
}
