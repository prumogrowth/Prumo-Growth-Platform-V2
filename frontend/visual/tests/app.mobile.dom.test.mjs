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
  assert.equal(get('team-list').children.length, 2);
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

test('mobile O5: novo ciclo após venda volta à conversa sem reabrir a IA',()=>{
  reset();env.inbox[1].click();env.openCase('Exemplo 16');
  assert.equal(get('visual-app').dataset.mobileView,'thread');
  get('detail-toggle').click();
  assert.equal(get('visual-app').dataset.mobileView,'detail');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Novo contato').click();
  const link=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Abrir novo atendimento humano'));
  assert.ok(link);link.click();
  assert.equal(get('visual-app').dataset.mobileView,'thread');
  assert.ok(get('thread-meta').textContent.includes('Caso A-116'));
  assert.ok(get('workflow-bar').textContent.includes('em atendimento pelo operador'));
});

test('mobile G2: painel mostra operadores supervisionados e pausa global fictícia',()=>{
  reset();env.selectActor('marina');
  get('team-nav-mobile').click();
  assert.equal(get('team-dialog').open,true);
  assert.equal(get('team-list').children.length,2);
  const pause=env.descendants(get('team-list')).find(x=>x.tagName==='BUTTON' &&
    x.textContent.includes('Solicitar pausa'));
  assert.ok(pause);pause.click();get('intake-dialog').close('confirm');
  assert.ok(get('team-list').textContent.includes('NÃO aplicado'));
  get('team-dialog').close();
  assert.equal(get('team-dialog').open,false);
});

test('mobile G3: indicadores por operadores aparecem sem dados de clientes',()=>{
  reset();env.selectActor('marina');
  get('team-nav-mobile').click();
  const dashboard=get('team-monitor');
  assert.ok(dashboard.textContent.includes('Monitoramento operacional da equipe'));
  assert.ok(dashboard.textContent.includes('Etapas comerciais canônicas'));
  assert.equal(dashboard.textContent.includes('Bianca Rocha'),false);
  assert.equal(dashboard.textContent.includes('Cliente Exemplo'),false);
  get('team-dialog').close();
});

test('mobile G3: alternar Operadores e Monitoramento mantém isolamento e privacidade',()=>{
  reset();env.selectActor('marina');get('team-nav-mobile').click();
  get('team-show-monitor').click();
  assert.equal(get('team-monitor').hidden,false);
  assert.ok(get('team-monitor').textContent.includes('Caso A-112'));
  assert.ok(get('team-monitor').textContent.includes('Etapas comerciais canônicas'));
  assert.equal(get('team-monitor').textContent.includes('Caso A-103'),false);
  get('team-show-members').click();
  assert.equal(get('team-monitor').hidden,true);
  get('team-dialog').close();
  env.selectActor('rafael');
  get('team-nav-mobile').click();
  assert.equal(get('team-dialog').open,false);
  assert.equal(get('team-monitor').textContent,'');
});

test('mobile G4: lotes por equipe só leitura e sem importação',()=>{
  reset();env.selectActor('marina');get('team-nav-mobile').click();get('team-show-batches').click();
  assert.equal(get('team-batches').hidden,false);
  assert.ok(get('team-batches').textContent.includes('L-G4-01'));
  assert.equal(get('team-batches').textContent.includes('L-G4-03'),false);
  get('team-show-monitor').click();
  assert.equal(get('team-batches').hidden,true);
  get('team-dialog').close();
});


test('mobile G3/G4: alternância entre gestores apaga painel anterior antes de mostrar a outra equipe',()=>{
  reset();env.selectActor('marina');get('team-nav-mobile').click();
  get('team-show-batches').click();
  assert.ok(get('team-batches').textContent.includes('L-G4-01'));
  assert.equal(get('team-batches').textContent.includes('L-G4-03'),false);
  env.selectActor('daniel');
  assert.equal(get('team-dialog').open,false);
  assert.equal(get('team-batches').textContent,'');
  assert.equal(get('team-monitor').textContent,'');
  get('team-nav-mobile').click();
  get('team-show-monitor').click();
  const monitor=get('team-monitor').textContent;
  assert.ok(monitor.includes('Bianca Rocha'));
  assert.ok(monitor.includes('Caso A-103'));
  assert.equal(monitor.includes('Rafael Lima'),false);
  assert.equal(monitor.includes('Caso A-112'),false);
  get('team-show-batches').click();
  const batches=get('team-batches').textContent;
  assert.ok(batches.includes('L-G4-03'));
  assert.equal(batches.includes('L-G4-01'),false);
  env.selectActor('otavio');
  assert.equal(get('team-dialog').open,false);
  assert.equal(get('team-monitor').textContent,'');
  assert.equal(get('team-batches').textContent,'');
  assert.equal(get('team-nav-mobile').hidden,true);
});

test('FV-UI-021: foco acompanha a navegação entre telas móveis',()=>{
  reset();env.openCase('Exemplo 02');
  assert.equal(env.document.activeElement,get('thread-back'));
  assert.match(get('context-announcement').textContent,/Caso A-102 aberto/);
  get('detail-toggle').click();
  assert.equal(env.document.activeElement,get('detail-back'));
  get('detail-back').click();
  assert.equal(env.document.activeElement,get('detail-toggle'));
  get('thread-back').click();
  assert.equal(env.document.activeElement,get('search-input'));
});


test('FV-UI-022: Escape móvel reutiliza retorno com foco no painel visível',()=>{
  reset();env.openCase('Exemplo 02');
  get('detail-toggle').click();
  assert.equal(get('visual-app').dataset.mobileView,'detail');
  get('detail-back').focus();
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(get('visual-app').dataset.mobileView,'thread');
  assert.equal(env.document.activeElement,get('detail-toggle'));
  get('thread-back').focus();
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(get('visual-app').dataset.mobileView,'list');
  assert.equal(env.document.activeElement,get('search-input'));
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(get('visual-app').dataset.mobileView,'list');
});

test('FV-UI-022: Escape não navega sob modal aberto ou digitando no campo',()=>{
  reset();env.openCase('Exemplo 02');
  get('message-input').focus();
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(get('visual-app').dataset.mobileView,'thread');
  get('composer').fire('submit');
  get('message-input').value='Rascunho válido apenas no caso';
  get('composer').fire('submit');
  assert.equal(get('message-preview-dialog').open,true);
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(get('message-preview-dialog').open,true);
  get('message-preview-dialog').close('cancel');
  assert.equal(get('message-input').value,'Rascunho válido apenas no caso');
  assert.equal(env.document.activeElement,get('message-input'));
});
