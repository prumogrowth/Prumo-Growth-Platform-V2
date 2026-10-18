/** CF-OP-02 / FV-03: somente projeções sintéticas recebidas como dados.
 * A janela Meta e os prazos C09 são autoritativos do S0, JAMAIS Date.now() no browser.
 */
import { getActor, visibleConversations } from './fixtures.mjs';

export const DEMO_TEMPLATES = Object.freeze([
  { id: 'modelo_continuidade_demo', version: 'v1-demo', title: 'Retomar conversa', eligibility: 'Exemplo fictício' },
  { id: 'modelo_confirmacao_demo', version: 'v1-demo', title: 'Solicitar resposta', eligibility: 'Exemplo fictício' }
]);
export const FOLLOWUP_ACTIONS = Object.freeze(['single_template', 'request_chain']);

export function isInActiveInbox(record) {
  // Fonte: projeção do servidor. Não usar expiração calculada no navegador.
  return record?.inboxProjection !== 'historical';
}

export function projectedMetaWindow(record) {
  return record?.metaWindowProjection ?? 'unknown';
}

export function humanCompletion(record, simulatedCompletion = false) {
  return simulatedCompletion ? 'completed_demo' : (record?.humanCompletionProjection ?? 'pending');
}

function currentlyAssigned(record, actorId, shopId) {
  const actor = getActor(actorId);
  return Boolean(record && actor && actor.teamState !== 'suspended' && actor.teamState !== 'removed' &&
    actor.shops.includes(shopId) && record.shopId === shopId && record.assignedTo === actorId);
}

export function mayMockFreeText(record, actorId, shopId, simulatedCompletion = false) {
  // Caso histórico, janela ausente/vencida e conclusão interrompem compositor.
  return currentlyAssigned(record, actorId, shopId) &&
    isInActiveInbox(record) && projectedMetaWindow(record) === 'open' &&
    humanCompletion(record, simulatedCompletion) === 'pending' &&
    record?.allowedActionsProjection?.includes('free_text') === true;
}

export function projectedFollowupActions(record, actorId, shopId, simulatedCompletion = false) {
  if (!currentlyAssigned(record, actorId, shopId) || !isInActiveInbox(record) ||
      humanCompletion(record, simulatedCompletion) !== 'pending' || projectedMetaWindow(record) !== 'expired') return [];
  const allowed = record.allowedActionsProjection ?? [];
  return FOLLOWUP_ACTIONS.filter(action => allowed.includes(action));
}

export function projectInbox(records, actorId, shopId, placement = 'active') {
  const allowed = visibleConversations(records, actorId, shopId);
  return allowed.filter(record => placement === 'history' ? !isInActiveInbox(record) : isInActiveInbox(record));
}

export function projectedFollowupState(record, localRequest = null) {
  const plan = record?.followupProjection ?? null;
  if (localRequest) return { ...localRequest, source: 'local_demo', confirmedSent: false };
  return plan ? { ...plan, source: 'fixture_projection' } : null;
}

export function applyLocalFollowupRequest(record, actorId, shopId, kind, template) {
  const actions = projectedFollowupActions(record, actorId, shopId);
  if (!actions.includes(kind)) throw new Error('ACAO_INELEGIVEL_NA_DEMONSTRACAO');
  if (kind === 'single_template') {
    if (!DEMO_TEMPLATES.some(t => t.id === template?.id && t.version === template.version))
      throw new Error('TEMPLATE_NAO_ELEGIVEL_NA_DEMONSTRACAO');
    return { kind, state: 'requested', template: { id: template.id, version: template.version }, confirmedSent: false };
  }
  return { kind, state: 'requested', confirmedSent: false };
}

export function isSyntheticBankProtected(record) {
  return ['cadastro enviado ao banco', 'vendido'].includes(record?.status);
}
