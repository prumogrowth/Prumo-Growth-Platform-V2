import test from 'node:test';
import assert from 'node:assert/strict';
import { installMockDOM } from './dom-fixture.mjs';

// A aplicação depende de um DOM. O mock é instalado ANTES do import.
// Este ensaio não substitui Chromium, valida layout nem comprova autenticação.
const env = installMockDOM();
await import('../app.mjs');

const get = id => env.get(id);
const buttons = fragment => [...env.descendants(get('workflow-bar')),...env.descendants(get('thread-actions'))].filter(n =>
  n.tagName === 'BUTTON' && n.textContent.includes(fragment));
// Legacy journeys explicitly select the active subset of the new continuous list.
const reset = () => {get('reset-app').click();env.inbox[0].click();};

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
  assert.equal(buttons('Enviar template').length, 1);
  assert.equal(buttons('Cadeia por IA').length, 1);
});

test('template individual usa seleção por caso e não confunde pedido com envio', () => {
  reset();
  env.openCase('Exemplo 08');
  buttons('Enviar template')[0].click();
  assert.equal(get('template-dialog')._open, true);
  assert.equal(get('template-select').children.length, 1);
  assert.equal(get('template-select').value, 'modelo_continuidade_demo');
  get('template-dialog').close('cancel');
  assert.equal(get('template-dialog')._open, false);
  assert.equal(buttons('Enviar template').length, 1);
  buttons('Enviar template')[0].click();
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
  assert.ok(get('terminal-banner').textContent.includes('Perdido'));
});

test('gestor vê equipe somente quando ativo e preserva escopo por loja', () => {
  reset();
  env.selectActor('marina');env.inbox[0].click();
  assert.equal(env.cards().length, 12); // inclui transferência fictícia A-117 de escopo por caso
  assert.equal(get('team-nav').hidden, false);
  get('team-nav').click();
  assert.equal(get('team-dialog')._open, true);
  assert.equal(get('team-list').children.length, 2);
  get('team-dialog').close();
  env.selectShop('horizonte');env.inbox[0].click();
  assert.equal(env.cards().length, 2);
  env.selectActor('otavio');env.inbox[0].click();
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
  assert.equal(get('terminal-banner').textContent.includes('Perdido'), false);
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
  buttons('Enviar template')[0].click();
  const select=get('template-select');
  select.focus();
  assert.equal(get('template-dialog')._open,true);
  env.document.fire('keydown',{key:'k',ctrlKey:true});
  assert.equal(env.document.activeElement,select);
  assert.equal(get('template-dialog')._open,true);
  get('template-dialog').close('cancel');
  env.document.fire('keydown',{key:'k',ctrlKey:true});
  assert.equal(env.document.activeElement,select);
});

test('troca de perfil invalida confirmação modal de caso antigo', () => {
  reset();
  env.openCase('Exemplo 02');
  buttons('Concluir atendimento')[0].click();
  assert.equal(get('completion-dialog').open, true);
  env.selectActor('marina');env.inbox[0].click();
  assert.equal(get('completion-dialog').open, false);
  get('completion-dialog').close('confirm'); // resposta atrasada não deve alterar outra sessão
  env.selectActor('rafael');env.inbox[0].click();
  env.openCase('Exemplo 02');
  assert.equal(buttons('Concluir atendimento').length, 1);
});

test('troca de conversa invalida confirmação de template de outro caso', () => {
  reset();
  env.openCase('Exemplo 08');
  buttons('Enviar template')[0].click();
  assert.equal(get('template-dialog').open, true);
  env.openCase('Exemplo 02');
  assert.equal(get('template-dialog').open, false);
  get('template-dialog').close('confirm');
  env.openCase('Exemplo 08');
  assert.equal(buttons('Enviar template').length, 1);
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
  assert.ok(get('workflow-bar').textContent.includes('Solicitação simulada'));
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
  env.selectActor('marina');env.inbox[0].click();
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
  reset();env.selectActor('marina');env.inbox[0].click();env.openCase('Exemplo 05');
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
  assert.ok(get('detail-content').textContent.includes('em atendimento pelo operador'));
  assert.equal(get('message-input').disabled,false);
  const back=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Consultar atendimento de origem'));
  assert.ok(back);
  back.click();
  assert.ok(get('thread-meta').textContent.includes('Caso A-105'));
  assert.ok(get('detail-content').textContent.includes('cadastro enviado ao banco'));
  assert.equal(get('message-input').disabled,true);
});

test('O5: histórico de vendido é preservado em separado do novo contato',()=>{
  reset();env.inbox[1].click();
  env.openCase('Exemplo 16');
  assert.ok(get('detail-content').textContent.includes('vendido'));
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Novo contato').click();
  const navigate=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Abrir novo atendimento humano'));
  assert.ok(navigate);navigate.click();
  assert.equal(env.inbox[0].attrs['aria-pressed'],'true');
  assert.ok(get('thread-meta').textContent.includes('Caso A-116'));
  assert.ok(get('detail-content').textContent.includes('em atendimento pelo operador'));
  assert.equal(get('message-input').disabled,false);
});

test('O5: supervisora vê vínculo D2 mas não ganha ação humana por supervisão',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();env.openCase('Exemplo 15');
  assert.equal(get('message-input').disabled,true);
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Novo contato').click();
  assert.ok(get('detail-content').textContent.includes('Continuidade humana em novo ciclo'));
  assert.equal(get('message-input').disabled,true);
});

test('G2: Marina vê Rafael e Lia, não Bianca ou Otávio, independente do filtro de loja',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();
  get('team-nav').click();
  const panel=()=>get('team-list').textContent;
  assert.equal(get('team-list').children.length,2);
  assert.ok(panel().includes('Rafael Lima'));
  assert.ok(panel().includes('Lia Martins'));
  assert.equal(panel().includes('Bianca Rocha'),false);
  assert.equal(panel().includes('Otávio'),false);
  get('team-dialog').close();
  env.selectShop('horizonte');env.inbox[0].click();
  get('team-nav').click();
  assert.equal(get('team-list').children.length,2);
  assert.ok(panel().includes('Rafael Lima'));
  assert.ok(panel().includes('Lia Martins'));
  get('team-dialog').close();
});

test('G2: Daniel só gerencia Bianca e Otávio, mesmo compartilhando as lojas',()=>{
  reset();env.selectActor('daniel');env.inbox[0].click();
  assert.equal(env.cards().length,1);
  get('team-nav').click();
  const text=get('team-list').textContent;
  assert.ok(text.includes('Bianca Rocha')&&text.includes('Otávio'));
  assert.equal(text.includes('Rafael Lima'),false);
  assert.equal(text.includes('Lia Martins'),false);
  assert.ok(text.includes('Aurora Motos, Horizonte Motos'));
  get('team-dialog').close();
  env.selectShop('horizonte');env.inbox[0].click();
  assert.equal(env.cards().length,1);
  env.openCase('Exemplo 18');
  assert.equal(get('message-input').disabled,true); // Bianca tem o caso, Daniel só supervisiona
});

