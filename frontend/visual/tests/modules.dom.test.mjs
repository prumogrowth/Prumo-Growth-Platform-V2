import test from 'node:test';
import assert from 'node:assert/strict';
import { installMockDOM } from './dom-fixture.mjs';
const env=installMockDOM();await import('../app.mjs');
const get=id=>env.get(id), reset=()=>get('reset-app').click();
const detail=()=>env.descendants(get('detail-content'));
const bank=()=>env.descendants(get('bank-content'));

test('REV-018/022: somente três abas e nenhum nome duplicado no painel',()=>{
 reset();env.openCase('Exemplo 02');
 assert.deepEqual(detail().filter(n=>n.attrs.role==='tab').map(n=>n.textContent),['Resumo','Histórico','Notas']);
 assert.doesNotMatch(get('detail-content').textContent,/Cliente Exemplo 02|REGRAS DA EXPERIÊNCIA/);
 assert.match(get('detail-content').textContent,/Rafael Lima/);
});
test('REV-002/024: consultar Banco não seleciona nem lê a conversa',()=>{
 reset();const title=get('thread-title').textContent;
 const unread=env.cards().find(n=>n.textContent.includes('Exemplo 02')).textContent;
 get('bank-nav').click();assert.equal(get('bank-dialog').open,true);
 get('bank-case-select').value='A-108';get('bank-case-select').fire('change');
 assert.match(get('bank-content').textContent,/Valor fictício confirmado|v1-ficticia/);
 assert.equal(get('thread-title').textContent,title);
 assert.equal(env.cards().find(n=>n.textContent.includes('Exemplo 02')).textContent,unread);
 assert.equal(bank().some(n=>['INPUT','TEXTAREA'].includes(n.tagName)),false);
 get('bank-close').click();assert.equal(env.document.activeElement,get('bank-nav'));
});
test('AT-01/02: ficha inicial F01, atualização F03, versões e snapshot coexistem',()=>{
 reset();env.openCase('Exemplo 15');env.openArea('Banco');
 const text=get('bank-content').textContent;
 for(const part of ['F01 · coleta inicial','F03 · atualização confirmada','live-form-v1-demo','live-form-v2-demo','bank-demo-v1','snapshot preservado','Aptidão para remessa','Confirmada apenas na fixture · sem remessa iniciada','Decisão bancária não confirmada'])assert.ok(text.includes(part),part);
 assert.equal(bank().some(n=>n.tagName==='INPUT'),false);
});
test('AT-01: supervisão não obtém D3/D4 ao usar o novo destino',()=>{
 reset();env.selectActor('marina');get('bank-nav').click();
 for(const id of ['A-108','A-114','A-105']){
   get('bank-case-select').value=id;get('bank-case-select').fire('change');
   assert.doesNotMatch(get('bank-content').textContent,/Valor fictício confirmado|v1-ficticia|bank-demo-v1|f03-form-v2-demo|Valor sintético/);
 }
 get('bank-case-select').value='B-201';get('bank-case-select').fire('change');
 assert.doesNotMatch(get('bank-content').textContent,/Horizonte/);
});
test('REV-021: comunicações acumulativas mantêm cada resultado autorizado',()=>{
 reset();env.openCase('Exemplo 09');
 assert.equal(detail().filter(n=>n.className==='ai-communication').length,5);
 const f03=detail().filter(n=>n.dataset.source==='F03');assert.equal(f03.length,2);
 assert.match(f03[0].textContent,/concl-a108-1/);assert.match(f03[1].textContent,/concl-a108-2/);
});
test('REV-027/AT-07: rascunho não vira nota e permanece ao navegar entre abas e módulos',()=>{
 reset();env.openCase('Exemplo 02');env.openArea('Notas');
 let input=detail().find(n=>n.id==='note-text');input.value='Não submetida';input.fire('input');
 get('message-input').value='Texto e emoji 🙂';
 get('bank-nav').click();get('bank-close').click();
 env.openArea('Resumo');env.openArea('Notas');input=detail().find(n=>n.id==='note-text');
 assert.equal(input.value,'Não submetida');assert.equal(get('message-input').value,'Texto e emoji 🙂');
 assert.equal(detail().filter(n=>n.className==='detail-row').length,0);
 env.openCase('Exemplo 05');env.openArea('Notas');assert.equal(detail().some(n=>n.id==='note-text'),false);
 env.selectActor('marina');env.openCase('Exemplo 02');env.openArea('Notas');
 assert.equal(detail().some(n=>n.id==='note-text'),false);
});
test('REV-028/030: tentativas canceladas têm histórico e não permanecem no futuro',()=>{
 reset();env.openCase('Exemplo 11');env.openArea('Histórico');
 const future=detail().find(n=>n.id==='future-attempts');assert.ok(future);
 assert.equal(env.descendants(future).some(n=>n.dataset.state==='cancelled'),false);
 assert.ok(detail().some(n=>n.dataset.state==='cancelled'));
 assert.ok(detail().some(n=>n.dataset.state==='failed'));
 assert.ok(detail().some(n=>n.dataset.state==='uncertain'));
});
test('REV-036: gestão mantém módulos e supervisão não se torna operação',()=>{
 reset();env.selectActor('marina');env.openCase('Exemplo 02');
 assert.equal(get('message-input').disabled,true);
 get('team-nav').click();assert.equal(get('team-dialog').open,true);
 for(const id of ['team-show-members','team-show-monitor','team-show-batches','team-show-queue']){
   get(id).click();assert.equal(get('team-dialog').open,true);
 }
 get('team-close').click();assert.equal(get('message-input').disabled,true);
 env.selectActor('rafael');get('team-nav').click();assert.equal(get('team-dialog').open,false);
});
