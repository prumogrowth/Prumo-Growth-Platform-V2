import test from 'node:test';
import assert from 'node:assert/strict';
import { insertDraftEmoji, audioDuration } from '../communication-composer.mjs';
import { installMockDOM } from './dom-fixture.mjs';

test('emoji insere no cursor e substitui seleção preservando o restante do rascunho',()=>{
  assert.deepEqual(insertDraftEmoji('Olá, cliente',3,3,'😊'),{value:'Olá😊, cliente',cursor:5});
  assert.deepEqual(insertDraftEmoji('Olá, cliente',5,12,'👋'),{value:'Olá, 👋',cursor:7});
  assert.equal(insertDraftEmoji('a'.repeat(499),499,499,'😊'),null);
  assert.equal(insertDraftEmoji('texto',0,0,'<script>'),null);
  assert.equal(audioDuration(65.9),'1:05');
});
const env=installMockDOM();
await import('../app.mjs');
const get=id=>env.get(id);
test('seleção por teclado insere sem prévia/envio automático; cancelamento mantém rascunho',()=>{
  env.openCase('Exemplo 02');get('message-input').value='Teste';get('message-input').fire('input');
  get('emoji-toggle').click();assert.equal(get('emoji-picker').hidden,false);
  const options=get('emoji-picker').children;
  assert.equal(env.document.activeElement,options[0]);
  options[0].fire('keydown',{key:'ArrowRight'});assert.equal(env.document.activeElement,options[1]);
  options[1].click();assert.equal(get('message-input').value,'Teste😊');
  assert.equal(get('message-preview-dialog').open,false);assert.equal(get('emoji-picker').hidden,true);
  get('emoji-toggle').click();get('emoji-picker').fire('keydown',{key:'Escape'});
  assert.equal(get('message-input').value,'Teste😊');assert.equal(env.document.activeElement,get('message-input'));
});
test('troca de caso e perfil descarta picker e bloqueia ferramentas sem autoria',()=>{
  env.openCase('Exemplo 02');get('emoji-toggle').click();env.openCase('Exemplo 08');
  assert.equal(get('emoji-picker').hidden,true);assert.equal(get('emoji-toggle').disabled,true);
  assert.equal(get('audio-record').disabled,true);assert.match(get('composer-availability').textContent,/encerrada/);
  env.selectActor('marina');env.openCase('Exemplo 02');
  assert.equal(get('emoji-toggle').disabled,true);assert.equal(get('audio-record').disabled,true);
  assert.match(get('composer-availability').textContent,/indisponível/);
});
