import test from 'node:test';
import assert from 'node:assert/strict';
import {installMockDOM} from './dom-fixture.mjs';

const env=installMockDOM();
await import('../app.mjs');
const get=id=>env.get(id);
const reset=()=>get('reset-app').click();
const card=name=>env.cards().find(x=>x.getAttribute('aria-label')?.includes(name));
const attention=name=>env.descendants(card(name)).find(x=>
  x.classList.contains('attention-unread')||x.classList.contains('attention-pending'));

test('FV-UI-015 operador vê contador e leitura sem resposta muda a MESMA bolinha',()=>{
  reset();
  assert.equal(attention('Exemplo 02').textContent,'2');
  assert.ok(attention('Exemplo 02').classList.contains('attention-unread'));
  env.openCase('Exemplo 02');
  assert.ok(attention('Exemplo 02').classList.contains('attention-pending'));
  assert.equal(attention('Exemplo 02').textContent,'');
  assert.match(attention('Exemplo 02').getAttribute('aria-label'),/Visualizada pelo titular/);
});

test('FV-UI-017 mensagem local NÃO enviada não comprova resposta humana',()=>{
  reset();
  env.openCase('Exemplo 02');
  get('message-input').value='Resposta humana local de demonstração';
  get('composer').fire('submit');
  assert.equal(get('message-preview-dialog').open,true);
  assert.ok(attention('Exemplo 02').classList.contains('attention-pending'));
  get('message-preview-dialog').close('confirm');
  assert.ok(attention('Exemplo 02').classList.contains('attention-pending'));
  assert.match(get('thread-body').textContent,/NÃO ENVIADA/);
});

test('FV-UI-015 gestor apenas supervisor não marca mensagens como lidas pelo operador',()=>{
  reset();
  env.selectActor('marina');
  assert.equal(attention('Exemplo 02').textContent,'2');
  env.openCase('Exemplo 02');
  assert.ok(attention('Exemplo 02').classList.contains('attention-unread'));
  env.selectActor('rafael');
  assert.equal(attention('Exemplo 02').textContent,'2');
});

test('FV-UI-015 troca de ator não transforma leitura de gestor em confirmação do operador',()=>{
  reset();
  env.selectActor('marina');
  env.openCase('Exemplo 02');
  env.selectActor('daniel');
  assert.equal(card('Exemplo 02'),undefined);
  env.selectActor('rafael');
  assert.equal(attention('Exemplo 02').textContent,'2');
});

test('FV-UI-015 gestor recebe confirmação ANTES do pedido fictício de pausa',()=>{
  reset();env.selectActor('marina');
  get('team-nav').click();
  const btn=()=>env.descendants(get('team-list')).find(n=>
    n.tagName==='BUTTON' && n.textContent.includes('Solicitar pausa de novos leads'));
  assert.ok(btn());
  btn().click();
  assert.equal(get('intake-dialog').open,true);
  assert.ok(!get('team-list').textContent.includes('SOLICITADO LOCALMENTE'));
  get('intake-dialog').close('cancel');
  assert.ok(btn(),'Cancelamento mantém botão disponível');
  btn().click();
  get('intake-dialog').close('confirm');
  assert.ok(get('team-list').textContent.includes('SOLICITADO LOCALMENTE'));
  assert.ok(get('team-list').textContent.includes('NÃO aplicado'));
});

test('FV-UI-015 confirmação antiga é descartada após troca de ator',()=>{
  reset();env.selectActor('marina');get('team-nav').click();
  const btn=env.descendants(get('team-list')).find(n=>
    n.tagName==='BUTTON' && n.textContent.includes('Solicitar pausa'));
  btn.click();assert.equal(get('intake-dialog').open,true);
  env.selectActor('daniel');
  assert.equal(get('intake-dialog').open,false);
  get('intake-dialog').close('confirm');
  get('team-nav').click();
  assert.ok(!get('team-list').textContent.includes('SOLICITADO LOCALMENTE'));
});

test('FV-UI-015 operador comum não pode gerar pedido gerencial',()=>{
  reset();get('team-nav').click();
  assert.equal(get('team-dialog').open,false);
  assert.equal(get('intake-dialog').open,false);
});
