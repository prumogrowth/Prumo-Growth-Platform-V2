/** FV-UI-001. Navegação e demonstração em memória; NÃO é frontend autenticado.
 * Não chamar backend, OpenAI, Meta, Banco, storage ou permitir efeito comercial.
 */
import {
  ACTORS, COMMERCIAL_STATUSES, getActor, getShop, visibleConversations,
  canSimulateCompletion, statusTone
} from './fixtures.mjs';
import {
  DETAIL_TABS, projectQueue, summaryOf, canWriteNote, canSeeTeamSummary,
  activityFor, modelExtraction
} from './view-model.mjs';
import {
  DEMO_TEMPLATES, copyCFDemoFixtures, isInActiveInbox, projectedMetaWindow,
  humanCompletion, mayMockFreeText, projectedFollowupActions, projectInbox,
  projectedFollowupState, applyLocalFollowupRequest, isSyntheticBankProtected
} from './cf-op-02.mjs';

const $ = id => document.getElementById(id);
const app = $('visual-app');
const list = $('conversation-items');
const state = {
  actorId: 'rafael', shopId: 'aurora', filter: 'all', statusFilter: 'all', detailTab: 'overview', query: '',
  selectedId: 'A-102', cases: copyCFDemoFixtures(), processing: {}, followupRequests: {}, inboxView: 'active',
  mobileView: 'list', dialogContext: { completion: null, template: null }
};

function el(tag, className='', text=null) {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (text !== null) n.textContent = String(text);
  return n;
}
function ico(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'icon small'); svg.setAttribute('aria-hidden','true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', '#i-' + name); svg.append(use); return svg;
}
function selectedCase() { return accessible().find(x => x.id === state.selectedId) ?? null; }
function accessible() { return visibleConversations(state.cases, state.actorId, state.shopId); }
function filtered() {
  return projectQueue(state.cases, state.actorId, state.shopId, {
    query: state.query, filter: state.filter, status: state.statusFilter
  }).filter(record => state.inboxView === 'history' ? record.inboxProjection === 'historical' : isInActiveInbox(record));
}

function canMockMessage(record) {
  return mayMockFreeText(record,state.actorId,state.shopId,Boolean(state.processing[record?.id]));
}
function canMockClose(record) {
  return canSimulateCompletion(record,state.actorId,state.shopId) &&
    isInActiveInbox(record) && humanCompletion(record) === 'pending' &&
    record?.allowedActionsProjection?.includes('complete') &&
    !state.processing[record.id] && !state.followupRequests[record.id];
}

