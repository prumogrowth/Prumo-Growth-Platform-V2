/** S0 command-result presentation boundary — CANDIDATE only, no transport.
 * Mirrors conceptual C01–C24 outcomes, not live auth or financial authority.
 * Actor/session, server signature, idempotency and effect truth MUST be verified
 * by S0. Never interpret API/provider acceptance as commercial confirmation.
 */
export const S0_COMMAND_RESULT_PROPOSAL = 's0-command-result-proposal/0.1';
export const S0_COMMAND_OUTCOMES = Object.freeze([
  'APPLIED', 'ALREADY_APPLIED', 'ACCEPTED_FOR_PROCESSING',
  'PENDING_EXTERNAL', 'UNCERTAIN_EXTERNAL', 'REJECTED'
]);
// C13 is historical and not a Consultor UI action after FV-DOC-03 §3.
// This boundary does not ratify any command or authorize its execution.
// Buttons to request C14/Meta/AI/MCP/admin remain unavailable.
export const HUMAN_COMMAND_IDS = Object.freeze([
  'C11', 'C12', 'C15', 'C16', 'C17', 'C18'
]);
const ALLOWED_KEYS = Object.freeze([
  'contract_id', 'contract_version', 'request_id', 'correlation_id',
  'actor_id', 'scope_ref', 'aggregate_ref', 'expected_version'
]);
const isPlain = o => o !== null && typeof o === 'object' &&
  !Array.isArray(o) && (Object.getPrototypeOf(o) === Object.prototype ||
  Object.getPrototypeOf(o) === null);
const str = x => typeof x === 'string' && x.length > 0 && x.trim() === x;

const reject = Object.freeze({
  accepted:false, displayState:'untrusted', hasVerifiedEffect:false,
  canRefresh:false, code:'UNTRUSTED_COMMAND_RESULT'
});

/** This only STAGES a claimed backend result for display and reread.
 * Matching strings and self-declared effect confirmation cannot authenticate
 * a caller or prove a payment/sale. Never enable another privileged action
 * from this function alone. S0 needs authenticated session and audit.
 */
export function stageCandidateCommandResult(response, expected) {
  if (!isPlain(response) || !isPlain(expected) ||
      !HUMAN_COMMAND_IDS.includes(expected.contract_id)) return reject;
  for (const key of ALLOWED_KEYS)
    if (!str(expected[key]) || response[key] !== expected[key]) return reject;
  if (response.schema_version !== S0_COMMAND_RESULT_PROPOSAL ||
      !isPlain(response.outcome) ||
      !S0_COMMAND_OUTCOMES.includes(response.outcome.status)) return reject;
  const status=response.outcome.status;
  const applied=status==='APPLIED' || status==='ALREADY_APPLIED';
  if (applied) {
    // Effect identifiers and versions must be authoritative in S0; these
    // fields alone are only STRUCTURAL evidence, not authentic proof.
    if (response.outcome.confirmed_persisted !== true ||
        !str(response.outcome.effect_id) ||
        !str(response.outcome.source_of_truth_version) ||
        response.outcome.reason_code != null) return reject;
    return Object.freeze({
      accepted:true, displayState:'claimed_applied', hasVerifiedEffect:false,
      canRefresh:true, code:status
    });
  }
  if (response.outcome.confirmed_persisted === true ||
      response.outcome.effect_id != null ||
      response.outcome.source_of_truth_version != null) return reject;
  if (status === 'REJECTED') {
    if (!str(response.outcome.reason_code)) return reject;
    // Do not echo arbitrary reason/details or personally identifying data.
    return Object.freeze({
      accepted:true, displayState:'rejected', hasVerifiedEffect:false,
      canRefresh:true, code:'REJECTED'
    });
  }
  if (response.outcome.reason_code != null) return reject;
  return Object.freeze({
    accepted:true, displayState:'pending', hasVerifiedEffect:false,
    canRefresh:true, code:status
  });
}
