/** Fixtures exclusivamente sintéticas para a experiência visual FV-UI-001.
 * Não são regras S0, catálogo de dados, autenticação ou fonte real de autorização.
 */
export const COMMERCIAL_STATUSES = Object.freeze([
  'aguardando primeiro disparo',
  'primeiro disparo enviado',
  'em atendimento pela IA',
  'em atendimento pelo operador',
  'cadastro enviado ao operador',
  'cadastro enviado ao banco',
  'vendido',
  'perdido'
]);

export const SHOPS = Object.freeze([
  { id: 'aurora', name: 'Aurora Motos', city: 'Caruaru · concessionária fictícia' },
  { id: 'horizonte', name: 'Horizonte Motos', city: 'Recife · concessionária fictícia' }
]);

export const ACTORS = Object.freeze([
  { id: 'rafael', name: 'Rafael Lima', role: 'operador', shops: ['aurora'], organization: 'Prumo' },
  { id: 'bianca', name: 'Bianca Rocha', role: 'operador', shops: ['aurora'], organization: 'Prumo' },
  { id: 'marina', name: 'Marina Costa', role: 'gestor', shops: ['aurora', 'horizonte'], organization: 'Prumo' },
  { id: 'lia', name: 'Lia Martins', role: 'operador', shops: ['horizonte'], organization: 'Prumo' },
  { id: 'otavio', name: 'Otávio (suspenso)', role: 'operador', shops: ['aurora'], organization: 'Prumo', teamState: 'suspended' }
]);

const msg = (id, side, body, time, type='text') => ({ id, side, body, time, type });

export const INITIAL_CONVERSATIONS = Object.freeze([
  {
    id: 'A-102', shopId: 'aurora', name: 'Cliente Exemplo 02', initials: 'CE',
    status: 'em atendimento pelo operador', assignedTo: 'rafael', unread: 2,
    updatedAt: '10:42', tag: 'Aguardando retorno',
    messages: [
      msg('a102-1', 'in', 'Olá! Gostaria de continuar o atendimento que comecei mais cedo.', '10:31'),
      msg('a102-2', 'out', 'Claro! Vou acompanhar seu atendimento por aqui.', '10:34'),
      msg('a102-3', 'in', 'Estou procurando uma opção que combine com meu uso no dia a dia.', '10:40'),
      msg('a102-4', 'in', 'Podemos conversar sobre as próximas etapas?', '10:42')
    ]
  },
  {
    id: 'A-105', shopId: 'aurora', name: 'Cliente Exemplo 05', initials: 'CE',
    status: 'cadastro enviado ao banco', assignedTo: 'rafael', unread: 0,
    updatedAt: '09:18', tag: 'Aguardando banco',
    messages: [
      msg('a105-1', 'in', 'Conseguimos seguir com meu processo?', '09:12'),
      msg('a105-2', 'out', 'O encaminhamento aparece registrado neste exemplo de demonstração.', '09:18')
    ]
  },
  {
    id: 'A-103', shopId: 'aurora', name: 'Cliente Exemplo 03', initials: 'CE',
    status: 'cadastro enviado ao operador', assignedTo: 'bianca', unread: 1,
    updatedAt: 'Ontem', tag: 'Em conferência',
    messages: [
      msg('a103-1', 'in', 'Posso confirmar alguns detalhes com a equipe?', 'Ontem'),
      msg('a103-2', 'system', 'Transferência para atendimento humano (exemplo sintético).', 'Ontem')
    ]
  },
  {
    id: 'A-101', shopId: 'aurora', name: 'Cliente Exemplo 01', initials: 'CE',
    status: 'em atendimento pela IA', assignedTo: null, unread: 0,
    updatedAt: 'Ontem', tag: 'Atendimento IA',
    messages: [
      msg('a101-1', 'in', 'Quero entender como funciona o processo.', 'Ontem'),
      msg('a101-2', 'ai', 'Posso explicar as etapas gerais do atendimento.', 'Ontem')
    ]
  },
  {
    id: 'A-106', shopId: 'aurora', name: 'Cliente Exemplo 06', initials: 'CE',
    status: 'em atendimento pelo operador', assignedTo: 'marina', unread: 0,
    updatedAt: 'Segunda', tag: 'Gestora autoatribuída',
    messages: [
      msg('a106-1', 'in', 'Gostaria de esclarecer minha solicitação com uma pessoa.', 'Segunda'),
      msg('a106-2', 'out', 'Estou disponível para acompanhar este caso.', 'Segunda')
    ]
  },
  {
    id: 'B-201', shopId: 'horizonte', name: 'Cliente Exemplo 01', initials: 'CE',
    status: 'em atendimento pelo operador', assignedTo: 'lia', unread: 1,
    updatedAt: '11:02', tag: 'Pendente',
    messages: [
      msg('b201-1', 'in', 'Este atendimento é da concessionária Horizonte.', '11:02')
    ]
  },
  {
    id: 'B-202', shopId: 'horizonte', name: 'Cliente Exemplo 07', initials: 'CE',
    status: 'primeiro disparo enviado', assignedTo: null, unread: 0,
    updatedAt: 'Ontem', tag: 'Primeiro contato',
    messages: [msg('b202-1', 'system', 'Primeiro disparo apenas ilustrativo.', 'Ontem')]
  }
]);

export function getActor(actorId) {
  return ACTORS.find(actor => actor.id === actorId) ?? null;
}
export function getShop(shopId) {
  return SHOPS.find(shop => shop.id === shopId) ?? null;
}
export function visibleConversations(records, actorId, shopId) {
  const actor = getActor(actorId);
  if (!actor || actor.teamState === 'suspended' || actor.teamState === 'removed' || !actor.shops.includes(shopId)) return [];
  return records.filter(record => record.shopId === shopId &&
    (actor.role === 'gestor' || record.assignedTo === actorId));
}
export function canSimulateCompletion(record, actorId, shopId) {
  const actor = getActor(actorId);
  return Boolean(actor && actor.teamState !== 'suspended' && actor.teamState !== 'removed' && record && actor.shops.includes(shopId) &&
    record.shopId === shopId && record.assignedTo === actorId &&
    record.status === 'em atendimento pelo operador');
}
export function statusTone(status) {
  if (status === 'em atendimento pelo operador') return 'human';
  if (status === 'em atendimento pela IA') return 'ai';
  if (status === 'cadastro enviado ao banco') return 'bank';
  if (status === 'vendido') return 'success';
  if (status === 'perdido') return 'danger';
  return 'neutral';
}
export function copyFixtures() {
  return INITIAL_CONVERSATIONS.map(record => ({ ...record, messages: record.messages.map(m => ({ ...m })), notes: [], }));
}