function captureDialogContext(kind) {
  state.dialogContext[kind] = {
    actorId: state.actorId, shopId: state.shopId, caseId: state.selectedId
  };
}
function consumeDialogContext(kind) {
  const saved = state.dialogContext[kind];
  state.dialogContext[kind] = null;
  return Boolean(saved && saved.actorId === state.actorId &&
    saved.shopId === state.shopId && saved.caseId === state.selectedId);
}
function closeTransientDialogs() {
  for (const [kind,id] of [['completion','completion-dialog'],['template','template-dialog']]) {
    state.dialogContext[kind] = null;
    const dialog = $(id);
    dialog.returnValue = '';
    if (dialog.open) dialog.close();
  }
}
function showToast(message) {
  const node = $('toast'); node.textContent = message; node.hidden = false;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { node.hidden = true; }, 3700);
}
function goto(view) {
  state.mobileView = view;
  app.dataset.mobileView = view;
  if (view === 'thread') $('message-input').blur();
}
function updateSelectors() {
  const actor = getActor(state.actorId);
  const actorSelect = $('actor-select');
  actorSelect.replaceChildren(...ACTORS.map(a => {
    const o = el('option', '', `${a.name} · ${a.role === 'gestor' ? 'Gestor' : 'Operador'} da Prumo`);
    o.value = a.id; return o;
  }));
  actorSelect.value = state.actorId;
  const showTeam=actor.role==='gestor' && actor.teamState==='active';
  $('team-nav-mobile').hidden=!showTeam;
  $('team-nav').hidden=!showTeam;
  const shopSelect = $('shop-select');
  shopSelect.replaceChildren(...actor.shops.map(id => {
    const shop = getShop(id); const o = el('option', '', `${shop.name} · fictícia`); o.value = id; return o;
  }));
  shopSelect.value = state.shopId;
  const statusSelect = $('status-filter');
  statusSelect.replaceChildren(el('option','', 'Todos os estados comerciais'),
    ...COMMERCIAL_STATUSES.map(status => { const opt=el('option','',status);opt.value=status;return opt;}));
  statusSelect.options[0].value='all';statusSelect.value=state.statusFilter;
}
function renderList() {
  const items = filtered();
  const listProjection = projectInbox(state.cases,state.actorId,state.shopId,state.inboxView);
  const total = listProjection.length;
  $('list-count').textContent = `${total} ${total === 1 ? 'atendimento' : 'atendimentos'}`;
  const currentActor = getActor(state.actorId);
  $('list-context').textContent = currentActor.teamState !== 'active' ? 'Acesso fictício suspenso' : currentActor.role === 'gestor' ? 'Visão de supervisão' : 'Atribuídos a mim';
  const activeRows=projectInbox(state.cases,state.actorId,state.shopId,'active');
  const summary={total:activeRows.length,unread:activeRows.filter(x=>x.unread>0).length,human:activeRows.filter(x=>x.status==='em atendimento pelo operador').length};
  const tiles=[['Total',summary.total],['Não lidas',summary.unread],['Em atendimento',summary.human]];
  $('queue-summary').replaceChildren(...tiles.map(([label,value])=>{
    const tile=el('div','summary-tile');tile.append(el('strong','',value),el('span','',label));return tile;
  }));
  document.querySelectorAll('[data-inbox]').forEach(button => {
    const active=button.dataset.inbox===state.inboxView;
    button.classList.toggle('selected',active);button.setAttribute('aria-pressed',String(active));
  });
  const nodes = items.map((item, idx) => {
    const card = el('button', 'conversation-card' + (item.id === state.selectedId ? ' is-selected' : ''));
    card.type = 'button'; card.setAttribute('aria-pressed', String(item.id === state.selectedId));
    card.setAttribute('aria-label', `Abrir conversa ${item.name}, ${item.status}, ${item.unread} não lidas`);
    const avatar = el('div', 'avatar a' + (idx%4+1), item.initials); avatar.setAttribute('aria-hidden','true');
    const center = el('div','item-center');
    const row = el('div','item-title-row'); row.append(el('span','item-title',item.name),el('span','item-time',item.updatedAt));
    const preview = item.messages.at(-1)?.body ?? 'Sem mensagens';
    const foot = el('div', 'item-foot'); foot.append(el('span','micro-tag',item.tag));
    if(projectedMetaWindow(item)==='expired') foot.append(el('span','window-mini','Janela expirada'));
    if (item.unread > 0) foot.append(el('span','unread',item.unread));
    center.append(row, el('div','item-preview',preview),foot);
    card.append(avatar,center);
    card.addEventListener('click', () => {
      closeTransientDialogs();state.selectedId = item.id; item.unread = 0;state.detailTab='overview';
      goto('thread'); render();
    });
    return card;
  });
  if (!nodes.length) {
    const box = el('div','no-results');
    const suspended = getActor(state.actorId).teamState !== 'active';
    box.append(el('strong','', suspended?'Sem acesso demonstrativo':'Nenhuma conversa neste filtro'),el('span','', suspended?'Profissional suspenso na fixture. Acesso real pertence ao S0/S1-002.':'Altere a busca, o filtro ou o perfil fictício.'));
    list.replaceChildren(box);
  } else list.replaceChildren(...nodes);
  document.querySelectorAll('[data-filter]').forEach(btn => {
    const active = btn.dataset.filter === state.filter;
    btn.classList.toggle('selected', active);
    btn.setAttribute('aria-pressed', String(active));
  });
}
function renderThread() {
  const item = selectedCase();
  $('thread-title').textContent = item?.name ?? 'Selecione uma conversa';
  $('thread-meta').textContent = item ? `${getShop(item.shopId).name} · Caso ${item.id} · ${isInActiveInbox(item)?'Lista ativa':'Histórico preservado'} · demo` : 'Nenhum atendimento selecionado';
  const body = $('thread-body'); const bar = $('workflow-bar');
  const input = $('message-input'); const button = document.querySelector('.send-button');
  if (!item) {
    const empty = el('div','thread-placeholder');
    empty.append(el('h2','', 'Sua central de conversas'),el('p','', 'Selecione um atendimento na lista. Apenas dados fictícios serão exibidos.'));
    body.replaceChildren(empty); bar.replaceChildren(); input.disabled = true; button.disabled = true;
    $('detail-toggle').disabled = true; return;
  }
  $('detail-toggle').disabled = false;
  const children = [el('span','day-separator','CONVERSA SINTÉTICA · EXEMPLO VISUAL')];
  for (const m of item.messages) {
    const bubble = el('div', 'message ' + m.side);
    bubble.append(el('p','', m.body), el('small','',m.time));
    children.push(bubble);
  }
  body.replaceChildren(...children);
  // Rolar somente depois de renderizar; não dispara solicitações externas.
  body.scrollTop = body.scrollHeight;
  const note = el('div','workflow-copy');
  const s = el('span', 'status-indicator ' + statusTone(item.status), item.status);
  const t = el('span', 'tiny-note', 'Estado comercial · não alterado pela interface');
  note.append(s,t);
  bar.replaceChildren(note);
  const meta=projectedMetaWindow(item);
  bar.append(el('span','window-indicator '+(meta==='open'?'open':'closed'),meta==='open'?'Janela Meta aberta · projeção':meta==='expired'?'Janela Meta expirada · projeção':'Janela Meta não confirmada'));
  const completionState = humanCompletion(item,Boolean(state.processing[item.id]));
  if(completionState==='completed' || completionState==='completed_demo')
    bar.append(el('span','status-indicator','Etapa humana concluída · demo'));
  else if(completionState==='unknown')
    bar.append(el('span','status-indicator','Etapa humana não confirmada'));
  if(!isInActiveInbox(item)) bar.append(el('span','status-indicator','Histórico · somente leitura'));
  if(item.reassignmentProjection==='protected_queue') bar.append(el('span','status-indicator','Fila protegida · sem responsável elegível'));
  if (canMockClose(item)) {
    const close = el('button', 'btn btn-primary', 'Concluir atendimento');
    close.type = 'button'; close.id='request-completion';
    close.addEventListener('click', () => {
      if(!canMockClose(selectedCase()))return;
      captureDialogContext('completion');
      const dialog=$('completion-dialog');dialog.returnValue='';dialog.showModal();
    });
    bar.append(close);
  } else if (state.processing[item.id]) {
    const label = state.processing[item.id].kind === 'accepted' ? 'Solicitação simulada' : 'Resultado fictício';
    bar.append(el('span','status-indicator human',label));
  }
  const fActions=projectedFollowupActions(item,state.actorId,state.shopId,Boolean(state.processing[item.id]));
  const pendingLocal=state.followupRequests[item.id];
  if(fActions.includes('single_template') && !pendingLocal){
    const btn=el('button','btn btn-light','Selecionar e solicitar template aprovado');btn.type='button';
    btn.addEventListener('click',()=>{
      const current=selectedCase();
      if(!current || !projectedFollowupActions(current,state.actorId,state.shopId).includes('single_template'))return;
      const eligible=DEMO_TEMPLATES.filter(t=>current.eligibleTemplatesProjection?.includes(t.id+'@'+t.version));
      if(!eligible.length){showToast('Nenhum template elegível neste caso fictício.');return;}
      $('template-select').replaceChildren(...eligible.map(template=>{
        const option=el('option','',template.title+' · '+template.version+' (fictício)');
        option.value=template.id;return option;
      }));
      captureDialogContext('template');
      const dialog=$('template-dialog');dialog.returnValue='';dialog.showModal();
    });
    bar.append(btn);
  }
  if(fActions.includes('request_chain') && !pendingLocal){
    const btn=el('button','btn btn-light','Solicitar cadeia de tentativas à IA');btn.type='button';
    btn.addEventListener('click',()=>{
      try {state.followupRequests[item.id]=applyLocalFollowupRequest(item,state.actorId,state.shopId,'request_chain');
        state.detailTab='followup';render();showToast('Solicitação fictícia de cadeia. Não há plano persistido nem envio.');}
      catch(error){showToast('Operação não disponível neste cenário.');}
    });bar.append(btn);
  }
  if(pendingLocal) bar.append(el('span','status-indicator','Pedido simulado · não enviado'));
  const composeAllowed = canMockMessage(item);
  input.disabled = !composeAllowed;
  button.disabled = !composeAllowed;
  input.placeholder = composeAllowed ? 'Escrever mensagem de demonstração…' : meta==='expired' ? 'Janela de 24h encerrada · somente template aprovado' : 'Texto livre indisponível neste contexto';
}
function detailSection(title) {
  const section = el('section','detail-section'); section.append(el('h3','detail-label',title)); return section;
}
function prop(label,value) {
  const line=el('div','property'); line.append(el('span','',label),el('strong','',value));return line;
}
function callout(title,text,tone='') {
  const n=el('div','detail-callout ' + tone); n.append(el('strong','',title),el('div','',text));return n;
}
function renderDetails() {
  const target=$('detail-content');const item=selectedCase();
  if(!item){target.replaceChildren(el('p','detail-placeholder','Selecione uma conversa para ver informações do caso.'));return;}
  const profile=el('div','profile-detail');const avatar=el('div','avatar',item.initials);
  profile.append(avatar,el('strong','',item.name),el('span','',`Caso ${item.id} · exemplo fictício`));
  const tabs=el('div','detail-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Detalhes do caso fictício');
  for(const tab of DETAIL_TABS){
    const button=el('button','detail-tab'+(state.detailTab===tab.id?' active':''),tab.title);
    button.type='button';button.id='case-tab-'+tab.id;
    button.setAttribute('role','tab');button.setAttribute('aria-selected',String(state.detailTab===tab.id));
    button.setAttribute('aria-controls','case-tab-panel');
    button.setAttribute('tabindex',state.detailTab===tab.id?'0':'-1');
    button.addEventListener('click',()=>{state.detailTab=tab.id;renderDetails();
      target.querySelector('.detail-tab.active')?.focus();});
    button.addEventListener('keydown',e=>{if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight')return;
      e.preventDefault();const i=DETAIL_TABS.findIndex(x=>x.id===tab.id);
      state.detailTab=DETAIL_TABS[(i+(e.key==='ArrowRight'?1:DETAIL_TABS.length-1))%DETAIL_TABS.length].id;
      renderDetails();const active=target.querySelector('.detail-tab.active');active?.focus();
    });tabs.append(button);
  }
  const content=el('div','tab-content');content.id='case-tab-panel';content.setAttribute('role','tabpanel');
  content.setAttribute('aria-labelledby','case-tab-'+state.detailTab);content.setAttribute('tabindex','0');
  if(state.detailTab==='overview'){
    const group=detailSection('CONTEXTO DO ATENDIMENTO');
    const actor=ACTORS.find(a=>a.id===item.assignedTo);
    group.append(
      prop('Concessionária',getShop(item.shopId).name),
      prop('Profissional atribuído',item.reassignmentProjection==='protected_queue'?'Fila protegida (demonstração)':actor?.name??'Sem atribuição'),
      prop('Estado comercial',item.status),
      prop('Janela Meta (projeção)',projectedMetaWindow(item)==='open'?'Aberta · fictícia':projectedMetaWindow(item)==='expired'?'Expirada · fictícia':'Não confirmada'),
      prop('Etapa humana',({'pending':'Pendente','completed':'Concluída · cenário fictício','completed_demo':'Concluída · pedido simulado','unknown':'Não confirmada'})[humanCompletion(item,Boolean(state.processing[item.id]))] ?? 'Não confirmada'),
      prop('Lista',isInActiveInbox(item)?'Ativa / pendente':'Histórico preservado')
    );
    if(item.reassignmentProjection==='protected_queue') group.append(callout('Acesso operacional protegido','A S1-002 decidirá o remanejamento real; não há escolha de operador pelo frontend.','warning'));
    if(isSyntheticBankProtected(item)) group.append(callout('Marco bancário protegido','Silêncio de cliente ou janela Meta expirada não representa negativa da instituição financeira.','warning'));
    const rule=detailSection('REGRAS DA EXPERIÊNCIA');
    rule.append(callout('Atendimento humano independente','Concluir a conversa não envia cadastro ao banco, não marca vendido ou perdido e não reativa a IA Vendedora.'));
    rule.append(el('p','detail-small','Gestores veem conversas fictícias por loja. Dados financeiros protegidos D3/D4 não são disponibilizados na simulação.'));
    content.append(group,rule);
  } else if(state.detailTab==='activity'){
    const activity=detailSection('HISTÓRICO DE EVENTOS FICTÍCIOS');
    const items=activityFor(item,state.processing[item.id]);
    for(const entry of items){const card=el('div','activity-item');
      card.append(el('strong','',entry.label),el('span','',entry.time));activity.append(card);}
    activity.append(el('p','detail-small','Linha do tempo ilustrativa, sem auditoria ou eventos reais do S0.'));
    content.append(activity);
  } else if(state.detailTab==='notes'){
    const notes=detailSection('NOTAS INTERNAS · SIMULAÇÃO');
    notes.append(callout('Informação privada de operação','Notas fictícias não são enviadas ao cliente e não persistem fora desta página.'));
    for(const n of item.notes??[]){const card=el('div','detail-row');
      card.append(el('strong','',n.text),el('span','',`${ACTORS.find(x=>x.id===n.actorId)?.name??'Profissional fictício'} · ${n.time}`));notes.append(card);}
    if(canWriteNote(item,state.actorId,state.shopId) && isInActiveInbox(item)){
      const form=el('form','note-form');form.id='internal-note-form';
      const label=el('label','field-label','Nova nota fictícia');label.htmlFor='note-text';
      const textarea=el('textarea','note-textarea');textarea.id='note-text';textarea.maxLength=250;
      textarea.placeholder='Anotação interna demonstrativa…';textarea.required=true;
      const add=el('button','btn btn-primary','Adicionar nota');add.type='submit';
      form.append(label,textarea,add);
      form.addEventListener('submit',e=>{e.preventDefault();const text=textarea.value.trim();
        if(!text||!canWriteNote(selectedCase(),state.actorId,state.shopId))return;
        item.notes??=[];item.notes.push({id:'n-'+(item.notes.length+1),text,actorId:state.actorId,time:'Agora · fictício'});
        renderDetails();showToast('Nota adicionada somente à memória do navegador.');
      });notes.append(form);
    }else notes.append(el('p','detail-small','Adição de nota não disponível neste perfil ou caso de demonstração.'));
    content.append(notes);
  } else if(state.detailTab==='extraction') {
    const extract=detailSection('FICHA E EXTRAÇÃO · FV-02');const proc=state.processing[item.id];
    if(!proc){
      const phase=humanCompletion(item);
      extract.append(phase==='completed' ? callout('Etapa concluída · retorno não disponível','A fixture informa conclusão humana, mas não informa resultado de extração. Não afirmar que ela foi solicitada, gravada ou concluída.','warning') :
        phase==='pending' ? callout('Ainda não solicitada','Após a conclusão humana, o S0 poderá solicitar extração. Nenhum dado foi processado neste exemplo.') :
        callout('Situação não confirmada','Não é possível afirmar que a etapa humana terminou ou que houve extração. Aguarde uma projeção confiável da S0.','warning'));
    }else{
      const scenario=modelExtraction(proc.kind);
      extract.append(callout(scenario.title,scenario.explanation,proc.kind==='accepted'||proc.kind==='partial'?'warning':''));
      if(proc.kind==='partial'){
        const example=el('div','detail-row');example.append(el('strong','','Campo ilustrativo A'),el('span','','Proposta sintética · não persistida'));
        const missing=el('div','detail-row');missing.append(el('strong','','Campo ilustrativo B'),el('span','','Sem fonte suficiente · pendente'));
        extract.append(example,missing);
      }
      if(canSimulateCompletion(item,state.actorId,state.shopId) && state.processing[item.id] && humanCompletion(item)==='pending'){
        const actions=el('div','scenario-options');
        for(const [kind,label] of [['partial','Retorno parcial'],['failed','Falha técnica'],['stale','Versão obsoleta']]){
          const button=el('button','btn btn-light',label);button.type='button';
          button.addEventListener('click',()=>{if(!canSimulateCompletion(selectedCase(),state.actorId,state.shopId))return;
            state.processing[item.id]={kind};render();showToast(modelExtraction(kind).title+'. Nenhuma API foi chamada.');});actions.append(button);
        }extract.append(actions);
      }
    }
    extract.append(el('p','detail-small','Sem editor cadastral rotineiro. A OpenAI apenas propõe; S0 decidirá autorização, validação e gravação no futuro.'));
    content.append(extract);
  } else {
    const followup=detailSection('RECONTATOS CONTEXTUAIS · CF-OP-02');
    const local=state.followupRequests[item.id]??null;
    const projection=projectedFollowupState(item,local);
    followup.append(callout('Regras de três acontecimentos separados',
      '24h desde último inbound habilitam mensagem livre. Conclusão humana apenas solicita extração. Outras 24h, após prova de envio do template final, podem levar a perdido SOMENTE por decisão S0 e ciclo elegível.'));
    if(!projection){
      followup.append(callout('Sem plano confirmado',
        projectedMetaWindow(item)==='expired'?
        'Janela livre vencida: somente pedido de template elegível ou solicitação de plano, se autorizado pelo S0.':'Nenhum plano pós-humano confirmado nesta demonstração.','warning'));
    } else if(projection.source==='local_demo'){
      const title=projection.kind==='request_chain'?'Solicitação de cadeia fictícia':'Solicitação de template individual fictícia';
      followup.append(callout(title,'SOLICITADO (demo), não agendado, não transmitido e nunca ENVIADO. A resposta da IA e o envio dependem de S0/Meta.','warning'));
      if(projection.template) followup.append(prop('Template simulado',projection.template.id+' · '+projection.template.version));
    } else {
      followup.append(callout('Plano projetado (dados artificiais)','Situação técnica fornecida pela fixture: '+projection.state+'. O navegador não calcula agendamento nem prova de envio.'));
      for(const attempt of projection.attempts??[]){
        const line=el('div','detail-row');
        line.append(el('strong','',attempt.label+' · '+attempt.state),el('span','',attempt.template+' · '+attempt.time));
        followup.append(line);
      }
      followup.append(prop('Template final efetivamente enviado',projection.finalSentConfirmed?'Confirmado apenas no cenário fictício':'Não confirmado'));
      followup.append(prop('Silêncio pós-final',projection.silenceResolution==='confirmed_eligible'?
        'Perda já representada pelo S0 fictício': 'Prazo não iniciado/sem decisão'));
    }
    if(isSyntheticBankProtected(item)) followup.append(callout('Sem perda por silêncio bancário','Remessa ao banco e vendido não são estados elegíveis para perda automática C09.','warning'));
    followup.append(el('p','detail-small','Não há templates reais, relógio local de 24h, chamada OpenAI nem envio WhatsApp. Fonte futura: projeções autorizadas pelo S0.'));
    content.append(followup);
  }
  target.replaceChildren(profile,tabs,content);
}

