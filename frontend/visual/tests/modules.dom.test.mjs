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
test('REV-002/024: Banco independente não marca conversa lida nem expõe não aptos',()=>{
 reset();const title=get('thread-title').textContent;
 const before=env.cards().find(n=>n.textContent.includes('Exemplo 02')).textContent;
 get('bank-nav').click();assert.equal(get('bank-dialog').open,true);
 assert.equal(get('visual-app').dataset.module,'bank');
 assert.equal(get('bank-case-select').hidden,true);
 assert.equal(get('bank-content').textContent,'');
 get('bank-case-select').value='A-108';get('bank-case-select').fire('change');
 assert.equal(get('bank-content').textContent,'');
 assert.equal(get('thread-title').textContent,title);
 assert.equal(env.cards().find(n=>n.textContent.includes('Exemplo 02')).textContent,before);
 get('bank-close').click();assert.equal(get('visual-app').dataset.module,'conversations');
});
test('AT-01/02: ciclo com remessa anterior não reaparece como novo cadastro a enviar',()=>{
 reset();env.openCase('Exemplo 15');get('bank-nav').click();
 assert.equal(get('bank-case-select').hidden,true);
 assert.equal(get('bank-content').textContent,'');
 assert.equal(bank().some(n=>n.tagName==='INPUT'),false);
});
test('AT-01: Gestão não concede consulta cadastral D3/D4 em Banco',()=>{
 reset();env.selectActor('marina');get('bank-nav').click();
 for(const id of ['A-108','A-114','A-105','B-201']){
   get('bank-case-select').value=id;get('bank-case-select').fire('change');
   assert.equal(get('bank-content').textContent,'');
 }
 assert.equal(get('bank-case-select').hidden,true);
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

test('COR07 N02: Banco somente aptos preserva rascunho e seleção da conversa A',()=>{
 reset();env.openCase('Exemplo 02');get('message-input').value='Rascunho A 🙂';
 get('bank-nav').click();assert.equal(get('bank-content').textContent,'');
 get('bank-close').click();
 assert.match(get('thread-meta').textContent,/Caso A-102/);
 assert.equal(get('message-input').value,'Rascunho A 🙂');
});
test('COR07 I02: supervisor recebe aviso conservador de saída sem prova',()=>{
 reset();env.selectActor('marina');env.openCase('Exemplo 02');
 assert.match(get('thread-body').textContent,/envio NÃO comprovado|Transporte não confirmado/);
 assert.doesNotMatch(get('thread-body').textContent,/ack-a102|proof-|apiAckRef/);
});
test('COR07 OBS01: resumo de contadores explicita ativos independente do filtro',()=>{
 reset();
 for(const inbox of env.inbox){inbox.click();
   assert.match(get('queue-summary').getAttribute('aria-label'),/ativos/i);
   assert.match(get('queue-summary').textContent,/Total de ativos/);
 }
});

test('FV-UX: banco exibe somente lista elegivel',()=>{
 reset();get('bank-nav').click();
 assert.equal(get('bank-content').textContent,'');
 assert.equal(get('bank-case-select').hidden,true);
 get('bank-close').click();
});

test('FV-UX: inicialização identifica Conversas como módulo ativo',()=>{
 reset();
 assert.equal(get('visual-app').dataset.module,'conversations');
 assert.equal(get('conversations-nav').getAttribute('aria-current'),'page');
 assert.equal(get('bank-dialog').open,false);
 assert.equal(get('team-dialog').open,false);
});
