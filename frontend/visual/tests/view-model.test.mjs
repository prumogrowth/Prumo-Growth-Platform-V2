import assert from 'node:assert/strict';
import test from 'node:test';
import { INITIAL_CONVERSATIONS, copyFixtures } from '../fixtures.mjs';
import { DETAIL_TABS, projectQueue, summaryOf, canWriteNote, canSeeTeamSummary, activityFor, modelExtraction } from '../view-model.mjs';

test('filtragem por status, leitura e busca respeitam escopo fictício', () => {
  assert.deepEqual(projectQueue(INITIAL_CONVERSATIONS, 'rafael', 'aurora', {status:'cadastro enviado ao banco'}).map(x=>x.id), ['A-105']);
  assert.deepEqual(projectQueue(INITIAL_CONVERSATIONS, 'rafael', 'horizonte', {query:'Cliente Exemplo 01'}), []);
  assert.deepEqual(projectQueue(INITIAL_CONVERSATIONS, 'marina', 'aurora', {filter:'mine'}).map(x=>x.id), ['A-106']);
  assert.deepEqual(projectQueue(INITIAL_CONVERSATIONS, 'rafael', 'aurora', {filter:'unread'}).map(x=>x.id), ['A-102']);
});

test('sumários só contam registros do contexto permitido', () => {
  assert.deepEqual(summaryOf(INITIAL_CONVERSATIONS,'rafael','aurora'), {total:2,unread:1,human:1,bank:1});
  assert.equal(summaryOf(INITIAL_CONVERSATIONS,'rafael','horizonte').total,0);
});

test('escrever nota fictícia exige atribuição e escopo, inclusive gestora', () => {
  const a102 = INITIAL_CONVERSATIONS.find(x=>x.id==='A-102');
  const a106 = INITIAL_CONVERSATIONS.find(x=>x.id==='A-106');
  assert.equal(canWriteNote(a102,'rafael','aurora'),true);
  assert.equal(canWriteNote(a102,'marina','aurora'),false);
  assert.equal(canWriteNote(a106,'marina','aurora'),true);
  assert.equal(canWriteNote(a102,'rafael','horizonte'),false);
});

test('painel da equipe é apenas gestorial na loja concedida', () => {
  assert.equal(canSeeTeamSummary('marina','horizonte'),true);
  assert.equal(canSeeTeamSummary('rafael','aurora'),false);
  assert.equal(canSeeTeamSummary('marina','inexistente'),true); // equipe independe do filtro de concessionária
  assert.equal(canSeeTeamSummary('daniel','aurora'),true);
  assert.equal(canSeeTeamSummary('otavio','aurora'),false);
});

test('histórico sintético preserva autoria e notas, sem nova transição', () => {
  const copy=copyFixtures(); copy[0].notes.push({id:'1',text:'Nota de demonstração',time:'Agora',actorId:'rafael'});
  const list=activityFor(copy[0],modelExtraction('accepted'));
  assert.ok(list.some(event=>event.kind==='note'));
  assert.ok(list.some(event=>event.kind==='extraction'));
  assert.equal(copy[0].status,'em atendimento pelo operador');
});

test('cenários de extração são claramente simulados e nunca persistidos', () => {
  assert.deepEqual(DETAIL_TABS.map(x=>x.id),['overview','activity','notes','extraction','bank','postmark','followup']);
  for (const k of ['accepted','partial','failed','stale']) {
    const x=modelExtraction(k);assert.equal(x.persisted,false);assert.equal(x.commercialTransition,false);
    assert.match(x.title,/simulação/i);
  }
  assert.throws(()=>modelExtraction('applied'),/CENARIO_NAO_SUPORTADO/);
});

test('FV-UI-056: busca em português ignora acentos e colapsa espaços sem ampliar o escopo',()=>{
  const rows=copyFixtures();
  const target=rows.find(row=>row.id==='A-102');
  assert.ok(target);
  target.name='João  da Silva';
  assert.deepEqual(projectQueue(rows,'rafael','aurora',{query:'  JOAO   DA    SILVA  '}).map(x=>x.id),['A-102']);
  assert.deepEqual(projectQueue(rows,'rafael','aurora',{query:'joão da silva'}).map(x=>x.id),['A-102']);
  assert.deepEqual(projectQueue(rows,'rafael','aurora',{query:'JOÃO da silva'.normalize('NFD')}).map(x=>x.id),['A-102']);
  assert.deepEqual(projectQueue(rows,'marina','horizonte',{query:'joao da silva'}).map(x=>x.id),[]);
  assert.deepEqual(projectQueue(rows,'rafael','horizonte',{query:'joao da silva'}).map(x=>x.id),[]);
  assert.deepEqual(projectQueue(rows,'rafael','aurora',{query:'CADÁSTRO    ENVIADO  AO BANCO'}).map(x=>x.id),['A-105']);
  assert.deepEqual(projectQueue(rows,'rafael','aurora',{query:'  A-105  '}).map(x=>x.id),['A-105']);
  assert.deepEqual(projectQueue(rows,'rafael','aurora',{query:'    '}).map(x=>x.id),projectQueue(rows,'rafael','aurora').map(x=>x.id));
});