test('G2: solicitação de pausa não concede lojas nem altera atribuição/estado comercial',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();
  get('team-nav').click();
  const team=get('team-list');
  const button=env.descendants(team).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Solicitar pausa'));
  assert.ok(button);
  button.click();
  assert.equal(get('intake-dialog').open,true);
  assert.ok(!team.textContent.includes('SOLICITADO LOCALMENTE'));
  get('intake-dialog').close('confirm');
  assert.ok(team.textContent.includes('SOLICITADO LOCALMENTE'));
  assert.ok(team.textContent.includes('todas as lojas concedidas'));
  assert.ok(team.textContent.includes('NÃO aplicado'));
  assert.equal(env.descendants(team).filter(n=>n.tagName==='SELECT').length,0);
  get('team-dialog').close();
  env.openCase('Exemplo 02');
  assert.ok(get('detail-content').textContent.includes('em atendimento pelo operador'));
  assert.ok(get('thread-meta').textContent.includes('Caso A-102'));
});

test('G2: pedido local de retomada de Bianca mantém pausa confirmada na fixture',()=>{
  reset();env.selectActor('daniel');env.inbox[0].click();get('team-nav').click();
  const team=get('team-list'),button=env.descendants(team).find(n=>n.tagName==='BUTTON' &&
    n.textContent.includes('Solicitar retomada'));
  assert.ok(button);button.click();get('intake-dialog').close('confirm');
  assert.ok(team.textContent.includes('Novos leads pausados (projeção fictícia)'));
  assert.ok(team.textContent.includes('SOLICITADO LOCALMENTE'));
  assert.equal(env.descendants(team).filter(n=>n.tagName==='BUTTON').length,0);
  get('team-dialog').close();
  env.selectActor('rafael');env.inbox[0].click();env.selectActor('daniel');env.inbox[0].click();
  get('team-nav').click();
  assert.equal(get('team-list').textContent.includes('SOLICITADO LOCALMENTE'),false);
  get('team-dialog').close();
});

test('G3: Marina visualiza indicadores da própria equipe e etapas comerciais separadas',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  const dashboard=get('team-monitor');
  assert.ok(dashboard.textContent.includes('Monitoramento operacional da equipe'));
  assert.ok(dashboard.textContent.includes('Janela Meta expirada com etapa humana pendente'));
  assert.ok(dashboard.textContent.includes('fila protegida'));
  assert.ok(dashboard.textContent.includes('Etapas comerciais canônicas'));
  assert.ok(dashboard.textContent.includes('Rafael Lima'));
  assert.ok(dashboard.textContent.includes('Lia Martins'));
  assert.equal(dashboard.textContent.includes('Bianca Rocha'),false);
  assert.equal(dashboard.textContent.includes('Cliente Exemplo'),false);
  assert.equal(dashboard.textContent.includes('bank-demo-v1'),false);
  assert.ok(dashboard.textContent.includes('NÃO VERIFICADOS'));
  get('team-dialog').close();
});

test('G3: Daniel não enxerga indicadores nem operadores de Marina',()=>{
  reset();env.selectActor('daniel');env.inbox[0].click();get('team-nav').click();
  const dashboard=get('team-monitor');
  assert.ok(dashboard.textContent.includes('Bianca Rocha'));
  assert.ok(dashboard.textContent.includes('Otávio'));
  assert.equal(dashboard.textContent.includes('Rafael Lima'),false);
  assert.equal(dashboard.textContent.includes('Lia Martins'),false);
  assert.ok(dashboard.textContent.includes('Entrada de leads pausada: 1'));
  assert.ok(dashboard.textContent.includes('Conta indisponível: 1'));
  get('team-dialog').close();
});

test('G3: troca de filtro de loja não muda abrangência da equipe monitorada',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  const initial=get('team-monitor').textContent;
  get('team-dialog').close();
  env.selectShop('horizonte');env.inbox[0].click();get('team-nav').click();
  assert.equal(get('team-monitor').textContent,initial);
  get('team-dialog').close();
});

test('G3: pausa solicitada localmente não vira disponibilidade aplicada nos indicadores',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  const before=get('team-monitor').textContent;
  const pause=env.descendants(get('team-list')).find(x=>x.tagName==='BUTTON' &&
    x.textContent.includes('Solicitar pausa'));
  assert.ok(pause);pause.click();get('intake-dialog').close('confirm');
  assert.equal(get('team-monitor').textContent,before);
  assert.ok(get('team-list').textContent.includes('NÃO aplicado'));
  get('team-dialog').close();
});

test('G3: operador e perfil suspenso não abrem painel de indicadores',()=>{
  reset();
  get('team-nav').click();
  assert.equal(get('team-dialog').open,false);
  env.selectActor('otavio');env.inbox[0].click();get('team-nav').click();
  assert.equal(get('team-dialog').open,false);
  assert.equal(get('team-monitor').textContent,'');
});

test('G3: monitoramento de Marina não revela casos de Bianca ou de Daniel',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  get('team-show-monitor').click();
  assert.equal(get('team-list').hidden,true);
  assert.equal(get('team-monitor').hidden,false);
  assert.equal(get('team-show-monitor').attrs['aria-pressed'],'true');
  const text=get('team-monitor').textContent;
  for(const allowed of ['G3 · MONITORAMENTO','Rafael Lima','Lia Martins','Caso A-102','Caso A-112','Caso B-201','Fila protegida'])
    assert.ok(text.includes(allowed),'Esperado: '+allowed);
  for(const denied of ['Bianca Rocha','Otávio','Caso A-103','Caso B-203'])
    assert.equal(text.includes(denied),false);
  assert.ok(text.includes('Espera observada: 18 min (fictícia, não SLA).'));
  assert.ok(text.includes('Tempo de espera não informado'));
  get('team-show-members').click();
  assert.equal(get('team-monitor').hidden,true);
  assert.equal(get('team-list').hidden,false);
  get('team-dialog').close();
});

test('G3: Daniel só enxerga equipe própria, mesmo na mesma concessionária',()=>{
  reset();env.selectActor('daniel');env.inbox[0].click();get('team-nav').click();
  get('team-show-monitor').click();
  const text=get('team-monitor').textContent;
  assert.ok(text.includes('Bianca Rocha')&&text.includes('Otávio'));
  assert.ok(text.includes('Caso A-103')&&text.includes('Caso B-203'));
  for(const forbidden of ['Rafael Lima','Lia Martins','Caso A-102','Caso B-201','Caso A-112']){
    assert.equal(text.includes(forbidden),false);
  }
  get('team-dialog').close();
});

test('G3: pedido local de pausa não muda pausa confirmada nem estado comercial',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  const btn=env.descendants(get('team-list')).find(x=>x.tagName==='BUTTON' && x.textContent.includes('Solicitar pausa'));
  assert.ok(btn);btn.click();get('intake-dialog').close('confirm');
  get('team-show-monitor').click();
  const tiles=env.descendants(get('team-monitor')).filter(x=>x.classList.contains('team-monitor-metric'));
  const pending=tiles.find(x=>x.textContent.includes('Pedidos locais pendentes'));
  const paused=tiles.find(x=>x.textContent.includes('Novos leads pausados'));
  assert.ok(pending&&pending.textContent.startsWith('1'));
  assert.ok(paused&&paused.textContent.startsWith('0'));
  assert.ok(get('team-monitor').textContent.includes('Estado comercial preservado'));
  get('team-dialog').close();
});

