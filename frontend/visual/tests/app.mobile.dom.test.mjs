import test from 'node:test';
import assert from 'node:assert/strict';
import { installMockDOM } from './dom-fixture.mjs';

const env = installMockDOM({mobile:true});
await import('../app.mjs');

const get = id => env.get(id);
const reset = () => get('reset-app').click();

test('mobile: lista → conversa → detalhes → conversa → lista', () => {
  reset();
  assert.equal(get('visual-app').dataset.mobileView, 'list');
  env.openCase('Exemplo 02');
  assert.equal(get('visual-app').dataset.mobileView, 'thread');
  get('detail-toggle').click();
  assert.equal(get('visual-app').dataset.mobileView, 'detail');
  get('detail-back').click();
  assert.equal(get('visual-app').dataset.mobileView, 'thread');
  get('thread-back').click();
  assert.equal(get('visual-app').dataset.mobileView, 'list');
});

test('mobile: gestor ativo acessa equipe; operador e suspenso não', () => {
  reset();
  assert.equal(get('team-nav-mobile').hidden, true);
  env.selectActor('marina');
  assert.equal(get('team-nav-mobile').hidden, false);
  get('team-nav-mobile').click();
  assert.equal(get('team-dialog')._open, true);
  assert.equal(get('team-list').children.length, 4);
  get('team-dialog').close();
  env.selectActor('rafael');
  assert.equal(get('team-nav-mobile').hidden, true);
  env.selectActor('otavio');
  assert.equal(get('team-nav-mobile').hidden, true);
  assert.equal(env.cards().length, 0);
});

test('mobile: histórico é aberto somente leitura e pode voltar à lista', () => {
  reset();
  env.inbox[1].click();
  assert.equal(env.cards().length, 3);
  env.openCase('Exemplo 12');
  assert.equal(get('visual-app').dataset.mobileView, 'thread');
  assert.equal(get('message-input').disabled, true);
  get('thread-back').click();
  assert.equal(get('visual-app').dataset.mobileView, 'list');
});

test('mobile: operador pendente com janela expirada vê ações sem compositor livre', () => {
  reset();
  env.openCase('Exemplo 08');
  assert.equal(get('message-input').disabled, true);
  const actions = env.descendants(get('workflow-bar')).filter(x=>x.tagName==='BUTTON');
  assert.ok(actions.some(x=>x.textContent.includes('Selecionar e solicitar template')));
  assert.ok(actions.some(x=>x.textContent.includes('Solicitar cadeia')));
  assert.equal(get('visual-app').dataset.mobileView, 'thread');
});
