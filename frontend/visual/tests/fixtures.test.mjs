import assert from 'node:assert/strict';
import test from 'node:test';
import {
  ACTORS, COMMERCIAL_STATUSES, INITIAL_CONVERSATIONS,
  canSimulateCompletion, copyFixtures, visibleConversations
} from '../fixtures.mjs';

test('há apenas os oito estados comerciais canônicos', () => {
  assert.equal(COMMERCIAL_STATUSES.length, 8);
  assert.equal(new Set(COMMERCIAL_STATUSES).size, 8);
  for (const caseRecord of INITIAL_CONVERSATIONS) assert.ok(COMMERCIAL_STATUSES.includes(caseRecord.status));
});

test('todos os personagens são profissionais fictícios da Prumo', () => {
  assert.ok(ACTORS.every(actor => actor.organization === 'Prumo'));
});

test('operador só visualiza casos atribuídos e dentro do escopo fictício', () => {
  assert.deepEqual(visibleConversations(INITIAL_CONVERSATIONS, 'rafael', 'aurora').map(x=>x.id), ['A-102', 'A-105']);
  assert.deepEqual(visibleConversations(INITIAL_CONVERSATIONS, 'rafael', 'horizonte'), []);
  assert.deepEqual(visibleConversations(INITIAL_CONVERSATIONS, 'bianca', 'aurora').map(x=>x.id), ['A-103']);
});

test('gestora só vê a própria equipe e pendências explicitamente vinculadas, mesmo compartilhando lojas', () => {
  const a = visibleConversations(INITIAL_CONVERSATIONS, 'marina', 'aurora');
  const b = visibleConversations(INITIAL_CONVERSATIONS, 'marina', 'horizonte');
  assert.ok(a.length >= 4 && b.length >= 2);
  assert.ok(!a.some(x=>x.assignedTo==='bianca'));
  assert.ok(!b.some(x=>x.assignedTo==='bianca'));
  assert.ok(a.some(x=>x.assignedTo==='rafael'));
  assert.ok(b.some(x=>x.assignedTo==='lia'));
  assert.ok(a.every(x => x.shopId === 'aurora'));
  assert.ok(b.every(x => x.shopId === 'horizonte'));
  assert.notEqual(a.find(x => x.name === 'Cliente Exemplo 01').id, b.find(x => x.name === 'Cliente Exemplo 01').id);
});

test('conclusão visual só aparece ao profissional designado, inclusive gestora autoatribuída', () => {
  const a102 = INITIAL_CONVERSATIONS.find(x => x.id === 'A-102');
  const a105 = INITIAL_CONVERSATIONS.find(x => x.id === 'A-105');
  const a106 = INITIAL_CONVERSATIONS.find(x => x.id === 'A-106');
  assert.equal(canSimulateCompletion(a102, 'rafael', 'aurora'), true);
  assert.equal(canSimulateCompletion(a102, 'marina', 'aurora'), false);
  assert.equal(canSimulateCompletion(a105, 'rafael', 'aurora'), false);
  assert.equal(canSimulateCompletion(a106, 'marina', 'aurora'), true);
  assert.equal(canSimulateCompletion(a102, 'rafael', 'horizonte'), false);
});

test('fixtures são cópias em memória e não mutam a base', () => {
  const c = copyFixtures();
  c[0].messages.push({ id:'sintetico', side:'out', body:'Teste' });
  assert.equal(INITIAL_CONVERSATIONS[0].messages.length, 4);
});