test('G3: troca de perfil encerra monitoramento e apaga conteúdo do gestor anterior',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();get('team-show-monitor').click();
  assert.ok(get('team-monitor').textContent.includes('Rafael Lima'));
  env.selectActor('daniel');env.inbox[0].click();
  assert.equal(get('team-dialog').open,false);
  assert.equal(get('team-monitor').textContent,'');
  assert.equal(get('team-list').textContent,'');
  get('team-nav').click();get('team-show-monitor').click();
  assert.equal(get('team-monitor').textContent.includes('Rafael Lima'),false);
  assert.ok(get('team-monitor').textContent.includes('Bianca Rocha'));
  get('team-dialog').close();
});

test('G4: Marina vê seus lotes de Aurora/Horizonte sem herdar Daniel',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  get('team-show-batches').click();
  assert.equal(get('team-batches').hidden,false);
  assert.equal(get('team-monitor').hidden,true);
  assert.equal(get('team-list').hidden,true);
  const t=get('team-batches').textContent;
  assert.ok(t.includes('L-G4-01')&&t.includes('L-G4-02'));
  assert.equal(t.includes('L-G4-03'),false);
  assert.ok(t.includes('batch-demo-v1'));
  assert.ok(t.includes('Contagens não confirmadas'));
  assert.equal(env.descendants(get('team-batches')).filter(n=>n.tagName==='INPUT' || n.tagName==='SELECT').length,0);
  get('team-show-members').click();
  assert.equal(get('team-batches').hidden,true);
  get('team-dialog').close();
});

test('G4: Daniel vê somente seus lotes e a ausência de elegibilidade real',()=>{
  reset();env.selectActor('daniel');env.inbox[0].click();get('team-nav').click();
  get('team-show-batches').click();
  const t=get('team-batches').textContent;
  assert.ok(t.includes('L-G4-03')&&t.includes('L-G4-04'));
  assert.ok(t.includes('Distribuição bloqueada na fixture'));
  assert.equal(t.includes('L-G4-01'),false);
  assert.equal(t.includes('L-G4-02'),false);
  get('team-dialog').close();
});

test('G4: troca de perfil encerra lote anterior e retira dados da interface',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();get('team-show-batches').click();
  assert.ok(get('team-batches').textContent.includes('L-G4-01'));
  env.selectActor('daniel');env.inbox[0].click();
  assert.equal(get('team-batches').textContent,'');
  assert.equal(get('team-dialog').open,false);
  get('team-nav').click();get('team-show-batches').click();
  assert.equal(get('team-batches').textContent.includes('L-G4-01'),false);
  assert.ok(get('team-batches').textContent.includes('L-G4-03'));
  get('team-dialog').close();
});


test('FV-UI-017: nomes visíveis respeitam Consultor e Gestor sem alterar roles técnicas',()=>{
  reset();
  assert.match(get('actor-select').textContent,/Rafael Lima · Consultor da Prumo/);
  env.selectActor('marina');env.inbox[0].click();
  assert.match(get('actor-select').textContent,/Marina Costa · Gestor da Prumo/);
  get('team-nav').click();
  assert.match(get('team-list').textContent,/concedidas pelo Diretor/);
  get('team-dialog').close();
});

test('FV-UI-017: texto digitado não é enviado; prévia mostra autoria antes do aceite',()=>{
  reset();env.openCase('Exemplo 02');
  const before=get('thread-body').textContent;
  get('message-input').value='Mensagem de teste';
  get('composer').fire('submit');
  assert.equal(get('message-preview-dialog').open,true);
  assert.equal(get('message-preview-body').textContent,'Consultor Rafael Lima:\nMensagem de teste');
  assert.equal(get('thread-body').textContent,before);
  get('message-preview-dialog').close('cancel');
  assert.equal(get('message-input').value,'Mensagem de teste');
  assert.equal(get('thread-body').textContent,before);
  get('composer').fire('submit');
  get('message-preview-dialog').close('confirm');
  assert.match(get('thread-body').textContent,/Consultor Rafael Lima:\nMensagem de teste/);
  assert.match(get('thread-body').textContent,/NÃO ENVIADA/);
  assert.match(get('conversation-items').textContent,/Podemos conversar sobre as próximas etapas/);
  assert.doesNotMatch(get('conversation-items').textContent,/Mensagem fictícia preparada/);
  assert.equal(get('message-input').value,'');
  assert.ok(get('conversation-items').textContent.includes('Cliente Exemplo 02'));
});

test('FV-UI-017: Gestor titular tem autoria Gestor, sem conceder envio à supervisão',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();
  env.openCase('Exemplo 06');
  get('message-input').value='Contato do Gestor';
  get('composer').fire('submit');
  assert.equal(get('message-preview-dialog').open,true);
  assert.equal(get('message-preview-body').textContent,'Gestor Marina Costa:\nContato do Gestor');
  get('message-preview-dialog').close('confirm');
  assert.match(get('thread-body').textContent,/Gestor Marina Costa:\nContato do Gestor/);
  env.openCase('Exemplo 02');
  assert.equal(get('message-input').disabled,true);
  get('message-input').value='Texto indevido';
  get('composer').fire('submit');
  assert.equal(get('message-preview-dialog').open,false);
});

test('FV-UI-017: mudança de caso invalida prévia e apaga rascunho anterior',()=>{
  reset();env.openCase('Exemplo 02');
  get('message-input').value='Texto privado do caso 02';
  get('composer').fire('submit');
  assert.equal(get('message-preview-dialog').open,true);
  env.openCase('Exemplo 05');
  assert.equal(get('message-preview-dialog').open,false);
  assert.equal(get('message-preview-body').textContent,'');
  assert.equal(get('message-input').value,'');
  get('message-preview-dialog').close('confirm');
  assert.equal(get('thread-body').textContent.includes('Texto privado do caso 02'),false);
  env.openCase('Exemplo 02');
  assert.equal(get('thread-body').textContent.includes('Texto privado do caso 02'),false);
});

test('FV-UI-017: mudança de ator, loja e reset descartam rascunhos; confirmação velha falha',()=>{
  reset();env.openCase('Exemplo 02');
  get('message-input').value='Rascunho de Rafael';
  get('composer').fire('submit');
  env.selectActor('marina');env.inbox[0].click();
  assert.equal(get('message-input').value,'');
  get('message-preview-dialog').close('confirm');
  env.selectShop('horizonte');env.inbox[0].click();
  assert.equal(get('message-input').value,'');
  env.selectShop('aurora');env.inbox[0].click();
  env.openCase('Exemplo 06');
  get('message-input').value='Rascunho da loja Aurora';
  env.selectShop('horizonte');env.inbox[0].click();
  assert.equal(get('message-input').value,'');
  get('reset-app').click();
  assert.equal(get('message-input').value,'');
  assert.equal(get('thread-body').textContent.includes('Rascunho de Rafael'),false);
});

test('FV-UI-017: alteração durante prévia invalida confirmação antiga',()=>{
  reset();env.openCase('Exemplo 02');
  get('message-input').value='Texto inicial';
  get('composer').fire('submit');
  get('message-input').value='Texto alterado após prévia';
  get('message-preview-dialog').close('confirm');
  assert.equal(get('thread-body').textContent.includes('Texto alterado após prévia'),false);
  assert.equal(get('thread-body').textContent.includes('Texto inicial'),false);
});


