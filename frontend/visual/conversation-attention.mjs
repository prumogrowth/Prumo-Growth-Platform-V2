/** Single two-state badge for inbox conversations — synthetic contract only.
 * This file does not mark messages read, run a timer, check Meta receipts,
 * authenticate a user or grant access to conversation/customer data.
 *
 * For real use S0 must provide per-operator read and human-reply evidence.
 * A manager opening a conversation must NEVER mark it read on behalf of
 * an operator. An unread count is not itself proof of response pending.
 */
import { visibleConversations } from './fixtures.mjs';
import { stageMockMessageTransport } from './transport-state-view.mjs';

export const ATTENTION_PROPOSAL_VERSION = 'ui-attention-proposal/0.1';

/** Only already-authorized synthetic records. Local/uncertain outgoing messages
 * never replace the last confirmed record. Supervisor visibility is read-only;
 * validating the fixture's assignee transport does not acknowledge any reading.
 */
/** A readable body is the representation supported by this synthetic runtime.
 * Local audio already carries a readable label; unknown/raw media is not a receipt.
 * Never coerce null/objects/whitespace into a confirmed human message.
 */
// Critério de legibilidade, sem mutar a mensagem persistida. Caracteres
// Unicode invisíveis isolados não confirmam uma mensagem; emoji com ZWJ
// e seletores de apresentação continuam legíveis quando há base visível.
const LEGIBLE_CODE_POINT = /[^\p{White_Space}\p{Default_Ignorable_Code_Point}\p{Cc}]/u;
export function hasDemoMessageContent(message) {
  return Boolean(message && typeof message === 'object' &&
    typeof message.body === 'string' && LEGIBLE_CODE_POINT.test(message.body));
}
export function confirmedDemoMessages(record, actorId, shopId) {
  if (!record || !visibleConversations([record], actorId, shopId).length) return [];
  return (Array.isArray(record.messages) ? record.messages : []).filter(message => {
    if (!hasDemoMessageContent(message)) return false;
    if (message.deliveryState === 'local_demo_not_sent') return false;
    if (message.side === 'out')
      return stageMockMessageTransport(record, message, record.assignedTo, shopId).provedSent;
    return ['in', 'ai', 'system'].includes(message.side) && message.deliveryState == null;
  });
}

export function latestConfirmedDemoMessage(record, actorId, shopId) {
  // A prévia representa a última mensagem de conversa, não um evento interno.
  return confirmedDemoMessages(record, actorId, shopId)
    .filter(message => ['in','out','ai'].includes(message.side)).at(-1) ?? null;
}

export function projectDemoAttention(record, actorId, shopId) {
  if (!record || !visibleConversations([record], actorId, shopId).length) return ATTENTION_EMPTY;
  const confirmed = confirmedDemoMessages(record, actorId, shopId);
  const inbound = confirmed.filter(message => message.side === 'in');
  const lastHumanRelevant = confirmed.filter(message => ['in', 'out'].includes(message.side)).at(-1);
  return stageConversationAttention({
    schema_version: ATTENTION_PROPOSAL_VERSION,
    unread_inbound_count: inbound.length ? record.unread : 0,
    operator_read_confirmed: record.demoReadByAssigned === true &&
      record.demoReadProjection?.source === 'local_fixture' &&
      record.demoReadProjection.actorId === record.assignedTo &&
      record.demoReadProjection.caseId === record.id &&
      record.demoReadProjection.shopId === record.shopId &&
      record.demoReadProjection.messageRef === inbound.at(-1)?.id && inbound.length > 0,
    human_reply_pending: lastHumanRelevant?.side === 'in'
  });
}
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
