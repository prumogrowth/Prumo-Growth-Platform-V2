/** CF-OP-02 / FV-03: somente projeções sintéticas recebidas como dados.
 * A janela Meta e os prazos C09 são autoritativos do S0, JAMAIS Date.now() no browser.
 */
import { getActor, visibleConversations, copyFixtures } from './fixtures.mjs';

export const DEMO_TEMPLATES = Object.freeze([
  { id: 'modelo_continuidade_demo', version: 'v1-demo', title: 'Retomar conversa', eligibility: 'Exemplo fictício' },
  { id: 'modelo_confirmacao_demo', version: 'v1-demo', title: 'Solicitar resposta', eligibility: 'Exemplo fictício' }
]);
export const FOLLOWUP_ACTIONS = Object.freeze(['single_template', 'request_chain']);

export function isInActiveInbox(record) {
  // Fonte: projeção do servidor. Não usar expiração calculada no navegador.
  return record?.inboxProjection === 'active';
}

export function projectedMetaWindow(record) {
  return record?.metaWindowProjection ?? 'unknown';
}

export function humanCompletion(record, simulatedCompletion = false) {
  return simulatedCompletion ? 'completed_demo' : (record?.humanCompletionProjection ?? 'unknown');
}

function currentlyAssigned(record, actorId, shopId) {
  const actor = getActor(actorId);
  return Boolean(record && actor && actor.teamState === 'active' &&
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
  return FOLLOWUP_ACTIONS.filter(action => allowed.includes(action) &&
    (action !== 'single_template' || DEMO_TEMPLATES.some(t => record.eligibleTemplatesProjection?.includes(t.id + '@' + t.version))));
}

export function projectInbox(records, actorId, shopId, placement = 'active') {
  const allowed = visibleConversations(records, actorId, shopId);
  return allowed.filter(record => placement === 'history' ? record.inboxProjection === 'historical' : record.inboxProjection === 'active');
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
    if (!DEMO_TEMPLATES.some(t => t.id === template?.id && t.version === template.version &&
      record.eligibleTemplatesProjection?.includes(t.id + '@' + t.version)))
      throw new Error('TEMPLATE_NAO_ELEGIVEL_NA_DEMONSTRACAO');
    return { kind, state: 'requested', template: { id: template.id, version: template.version }, confirmedSent: false };
  }
  return { kind, state: 'requested', confirmedSent: false };
}

export function isSyntheticBankProtected(record) {
  return ['cadastro enviado ao banco', 'vendido'].includes(record?.status);
}