test('FV-UI-018: Marina e Daniel enxergam fila compartilhada da loja, sem herdar carteira rival',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  get('team-show-queue').click();
  assert.equal(get('team-queue').hidden,false);
  assert.ok(get('team-queue').textContent.includes('FILA-A-01'));
  assert.equal(get('team-queue').textContent.includes('FILA-H-01'),false);
  get('team-dialog').close();
  env.selectActor('daniel');env.inbox[0].click();get('team-nav').click();get('team-show-queue').click();
  assert.ok(get('team-queue').textContent.includes('FILA-A-01'));
  assert.equal(env.cards().some(x=>x.textContent.includes('Exemplo 02')),false);
  get('team-dialog').close();
});

test('FV-UI-018: claim exige confirmação mas não reatribui nem concede case grant',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();get('team-show-queue').click();
  const buttons=env.descendants(get('team-queue')).filter(x=>x.tagName==='BUTTON');
  buttons.find(x=>x.textContent==='Solicitar assunção').click();
  assert.equal(get('queue-action-dialog').open,true);
  get('queue-action-dialog').close('cancel');
  assert.ok(get('team-queue').textContent.includes('Solicitar assunção'));
  buttons.find(x=>x.textContent==='Solicitar assunção').click();
  get('queue-action-dialog').close('confirm');
  assert.match(get('team-queue').textContent,/SOLICITADO LOCALMENTE · NÃO ATRIBUÍDO/);
  assert.equal(get('team-queue').textContent.includes('Solicitar assunção'),false);
  get('team-dialog').close();
});

test('FV-UI-018: atribuição só oferece equipe ativa e descarta intenção após troca de perfil',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();get('team-show-queue').click();
  const btn=env.descendants(get('team-queue')).find(x=>x.tagName==='BUTTON' &&
    x.textContent==='Solicitar atribuição à equipe');
  btn.click();
  assert.equal(get('queue-action-dialog').open,true);
  assert.match(get('queue-assignee').textContent,/Rafael Lima/);
  assert.equal(get('queue-assignee').textContent.includes('Bianca Rocha'),false);
  env.selectActor('daniel');env.inbox[0].click();
  assert.equal(get('queue-action-dialog').open,false);
  get('queue-action-dialog').close('confirm');
  get('team-nav').click();get('team-show-queue').click();
  assert.ok(get('team-queue').textContent.includes('Solicitar atribuição à equipe'));
  get('team-dialog').close();
});

test('FV-UI-018: caso Lia com exceção só abre A-117 em Aurora sem grant geral',()=>{
  reset();env.selectActor('lia');env.inbox[0].click();
  assert.ok(get('shop-select').textContent.includes('Aurora Motos · somente caso excepcional'));
  env.selectShop('aurora');env.inbox[0].click();
  assert.equal(env.cards().length,1);
  env.openCase('Exemplo 19');
  assert.equal(get('message-input').disabled,false);
  assert.ok(get('thread-meta').textContent.includes('A-117'));
  assert.match(get('workflow-bar').textContent,/Acesso excepcional: SOMENTE este caso/);
  assert.equal(env.cards().some(x=>x.textContent.includes('Exemplo 02')),false);
  env.selectShop('horizonte');env.inbox[0].click();
  assert.equal(get('thread-meta').textContent.includes('A-117'),false);
});


test('FV-UI-019: duas conclusões F03 fictícias têm recortes distintos, sem editor',()=>{
  reset();env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(x=>x.attrs.role==='tab')
    .find(x=>x.textContent==='Extração').click();
  const t=get('detail-content').textContent;
  assert.match(t,/concl-a108-1/);assert.match(t,/f03-a108-2/);
  assert.match(t,/a108-1/);assert.match(t,/a108-2/);
  assert.match(t,/v1-ficticia/);
  assert.equal(t.includes('Corrigir cadastro'),false);
  assert.equal(env.descendants(get('detail-content')).some(x=>x.tagName==='INPUT'),false);
});

test('FV-UI-019: esclarecimento alternativo libera segunda conclusão apenas na demo',()=>{
  reset();env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(x=>x.attrs.role==='tab')
    .find(x=>x.textContent==='Extração').click();
  assert.equal(get('message-input').disabled,true);
  const before=get('workflow-bar').textContent;
  const review=env.descendants(get('detail-content')).find(x=>x.id==='show-clarification-demo');
  assert.ok(review);review.click();
  assert.ok(get('workflow-bar').textContent.includes('CENÁRIO ALTERNATIVO'));
  assert.equal(get('message-input').disabled,false);
  assert.equal(buttons('Concluir atendimento').length,1);
  buttons('Concluir atendimento')[0].click();
  get('completion-dialog').close('confirm');
  const t=get('detail-content').textContent;
  assert.match(t,/local-review-A-108-review-a108-v3-demo/);
  assert.match(t,/corte apenas candidato/i);
  assert.match(t,/a108-3/);
  assert.match(t,/f03-a108-1/);
  assert.match(t,/f03-a108-2/);
  assert.match(t,/v1-ficticia/);
  assert.equal(get('message-input').disabled,true);
  assert.equal(buttons('Concluir atendimento').length,0);
  assert.equal(t.includes('ficha gravada agora'),false);
  assert.notEqual(before,get('workflow-bar').textContent);
});

test('FV-UI-019: Gestor supervisor não recebe histórico de F03 nem versão de cliente',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(x=>x.attrs.role==='tab')
    .find(x=>x.textContent==='Extração').click();
  const t=get('detail-content').textContent;
  assert.equal(t.includes('f03-a108-1'),false);
  assert.equal(t.includes('client09-aurora-only'),false);
  assert.equal(t.includes('show-clarification-demo'),false);
  assert.equal(env.descendants(get('detail-content')).some(x=>x.id==='show-clarification-demo'),false);
});

test('FV-UI-019: versões da ficha viva não modificam remessa antiga',()=>{
  reset();env.openCase('Exemplo 15');
  env.descendants(get('detail-content')).filter(x=>x.attrs.role==='tab')
    .find(x=>x.textContent==='Extração').click();
  const t=get('detail-content').textContent;
  assert.match(t,/live-form-v2-demo/);
  assert.match(t,/bank-demo-v1/);
  assert.match(t,/snapshot preservado/);
});

test('FV-UI-019: troca de perfil limpa cenário alternativo e não migra autorização',()=>{
  reset();env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(x=>x.attrs.role==='tab')
    .find(x=>x.textContent==='Extração').click();
  env.descendants(get('detail-content')).find(x=>x.id==='show-clarification-demo').click();
  assert.equal(get('message-input').disabled,false);
  env.selectActor('marina');env.inbox[0].click();
  env.selectActor('rafael');env.inbox[0].click();env.openCase('Exemplo 09');
  assert.equal(get('message-input').disabled,true);
  assert.equal(get('workflow-bar').textContent.includes('CENÁRIO ALTERNATIVO'),false);
});


test('FV-UI-020: ACK da API não aparece como envio comprovado',()=>{
  reset();env.openCase('Exemplo 02');
  const t=get('thread-body').textContent;
  assert.match(t,/API aceitou · envio NÃO comprovado/);
  assert.match(t,/Sem prova de envio/);
  assert.equal(t.includes('Entrega comprovada'),false);
  assert.equal(t.includes('Envio comprovado · fixture'),false);
});

test('FV-UI-020: recibo de envio provado difere de estado comercial bancário',()=>{
  reset();env.openCase('Exemplo 05');
  const t=get('thread-body').textContent;
  assert.match(t,/Envio comprovado · fixture/);
  assert.match(get('detail-content').textContent,/cadastro enviado ao banco/);
  assert.equal(t.includes('Entrega comprovada'),false);
});

