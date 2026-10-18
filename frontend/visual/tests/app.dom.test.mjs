import test from 'node:test';
import assert from 'node:assert/strict';
import { installMockDOM } from './dom-fixture.mjs';

// A aplicação depende de um DOM. O mock é instalado ANTES do import.
// Este ensaio não substitui Chromium, valida layout nem comprova autenticação.
const env = installMockDOM();
await import('../app.mjs');

const get = id => env.get(id);
const buttons = fragment => env.descendants(get('workflow-bar')).filter(n =>
  n.tagName === 'BUTTON' && n.textContent.includes(fragment));
const reset = () => get('reset-app').click();

test('inbox mostra apenas os seis casos sintéticos ativos do operador autorizado', () => {
  reset();
  assert.equal(env.cards().length, 6);
  assert.equal(get('team-nav').hidden, true);
  assert.equal(get('team-nav-mobile').hidden, true);
});

test('janela expirada bloqueia texto livre e fornece ações separadas elegíveis', () => {
  reset();
  env.openCase('Exemplo 08');
  assert.equal(get('message-input').disabled, true);
  assert.equal(buttons('Selecionar e solicitar template').length, 1);
  assert.equal(buttons('Solicitar cadeia de tentativas à IA').length, 1);
});

test('template individual usa seleção por caso e não confunde pedido com envio', () => {
  reset();
  env.openCase('Exemplo 08');
  buttons('Selecionar e solicitar template')[0].click();
  assert.equal(get('template-dialog')._open, true);
  assert.equal(get('template-select').children.length, 1);
  assert.equal(get('template-select').value, 'modelo_continuidade_demo');
  get('template-dialog').close('cancel');
  assert.equal(get('template-dialog')._open, false);
  assert.equal(buttons('Selecionar e solicitar template').length, 1);
  buttons('Selecionar e solicitar template')[0].click();
  get('template-dialog').close('confirm');
  assert.ok(get('workflow-bar').textContent.includes('Pedido simulado'));
  assert.equal(get('message-input').disabled, true);
  assert.ok(get('detail-content').textContent.includes('SOLICITADO'));
});

test('histórico continua legível e não permite mensagem em caso perdido', () => {
  reset();
  env.inbox[1].click();
  assert.equal(env.cards().length, 2);
  env.openCase('Exemplo 12');
  assert.equal(get('message-input').disabled, true);
  assert.ok(get('workflow-bar').textContent.includes('perdido'));
});

test('gestor vê equipe somente quando ativo e preserva escopo por loja', () => {
  reset();
  env.selectActor('marina');
  assert.equal(env.cards().length, 10);
  assert.equal(get('team-nav').hidden, false);
  get('team-nav').click();
  assert.equal(get('team-dialog')._open, true);
  assert.equal(get('team-list').children.length, 4);
  get('team-dialog').close();
  env.selectShop('horizonte');
  assert.equal(env.cards().length, 2);
  env.selectActor('otavio');
  assert.equal(env.cards().length, 0);
  assert.equal(get('team-nav').hidden, true);
  assert.equal(get('team-nav-mobile').hidden, true);
  assert.ok(get('conversation-items').textContent.includes('Sem acesso demonstrativo'));
});

test('conclusão humana pede extração apenas uma vez e sem mudança comercial', () => {
  reset();
  env.openCase('Exemplo 02');
  assert.equal(get('message-input').disabled, false);
  assert.equal(buttons('Concluir atendimento').length, 1);
  buttons('Concluir atendimento')[0].click();
  assert.equal(get('completion-dialog')._open, true);
  get('completion-dialog').close('cancel');
  assert.equal(buttons('Concluir atendimento').length, 1);
  buttons('Concluir atendimento')[0].click();
  get('completion-dialog').close('confirm');
  assert.ok(get('workflow-bar').textContent.includes('Solicitação simulada'));
  assert.equal(get('message-input').disabled, true);
  assert.equal(buttons('Concluir atendimento').length, 0);
  assert.equal(get('workflow-bar').textContent.includes('perdido'), false);
});

test('botão equipe é uma opção não operacional para operador, sem privilégio oculto', () => {
  reset();
  assert.equal(get('team-nav').hidden, true);
  get('team-nav').click(); // O mock chama handler mesmo se oculto: backend NÃO seria dependente disso.
  assert.equal(get('team-dialog')._open, false);
});

test('atalho de busca não desloca foco para trás de diálogo aberto', () => {
  reset();
  env.openCase('Exemplo 08');
  buttons('Selecionar e solicitar template')[0].click();
  const select=get('template-select');
  select.focus();
  assert.equal(get('template-dialog')._open,true);
  env.document.fire('keydown',{key:'k',ctrlKey:true});
  assert.equal(env.document.activeElement,select);
  assert.equal(get('template-dialog')._open,true);
  get('template-dialog').close('cancel');
  env.document.fire('keydown',{key:'k',ctrlKey:true});
  assert.equal(env.document.activeElement,get('search-input'));
});
