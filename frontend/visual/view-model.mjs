/** FV-UI-002. Projeções de INTERFACE somente sobre fixtures sintéticas.
 * Nenhuma função autentica, valida autorização real, grava no S0 ou chama provedor.
 */
import { getActor, hasMockCaseScope, visibleConversations } from './fixtures.mjs';

export const DETAIL_TABS = Object.freeze([
  { id: 'overview', title: 'Resumo' },
  { id: 'activity', title: 'Histórico' },
  { id: 'notes', title: 'Notas' },
  { id: 'extraction', title: 'Extração' },
  { id: 'bank', title: 'Banco' },
  { id: 'postmark', title: 'Novo contato' },
  { id: 'followup', title: 'Recontatos' }
]);
export const EXTRACTION_SCENARIOS = Object.freeze(['accepted', 'partial', 'failed', 'stale']);

export function projectQueue(records, actorId, shopId, { query = '', filter = 'all', status = 'all' } = {}) {
  let rows = visibleConversations(records, actorId, shopId);
  if (filter === 'unread') rows = rows.filter(row => row.unread > 0);
  if (filter === 'mine') rows = rows.filter(row => row.assignedTo === actorId);
  if (status !== 'all') rows = rows.filter(row => row.status === status);
  const term = String(query).toLocaleLowerCase('pt-BR').trim();
  if (term) rows = rows.filter(row => [row.id, row.name, row.tag, row.status]
    .some(value => String(value ?? '').toLocaleLowerCase('pt-BR').includes(term)));
  return rows;
}

export function summaryOf(records, actorId, shopId) {
  const rows = visibleConversations(records, actorId, shopId);
  return Object.freeze({
    total: rows.length,
    unread: rows.filter(row => row.unread > 0).length,
    human: rows.filter(row => row.status === 'em atendimento pelo operador').length,
    bank: rows.filter(row => row.status === 'cadastro enviado ao banco').length
  });
}

export function canWriteNote(record, actorId, shopId) {
  const actor = getActor(actorId);
  return Boolean(actor && hasMockCaseScope(record,actorId,shopId) &&
    record.assignedTo === actorId);
}

export function canSeeTeamSummary(actorId, _shopId) {
  // G2: gestor supervisiona PESSOAS, não concessionárias. O filtro de loja
  // restringe a lista de atendimentos, mas nunca define a equipe do gestor.
  const actor = getActor(actorId);
  return Boolean(actor?.role === 'gestor' && actor.teamState === 'active');
}

export function activityFor(record, processing) {
  if (!record) return [];
  const history = [
    { id: 'registered-' + record.id, label: 'Caso de exemplo disponível na fila', time: 'Demonstração', kind: 'fixture' },
    ...record.messages.map(m => ({ id: 'msg-' + m.id, label: m.side === 'out' ? 'Mensagem humana fictícia' : m.side === 'ai' ? 'Mensagem IA fictícia' : m.side === 'system' ? 'Evento técnico fictício' : 'Mensagem de cliente fictícia', time: m.time, kind: 'message' })),
    ...(record.notes ?? []).map(n => ({ id: 'note-' + n.id, label: 'Nota interna inserida na demonstração', time: n.time, kind: 'note' }))
  ];
  if (processing) history.push({ id: 'extract-' + record.id, label: 'Extração pós-atendimento: cenário ' + processing.kind + ' (simulado)', time: 'Agora · simulado', kind: 'extraction' });
  return history.reverse();
}

export function modelExtraction(kind) {
  if (!EXTRACTION_SCENARIOS.includes(kind)) throw new Error('CENARIO_NAO_SUPORTADO');
  const statuses = {
    accepted: { title: 'Solicitação registrada — simulação', explanation: 'Somente o pedido foi representado. Nenhuma chamada ou gravação ocorreu.' },
    partial: { title: 'Proposta parcial — simulação', explanation: 'Há valores propostos e pendências fictícias. Nenhuma ficha foi persistida.' },
    failed: { title: 'Falha técnica — simulação', explanation: 'A extração fictícia falhou; o caso e o status comercial permanecem inalterados.' },
    stale: { title: 'Versão desatualizada — simulação', explanation: 'O resultado seria descartado pelo S0 se mensagens/versões tivessem mudado.' }
  };
  return Object.freeze({ kind, ...statuses[kind], persisted: false, commercialTransition: false });
}