test('FV-UI-020: mensagem incerta não zera pendência de resposta do Gestor titular',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();env.openCase('Exemplo 06');
  assert.match(get('thread-body').textContent,/Resultado incerto/);
  assert.match(get('thread-body').textContent,/Não tentar reenvio automático/);
  assert.ok(env.cards().find(x=>x.textContent.includes('Exemplo 06')).textContent.length>0);
  const notice=env.descendants(env.cards().find(x=>x.textContent.includes('Exemplo 06')))
    .find(x=>x.classList.contains('attention-pending'));
  assert.ok(notice);
});

test('FV-UI-020: supervisor não vê detalhes de transporte do Consultor titular',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();env.openCase('Exemplo 02');
  assert.equal(get('thread-body').textContent.includes('API aceitou · envio NÃO comprovado'),false);
});

test('FV-UI-020: falha F03 fictícia não oferece retentativa automática nem editor',()=>{
  reset();env.openCase('Exemplo 02');buttons('Concluir atendimento')[0].click();
  get('completion-dialog').close('confirm');
  const fail=env.descendants(get('detail-content')).find(x=>x.tagName==='BUTTON' && x.textContent==='Falha técnica');
  assert.ok(fail);fail.click();
  const t=get('detail-content').textContent;
  assert.match(t,/não há correção manual ou retentativa automática/i);
  assert.equal(t.includes('Corrigir dado'),false);
});

test('FV-UI-021: contexto anunciado muda com perfil, loja e caso sem resíduo anterior',()=>{
  reset();
  assert.match(get('context-announcement').textContent,/Consultor fictício/);
  env.openCase('Exemplo 02');
  assert.match(get('context-announcement').textContent,/Caso A-102 aberto/);
  env.selectActor('marina');env.inbox[0].click();
  assert.match(get('context-announcement').textContent,/Gestor fictício/);
  assert.equal(get('context-announcement').textContent.includes('A-102'),false);
  env.selectShop('horizonte');env.inbox[0].click();
  assert.match(get('context-announcement').textContent,/Concessionária Horizonte/);
  assert.equal(get('context-announcement').textContent.includes('Aurora'),false);
  env.inbox[1].click();
  assert.match(get('context-announcement').textContent,/Histórico/);
});

test('FV-UI-021: Home e End alcançam extremos das abas sem perder roving tabindex',()=>{
  reset();env.openCase('Exemplo 02');get('detail-toggle').click();
  const tabs=()=>env.descendants(get('detail-content')).filter(x=>x.attrs.role==='tab');
  const first=tabs()[0],last=tabs().at(-1);
  first.fire('keydown',{key:'End'});
  let selected=tabs().find(x=>x.attrs['aria-selected']==='true');
  assert.equal(selected.textContent,last.textContent);
  assert.equal(selected.attrs.tabindex,'0');
  assert.equal(env.document.activeElement,selected);
  selected.fire('keydown',{key:'Home'});
  selected=tabs().find(x=>x.attrs['aria-selected']==='true');
  assert.equal(selected.textContent,first.textContent);
  assert.equal(selected.attrs.tabindex,'0');
  assert.equal(env.document.activeElement,selected);
  assert.equal(tabs().filter(x=>x.attrs.tabindex==='0').length,1);
});


test('FV-UI-022: cancelar prévia conserva texto e devolve foco somente no mesmo contexto',()=>{
  reset();env.openCase('Exemplo 02');
  get('message-input').value='Não enviar ainda';
  get('composer').fire('submit');
  assert.equal(get('message-preview-dialog').open,true);
  get('message-preview-dialog').close('cancel');
  assert.equal(get('message-input').value,'Não enviar ainda');
  assert.equal(env.document.activeElement,get('message-input'));
  assert.equal(get('thread-body').textContent.includes('Não enviar ainda'),false);
});

test('FV-UI-022: prévia antiga fechada após trocar ator não rouba foco de outra sessão',()=>{
  reset();env.openCase('Exemplo 02');
  get('message-input').value='Mensagem para Rafael';
  get('composer').fire('submit');
  assert.equal(get('message-preview-dialog').open,true);
  env.selectActor('marina');env.inbox[0].click();
  get('search-input').focus();
  get('message-preview-dialog').close('cancel');
  assert.equal(env.document.activeElement,get('search-input'));
  assert.equal(get('message-input').value,'');
  assert.equal(get('thread-body').textContent.includes('Mensagem para Rafael'),false);
});


test('FV-UI-029: confirmar pausa repõe foco em aba persistente da equipe',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  const buttons=env.descendants(get('team-list')).filter(n=>n.tagName==='BUTTON' && n.textContent.includes('Solicitar pausa'));
  assert.ok(buttons.length);buttons[0].click();
  assert.equal(get('intake-dialog').open,true);
  get('intake-dialog').close('confirm');
  assert.equal(env.document.activeElement,get('team-show-members'));
  assert.match(get('team-action-announcement').textContent,/não aplicada no S0\/S1/i);
  assert.equal(get('team-dialog').open,true);
  get('team-dialog').close();
});

test('FV-UI-029: confirmar fila repõe foco sem simular atribuição efetiva',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();get('team-show-queue').click();
  const actions=env.descendants(get('team-queue')).filter(n=>n.tagName==='BUTTON' && n.textContent.includes('Solicitar assunção'));
  assert.ok(actions.length);actions[0].click();
  assert.equal(get('queue-action-dialog').open,true);
  get('queue-action-dialog').close('confirm');
  assert.equal(env.document.activeElement,get('team-show-queue'));
  assert.match(get('team-action-announcement').textContent,/Nenhuma atribuição ou permissão aplicada/);
  assert.equal(get('team-dialog').open,true);
  get('team-dialog').close();
});


test('FV-UI-031: nota local recria formulário e retorna foco ao campo vazio',()=>{
  reset();env.openCase('Exemplo 02');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Notas').click();
  const form=env.descendants(get('detail-content')).find(n=>n.id==='internal-note-form');
  const original=env.descendants(form).find(n=>n.id==='note-text');
  original.value='Nota de acessibilidade somente local';original.focus();
  form.fire('submit');
  const renewed=env.descendants(get('detail-content')).find(n=>n.id==='note-text');
  assert.ok(renewed);
  assert.notEqual(renewed,original,'o formulário deve ter sido recriado');
  assert.equal(env.document.activeElement,renewed,'foco deve permanecer no contexto da nota');
  assert.equal(renewed.value,'');
  assert.match(get('detail-content').textContent,/Nota de acessibilidade somente local/);
  assert.match(get('toast').textContent,/somente à memória do navegador/);
});

test('FV-UI-031: callback obsoleto não reorienta foco nem registra nota em outro caso',()=>{
  reset();env.openCase('Exemplo 02');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Notas').click();
  const form=env.descendants(get('detail-content')).find(n=>n.id==='internal-note-form');
  env.descendants(form).find(n=>n.id==='note-text').value='Texto obsoleto 031';
  env.openCase('Exemplo 05');
  get('search-input').focus();
  form.fire('submit');
  assert.equal(env.document.activeElement,get('search-input'));
  assert.equal(get('detail-content').textContent.includes('Texto obsoleto 031'),false);
});

