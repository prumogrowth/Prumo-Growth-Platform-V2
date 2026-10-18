import assert from 'node:assert/strict';
import test from 'node:test';
import { visibleConversations, COMMERCIAL_STATUSES } from '../fixtures.mjs';
import {
  DEMO_TEMPLATES, copyCFDemoFixtures, isInActiveInbox, projectedMetaWindow,
  humanCompletion, mayMockFreeText, projectedFollowupActions, projectInbox,
  projectedFollowupState, applyLocalFollowupRequest, isSyntheticBankProtected
} from '../cf-op-02.mjs';

const cases = () => copyCFDemoFixtures();
const byId = (items, id) => items.find(row => row.id === id);

test('FV3-01: janela vencida e humano pendente fica ativo, mas composer bloqueado', () => {
  const rows=cases(), record=byId(rows,'A-107');
  assert.equal(isInActiveInbox(record),true);
  assert.equal(humanCompletion(record),'pending');
  assert.equal(projectedMetaWindow(record),'expired');
  assert.equal(mayMockFreeText(record,'rafael','aurora'),false);
  assert.deepEqual(projectedFollowupActions(record,'rafael','aurora'),['single_template','request_chain']);
  assert.equal(record.status,'em atendimento pelo operador');
});

test('FV3-02/03: ações separadas são só solicitações, sem envio ou plano gravado', () => {
  const record=byId(cases(),'A-107');
  const req=applyLocalFollowupRequest(record,'rafael','aurora','single_template',DEMO_TEMPLATES[0]);
  assert.equal(req.kind,'single_template');
  assert.equal(projectedFollowupState(record,req).confirmedSent,false);
  const chain=applyLocalFollowupRequest(record,'rafael','aurora','request_chain');
  assert.equal(chain.kind,'request_chain');
  assert.equal(chain.state,'requested');
  assert.equal(projectedFollowupState(record,chain).source,'local_demo');
  assert.throws(()=>applyLocalFollowupRequest(record,'rafael','aurora','single_template',{id:'novo',version:'v0'}),/TEMPLATE_NAO_ELEGIVEL/);
});

test('FV3-04: template outbound não reabre o compositor', () => {
  const record=byId(cases(),'A-107');
  const local=applyLocalFollowupRequest(record,'rafael','aurora','single_template',DEMO_TEMPLATES[0]);
  assert.equal(local.confirmedSent,false);
  assert.equal(projectedMetaWindow(record),'expired');
  assert.equal(mayMockFreeText(record,'rafael','aurora'),false);
});

test('FV3-06: conclusão com janela aberta mantém conversa na fila, mas não libera digitação', () => {
  const record=byId(cases(),'A-108');
  assert.equal(humanCompletion(record),'completed');
  assert.equal(projectedMetaWindow(record),'open');
  assert.equal(isInActiveInbox(record),true);
  assert.equal(mayMockFreeText(record,'rafael','aurora'),false);
  assert.equal(mayMockFreeText(byId(cases(),'A-102'),'rafael','aurora',true),false);
});

test('FV3-07: concluído e expirado vai somente ao histórico preservado', () => {
  const rows=cases(),record=byId(rows,'A-109');
  assert.equal(isInActiveInbox(record),false);
  assert.ok(projectInbox(rows,'rafael','aurora','history').some(r=>r.id==='A-109'));
  assert.ok(!projectInbox(rows,'rafael','aurora','active').some(r=>r.id==='A-109'));
  assert.ok(record.messages.length>0);
});

test('FV3-08/09: envio final pendente NÃO prova perda; banco nunca perde por silêncio', () => {
  const pending=byId(cases(),'A-113');
  const oldBank=byId(cases(),'A-105');
  const lost=byId(cases(),'A-111');
  assert.equal(projectedFollowupState(pending).finalSentConfirmed,false);
  assert.equal(projectedFollowupState(pending).silenceResolution,'not_started');
  assert.equal(pending.status,'em atendimento pelo operador');
  assert.equal(isSyntheticBankProtected(oldBank),true);
  assert.equal(oldBank.status,'cadastro enviado ao banco');
  assert.equal(lost.status,'perdido'); // projeção de status já provido pela fixture; não calculado pelo browser
  assert.equal(isInActiveInbox(lost),false);
  assert.equal(projectedFollowupState(lost).finalSentConfirmed,true);
  assert.ok(COMMERCIAL_STATUSES.includes(lost.status));
});

test('FV3-10/11: supervisor e pessoa suspensa não enviam, concluem ou veem carteira', () => {
  const expired=byId(cases(),'A-107');
  assert.deepEqual(projectedFollowupActions(expired,'marina','aurora'),[]);
  assert.deepEqual(projectedFollowupActions(expired,'otavio','aurora'),[]);
  assert.deepEqual(visibleConversations(cases(),'otavio','aurora'),[]);
  assert.equal(mayMockFreeText(expired,'otavio','aurora'),false);
});

test('FV3-12: caso de fila protegida não é atribuído por JS e histórias não cruzam lojas', () => {
  const rows=cases(),guarded=byId(rows,'A-112');
  assert.equal(guarded.reassignmentProjection,'protected_queue');
  assert.equal(guarded.assignedTo,null);
  assert.equal(mayMockFreeText(guarded,'marina','aurora'),false);
  assert.deepEqual(projectedFollowupActions(guarded,'marina','aurora'),[]);
  const horizon=projectInbox(rows,'marina','horizonte','active');
  assert.ok(horizon.every(c=>c.shopId==='horizonte'));
  assert.ok(!horizon.some(c=>c.id===guarded.id));
});

test('conversa com cadeia já projetada não permite plano duplicado por inferência', () => {
  const planned=byId(cases(),'A-110');
  const projection=projectedFollowupState(planned);
  assert.equal(projection.state,'scheduled');
  assert.ok(projection.attempts.some(a=>a.label==='Template final'));
  assert.deepEqual(projectedFollowupActions(planned,'rafael','aurora'),[]);
  assert.throws(()=>applyLocalFollowupRequest(planned,'rafael','aurora','request_chain'),/ACAO_INELEGIVEL/);
});

test('permissões são deny-by-default sem janela/allowed_actions projetadas', () => {
  const record=byId(cases(),'A-103');
  assert.equal(projectedMetaWindow(record),'unknown');
  assert.equal(mayMockFreeText(record,'bianca','aurora'),false);
  assert.deepEqual(projectedFollowupActions(record,'bianca','aurora'),[]);
});
