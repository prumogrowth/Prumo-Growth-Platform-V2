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

test('lista de templates é elegível por caso e versão; catálogo global não concede autorização', () => {
  const record=byId(cases(),'A-107');
  assert.deepEqual(record.eligibleTemplatesProjection,['modelo_continuidade_demo@v1-demo']);
  assert.equal(projectedFollowupActions(record,'rafael','aurora').includes('single_template'),true);
  assert.throws(
    ()=>applyLocalFollowupRequest(record,'rafael','aurora','single_template',DEMO_TEMPLATES[1]),
    /TEMPLATE_NAO_ELEGIVEL/
  );
  const changed={...record,eligibleTemplatesProjection:[]};
  assert.deepEqual(projectedFollowupActions(changed,'rafael','aurora'),['request_chain']);
});

test('deny-by-default: projeções ausentes de janela, lista e conclusão não abrem ações', () => {
  const record={...byId(cases(),'A-107'), inboxProjection:undefined, humanCompletionProjection:undefined, metaWindowProjection:undefined};
  assert.equal(isInActiveInbox(record),false);
  assert.equal(humanCompletion(record),'unknown');
  assert.deepEqual(projectedFollowupActions(record,'rafael','aurora'),[]);
  assert.equal(mayMockFreeText(record,'rafael','aurora'),false);
  const rows=[record];
  assert.equal(projectInbox(rows,'rafael','aurora','active').length,0);
  assert.equal(projectInbox(rows,'rafael','aurora','history').length,0);
});

test('pedido aceito no browser não confirma conclusão humana', () => {
  const record=byId(cases(),'A-102');
  assert.equal(humanCompletion(record,true),'requested_demo');
  assert.equal(mayMockFreeText(record,'rafael','aurora',true),false);
  assert.deepEqual(projectedFollowupActions(record,'rafael','aurora',true),[]);
});

test('marcos banco, venda e perda não reabrem o mesmo ciclo por permissão de chat residual', () => {
  const base=byId(cases(),'A-102');
  for (const status of ['cadastro enviado ao banco','vendido','perdido']) {
    const forged={...base,status,inboxProjection:'active',
      metaWindowProjection:'open',humanCompletionProjection:'pending',
      allowedActionsProjection:['free_text','single_template','request_chain'],
      eligibleTemplatesProjection:['modelo_continuidade_demo@v1-demo']};
    assert.equal(mayMockFreeText(forged,'rafael','aurora'),false);
    const expired={...forged,metaWindowProjection:'expired'};
    assert.deepEqual(projectedFollowupActions(expired,'rafael','aurora'),[]);
  }
});

test('auditoria: reset de fixtures não compartilha projeções O3/O4/O5',()=>{
  const first=copyCFDemoFixtures();
  const second=copyCFDemoFixtures();
  const firstById=id=>first.find(x=>x.id===id);
  const secondById=id=>second.find(x=>x.id===id);
  firstById('A-108').registrationProjection.fields[0].safeDisplayValue='ALTERADO';
  firstById('A-108').registrationProjection.missing.push('ALTERADO');
  firstById('A-114').postmarkProjection.linkVersionRef='ALTERADO';
  firstById('A-110').followupProjection.attempts[0].state='ALTERADO';
  firstById('A-105').bankProjection.submissionVersionRef='ALTERADO';
  assert.notEqual(secondById('A-108').registrationProjection.fields[0].safeDisplayValue,'ALTERADO');
  assert.ok(!secondById('A-108').registrationProjection.missing.includes('ALTERADO'));
  assert.notEqual(secondById('A-114').postmarkProjection.linkVersionRef,'ALTERADO');
  assert.notEqual(secondById('A-110').followupProjection.attempts[0].state,'ALTERADO');
  assert.notEqual(secondById('A-105').bankProjection.submissionVersionRef,'ALTERADO');
  const third=copyCFDemoFixtures();
  assert.equal(third.find(x=>x.id==='A-114').postmarkProjection.linkVersionRef,
    secondById('A-114').postmarkProjection.linkVersionRef);
});