test('FV-UI-032: resultado técnico fictício restaura foco da aba Extração',()=>{
  reset();env.openCase('Exemplo 02');
  buttons('Concluir atendimento')[0].click();get('completion-dialog').close('confirm');
  const action=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' && n.textContent==='Retorno parcial');
  assert.ok(action);action.focus();action.click();
  const tab=env.descendants(get('detail-content')).find(n=>n.id==='case-tab-extraction');
  assert.equal(env.document.activeElement,tab);
  assert.match(get('context-announcement').textContent,/Resultado técnico fictício Retorno parcial/);
  assert.match(get('detail-content').textContent,/Campo ilustrativo A/);
  const failure=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' && n.textContent==='Falha técnica');
  assert.ok(failure);failure.click();
  assert.equal(env.document.activeElement,env.descendants(get('detail-content')).find(n=>n.id==='case-tab-extraction'));
  assert.match(get('context-announcement').textContent,/Resultado técnico fictício Falha técnica/);
});

test('FV-UI-032: esclarecimento recriado ancora o foco sem afirmar F03',()=>{
  reset();env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab').find(n=>n.textContent==='Extração').click();
  const button=env.descendants(get('detail-content')).find(n=>n.id==='show-clarification-demo');
  assert.ok(button);button.focus();button.click();
  assert.equal(env.document.activeElement,env.descendants(get('detail-content')).find(n=>n.id==='case-tab-extraction'));
  assert.match(get('context-announcement').textContent,/Cenário de esclarecimento fictício do caso A-108/);
  assert.equal(env.descendants(get('detail-content')).some(n=>n.id==='show-clarification-demo'),false);
  assert.match(get('detail-content').textContent,/nenhuma IA foi acionada/);
});

test('FV-UI-032: O5 desktop foca região do novo caso autorizado',()=>{
  reset();env.openCase('Exemplo 05');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab').find(n=>n.textContent==='Novo contato').click();
  const btn=env.descendants(get('detail-content')).find(n=>n.tagName==='BUTTON' && n.textContent.includes('Abrir novo atendimento humano'));
  assert.ok(btn);btn.click();
  assert.equal(env.document.activeElement,get('thread-pane'));
  assert.match(get('thread-meta').textContent,/Caso A-114/);
  assert.match(get('context-announcement').textContent,/Caso A-114 aberto por vínculo fictício autorizado/);
  assert.match(get('detail-content').textContent,/em atendimento pelo operador/);
});


test('FV-UI-037: segue mudança de tema do SO apenas antes da seleção manual', () => {
  reset();env.setSystemDark(true);
  assert.equal(get('visual-app').dataset.theme,'dark');
  assert.equal(get('theme-dark').getAttribute('aria-pressed'),'true');
  env.setSystemDark(false);
  assert.equal(get('visual-app').dataset.theme,'light');
  get('theme-light').click();env.setSystemDark(true);
  assert.equal(get('visual-app').dataset.theme,'light');
  assert.equal(get('theme-light').getAttribute('aria-pressed'),'true');
  assert.equal(env.cards().length,8);
});

test('FV-UI-036: tema claro/escuro alterna sem perder o caso selecionado', () => {
  reset();
  assert.equal(get('visual-app').dataset.theme, 'light');
  get('theme-dark').click();
  assert.equal(get('visual-app').dataset.theme, 'dark');
  assert.equal(get('theme-dark').getAttribute('aria-pressed'), 'true');
  assert.equal(get('theme-light').getAttribute('aria-pressed'), 'false');
  env.openCase('Exemplo 02');
  get('theme-light').click();
  assert.equal(get('visual-app').dataset.theme, 'light');
  assert.equal(get('theme-light').getAttribute('aria-pressed'), 'true');
  assert.match(get('thread-title').textContent, /Cliente Exemplo 02/);
});

test('FV-UI-054: limpeza mantém contexto, aba, foco e reabre resultados',()=>{
  reset();
  const actor=get('actor-select').value,shop=get('shop-select').value;
  assert.equal(get('filter-reset-controls').hidden,true);
  get('search-input').value='fv-ui-054-sem-caso';
  get('search-input').fire('input');
  assert.equal(get('filter-reset-controls').hidden,true);
  assert.equal(env.descendants(get('conversation-items')).filter(n=>n.classList.contains('empty-reset')).length,1);
  env.filters[1].click();
  get('status-filter').value='em atendimento pelo operador';
  get('status-filter').fire('change');
  assert.equal(env.cards().length,0);
  assert.equal(get('filter-reset-controls').hidden,true);
  const emptyAction=env.descendants(get('conversation-items')).find(n=>n.classList.contains('empty-reset'));
  assert.ok(emptyAction);
  emptyAction.click();
  assert.equal(get('search-input').value,'');
  assert.equal(get('status-filter').value,'all');
  assert.equal(env.filters[0].getAttribute('aria-pressed'),'true');
  assert.equal(get('filter-reset-controls').hidden,true);
  assert.equal(get('actor-select').value,actor);
  assert.equal(get('shop-select').value,shop);
  assert.equal(env.inbox[0].getAttribute('aria-pressed'),'true');
  assert.equal(env.document.activeElement,get('search-input'));
  assert.equal(env.cards().length,8);
  env.inbox[1].click();
  get('search-input').value='fv-ui-054-historico-sem-caso';
  get('search-input').fire('input');
  assert.equal(get('filter-reset-controls').hidden,true);
  const historyEmptyAction=env.descendants(get('conversation-items')).find(n=>n.classList.contains('empty-reset'));
  assert.ok(historyEmptyAction);
  historyEmptyAction.click();
  assert.equal(env.inbox[1].getAttribute('aria-pressed'),'true');
  assert.equal(env.cards().length,3);
});

test('FV-UI-055: uma só ação de limpeza com e sem resultados',()=>{
  reset();
  const actor=get('actor-select').value,shop=get('shop-select').value;
  get('search-input').value='Cliente Exemplo';
  get('search-input').fire('input');
  assert.ok(env.cards().length>0);
  assert.equal(get('filter-reset-controls').hidden,false);
  assert.equal(env.descendants(get('conversation-items')).filter(n=>n.classList.contains('empty-reset')).length,0);
  get('clear-list-filters').click();
  assert.equal(get('filter-reset-controls').hidden,true);
  get('search-input').value='FV-UI-055-resultado-inexistente-xyzz';
  get('search-input').fire('input');
  assert.equal(env.cards().length,0);
  assert.equal(get('filter-reset-controls').hidden,true);
  const empties=env.descendants(get('conversation-items')).filter(n=>n.classList.contains('empty-reset'));
  assert.equal(empties.length,1);
  empties[0].click();
  assert.equal(get('filter-reset-controls').hidden,true);
  assert.equal(env.cards().length,8);
  assert.equal(env.document.activeElement,get('search-input'));
  assert.equal(get('actor-select').value,actor);
  assert.equal(get('shop-select').value,shop);
  assert.equal(env.inbox[0].getAttribute('aria-pressed'),'true');
});

