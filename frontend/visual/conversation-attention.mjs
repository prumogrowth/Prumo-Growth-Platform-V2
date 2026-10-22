/** Single two-state badge for inbox conversations — synthetic contract only.
 * This file does not mark messages read, run a timer, check Meta receipts,
 * authenticate a user or grant access to conversation/customer data.
 *
 * For real use S0 must provide per-operator read and human-reply evidence.
 * A manager opening a conversation must NEVER mark it read on behalf of
 * an operator. An unread count is not itself proof of response pending.
 */
export const ATTENTION_PROPOSAL_VERSION = 'ui-attention-proposal/0.1';
const isPlain = o => o !== null && typeof o === 'object' && !Array.isArray(o) &&
  (Object.getPrototypeOf(o) === Object.prototype || Object.getPrototypeOf(o) === null);
const ATTENTION_EMPTY = Object.freeze({kind:'none',count:null,label:null});

/** Accepts a source-minimized per-case projection, never raw message content.
 * The result has exactly ONE visual state: unread numbered or read awaiting
 * response unnumbered; those two states cannot display simultaneously.
 */
export function stageConversationAttention(projection) {
  if (!isPlain(projection) ||
      projection.schema_version !== ATTENTION_PROPOSAL_VERSION ||
      !Number.isSafeInteger(projection.unread_inbound_count) ||
      projection.unread_inbound_count < 0 ||
      typeof projection.operator_read_confirmed !== 'boolean' ||
      typeof projection.human_reply_pending !== 'boolean') return ATTENTION_EMPTY;
  const count=projection.unread_inbound_count;
  if (count > 0) return Object.freeze({
    kind:'unread',count:Math.min(count,99),
    label:count > 99 ? 'Mais de 99 mensagens não lidas' :
      count === 1 ? '1 mensagem não lida' : count+' mensagens não lidas'
  });
  if(projection.operator_read_confirmed && projection.human_reply_pending)
    return Object.freeze({
      kind:'read_awaiting_reply',count:null,
      label:'Visualizada pelo titular; resposta humana pendente'
    });
  return ATTENTION_EMPTY;
}

/** A supervisory read is passive: it may display a permitted projection,
 * but never writes/acknowledges the operator read marker.
 * This helper classifies eligibility for a FUTURE server call, not authorization.
 */
export function canStageReadAcknowledgment(context) {
  return isPlain(context) && (context.role === 'operador' ||
    (context.role === 'gestor' && context.acting_as_assigned_operator === true)) &&
    context.account_active === true &&
    typeof context.actor_id === 'string' && context.actor_id.length>0 &&
    context.actor_id === context.assigned_actor_id &&
    typeof context.case_ref === 'string' && context.case_ref.length>0 &&
    context.case_version != null && typeof context.case_version === 'string' &&
    context.case_version.length>0;
}
