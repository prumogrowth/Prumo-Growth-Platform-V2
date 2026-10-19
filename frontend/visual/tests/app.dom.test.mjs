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
  assert.equal(env.cards().length, 8);
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
  assert.equal(env.cards().length, 3);
  env.openCase('Exemplo 12');
  assert.equal(get('message-input').disabled, true);
  assert.ok(get('workflow-bar').textContent.includes('perdido'));
});

test('gestor vê equipe somente quando ativo e preserva escopo por loja', () => {
  reset();
  env.selectActor('marina');
  assert.equal(env.cards().length, 11);
  assert.equal(get('team-nav').hidden, false);
  get('team-nav').click();
  assert.equal(get('team-dialog')._open, true);
  assert.equal(get('team-list').children.length, 2);
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

test('troca de perfil invalida confirmação modal de caso antigo', () => {
  reset();
  env.openCase('Exemplo 02');
  buttons('Concluir atendimento')[0].click();
  assert.equal(get('completion-dialog').open, true);
  env.selectActor('marina');
  assert.equal(get('completion-dialog').open, false);
  get('completion-dialog').close('confirm'); // resposta atrasada não deve alterar outra sessão
  env.selectActor('rafael');
  env.openCase('Exemplo 02');
  assert.equal(buttons('Concluir atendimento').length, 1);
});

test('troca de conversa invalida confirmação de template de outro caso', () => {
  reset();
  env.openCase('Exemplo 08');
  buttons('Selecionar e solicitar template')[0].click();
  assert.equal(get('template-dialog').open, true);
  env.openCase('Exemplo 02');
  assert.equal(get('template-dialog').open, false);
  get('template-dialog').close('confirm');
  env.openCase('Exemplo 08');
  assert.equal(buttons('Selecionar e solicitar template').length, 1);
  assert.equal(get('workflow-bar').textContent.includes('Pedido simulado'), false);
});

test('projeção desconhecida não aparece como conclusão humana ou extração processada', () => {
  reset();
  env.openCase('Exemplo 05');
  assert.ok(get('workflow-bar').textContent.includes('Etapa humana não confirmada'));
  get('detail-toggle').click();
  const tabs=env.descendants(get('detail-content')).filter(x=>x.attrs.role==='tab');
  tabs.find(x=>x.textContent==='Extração').click();
  assert.ok(get('detail-content').textContent.includes('Situação não confirmada'));
  assert.equal(get('detail-content').textContent.includes('Etapa concluída · retorno não disponível'),false);
});

test('pedido aceito não mostra falsa conclusão confirmada', () => {
  reset(); env.openCase('Exemplo 02');
  buttons('Concluir atendimento')[0].click();
  get('completion-dialog').close('confirm');
  assert.ok(get('workflow-bar').textContent.includes('Conclusão solicitada'));
  assert.equal(get('workflow-bar').textContent.includes('Etapa humana concluída'),false);
  assert.ok(get('detail-content').textContent.includes('Solicitação registrada'));
});

test('formulário de nota obsoleto não escreve em outro caso da fila', () => {
  reset(); env.openCase('Exemplo 02');
  const tabs = env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab');
  tabs.find(x=>x.textContent==='Notas').click();
  const form=env.descendants(get('detail-content')).find(n=>n.id==='internal-note-form');
  const editor=env.descendants(form).find(n=>n.id==='note-text');
  editor.value='Nota obsoleta que deve ser rejeitada';
  env.openCase('Exemplo 05');
  form.fire('submit'); // callback tardio sobre formulário que já saiu da tela
  env.openCase('Exemplo 02');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(x=>x.textContent==='Notas').click();
  assert.equal(get('detail-content').textContent.includes('Nota obsoleta que deve ser rejeitada'),false);
});

test('O3: operador vê ficha confirmada com fonte, versão, pendência e conflito fictícios', () => {
  reset();
  env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Extração').click();
  const text=get('detail-content').textContent;
  assert.ok(text.includes('v1-ficticia'));
  assert.ok(text.includes('Valor fictício confirmado'));
  assert.ok(text.includes('Mensagem ilustrativa do cliente'));
  assert.ok(text.includes('Informação demonstrativa B — ausente'));
  assert.ok(text.includes('Informação demonstrativa D — fontes'));
  assert.equal(text.includes('Somente proposta'),false);
});

test('O3: gestora supervisora não recebe campos, valores, fontes e pendências D3', () => {
  reset();
  env.selectActor('marina');
  env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Extração').click();
  const text=get('detail-content').textContent;
  assert.ok(text.includes('Detalhes restritos ao responsável'));
  for(const forbidden of ['Valor fictício confirmado','v1-ficticia','a108-1',
    'Informação demonstrativa B — ausente','Informação demonstrativa D — fontes']){
    assert.equal(text.includes(forbidden),false);
  }
});

test('O4: operador atribuído vê só remessa sintética comprovada e retorno pendente',()=>{
  reset();env.openCase('Exemplo 05');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Banco').click();
  const text=get('detail-content').textContent;
  assert.ok(text.includes('bank-demo-v1'));
  assert.ok(text.includes('Remessa confirmada apenas na fixture'));
  assert.ok(text.includes('Decisão bancária não confirmada'));
  assert.equal(text.includes('Retorno do banco confirmado'),false);
  assert.ok(text.includes('cadastro enviado ao banco'));
});

test('O4: gestora sem atribuição vê só marco bancário, sem prova D4',()=>{
  reset();env.selectActor('marina');env.openCase('Exemplo 05');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Banco').click();
  const text=get('detail-content').textContent;
  assert.ok(text.includes('Acompanhamento bancário · resumo'));
  assert.ok(text.includes('sem documento'));
  assert.equal(text.includes('bank-demo-v1'),false);
  assert.equal(text.includes('Remessa confirmada apenas na fixture'),false);
});

test('O5: remessa bancária mantém caso original e navega para atendimento humano independente',()=>{
  reset();env.openCase('Exemplo 05');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Novo contato').click();
  const detail=get('detail-content').textContent;
  assert.ok(detail.includes('Novo atendimento humano confirmado'));
  assert.ok(detail.includes('cadastro enviado ao banco'));
  const open=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Abrir novo atendimento humano'));
  assert.ok(open);
  open.click();
  assert.ok(get('thread-meta').textContent.includes('Caso A-114'));
  assert.ok(get('workflow-bar').textContent.includes('em atendimento pelo operador'));
  assert.equal(get('message-input').disabled,false);
  const back=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Consultar atendimento de origem'));
  assert.ok(back);
  back.click();
  assert.ok(get('thread-meta').textContent.includes('Caso A-105'));
  assert.ok(get('workflow-bar').textContent.includes('cadastro enviado ao banco'));
  assert.equal(get('message-input').disabled,true);
});

test('O5: histórico de vendido é preservado em separado do novo contato',()=>{
  reset();env.inbox[1].click();
  env.openCase('Exemplo 16');
  assert.ok(get('workflow-bar').textContent.includes('vendido'));
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Novo contato').click();
  const navigate=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Abrir novo atendimento humano'));
  assert.ok(navigate);navigate.click();
  assert.equal(env.inbox[0].attrs['aria-pressed'],'true');
  assert.ok(get('thread-meta').textContent.includes('Caso A-116'));
  assert.ok(get('workflow-bar').textContent.includes('em atendimento pelo operador'));
  assert.equal(get('message-input').disabled,false);
});

test('O5: supervisora vê vínculo D2 mas não ganha ação humana por supervisão',()=>{
  reset();env.selectActor('marina');env.openCase('Exemplo 15');
  assert.equal(get('message-input').disabled,true);
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Novo contato').click();
  assert.ok(get('detail-content').textContent.includes('Continuidade humana em novo ciclo'));
  assert.equal(get('message-input').disabled,true);
});

test('G2: Marina vê Rafael e Lia, não Bianca ou Otávio, independente do filtro de loja',()=>{
  reset();env.selectActor('marina');
  get('team-nav').click();
  const panel=()=>get('team-list').textContent;
  assert.equal(get('team-list').children.length,2);
  assert.ok(panel().includes('Rafael Lima'));
  assert.ok(panel().includes('Lia Martins'));
  assert.equal(panel().includes('Bianca Rocha'),false);
  assert.equal(panel().includes('Otávio'),false);
  get('team-dialog').close();
  env.selectShop('horizonte');
  get('team-nav').click();
  assert.equal(get('team-list').children.length,2);
  assert.ok(panel().includes('Rafael Lima'));
  assert.ok(panel().includes('Lia Martins'));
  get('team-dialog').close();
});

test('G2: Daniel só gerencia Bianca e Otávio, mesmo compartilhando as lojas',()=>{
  reset();env.selectActor('daniel');
  assert.equal(env.cards().length,1);
  get('team-nav').click();
  const text=get('team-list').textContent;
  assert.ok(text.includes('Bianca Rocha')&&text.includes('Otávio'));
  assert.equal(text.includes('Rafael Lima'),false);
  assert.equal(text.includes('Lia Martins'),false);
  assert.ok(text.includes('Aurora Motos, Horizonte Motos'));
  get('team-dialog').close();
  env.selectShop('horizonte');
  assert.equal(env.cards().length,1);
  env.openCase('Exemplo 18');
  assert.equal(get('message-input').disabled,true); // Bianca tem o caso, Daniel só supervisiona
});

test('G2: solicitação de pausa não concede lojas nem altera atribuição/estado comercial',()=>{
  reset();env.selectActor('marina');
  get('team-nav').click();
  const team=get('team-list');
  const button=env.descendants(team).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Solicitar pausa'));
  assert.ok(button);
  button.click();
  assert.ok(team.textContent.includes('SOLICITADO LOCALMENTE'));
  assert.ok(team.textContent.includes('todas as lojas concedidas'));
  assert.ok(team.textContent.includes('NÃO aplicado'));
  assert.equal(env.descendants(team).filter(n=>n.tagName==='SELECT').length,0);
  get('team-dialog').close();
  env.openCase('Exemplo 02');
  assert.ok(get('workflow-bar').textContent.includes('em atendimento pelo operador'));
  assert.ok(get('thread-meta').textContent.includes('Caso A-102'));
});

test('G2: pedido local de retomada de Bianca mantém pausa confirmada na fixture',()=>{
  reset();env.selectActor('daniel');get('team-nav').click();
  const team=get('team-list'),button=env.descendants(team).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Solicitar retomada'));
  assert.ok(button);button.click();
  assert.ok(team.textContent.includes('Novos leads pausados (projeção fictícia)'));
  assert.ok(team.textContent.includes('SOLICITADO LOCALMENTE'));
  assert.equal(env.descendants(team).filter(n=>n.tagName==='BUTTON').length,0);
  get('team-dialog').close();
  env.selectActor('rafael');env.selectActor('daniel');
  get('team-nav').click();
  assert.equal(get('team-list').textContent.includes('SOLICITADO LOCALMENTE'),false);
  get('team-dialog').close();
});