test('FV-UI-056: interface respeita busca normalizada sem trocar identidade ou contexto',()=>{
  reset();
  const actor=get('actor-select').value,shop=get('shop-select').value;
  get('search-input').value='  CLIENTE    EXÉMPLO    02  ';
  get('search-input').fire('input');
  assert.deepEqual(env.cards().map(n=>n.getAttribute('aria-label')).filter(x=>x.includes('Exemplo 02')).length,1);
  assert.equal(get('filter-reset-controls').hidden,false);
  get('search-input').value='  CÁDASTRO    ENVIADO AO  BANCO ';
  get('search-input').fire('input');
  assert.equal(env.cards().length,1);
  assert.match(env.cards()[0].getAttribute('aria-label'),/Cliente Exemplo 05/);
  assert.equal(get('actor-select').value,actor);
  assert.equal(get('shop-select').value,shop);
  assert.equal(env.inbox[0].getAttribute('aria-pressed'),'true');
  get('clear-list-filters').click();
  assert.equal(get('search-input').value,'');
  assert.equal(env.cards().length,8);
  assert.equal(env.document.activeElement,get('search-input'));
});

test('FV-UI-057: Esc limpa apenas texto de busca e preserva filtros e contexto',()=>{
  reset();
  const actor=get('actor-select').value,shop=get('shop-select').value;
  env.filters[1].click();
  const unreadCount=env.cards().length;
  assert.ok(unreadCount>0 && unreadCount<8);
  const input=get('search-input');
  input.value='FV-UI-057-nenhum-resultado';
  input.fire('input');input.focus();
  assert.equal(env.cards().length,0);
  assert.equal(get('filter-reset-controls').hidden,true);
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(input.value,'');
  assert.equal(env.cards().length,unreadCount);
  assert.equal(env.filters[1].getAttribute('aria-pressed'),'true');
  assert.equal(env.inbox[0].getAttribute('aria-pressed'),'true');
  assert.equal(get('filter-reset-controls').hidden,false);
  assert.equal(get('actor-select').value,actor);
  assert.equal(get('shop-select').value,shop);
  assert.equal(env.document.activeElement,input);
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(env.filters[1].getAttribute('aria-pressed'),'true');
  assert.equal(env.cards().length,unreadCount);
  get('clear-list-filters').click();
  assert.equal(env.cards().length,8);
});

test('FV-UI-057: Escape não rouba contexto de diálogo modal aberto',()=>{
  reset();env.openCase('Exemplo 08');
  buttons('Enviar template')[0].click();
  assert.equal(get('template-dialog').open,true);
  const input=get('search-input');
  input.value='Cliente Exemplo 02';input.fire('input');input.focus();
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(input.value,'Cliente Exemplo 02');
  assert.equal(get('template-dialog').open,true);
  get('template-dialog').close('cancel');
  env.document.fire('keydown',{key:'Escape'});
  assert.equal(input.value,'');
});

test('FV-UI-058: seta para baixo transfere foco sem abrir atendimento',()=>{
  reset();
  const input=get('search-input'), actor=get('actor-select').value, shop=get('shop-select').value;
  assert.equal(get('thread-title').textContent,'Selecione uma conversa');
  input.value='Cliente Exemplo 05';input.fire('input');input.focus();
  assert.equal(env.cards().length,1);
  const first=env.cards()[0];
  env.document.fire('keydown',{key:'ArrowDown'});
  assert.equal(env.document.activeElement,first);
  assert.equal(first.getAttribute('aria-pressed'),'false');
  assert.equal(get('thread-title').textContent,'Selecione uma conversa');
  assert.equal(get('actor-select').value,actor);
  assert.equal(get('shop-select').value,shop);
  assert.equal(input.value,'Cliente Exemplo 05');
});

test('FV-UI-058: zero resultados, modificadores, IME ou modal conservam foco',()=>{
  reset();
  const input=get('search-input');
  input.value='FV-UI-058-sem-resultados';input.fire('input');input.focus();
  assert.equal(env.cards().length,0);
  env.document.fire('keydown',{key:'ArrowDown'});
  assert.equal(env.document.activeElement,input);
  input.value='Cliente Exemplo';input.fire('input');
  assert.ok(env.cards().length>0);
  for(const more of [{ctrlKey:true},{metaKey:true},{altKey:true},{isComposing:true}]){
    env.document.fire('keydown',{key:'ArrowDown',...more});
    assert.equal(env.document.activeElement,input);
  }
  input.value='Cliente Exemplo 08';input.fire('input');
  env.openCase('Exemplo 08');
  buttons('Enviar template')[0].click();
  input.focus();
  env.document.fire('keydown',{key:'ArrowDown'});
  assert.equal(env.document.activeElement,input);
  assert.equal(get('template-dialog').open,true);
  get('template-dialog').close('cancel');
});

test('FVA-01: O2 O3 em sequência não migram rascunho, F03 ou autorização entre perfis',()=>{
  reset();
  env.openCase('Exemplo 02');
  get('message-input').value='FVA-01 rascunho local confidencial';
  const originalActor=get('actor-select').value;
  assert.equal(originalActor,'rafael');
  env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Extração').click();
  assert.match(get('detail-content').textContent,/f03-a108-1/);
  env.selectActor('marina');env.inbox[0].click();
  assert.equal(get('message-input').value,'');
  assert.equal(get('thread-body').textContent.includes('FVA-01 rascunho'),false);
  env.openCase('Exemplo 09');
  env.descendants(get('detail-content')).filter(n=>n.attrs.role==='tab')
    .find(n=>n.textContent==='Extração').click();
  assert.equal(get('detail-content').textContent.includes('f03-a108-1'),false);
  assert.equal(get('message-input').disabled,true);
  env.selectActor('daniel');env.inbox[0].click();
  assert.equal(env.cards().some(n=>n.textContent.includes('Exemplo 09')),false);
  assert.equal(get('thread-body').textContent.includes('FVA-01 rascunho'),false);
  env.selectActor('otavio');env.inbox[0].click();
  assert.equal(env.cards().length,0);
  assert.equal(get('team-nav').hidden,true);
  assert.equal(get('message-input').disabled,true);
  assert.equal(get('detail-content').textContent.includes('f03-a108-1'),false);
  env.selectActor('rafael');env.inbox[0].click();
  env.openCase('Exemplo 02');
  assert.equal(get('message-input').value,'');
  assert.equal(get('thread-body').textContent.includes('FVA-01 rascunho'),false);
});

test('FVA-01: G2 fila compartilhada nao transforma pedido local em atribuição de outro Gestor',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();get('team-show-queue').click();
  assert.match(get('team-queue').textContent,/FILA-A-01/);
  const request=env.descendants(get('team-queue')).find(n=>
    n.tagName==='BUTTON' && n.textContent==='Solicitar assunção');
  assert.ok(request);request.click();
  assert.equal(get('queue-action-dialog').open,true);
  get('queue-action-dialog').close('confirm');
  assert.match(get('team-queue').textContent,/SOLICITADO LOCALMENTE · NÃO ATRIBUÍDO/);
  get('team-dialog').close();
  env.selectActor('daniel');env.inbox[0].click();
  get('team-nav').click();get('team-show-queue').click();
  assert.match(get('team-queue').textContent,/FILA-A-01/);
  assert.equal(get('team-queue').textContent.includes('SOLICITADO LOCALMENTE'),false);
  assert.ok(env.descendants(get('team-queue')).some(n=>
    n.tagName==='BUTTON' && n.textContent==='Solicitar assunção'));
  get('team-dialog').close();
  env.selectActor('marina');env.inbox[0].click();
  get('team-nav').click();get('team-show-queue').click();
  assert.equal(get('team-queue').textContent.includes('SOLICITADO LOCALMENTE'),false);
  assert.match(get('team-queue').textContent,/FILA-A-01/);
  get('team-dialog').close();
});

