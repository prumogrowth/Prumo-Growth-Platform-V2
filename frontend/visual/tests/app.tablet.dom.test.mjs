import test from 'node:test';
import assert from 'node:assert/strict';
import { installMockDOM } from './dom-fixture.mjs';

const env=installMockDOM({tablet:true});
await import('../app.mjs');
const get=id=>env.get(id);
const reset=()=>get('reset-app').click();
const openDetails=()=>{if(get('visual-app').classList.contains('details-hidden'))get('thread-title').click();};

test('FV-UI-034: Fechar detalhes restaura foco no botão de abertura',()=>{
  reset();env.openCase('Exemplo 02');
  openDetails();
  assert.equal(get('thread-title').getAttribute('aria-expanded'),'true');
  get('detail-close').focus();get('detail-close').click();
  assert.ok(get('visual-app').classList.contains('details-hidden'));
  assert.equal(get('thread-title').getAttribute('aria-expanded'),'false');
  assert.equal(env.document.activeElement,get('thread-title'));
  assert.match(get('thread-meta').textContent,/Caso A-102/);
});

test('FV-UI-034: Escape no painel flutuante fecha e foca abertura',()=>{
  reset();env.openCase('Exemplo 02');openDetails();
  get('detail-pane').focus();
  env.document.fire('keydown',{key:'Escape'});
  assert.ok(get('visual-app').classList.contains('details-hidden'));
  assert.equal(env.document.activeElement,get('thread-title'));
  assert.equal(get('thread-title').getAttribute('aria-expanded'),'false');
});

test('FV-UI-034: Escape fora do painel não fecha detalhes',()=>{
  reset();env.openCase('Exemplo 02');openDetails();
  get('message-input').focus();env.document.fire('keydown',{key:'Escape'});
  assert.equal(get('visual-app').classList.contains('details-hidden'),false);
  assert.equal(env.document.activeElement,get('message-input'));
});

test('FV-UI-034: diálogo modal bloqueia fechamento de detalhes',()=>{
  reset();env.openCase('Exemplo 02');openDetails();
  get('completion-dialog').showModal();get('detail-pane').focus();
  env.document.fire('keydown',{key:'Escape'});
  get('detail-close').click();
  assert.equal(get('visual-app').classList.contains('details-hidden'),false);
  get('completion-dialog').close('cancel');
});
