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
import { registrationProjectionFor, registrationStateCopy } from './registration-view.mjs';
import { bankProjectionFor, bankPhaseCopy } from './bank-view.mjs';
import { postmarkViewFor, postmarkCopy, mayMockOperateContinuation } from './postmark-view.mjs';
import { projectManagedTeam, requestMockIntake } from './team-operations.mjs';
import { projectManagerMonitor } from './team-monitor.mjs';
import { projectTeamMonitoring, describeMonitoring } from './team-monitoring.mjs';

const $ = id => document.getElementById(id);
const app = $('visual-app');
const list = $('conversation-items');
const state = {
  actorId: 'rafael', shopId: 'aurora', filter: 'all', statusFilter: 'all', detailTab: 'overview', query: '',
  selectedId: 'A-102', cases: copyCFDemoFixtures(), processing: {}, followupRequests: {}, inboxView: 'active',
  mobileView: 'list', dialogContext: { completion: null, template: null }, teamRequests:{}, teamPanel:'members'
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

function postmarkContextValid(record) {
  if(!record?.postmarkProjection)return true;
  // Operar caso novo exige atribuição própria, não permissão no histórico antigo.
  // Abrir o caso antigo ainda exige acesso à relação recíproca autorizada.
  return record.postmarkProjection.direction==='continuation' &&
    mayMockOperateContinuation(record,state.cases,state.actorId,state.shopId);
}
function canMockMessage(record) {
  return postmarkContextValid(record) &&
    mayMockFreeText(record,state.actorId,state.shopId,Boolean(state.processing[record?.id]));
}
function canMockClose(record) {
  return postmarkContextValid(record) && canSimulateCompletion(record,state.actorId,state.shopId) &&
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
  if(completionState==='completed')
    bar.append(el('span','status-indicator','Etapa humana concluída · projeção fictícia'));
  else if(completionState==='requested_demo')
    bar.append(el('span','status-indicator','Conclusão solicitada · simulação'));
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
  const fActions=postmarkContextValid(item) ? projectedFollowupActions(item,state.actorId,state.shopId,Boolean(state.processing[item.id])) : [];
  const pendingLocal=state.followupRequests[item.id];
  if(fActions.includes('single_template') && !pendingLocal){
    const btn=el('button','btn btn-light','Selecionar e solicitar template aprovado');btn.type='button';
    btn.addEventListener('click',()=>{
      const current=selectedCase();
      if(!current || current.id!==item.id || !postmarkContextValid(current) ||
        !projectedFollowupActions(current,state.actorId,state.shopId).includes('single_template'))return;
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
      if(selectedCase()?.id!==item.id || !postmarkContextValid(item))return;
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
      prop('Etapa humana',({'pending':'Pendente','completed':'Concluída · cenário fictício','requested_demo':'Conclusão solicitada · ainda não confirmada','unknown':'Não confirmada'})[humanCompletion(item,Boolean(state.processing[item.id]))] ?? 'Não confirmada'),
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
    if(postmarkContextValid(item) && canWriteNote(item,state.actorId,state.shopId) && isInActiveInbox(item)){
      const form=el('form','note-form');form.id='internal-note-form';
      const label=el('label','field-label','Nova nota fictícia');label.htmlFor='note-text';
      const textarea=el('textarea','note-textarea');textarea.id='note-text';textarea.maxLength=250;
      textarea.placeholder='Anotação interna demonstrativa…';textarea.required=true;
      const add=el('button','btn btn-primary','Adicionar nota');add.type='submit';
      form.append(label,textarea,add);
      form.addEventListener('submit',e=>{e.preventDefault();const text=textarea.value.trim();
        if(!text || selectedCase()?.id!==item.id || !postmarkContextValid(item) || !canWriteNote(item,state.actorId,state.shopId) || !isInActiveInbox(item))return;
        item.notes??=[];item.notes.push({id:'n-'+(item.notes.length+1),text,actorId:state.actorId,time:'Agora · fictício'});
        renderDetails();showToast('Nota adicionada somente à memória do navegador.');
      });notes.append(form);
    }else notes.append(el('p','detail-small','Adição de nota não disponível neste perfil ou caso de demonstração.'));
    content.append(notes);
  } else if(state.detailTab==='extraction') {
    const extract=detailSection('FICHA E EXTRAÇÃO · FV-02');const proc=state.processing[item.id];
    if(item.registrationProjection){
      // A tela demonstra leitura de uma projeção do S0; não aceita saída bruta da IA.
      const registration=registrationProjectionFor(item,state.actorId,state.shopId);
      const description=registrationStateCopy(registration);
      extract.append(callout(description.title,description.note,registration.confirmedPersisted?'success':'warning'));
      if(registration.visibility!=='detail'){
        extract.append(callout('Detalhes restritos ao responsável do caso',
          'A visualização de supervisão não concede leitura de ficha D3/D4. Nenhum valor, fonte ou pendência individual é exibido neste modo.','warning'));
      }else{
        if(registration.confirmedPersisted && registration.formVersionRef)
          extract.append(prop('Versão confirmada no cenário',registration.formVersionRef));
        const applied=detailSection('DADOS CONFIRMADOS NA FICHA FICTÍCIA');
        if(!registration.fields.length) applied.append(el('p','detail-small','Sem campo com valor, fonte e gravação confirmados.'));
        for(const field of registration.fields){
          const card=el('div','detail-row');
          card.append(el('strong','',field.label),el('div','',field.safeDisplayValue),
            el('span','',`Origem: ${field.sourceLabel} · referência ${field.sourceRef} · aplicado na versão ilustrativa`));
          applied.append(card);
        }
        extract.append(applied);
        const missing=detailSection('INFORMAÇÕES AUSENTES');
        if(!registration.missing.length) missing.append(el('p','detail-small','Nenhuma ausência informada nesta projeção.'));
        for(const label of registration.missing) missing.append(el('div','detail-row',label));
        extract.append(missing);
        const conflicts=detailSection('CONTRADIÇÕES / CONFERÊNCIA');
        if(!registration.conflicts.length) conflicts.append(el('p','detail-small','Nenhum conflito informado nesta projeção.'));
        for(const label of registration.conflicts) conflicts.append(el('div','detail-row',label));
        extract.append(conflicts);
      }
    } else if(!proc){
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
            if(selectedCase()?.id!==item.id)return;
            state.processing[item.id]={kind};render();showToast(modelExtraction(kind).title+'. Nenhuma API foi chamada.');});actions.append(button);
        }extract.append(actions);
      }
    }
    extract.append(el('p','detail-small','Sem editor cadastral rotineiro. A OpenAI apenas propõe; S0 decidirá autorização, validação e gravação no futuro.'));
    content.append(extract);
  } else if(state.detailTab==='bank'){
    const bank=detailSection('REMESSA E RETORNO BANCÁRIO · O4');
    const projection=bankProjectionFor(item,state.actorId,state.shopId);
    const copy=bankPhaseCopy(projection);
    bank.append(callout(copy.title,copy.description,
      projection.submissionConfirmed?'':'warning'));
    bank.append(prop('Estado comercial (somente leitura)',item.status));
    if(projection.visibility==='summary'){
      bank.append(el('p','detail-small','Supervisão da Prumo: sem acesso a documentos, provas bancárias, referências ou campos D4 nesta visualização.'));
    }else if(projection.visibility==='detail'){
      bank.append(prop('Situação operacional fictícia',projection.phase));
      if(projection.submissionSummary){
        bank.append(prop('Remessa na projeção',projection.submissionSummary.label));
        bank.append(prop('Versão técnica fictícia',projection.submissionSummary.versionRef));
        bank.append(prop('Comprovação',projection.submissionSummary.proofLabel));
        bank.append(prop('Responsabilidade',projection.submissionSummary.operatorLabel));
      }else bank.append(el('p','detail-small','Nenhuma remessa confirmada por versão e prova S0 neste cenário.'));
      if(projection.replySummary){
        bank.append(prop('Retorno na projeção',projection.replySummary.label));
        bank.append(prop('Versão do retorno fictício',projection.replySummary.versionRef));
      }else bank.append(callout('Decisão bancária não confirmada',
        'Não há aprovação, recusa ou venda inferida. A espera do banco não determina o desfecho comercial.','warning'));
    }
    bank.append(el('p','detail-small',
      'Somente leitura. Registros C15–C18 exigem profissional autorizado, prova verificada e confirmação S0. Sem formulário de prova real, envio, venda ou negativa neste protótipo.'));
    content.append(bank);
  } else if(state.detailTab==='postmark'){
    const contact=detailSection('NOVO CONTATO APÓS MARCO · O5');
    const projection=postmarkViewFor(item,state.cases,state.actorId,state.shopId);
    const copy=postmarkCopy(projection);
    contact.append(callout(copy.title,copy.description,projection.linked?'':'warning'));
    if(projection.linked){
      contact.append(prop('Marco original preservado',projection.sourceStatus));
      contact.append(prop('IA Vendedora', 'Silenciada definitivamente para o ciclo de origem'));
      contact.append(prop('Natureza do contato','Novo atendimento humano independente · cenário fictício'));
      const linked=state.cases.find(record=>record.id===projection.relatedCaseId);
      if(linked){
        contact.append(prop('Caso relacionado autorizado',linked.id));
        const open=el('button','btn btn-primary',
          projection.kind==='origin'?'Abrir novo atendimento humano':'Consultar atendimento de origem');
        open.type='button';
        open.addEventListener('click',()=>{
          // Revalidar escopo, reciprocidade e vínculo no clique; não criar caso.
          if(selectedCase()?.id!==item.id)return;
          const now=postmarkViewFor(item,state.cases,state.actorId,state.shopId);
          const target=state.cases.find(row=>row.id===now.relatedCaseId);
          if(!now.linked || !target)return;
          closeTransientDialogs();
          state.inboxView=target.inboxProjection==='historical'?'history':'active';
          state.filter='all';state.statusFilter='all';state.query='';
          $('search-input').value='';state.selectedId=target.id;state.detailTab='postmark';
          goto('thread');updateSelectors();render();
        });
        contact.append(open);
      }
    }else{
      contact.append(el('p','detail-small',
        'Nenhum ciclo é criado por esta tela. Vínculo ausente, divergente ou fora do escopo não concede acesso nem revela outro atendimento.'));
    }
    contact.append(el('p','detail-small',
      'Somente navegação sobre casos fictícios já projetados. A S0 decide criação, roteamento, versão, permissão e histórico. Não existe comando C14 nem reativação da IA Vendedora neste browser.'));
    content.append(contact);
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
  if($('team-dialog').open)$('team-dialog').close();
  state.teamRequests={};state.teamPanel='members';
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
function renderTeamMonitoring(){
  const target=$('team-monitor');
  const view=projectTeamMonitoring(state.actorId,state.cases);
  if(view.visibility!=='team_summary'){
    target.replaceChildren();return;
  }
  const section=el('section','team-monitor-section');
  section.append(el('h3','team-monitor-heading','Monitoramento operacional da equipe · G3'));
  section.append(el('p','detail-small',
    'Contagens somente sobre casos projetados e autorizados da equipe em todas as lojas concedidas. Não são métricas de SLA, produtividade ou tempo real.'));
  const tiles=el('div','team-monitor-grid');
  const keys=['activeCases','unreadCases','windowAttentionCases','protectedQueueCases','unassignedTeamCases','bankReplyPendingCases'];
  for(const key of keys){
    const tile=el('div','team-monitor-tile');
    tile.append(el('strong','',String(view.summary[key])),
      el('span','',describeMonitoring(key)));
    tiles.append(tile);
  }
  section.append(tiles);
  const states=el('p','team-monitor-states',
    `Operadores supervisionados: ${view.summary.operatorCount} · Entrada de leads pausada: ${view.summary.intakePausedCount} · Conta indisponível: ${view.summary.intakeUnavailableCount} · Casos no histórico: ${view.summary.historicalCases} · Casos ativos autoatribuídos ao gestor: ${view.summary.managerOwnedCases}`);
  section.append(states);
  const detail=el('div','team-monitor-operator-list');
  for(const member of view.operators){
    const line=el('div','team-monitor-operator');
    line.append(el('strong','',member.name),
      el('span','',`Ativos: ${member.activeCount} · Não lidos: ${member.unreadCount} · Janela vencida projetada: ${member.windowAttentionCount} · Histórico: ${member.historicalCount}`));
    detail.append(line);
  }
  section.append(detail);
  section.append(el('p','detail-small',
    'Prazos de espera e atrasos reais: NÃO VERIFICADOS. Nenhum relógio, dado cadastral ou prova bancária foi consultado. Um retorno pendente não é aprovação, recusa ou venda.'));
  target.replaceChildren(section);
}
function renderTeamSummary(){
  const team=$('team-list');
  if(!canSeeTeamSummary(state.actorId,state.shopId)){
    team.replaceChildren(el('p','detail-small','Equipe não disponível neste perfil fictício.'));
    renderTeamMonitoring();return;
  }
  const rows=projectManagedTeam(state.actorId,state.cases);
  team.replaceChildren(...rows.map(member=>{
    const card=el('div','team-member');
    card.append(el('strong','',member.name));
    const staffState=member.teamState==='active'?'Conta ativa (fictícia)':'Conta suspensa (fictícia)';
    const leadState=member.intake==='paused_confirmed'?'Novos leads pausados (projeção fictícia)':
      member.intake==='receiving'?'Apto a receber novos leads (projeção fictícia)':'Indisponível para receber';
    card.append(el('span','',`${staffState} · ${leadState} · ${member.cases} caso(s) na equipe`));
    card.append(el('span','',`Concessionárias concedidas pelo responsável (somente leitura): ${member.shops.map(id=>getShop(id)?.name??id).join(', ')}`));
    const requested=state.teamRequests[member.id];
    if(requested){
      card.append(el('span','',`SOLICITADO LOCALMENTE: ${requested.action==='pause'?'pausar novos leads':'retomar novos leads'} em todas as lojas concedidas. NÃO aplicado; redistribuição NÃO executada.`));
    }else if(member.teamState==='active' && ['receiving','paused_confirmed'].includes(member.intake)){
      const action=member.intake==='receiving'?'pause':'resume';
      const button=el('button','btn btn-light',action==='pause'?'Solicitar pausa de novos leads':'Solicitar retomada de novos leads');
      button.type='button';button.setAttribute('aria-label',`${action==='pause'?'Solicitar pausa':'Solicitar retomada'} de novos leads para ${member.name}, todas as concessionárias concedidas`);
      button.addEventListener('click',()=>{
        if(state.teamRequests[member.id])return;
        try{
          const requestedNow=requestMockIntake(state.actorId,member.id,action);
          state.teamRequests[member.id]=requestedNow;renderTeamSummary();
          showToast('Pedido fictício registrado somente no navegador. Nenhum lead foi redistribuído.');
        }catch{showToast('Ação indisponível para este gestor e operador.');}
      });
      card.append(button);
    }
    return card;
  }));
  renderTeamMonitoring();
}
function renderTeamMonitor(){
  const target=$('team-monitor');
  const projection=projectManagerMonitor(state.actorId,state.cases,state.teamRequests);
  if(projection.visibility!=='ready'){
    target.replaceChildren(el('p','detail-small','Monitoramento indisponível para este perfil.'));
    return;
  }
  const title=el('h3','detail-label','G3 · MONITORAMENTO DA PRÓPRIA EQUIPE');
  const note=el('p','team-hint',projection.asOf+
    '. Contagens da fixture, sem SLA verificado, sem cronômetro Meta/C09 e sem dados bancários D4.');
  const indicators=el('div','team-monitor-metrics');
  const data=projection.indicators;
  const values=[
    ['Operadores da equipe',data.teamMembers],
    ['Novos leads pausados',data.intakePaused],
    ['Casos ativos autorizados',data.operationalActive],
    ['Fila protegida',data.protectedQueue],
    ['Histórico autorizado',data.historical],
    ['Pedidos locais pendentes',data.pendingLocalRequests]
  ];
  for(const [label,value] of values){
    const tile=el('div','team-monitor-metric');
    tile.append(el('strong','',value),el('span','',label));indicators.append(tile);
  }
  const workload=el('div','team-monitor-list');
  workload.append(el('h3','detail-label','CARTEIRA POR PROFISSIONAL · DEMONSTRAÇÃO'));
  for(const member of projection.operators){
    const row=el('div','team-monitor-card');
    const availability=member.teamState!=='active'?'Conta suspensa · sem entrada':
      member.intake==='paused_confirmed'?'Novos leads pausados':
      member.intake==='receiving'?'Recebimento habilitado na fixture':'Entrada não confirmada';
    row.append(el('strong','',member.name),
      el('span','',member.cases+' caso(s) autorizados · '+availability));
    workload.append(row);
  }
  const signals=el('div','team-monitor-list');
  signals.append(el('h3','detail-label','SINAIS OPERACIONAIS PROJETADOS'));
  if(!projection.signals.length)
    signals.append(el('p','detail-small','Sem sinal técnico confirmado nesta projeção. Isso não significa ausência de pendências reais.'));
  for(const signal of projection.signals){
    const row=el('div','team-monitor-card');
    row.append(el('strong','',signal.label+' · Caso '+signal.caseId),
      el('span','',signal.shopName+' · '+signal.observedAt),
      el('span','',signal.observedWaitMinutes===null?
        'Tempo de espera não informado nesta projeção.':
        'Espera observada: '+signal.observedWaitMinutes+' min (fictícia, não SLA).'),
      el('span','', 'Estado comercial preservado: '+signal.commercialStatus));
    signals.append(row);
  }
  target.replaceChildren(title,note,indicators,workload,signals,
    el('p','team-hint','Sinais técnicos não são estados comerciais novos. '+
      'A S0 define prazos, prioridades, distribuição, permissões e confirmação de eventos.'));
}
function switchTeamPanel(panel){
  if(!canSeeTeamSummary(state.actorId,state.shopId))return;
  state.teamPanel=panel==='monitor'?'monitor':'members';
  const monitoring=state.teamPanel==='monitor';
  $('team-list').hidden=monitoring;
  $('team-monitor').hidden=!monitoring;
  $('team-show-members').setAttribute('aria-pressed',String(!monitoring));
  $('team-show-monitor').setAttribute('aria-pressed',String(monitoring));
  if(monitoring)renderTeamMonitor();
  else renderTeamSummary();
}
$('team-show-members').addEventListener('click',()=>switchTeamPanel('members'));
$('team-show-monitor').addEventListener('click',()=>switchTeamPanel('monitor'));

function openTeamSummary(){
  if(!canSeeTeamSummary(state.actorId,state.shopId)){
    showToast('A visão da equipe está disponível somente no perfil fictício de gestor.');return;
  }
  switchTeamPanel('members');
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
  const item=selectedCase();if(!item || !postmarkContextValid(item))return;
  const template=DEMO_TEMPLATES.find(x=>x.id===$('template-select').value);
  try {state.followupRequests[item.id]=applyLocalFollowupRequest(item,state.actorId,state.shopId,'single_template',template);
    state.detailTab='followup';render();showToast('Pedido fictício de template recebido. Envio não confirmado.');}
  catch(error){showToast('Template indisponível neste contexto.');}
});
if(window.matchMedia('(max-width:1040px)').matches){app.classList.add('details-hidden');$('detail-toggle').setAttribute('aria-expanded','false');}
updateSelectors();render();