test('FVA-01: exceção por caso não vira concessão geral nem sobrevive a troca de identidade',()=>{
  reset();env.selectActor('lia');env.inbox[0].click();
  assert.ok(get('shop-select').textContent.includes('somente caso excepcional'));
  env.selectShop('aurora');env.inbox[0].click();
  assert.equal(env.cards().length,1);
  env.openCase('Exemplo 19');
  assert.match(get('thread-meta').textContent,/A-117/);
  assert.match(get('workflow-bar').textContent,/Acesso excepcional: SOMENTE este caso/);
  assert.equal(env.cards().some(n=>n.textContent.includes('Exemplo 02')),false);
  env.selectActor('daniel');env.inbox[0].click();
  assert.equal(env.cards().some(n=>n.textContent.includes('Exemplo 19')),false);
  assert.equal(get('thread-meta').textContent.includes('A-117'),false);
  env.selectActor('rafael');env.inbox[0].click();
  assert.equal(env.cards().some(n=>n.textContent.includes('Exemplo 19')),false);
  env.selectActor('lia');env.inbox[0].click();
  env.selectShop('aurora');env.inbox[0].click();
  assert.equal(env.cards().length,1);
  assert.match(env.cards()[0].textContent,/Exemplo 19/);
  assert.equal(get('message-input').value,'');
});

test('FVA-02: template local não atravessa identidade fictícia ou confirmação obsoleta',()=>{
  reset();env.openCase('Exemplo 08');
  const before=get('workflow-bar').textContent;
  buttons('Enviar template')[0].click();
  assert.equal(get('template-dialog').open,true);
  env.selectActor('daniel');env.inbox[0].click();
  assert.equal(get('template-dialog').open,false);
  get('template-dialog').close('confirm'); // callback antigo não ressuscita solicitação
  env.selectActor('rafael');env.inbox[0].click();env.openCase('Exemplo 08');
  assert.equal(get('workflow-bar').textContent,before);
  assert.ok(buttons('Enviar template').length>0);
  buttons('Enviar template')[0].click();
  get('template-dialog').close('confirm');
  assert.match(get('detail-content').textContent,/SOLICITADO/);
  assert.equal(get('detail-content').textContent.includes('Envio comprovado · fixture'),false);
  assert.match(get('detail-content').textContent,/SOLICITADO \(demo\), não agendado, não transmitido e nunca ENVIADO/);
  env.selectActor('marina');env.inbox[0].click();env.selectActor('rafael');env.inbox[0].click();
  env.openCase('Exemplo 08');
  assert.equal(get('workflow-bar').textContent,before);
  assert.ok(buttons('Enviar template').length>0);
  assert.equal(get('detail-content').textContent.includes('SOLICITADO (demo)'),false);
});

test('FVA-02: troca de concessionária limpa intenção local da fila e preserva escopo',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();get('team-show-queue').click();
  const first=env.descendants(get('team-queue')).find(n=>
    n.tagName==='BUTTON' && n.textContent==='Solicitar assunção');
  assert.ok(first);first.click();get('queue-action-dialog').close('confirm');
  assert.match(get('team-queue').textContent,/FILA-A-01/);
  assert.match(get('team-queue').textContent,/SOLICITADO LOCALMENTE/);
  get('team-dialog').close();
  env.selectShop('horizonte');env.inbox[0].click();
  get('team-nav').click();get('team-show-queue').click();
  assert.match(get('team-queue').textContent,/FILA-H-01/);
  assert.equal(get('team-queue').textContent.includes('FILA-A-01'),false);
  assert.equal(get('team-queue').textContent.includes('SOLICITADO LOCALMENTE'),false);
  get('team-dialog').close();
  env.selectShop('aurora');env.inbox[0].click();get('team-nav').click();get('team-show-queue').click();
  assert.match(get('team-queue').textContent,/FILA-A-01/);
  assert.equal(get('team-queue').textContent.includes('SOLICITADO LOCALMENTE'),false);
  assert.ok(env.descendants(get('team-queue')).some(n=>
    n.tagName==='BUTTON' && n.textContent==='Solicitar assunção'));
  get('team-dialog').close();
});

test('FVA-02: F03 erro, versão obsoleta, incerteza e indisponibilidade nunca aplicam efeitos',()=>{
  reset();env.openCase('Exemplo 02');
  const status=get('workflow-bar').textContent;
  buttons('Concluir atendimento')[0].click();get('completion-dialog').close('confirm');
  for(const [label,needle] of [
    ['Versão obsoleta','Versão incompatível simulada'],
    ['Confirmação incerta','Confirmação externa incerta'],
    ['Permissão negada','Operação negada'],
    ['Serviço indisponível','Serviço indisponível']
  ]){
    const control=env.descendants(get('detail-content')).find(n=>
      n.tagName==='BUTTON' && n.textContent===label);
    assert.ok(control,label+' ausente');control.click();
    const text=get('detail-content').textContent;
    assert.ok(text.includes(needle),label+' não sinalizado');
    assert.match(text,/não há correção manual ou retentativa automática/i);
    assert.equal(text.includes('Ficha gravada'),false);
    assert.equal(text.includes('Corrigir cadastro'),false);
  }
  assert.match(get('detail-content').textContent,/em atendimento pelo operador/);
  assert.equal(get('detail-content').textContent.includes('cadastro enviado ao banco'),false);
  const obsolete=env.descendants(get('detail-content')).find(n=>
    n.tagName==='BUTTON' && n.textContent==='Falha técnica');
  env.openCase('Exemplo 05');
  const bankBefore=get('workflow-bar').textContent;
  assert.ok(obsolete);obsolete.click(); // ação do caso anterior fora de contexto
  assert.equal(get('workflow-bar').textContent,bankBefore);
  assert.match(get('detail-content').textContent,/cadastro enviado ao banco/);
  assert.equal(status.includes('cadastro enviado ao banco'),false);
});

test('FVA-02: pausa modal obsoleta não se torna aplicada por outro Gestor',()=>{
  reset();env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  const pause=env.descendants(get('team-list')).find(n=>
    n.tagName==='BUTTON' && n.textContent.includes('Solicitar pausa'));
  assert.ok(pause);pause.click();
  assert.equal(get('intake-dialog').open,true);
  env.selectActor('daniel');env.inbox[0].click();
  assert.equal(get('intake-dialog').open,false);
  get('intake-dialog').close('confirm');
  get('team-nav').click();
  assert.equal(get('team-list').textContent.includes('SOLICITADO LOCALMENTE'),false);
  get('team-dialog').close();
  env.selectActor('marina');env.inbox[0].click();get('team-nav').click();
  assert.equal(get('team-list').textContent.includes('SOLICITADO LOCALMENTE'),false);
  const restart=env.descendants(get('team-list')).find(n=>
    n.tagName==='BUTTON' && n.textContent.includes('Solicitar pausa'));
  restart.click();get('intake-dialog').close('confirm');
  assert.match(get('team-list').textContent,/SOLICITADO LOCALMENTE/);
  assert.match(get('team-list').textContent,/NÃO aplicado/);
  get('team-show-monitor').click();
  const monitor=get('team-monitor').textContent;
  assert.match(monitor,/Pedidos locais pendentes/);
  assert.match(monitor,/Novos leads pausados/);
  get('team-dialog').close();
});
