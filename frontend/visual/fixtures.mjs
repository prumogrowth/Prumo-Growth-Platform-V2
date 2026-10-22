/** Fixtures exclusivamente sintéticas para a experiência visual FV-UI-001.
 * Não são regras S0, catálogo de dados, autenticação ou fonte real de autorização.
 * Gestores fictícios supervisionam OPERADORES, não lojas. Lojas são concessões
 * somente leitura conferidas pelo RESPONSÁVEL na fixture, não editadas pelo gestor.
 * O S0 deve prover a projeção autorizada; filtros do browser NÃO são autenticação.
 * Ver frontend/docs/21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md.
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
  { id: 'rafael', name: 'Rafael Lima', role: 'operador', managerId:'marina', shops: ['aurora'], organization: 'Prumo', teamState: 'active',leadIntakeProjection:'receiving' },
  { id: 'bianca', name: 'Bianca Rocha', role: 'operador', managerId:'daniel', shops: ['aurora','horizonte'], organization: 'Prumo', teamState: 'active',leadIntakeProjection:'paused_confirmed' },
  { id: 'marina', name: 'Marina Costa', role: 'gestor', shops: ['aurora', 'horizonte'], organization: 'Prumo', teamState: 'active' },
  { id: 'daniel', name: 'Daniel Freitas', role: 'gestor', shops: ['aurora','horizonte'], organization: 'Prumo', teamState: 'active' },
  { id: 'lia', name: 'Lia Martins', role: 'operador', managerId:'marina', shops: ['horizonte'], organization: 'Prumo', teamState: 'active',leadIntakeProjection:'receiving' },
  { id: 'otavio', name: 'Otávio (suspenso)', role: 'operador', managerId:'daniel', shops: ['aurora'], organization: 'Prumo', teamState: 'suspended',leadIntakeProjection:'unknown' }
]);

const msg = (id, side, body, time, type='text') => ({ id, side, body, time, type });

export const INITIAL_CONVERSATIONS = Object.freeze([
  {
    id: 'A-102', shopId: 'aurora', name: 'Cliente Exemplo 02', initials: 'CE',
    status: 'em atendimento pelo operador', assignedTo: 'rafael', unread: 2,
    updatedAt: '10:42', tag: 'Aguardando retorno',
    messages: [
      msg('a102-1', 'in', 'Olá! Gostaria de continuar o atendimento que comecei mais cedo.', '10:31'),
      {...msg('a102-2', 'out', 'Claro! Vou acompanhar seu atendimento por aqui.', '10:34'),
        transportProjection:{source:'s0_fixture',caseRef:'A-102',shopRef:'aurora',
          messageRef:'a102-2',versionRef:'transport-a102-v1',
          state:'api_accepted',confirmed:false,apiAckRef:'ack-synthetic-102'}},
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
      {...msg('a105-2', 'out', 'O encaminhamento aparece registrado neste exemplo de demonstração.', '09:18'),
        transportProjection:{source:'s0_fixture',caseRef:'A-105',shopRef:'aurora',
          messageRef:'a105-2',versionRef:'transport-a105-v1',
          state:'sent_confirmed',confirmed:true,proofRef:'proof-synthetic-105'}}
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
    status: 'em atendimento pela IA', assignedTo: null, teamManagerId:'marina', unread: 0,
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
      {...msg('a106-2', 'out', 'Estou disponível para acompanhar este caso.', 'Segunda'),
        transportProjection:{source:'s0_fixture',caseRef:'A-106',shopRef:'aurora',
          messageRef:'a106-2',versionRef:'transport-a106-v1',
          state:'uncertain',confirmed:false}}
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
    id: 'B-203', shopId: 'horizonte', name:'Cliente Exemplo 18', initials:'CE',
    status:'em atendimento pelo operador', assignedTo:'bianca', unread:0,
    updatedAt:'Hoje · fictício', tag:'Equipe Daniel · loja B',
    messages:[msg('b203-1','in','Falo com Bianca em outra concessionária fictícia.', 'Hoje')]
  },
  {
    id: 'B-202', shopId: 'horizonte', name: 'Cliente Exemplo 07', initials: 'CE',
    status: 'primeiro disparo enviado', assignedTo: null, teamManagerId:'marina', unread: 0,
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
/** Relação de equipe definida pelo responsável na fixture, NÃO pelo gestor. */
export function managedOperators(managerId) {
  const manager=getActor(managerId);
  if(manager?.role!=='gestor' || manager.teamState!=='active')return [];
  return ACTORS.filter(operator=>operator.role==='operador' &&
    operator.managerId===managerId);
}
/** Concessão excepcional já CONFIRMADA na fixture de S0: SOMENTE o caso.
 * Não confere grant geral e nunca aceita parâmetro fornecido pelo navegador.
 */
export function hasMockCaseOnlyScope(record,actorId,shopId) {
  const actor=getActor(actorId),p=record?.caseOnlyAccessProjection;
  return Boolean(actor?.role==='operador' && actor.teamState==='active' &&
    record?.assignedTo===actorId && record.shopId===shopId &&
    p?.origin==='s0_fixture' && p.confirmed===true &&
    p.scope==='case_only' && p.reason==='manual_team_transfer' &&
    p.actorId===actorId && p.caseId===record.id && p.shopId===shopId &&
    typeof p.versionRef==='string' && p.versionRef.trim());
}
export function hasMockCaseScope(record,actorId,shopId) {
  const actor=getActor(actorId);
  return Boolean(actor && actor.teamState==='active' && record &&
    record.shopId===shopId &&
    (actor.shops.includes(shopId) || hasMockCaseOnlyScope(record,actorId,shopId)));
}
/** Filtro de concessionária pode incluir somente a loja de caso excepcional.
 * A presença da opção NÃO libera qualquer outro recurso nessa loja.
 */
export function visibleMockShops(records,actorId) {
  const actor=getActor(actorId);
  if(!actor || actor.teamState!=='active')return [];
  const shops=new Set(actor.shops);
  for(const record of Array.isArray(records)?records:[]) {
    if(hasMockCaseOnlyScope(record,actorId,record?.shopId))shops.add(record.shopId);
  }
  return [...shops];
}
export function visibleConversations(records, actorId, shopId) {
  const actor=getActor(actorId);
  if(!actor || actor.teamState!=='active' || !Array.isArray(records) ||
     !visibleMockShops(records,actorId).includes(shopId))return [];
  const team=actor.role==='gestor' ? managedOperators(actorId) : [];
  return records.filter(record=>{
    if(record.shopId!==shopId)return false;
    if(actor.role!=='gestor')return record.assignedTo===actorId &&
      hasMockCaseScope(record,actorId,shopId);
    if(record.assignedTo===actorId)return true; // gestor autoatribuído
    if(record.assignedTo==null)return record.teamManagerId===actorId;
    return team.some(operator=>operator.id===record.assignedTo &&
      (operator.shops.includes(record.shopId) ||
       hasMockCaseOnlyScope(record,operator.id,record.shopId)));
  });
}
export function canSimulateCompletion(record, actorId, shopId) {
  const actor = getActor(actorId);
  return Boolean(actor && hasMockCaseScope(record,actorId,shopId) &&
    record.assignedTo === actorId && record.status === 'em atendimento pelo operador');
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