/** Cenários visuais pré-projetados como se fossem vindos de S0; não são regras de S0. */
const SCENARIOS = Object.freeze([
  { id:'A-107', shopId:'aurora', name:'Cliente Exemplo 08', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:1, updatedAt:'Ontem', tag:'Janela expirada · pendente',
    inboxProjection:'active', metaWindowProjection:'expired', humanCompletionProjection:'pending',
    allowedActionsProjection:['single_template','request_chain','complete'],
    eligibleTemplatesProjection:['modelo_continuidade_demo@v1-demo'],
    messages:[{id:'a107-1',side:'in',body:'Preciso pensar e retorno depois.',time:'Ontem'}] },
  { id:'A-108', shopId:'aurora', name:'Cliente Exemplo 09', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'10:50', tag:'Etapa humana concluída',
    inboxProjection:'active', metaWindowProjection:'open', humanCompletionProjection:'completed',
    allowedActionsProjection:[],
    messages:[{id:'a108-1',side:'in',body:'Obrigado pelo atendimento. Vou analisar.',time:'10:50'}] },
  { id:'A-109', shopId:'aurora', name:'Cliente Exemplo 10', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'Ontem', tag:'Histórico preservado',
    inboxProjection:'historical', metaWindowProjection:'expired', humanCompletionProjection:'completed',
    allowedActionsProjection:[],
    messages:[{id:'a109-1',side:'in',body:'Encerramos nossa conversa por hoje.',time:'Ontem'}] },
  { id:'A-110', shopId:'aurora', name:'Cliente Exemplo 11', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'Ontem', tag:'Cadeia em andamento',
    inboxProjection:'active', metaWindowProjection:'expired', humanCompletionProjection:'pending',
    allowedActionsProjection:[],
    followupProjection:{state:'scheduled',attempts:[
      {label:'Tentativa 1',state:'scheduled',template:'Modelo autorizado ilustrativo',time:'Horário fictício'},
      {label:'Tentativa 2',state:'pending',template:'Modelo autorizado ilustrativo',time:'A definir no S0'},
      {label:'Template final',state:'pending',template:'Encerramento fictício separado',time:'A definir no S0'}
    ],finalSentConfirmed:false,silenceResolution:'not_started'},
    messages:[{id:'a110-1',side:'in',body:'Estou avaliando as opções e retorno quando puder.',time:'Ontem'}] },
  { id:'A-111', shopId:'aurora', name:'Cliente Exemplo 12', initials:'CE', assignedTo:'rafael',
    status:'perdido', unread:0, updatedAt:'Arquivo', tag:'Perda confirmada em cenário',
    inboxProjection:'historical', metaWindowProjection:'expired', humanCompletionProjection:'completed',
    allowedActionsProjection:[],
    followupProjection:{state:'finished',attempts:[
      {label:'Template final',state:'sent_confirmed',template:'Encerramento ilustrativo',time:'Prova S0 fictícia'}
    ],finalSentConfirmed:true,silenceResolution:'confirmed_eligible'},
    messages:[{id:'a111-1',side:'system',body:'Estado perdido representado como projeção histórica fictícia do S0; não foi calculado aqui.',time:'Arquivo'}] },
  { id:'A-112', shopId:'aurora', name:'Cliente Exemplo 13', initials:'CE', assignedTo:null,
    status:'em atendimento pelo operador', unread:0, updatedAt:'Ontem', tag:'Fila protegida',
    inboxProjection:'active', metaWindowProjection:'unknown', humanCompletionProjection:'pending',
    reassignmentProjection:'protected_queue',allowedActionsProjection:[],
    messages:[{id:'a112-1',side:'system',body:'Responsável fictício perdeu acesso; remanejamento cabe ao S1-002.',time:'Ontem'}] },
  { id:'A-113', shopId:'aurora', name:'Cliente Exemplo 14', initials:'CE', assignedTo:'rafael',
    status:'em atendimento pelo operador', unread:0, updatedAt:'Ontem', tag:'Envio final não confirmado',
    inboxProjection:'active', metaWindowProjection:'expired', humanCompletionProjection:'pending',
    allowedActionsProjection:[],
    followupProjection:{state:'awaiting_evidence',attempts:[
      {label:'Template final',state:'queued',template:'Encerramento ilustrativo',time:'Pendente de prova'}
    ],finalSentConfirmed:false,silenceResolution:'not_started'},
    messages:[{id:'a113-1',side:'in',body:'Vou verificar e responder.',time:'Ontem'}] },
]);

export function copyCFDemoFixtures() {
  const base = copyFixtures().map(record => {
    const windowState = { 'A-102':'open','A-105':'unknown','A-106':'open','B-201':'open' }[record.id] ?? 'unknown';
    return {
      ...record, inboxProjection:'active', metaWindowProjection:windowState,
      humanCompletionProjection:'pending',
      allowedActionsProjection: ['A-102','A-106','B-201'].includes(record.id) ? ['free_text','complete'] : []
    };
  });
  return [...base,...SCENARIOS.map(record => ({
    ...record, notes:[], messages:record.messages.map(m=>({...m})),
    allowedActionsProjection:[...(record.allowedActionsProjection??[])],
    eligibleTemplatesProjection:[...(record.eligibleTemplatesProjection??[])],
    followupProjection:record.followupProjection ? {
      ...record.followupProjection,attempts:record.followupProjection.attempts.map(a=>({...a}))
    } : undefined
  }))];
}