function render(){renderList();renderThread();renderDetails();app.dataset.mobileView=state.mobileView;}
function changeActor(actorId){
  const actor=getActor(actorId);if(!actor)return;
  closeTransientDialogs();
  state.actorId=actor.id;state.shopId=actor.shops[0];state.selectedId=null;state.detailTab='overview';state.statusFilter='all';state.inboxView='active';
  state.filter='all';state.query='';$('search-input').value='';goto('list');updateSelectors();render();
}
$('actor-select').addEventListener('change',event=>changeActor(event.target.value));
$('shop-select').addEventListener('change',event=>{
  const actor=getActor(state.actorId);
  if(!actor.shops.includes(event.target.value))return;
  closeTransientDialogs();
  state.shopId=event.target.value;state.selectedId=null;state.detailTab='overview';state.statusFilter='all';state.inboxView='active';$('status-filter').value='all';state.query='';$('search-input').value='';goto('list');render();
});
$('search-input').addEventListener('input',event=>{state.query=event.target.value;renderList();});
$('status-filter').addEventListener('change',event=>{state.statusFilter=event.target.value;renderList();});
document.querySelectorAll('[data-inbox]').forEach(button=>button.addEventListener('click',()=>{
 closeTransientDialogs();state.inboxView=button.dataset.inbox;state.selectedId=null;goto('list');render();
}));
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{state.filter=button.dataset.filter;renderList();}));
$('thread-back').addEventListener('click',()=>goto('list'));
$('detail-back').addEventListener('click',()=>goto('thread'));
$('detail-toggle').addEventListener('click',()=>{
  if (window.matchMedia('(max-width:760px)').matches) {goto('detail');return;}
  const hidden=app.classList.toggle('details-hidden');$('detail-toggle').setAttribute('aria-expanded',String(!hidden));
});
$('detail-close').addEventListener('click',()=>{app.classList.add('details-hidden');$('detail-toggle').setAttribute('aria-expanded','false');});
function openTeamSummary(){
  if(!canSeeTeamSummary(state.actorId,state.shopId)){
    showToast('A visão da equipe está disponível somente no perfil fictício de gestor.');return;
  }
  const team=$('team-list');
  const rows=ACTORS.filter(actor=>actor.shops.includes(state.shopId));
  team.replaceChildren(...rows.map(actor=>{
    const assigned=visibleConversations(state.cases,state.actorId,state.shopId)
      .filter(record=>record.assignedTo===actor.id).length;
    const card=el('div','team-member');
    const memberState=actor.teamState==='active'?'Ativo (fictício)':'Indisponível / suspenso (fictício)';
    card.append(el('strong','',actor.name),el('span','',`${actor.role==='gestor'?'Gestor':'Operador'} da Prumo · ${memberState} · ${assigned} caso(s) sintéticos atribuídos`));return card;
  }));
  const dialog=$('team-dialog');dialog.returnValue='';dialog.showModal();
}
$('team-nav').addEventListener('click',openTeamSummary);
$('team-nav-mobile').addEventListener('click',openTeamSummary);
$('team-close').addEventListener('click',()=>$('team-dialog').close());
document.addEventListener('keydown',event=>{
  // Não deslocar o foco para trás de um diálogo modal nativo.
  if(document.querySelector('dialog[open]'))return;
  const inField=['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName);
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){
    event.preventDefault();goto('list');$('search-input').focus();
  }
  if(event.key==='Escape'&&!inField&&!document.querySelector('dialog[open]')&&window.matchMedia('(max-width:760px)').matches){
    if(state.mobileView==='detail')goto('thread');else if(state.mobileView==='thread')goto('list');
  }
});
$('reset-app').addEventListener('click',()=>{
  state.cases=copyCFDemoFixtures();state.processing={};state.followupRequests={};changeActor('rafael');showToast('Dados de demonstração restaurados.');
});
$('composer').addEventListener('submit',event=>{
  event.preventDefault();const item=selectedCase();const input=$('message-input');const text=input.value.trim();
  if(!text || !item || !canMockMessage(item)) return;
  item.messages.push({id:`demo-${item.messages.length+1}`,side:'out',body:text,time:'Agora · fictício'});
  item.updatedAt='Agora';input.value='';render();showToast('Mensagem adicionada apenas à simulação local.');
});
$('completion-dialog').addEventListener('close',()=>{
  const isConfirm=$('completion-dialog').returnValue==='confirm';
  $('completion-dialog').returnValue='';
  const sameContext=consumeDialogContext('completion');
  if(!isConfirm || !sameContext)return;
  const item=selectedCase(); if(!item || !canMockClose(item))return;
  state.processing[item.id]={kind:'accepted'};state.detailTab='extraction';
  render();showToast('Solicitação de conclusão simulada. Nenhuma API foi chamada.');
});
$('template-dialog').addEventListener('close',()=>{
  const isConfirm=$('template-dialog').returnValue==='confirm';
  $('template-dialog').returnValue='';
  const sameContext=consumeDialogContext('template');
  if(!isConfirm || !sameContext)return;
  const item=selectedCase();if(!item)return;
  const template=DEMO_TEMPLATES.find(x=>x.id===$('template-select').value);
  try {state.followupRequests[item.id]=applyLocalFollowupRequest(item,state.actorId,state.shopId,'single_template',template);
    state.detailTab='followup';render();showToast('Pedido fictício de template recebido. Envio não confirmado.');}
  catch(error){showToast('Template indisponível neste contexto.');}
});
if(window.matchMedia('(max-width:1040px)').matches){app.classList.add('details-hidden');$('detail-toggle').setAttribute('aria-expanded','false');}
updateSelectors();render();
