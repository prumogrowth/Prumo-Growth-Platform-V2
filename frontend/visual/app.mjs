/** FV-UI-001. Navegação e demonstração em memória; NÃO é frontend autenticado.
 * Não chamar backend, OpenAI, Meta, Banco, storage ou permitir efeito comercial.
 */
import {
  ACTORS, COMMERCIAL_STATUSES, getActor, getShop, visibleConversations, visibleMockShops, hasMockCaseOnlyScope,
  canSimulateCompletion, statusTone
} from './fixtures.mjs';
import {
  DETAIL_TABS, projectQueue, summaryOf, canWriteNote, canSeeTeamSummary,
  activityFor, modelExtraction
} from './view-model.mjs';
import {
  DEMO_TEMPLATES, copyCFDemoFixtures, isInActiveInbox, projectedMetaWindow,
  humanCompletion, mayMockFreeText, projectedFollowupActions, projectInbox,
  projectedFollowupState, applyLocalFollowupRequest, isSyntheticBankProtected,
  hasProjectedAction, hasEligibleTemplateVersion
} from './cf-op-02.mjs';
import { registrationProjectionFor, registrationStateCopy } from './registration-view.mjs';
import { projectDemoOperationFeedback } from './operation-feedback.mjs';
import { stageMockMessageTransport } from './transport-state-view.mjs';
import { projectMockHumanCycleHistory, projectMockClarificationScene,
  stageMockRepeatCompletion, projectMockCustomerDossier } from './human-cycle-view.mjs';
import { bankProjectionFor, bankPhaseCopy } from './bank-view.mjs';
import { postmarkViewFor, postmarkCopy, mayMockOperateContinuation } from './postmark-view.mjs';
import { projectManagedTeam, requestMockIntake } from './team-operations.mjs';
import { projectSharedNewLeadQueue, requestMockQueueAction } from './distribution-view.mjs';
import { projectManagerPausePreview } from './team-pause-preview.mjs';
import { projectManagerMonitor } from './team-monitor.mjs';
import { projectManagerBatches } from './batch-monitor.mjs';
import { projectTeamMonitoring, describeMonitoring } from './team-monitoring.mjs';
import {
  canStageReadAcknowledgment, projectDemoAttention, latestConfirmedDemoMessage
} from './conversation-attention.mjs';
import { installCommunicationComposer, audioDuration } from './communication-composer.mjs';
import { withRevisionScenes } from './revision-fixtures.mjs';
import { aiCommunicationsFor, operationalHistoryFor, bankReadinessFor } from './relationship-view.mjs';

const $ = id => document.getElementById(id);
const app = $('visual-app');
const list = $('conversation-items');
// FV-UI-037: acompanhar a preferência do SO enquanto não houver escolha manual.
const systemColorScheme = window.matchMedia('(prefers-color-scheme: dark)');
// Cenários de avaliação da MESMA base. Não representam identidade autenticada.
const initialDemoActor = new URLSearchParams(window.location?.search ?? '').get('perfil') === 'gestor' ? 'marina' : 'rafael';
const state = {
  actorId: initialDemoActor, shopId: 'aurora', filter: 'all', statusFilter: 'all', detailTab: 'overview', query: '',
  selectedId: initialDemoActor === 'rafael' ? 'A-102' : null, cases: withRevisionScenes(copyCFDemoFixtures()), processing: {}, reviewScenes: {}, followupRequests: {}, inboxView: 'all',
  bankCaseId:null, noteDrafts:{}, mobileView: 'list', listLoading:false, theme: systemColorScheme.matches ? 'dark' : 'light', themeOverride:false,
  dialogContext: { completion: null, template: null, message: null }, intakeDialogContext:null, queueDialogContext:null, queueRequests:{}, teamRequests:{}, teamPanel:'members'
};
const communication = installCommunicationComposer({
  getContext: () => ({ key: `${state.actorId}:${state.shopId}:${state.selectedId}`,
    allowed: Boolean(selectedCase() && canMockMessage(selectedCase())) }),
  onNotice: showToast,
  onAttach: clip => {
    const item = selectedCase();
    if (!item || !canMockMessage(item)) return;
    const actor = getActor(state.actorId);
    item.messages.push({ id: `demo-audio-${item.messages.length+1}`, side:'out',
      body: `${humanRoleLabel(actor)} ${actor.name} · Áudio local (${audioDuration(clip.duration)})`,
      localAudioId: clip.id, time:'Agora · fictício', authorId:actor.id,
      deliveryState:'local_demo_not_sent' });
    render();
    showToast('Áudio anexado somente nesta demonstração. Sem upload ou envio pelo WhatsApp.');
  }
});

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
function selectedCase() {
  const base=accessible().find(x=>x.id===state.selectedId)??null;
  const staged=base && state.reviewScenes[base.id];
  return staged && staged.shopId===base.shopId && staged.assignedTo===base.assignedTo
    ? staged : base;
}

// Nomes exibidos; nenhum identificador técnico, role ou status é renomeado.
const HUMAN_ROLE_LABELS = Object.freeze({
  operador:'Consultor', gestor:'Gestor', responsavel:'Diretor', diretor:'Diretor'
});
function humanRoleLabel(actor) { return HUMAN_ROLE_LABELS[actor?.role] ?? null; }
function stageHumanMessagePreview(actor, rawText) {
  const role=humanRoleLabel(actor);
  const message=typeof rawText==='string' ? rawText.trim() : '';
  if(!role || typeof actor?.id!=='string' || !actor.id ||
     typeof actor.name!=='string' || !actor.name.trim() ||
     /[\r\n:]/.test(actor.name) || !message || message.length>500)return null;
  return Object.freeze({
    rawText,
    previewBody:`${role} ${actor.name.trim()}:\n${message}`,
    authorId:actor.id, roleLabel:role
  });
}
function clearComposerContext() {
  // Falha fechada: texto digitado nunca atravessa caso, pessoa ou loja.
  communication.reset();
  $('message-input').value='';
  $('message-preview-body').textContent='';
  state.dialogContext.message=null;
  const dialog=$('message-preview-dialog');
  dialog.returnValue='';
  if(dialog.open)dialog.close();
}

/** Apenas fixture local: S0 fornecerá evidência de leitura e resposta humana.
 * Última mensagem de cliente após a última resposta humana => pendência demo.
 * Não calcular pendência real a partir do texto/tempo no browser.
 */
function demoAttentionFor(item) {
  return projectDemoAttention(item,state.actorId,state.shopId);
}
function acknowledgeDemoReadByAssignee(item) {
  const actor=getActor(state.actorId);
  const eligible=canStageReadAcknowledgment({
    role:actor?.role,acting_as_assigned_operator:actor?.role==='gestor' && item.assignedTo===actor?.id,
    account_active:actor?.teamState==='active',
    actor_id:state.actorId,assigned_actor_id:item.assignedTo,
    case_ref:item.id,case_version:'local-fixture-only'
  });
  if(eligible) {
    // No backend API: this is a purely local synthetic demonstration.
    item.unread=0;item.demoReadByAssigned=true;
    item.demoReadProjection={source:'local_fixture',actorId:state.actorId,caseId:item.id,shopId:item.shopId};
  }
}
function accessible() { return visibleConversations(state.cases, state.actorId, state.shopId); }
function filtered() {
  return projectQueue(state.cases, state.actorId, state.shopId, {
    query: state.query, filter: state.filter, status: state.statusFilter
  }).filter(record => state.inboxView === 'all' ? ['active','historical'].includes(record.inboxProjection) :
    state.inboxView === 'history' ? record.inboxProjection === 'historical' : isInActiveInbox(record))
    .filter(record => state.filter !== 'pending' || demoAttentionFor(record).kind === 'read_awaiting_reply')
    .sort((a,b) => Number(!isInActiveInbox(a))-Number(!isInActiveInbox(b)));
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
    hasProjectedAction(record,'complete') &&
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
  clearComposerContext();
  state.queueDialogContext=null;
  const queueDialog=$('queue-action-dialog');queueDialog.returnValue='';
  if(queueDialog.open)queueDialog.close();
  if(state.intakeDialogContext){state.intakeDialogContext=null;}
  const intake=$('intake-dialog');intake.returnValue='';
  if(intake.open)intake.close();
  for (const [kind,id] of [['completion','completion-dialog'],['template','template-dialog']]) {
    state.dialogContext[kind] = null;
    const dialog = $(id);
    dialog.returnValue = '';
    if (dialog.open) dialog.close();
  }
}
function showToast(message) {
  // FV-UI-050: avisos longos precisam de tempo de leitura; não mudam operações.
  const node = $('toast'); node.hidden = false; node.textContent = message;
  clearTimeout(showToast.timer);
  const readingTime = Math.min(9000, Math.max(5000, message.length * 70));
  showToast.timer = setTimeout(() => { node.hidden = true; }, readingTime);
}
function applyTheme(theme) {
  if(!['light','dark'].includes(theme)) return false;
  state.theme = theme;
  app.dataset.theme = theme;
  // Diálogos nativos ficam fora de #visual-app; acompanhar também no body.
  if(document.body) document.body.dataset.theme = theme;
  [['theme-light','light'],['theme-dark','dark']].forEach(([id,value]) => {
    const active = theme === value;
    $(id).classList.toggle('selected', active);
    $(id).setAttribute('aria-pressed', String(active));
  });
  return true;
}
systemColorScheme.addEventListener('change', event => {
  // Escolha manual prevalece durante a sessão e não grava dados fora da página.
  if(!state.themeOverride) applyTheme(event.matches ? 'dark' : 'light');
});
function announceCurrentContext(detail=''){
  // Apenas identificadores visuais do cenário sintético, nunca dados D3/D4.
  const actor=getActor(state.actorId),shop=getShop(state.shopId);
  const actorLabel=humanRoleLabel(actor)??'Perfil indisponível';
  const context=[actorLabel+' fictício',shop?'Concessionária '+shop.name:'Concessionária indisponível'];
  if(detail)context.push(detail);
  $('context-announcement').textContent=context.join(' · ');
}
function goto(view) {
  if (view !== 'thread' && window.matchMedia('(max-width:760px)').matches)
    communication.reset();
  state.mobileView = view;
  app.dataset.mobileView = view;
  // FV-UI-028: o estado acessível acompanha o painel móvel de fato visível.
  // No desktop, aria-expanded permanece sob controle da abertura do painel lateral.
  if(window.matchMedia('(max-width:760px)').matches)
    setDetailsExpanded(view==='detail');
  if (view === 'thread') $('message-input').blur();
}
function updateSelectors() {
  const actor = getActor(state.actorId);
  const actorSelect = $('actor-select');
  actorSelect.replaceChildren(...ACTORS.map(a => {
    const o = el('option', '', `${a.name} · ${humanRoleLabel(a)??'Perfil não reconhecido'} da Prumo`);
    o.value = a.id; return o;
  }));
  actorSelect.value = state.actorId;
  const showTeam=actor.role==='gestor' && actor.teamState==='active';
  $('team-nav-mobile').hidden=!showTeam;
  $('team-nav').hidden=!showTeam;
  const shopSelect = $('shop-select');
  shopSelect.replaceChildren(...visibleMockShops(state.cases,state.actorId).map(id => {
    const shop = getShop(id);
    const context=actor.shops.includes(id)?'fictícia':'somente caso excepcional · fictício';
    const o = el('option', '', `${shop.name} · ${context}`); o.value = id; return o;
  }));
  shopSelect.value = state.shopId;
  $('commercial-filter').hidden = actor.role !== 'gestor';
  document.querySelectorAll('[data-filter]').forEach(button => {
    if(button.dataset.filter==='mine') button.hidden=actor.role!=='gestor';
  });
  const statusSelect = $('status-filter');
  statusSelect.replaceChildren(el('option','', 'Todos os estados comerciais'),
    ...COMMERCIAL_STATUSES.map(status => { const opt=el('option','',status);opt.value=status;return opt;}));
  statusSelect.options[0].value='all';statusSelect.value=state.statusFilter;
}
// FV-UI-054: redefinir só refinamentos, sem mudar perfil, loja ou aba.
function resetListRefinements() {
  state.query='';state.filter='all';state.statusFilter='all';
  $('search-input').value='';$('status-filter').value='all';
  renderList();$('search-input').focus();
}
function renderList() {
  list.setAttribute('aria-busy',String(state.listLoading));
  if(state.listLoading){
    const loading=el('p','no-results','Carregando conversas…');loading.setAttribute('role','status');
    list.replaceChildren(loading);$('list-count').textContent='Carregando';return;
  }
  const items = filtered();
  const listProjection = state.inboxView === 'all' ? accessible().filter(record=>['active','historical'].includes(record.inboxProjection)) : projectInbox(state.cases,state.actorId,state.shopId,state.inboxView);
  const total = listProjection.length;
  // FV-UI-052: anunciar quantidades quando existirem resultados; evitar
  // anúncio duplo de zero, já explicado por .no-results[role=status].
  // FV-UI-055: evitar duas ações idênticas quando o aviso vazio já oferece a limpeza.
  const hasRefinements = Boolean(state.query.trim() || state.filter!=='all' || state.statusFilter!=='all');
  const emptyHasReset = items.length===0 && total>0 && hasRefinements && getActor(state.actorId).teamState==='active';
  $('filter-reset-controls').hidden=!hasRefinements || emptyHasReset;
  const listCount = $('list-count');
  listCount.setAttribute('aria-live',items.length===0?'off':'polite');
  // FV-UI-049: o contador indica resultados visíveis sem perder o total desta aba.
  listCount.textContent = items.length !== total ? `${items.length} de ${total} atendimentos` : `${total} ${total === 1 ? 'atendimento' : 'atendimentos'}`;
  const currentActor = getActor(state.actorId);
  const placementLabel={all:'Todas',active:'Ativos',history:'Históricos'}[state.inboxView];
  const attentionLabel={all:'',unread:'Não lidas',pending:'Lidas sem resposta humana',mine:'Atribuídas a mim'}[state.filter];
  $('filter-summary').textContent=[placementLabel,attentionLabel,state.statusFilter!=='all'?state.statusFilter:''].filter(Boolean).join(' · ');
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
  const nodes = items.map(item => {
    const card = el('button', 'conversation-card' + (item.id === state.selectedId ? ' is-selected' : ''));
    card.type = 'button'; card.setAttribute('aria-pressed', String(item.id === state.selectedId));
    const attention=demoAttentionFor(item);
    const shopName=getShop(item.shopId)?.name ?? 'Concessionária indisponível';
    card.setAttribute('aria-label', `Abrir conversa ${item.name}, ${shopName}, ${item.status}, ${attention.label??'sem pendência indicada'}`);
    const center = el('div','item-center');
    const latest=latestConfirmedDemoMessage(item,state.actorId,state.shopId);
    // Time follows the confirmed message, never a local draft.
    const row = el('div','item-title-row');
    row.append(el('span','item-title',item.name),el('span','item-time',latest?.time ?? '—'));
    const foot = el('div', 'item-foot');
    foot.append(el('span','item-preview',latest?.body ?? 'Sem mensagem confirmada'));
    const shopLabel=el('span','item-shop',shopName);
    shopLabel.setAttribute('title',shopName);shopLabel.setAttribute('aria-label','Concessionária '+shopName);
    foot.append(shopLabel);
    if(projectedMetaWindow(item)==='expired') foot.append(el('span','window-mini','Janela expirada'));
    if(attention.kind!=='none'){
      const badge=el('span',attention.kind==='unread'?'unread attention-unread':'unread attention-pending',
        attention.kind==='unread'?attention.count:'');
      badge.setAttribute('role','img');
      badge.setAttribute('aria-label',attention.label);
      badge.setAttribute('title',attention.label);
      foot.append(badge);
    }
    center.append(row,foot);
    card.append(center);
    card.addEventListener('click', () => {
      closeTransientDialogs();state.selectedId = item.id; acknowledgeDemoReadByAssignee(item);state.detailTab='overview';
      goto('thread'); render();
      announceCurrentContext('Caso '+item.id+' aberto na demonstração');
      if(window.matchMedia('(max-width:760px)').matches)$('thread-back').focus();
    });
    return card;
  });
  if (!nodes.length) {
    // FV-UI-049: distinguir busca, filtros, aba vazia e suspensão sem alterar o escopo.
    const box = el('div','no-results');
    box.setAttribute('role','status');
    box.setAttribute('aria-live','polite');
    const suspended = currentActor.teamState !== 'active';
    const searching = Boolean(state.query.trim());
    const refined = searching || state.filter !== 'all' || state.statusFilter !== 'all';
    let heading, hint;
    if (suspended) {
      heading='Sem acesso demonstrativo';
      hint='Profissional suspenso na fixture. Acesso real pertence ao S0/S1-002.';
    } else if (total === 0) {
      heading='Nenhum atendimento nesta lista';
      hint='Altere Todos, Ativos ou Históricos no controle Filtrar conversas.';
    } else if (searching) {
      heading='Nenhuma conversa corresponde à busca';
      hint='Tente outro termo ou limpe a busca e os filtros desta lista.';
    } else if (refined) {
      heading='Nenhum atendimento com estes filtros';
      hint='Altere os filtros ou limpe a seleção atual para visualizar as conversas.';
    } else {
      heading='Nenhuma conversa disponível';
      hint='Não há conversas correspondentes nesta demonstração.';
    }
    box.append(el('strong','',heading),el('span','no-results-hint',hint));
    if (!suspended && total > 0 && refined) {
      const clear = el('button','btn btn-light empty-reset','Limpar busca e filtros');
      clear.type='button';
      clear.addEventListener('click',resetListRefinements);
      box.append(clear);
    }
    list.replaceChildren(box);
  } else list.replaceChildren(...nodes);
  document.querySelectorAll('[data-filter]').forEach(btn => {
    const active = btn.dataset.filter === state.filter;
    btn.classList.toggle('selected', active);
    btn.setAttribute('aria-pressed', String(active));
  });
}
function renderThread() {
  // Revalida também em rerenders de conclusão, perda de elegibilidade e troca de contexto.
  communication.sync();
  const item = selectedCase();
  $('thread-title').textContent = item?.name ?? 'Selecione uma conversa';
  $('thread-meta').textContent = item ? `${getShop(item.shopId).name} · Caso ${item.id}` : 'Nenhum atendimento selecionado';
  const body = $('thread-body'); const bar = $('workflow-bar');
  const followups=$('followup-actions');followups.replaceChildren();followups.hidden=true;
  $('thread-bottom').hidden=false;
  const actions=$('thread-actions');actions.replaceChildren();
  $('thread-title').disabled=!item;
  const terminal=$('terminal-banner');
  terminal.hidden=!(item?.inboxProjection==='historical' && ['vendido','perdido'].includes(item.status));
  terminal.textContent=terminal.hidden?'':(item.status==='vendido'?'✓ Vendido':'× Perdido')+' · Caso histórico · somente leitura';
  terminal.dataset.outcome=terminal.hidden?'':item.status;
  const input = $('message-input'); const button = document.querySelector('.send-button');
  const composeAllowed=Boolean(item && canMockMessage(item));
  $('composer').hidden=!composeAllowed;
  $('communication-tools').hidden=!composeAllowed;
  $('composer-demo-guidance').hidden=!terminal.hidden;
  if (!item) {
    const empty = el('div','thread-placeholder');
    empty.append(el('h2','', 'Sua central de conversas'),el('p','', 'Selecione um atendimento na lista. Apenas dados fictícios serão exibidos.'));
    body.replaceChildren(empty); bar.replaceChildren(); input.disabled = true; button.disabled = true;
    $('composer-availability').hidden = true;
    $('detail-toggle').disabled = true; return;
  }
  $('detail-toggle').disabled = false;
  const isExceptional=hasMockCaseOnlyScope(item,state.actorId,state.shopId);
  const children = [el('span','day-separator','Demonstração · dados fictícios')];
  for (const m of item.messages) {
    const bubble = el('div', 'message ' + m.side);
    bubble.append(el('p','', m.body), el('small','',m.time));
    if (m.localAudioId) {
      const clip = communication.getClip(m.localAudioId);
      if (clip) {
        const player = el('audio','local-audio-message');
        player.dataset.localAudioId = m.localAudioId;
        player.controls = true; player.preload = 'metadata'; player.src = clip.url;
        player.setAttribute('aria-label','Ouvir áudio local, não enviado');
        player.addEventListener('error',()=>showToast('Não foi possível reproduzir este áudio local.'));
        bubble.append(player);
      } else bubble.append(el('small','', 'Prévia de áudio descartada ao sair do contexto.'));
    }
    if(m.deliveryState==='local_demo_not_sent') {
      bubble.append(el('small','message-send-state','Somente simulação · NÃO ENVIADA'));
    } else if(m.side==='out') {
      const transport=stageMockMessageTransport(item,m,state.actorId,state.shopId);
      if(transport.visibility==='synthetic'){
        const label=el('small','message-transport-state',transport.label+' · SIMULAÇÃO');
        label.setAttribute('aria-label','Transporte ilustrativo: '+transport.label);
        bubble.append(label);
        if(transport.state==='uncertain' || transport.state==='api_accepted')
          bubble.append(el('small','message-transport-hint',
            'Sem prova de envio. Não tentar reenvio automático pelo navegador.'));
      }
    }
    children.push(bubble);
  }
  body.replaceChildren(...children);
  // Rolar somente depois de renderizar; não dispara solicitações externas.
  body.scrollTop = body.scrollHeight;
  bar.replaceChildren();
  if(isExceptional)bar.append(el('span','status-indicator',
    'Acesso excepcional: SOMENTE este caso · projeção fictícia'));
  const meta=projectedMetaWindow(item);
  const completionState = humanCompletion(item,Boolean(state.processing[item.id]));
  if(item.reviewSceneVersion)bar.append(el('span','status-indicator',
    'Esclarecimento · CENÁRIO ALTERNATIVO fictício, não reaberto no S0'));
  if(completionState==='unknown') bar.append(el('span','status-indicator','Etapa humana não confirmada'));
  if(item.reassignmentProjection==='protected_queue') bar.append(el('span','status-indicator','Fila protegida · sem responsável elegível'));
  if (canMockClose(item)) {
    const close = el('button', 'btn btn-primary', 'Concluir atendimento');
    close.type = 'button'; close.id='request-completion';
    close.addEventListener('click', () => {
      if(!canMockClose(selectedCase()))return;
      captureDialogContext('completion');
      const dialog=$('completion-dialog');dialog.returnValue='';dialog.showModal();
    });
    actions.append(close);
  } else if (state.processing[item.id]) {
    const label = state.processing[item.id].kind === 'accepted' ? 'Solicitação simulada' : 'Resultado fictício';
    bar.append(el('span','status-indicator human',label));
  }
  const fActions=postmarkContextValid(item) ? projectedFollowupActions(item,state.actorId,state.shopId,Boolean(state.processing[item.id])) : [];
  const pendingLocal=state.followupRequests[item.id];
  if(fActions.includes('single_template') && !pendingLocal){
    const btn=el('button','btn btn-light','Enviar template');btn.type='button';
    btn.addEventListener('click',()=>{
      const current=selectedCase();
      if(!current || current.id!==item.id || !postmarkContextValid(current) ||
        !projectedFollowupActions(current,state.actorId,state.shopId).includes('single_template'))return;
      const eligible=DEMO_TEMPLATES.filter(t=>hasEligibleTemplateVersion(current,t));
      if(!eligible.length){showToast('Nenhum template elegível neste caso fictício.');return;}
      $('template-select').replaceChildren(...eligible.map(template=>{
        const option=el('option','',template.title+' · '+template.version+' (fictício)');
        option.value=template.id;return option;
      }));
      captureDialogContext('template');
      const dialog=$('template-dialog');dialog.returnValue='';dialog.showModal();
    });
    followups.append(btn);
  }
  if(fActions.includes('request_chain') && !pendingLocal){
    const btn=el('button','btn btn-light','Cadeia por IA');btn.type='button';
    btn.addEventListener('click',()=>{
      if(selectedCase()?.id!==item.id || !postmarkContextValid(item))return;
      try {state.followupRequests[item.id]=applyLocalFollowupRequest(item,state.actorId,state.shopId,'request_chain');
        state.detailTab='activity';render();showToast('Solicitação fictícia de cadeia. Não há plano persistido nem envio.');}
      catch(error){showToast('Operação não disponível neste cenário.');}
    });followups.append(btn);
  }
  if(pendingLocal) bar.append(el('span','status-indicator','Pedido simulado · não enviado'));
  followups.hidden=followups.children.length===0;
  $('thread-bottom').hidden=!terminal.hidden && bar.children.length===0;
  input.disabled = !composeAllowed;
  button.disabled = !composeAllowed;
  const availability = $('composer-availability');
  availability.hidden = composeAllowed || !terminal.hidden;
  availability.textContent = composeAllowed ? '' : meta==='expired' ?
    'Janela de conversa encerrada'+(fActions.length && !pendingLocal ? ' · ações demonstrativas' : ' · envio indisponível no momento') : 'Envio indisponível no momento';
  input.placeholder = composeAllowed ? 'Escrever mensagem…' : 'Composição indisponível';
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
/** FV-UI-032: não devolver foco a um controle descartado no re-render.
 * A operação é local; só orientar o foco no mesmo caso com painel visível.
 */
function focusExtractionAfterRerender(caseId,notice){
  if(bankSelectedCase()?.id!==caseId || !$('bank-dialog').open)return;
  $('bank-case-select').focus();
  announceCurrentContext(notice);
}
function noteDraftKey(item){return state.actorId+'|'+state.shopId+'|'+item.id;}
function caseForBank(id){
  const base=accessible().find(row=>row.id===id);
  const review=base && state.reviewScenes[base.id];
  return review && review.shopId===base.shopId && review.assignedTo===base.assignedTo ? review : base;
}
function bankSelectedCase(){return caseForBank(state.bankCaseId);}
let bankOpener='bank-nav';
function openBank(caseId=null,opener=null){
  const rows=accessible();
  state.bankCaseId=rows.some(row=>row.id===caseId)?caseId:
    rows.some(row=>row.id===state.bankCaseId)?state.bankCaseId:
    rows.some(row=>row.id===state.selectedId)?state.selectedId:rows[0]?.id??null;
  bankOpener=opener ?? (window.matchMedia('(max-width:760px)').matches?'bank-nav-mobile':'bank-nav');
  communication.reset();
  renderBank();
  if(!$('bank-dialog').open)$('bank-dialog').showModal();
  $('bank-case-select').focus();
}
function renderBank(){
  const select=$('bank-case-select');
  select.replaceChildren(...accessible().map(row=>{const option=el('option','',row.name+' · '+row.id+' · '+getShop(row.shopId).name);option.value=row.id;return option;}));
  select.value=state.bankCaseId??'';
  const target=$('bank-content'),item=bankSelectedCase();
  if(!item){target.replaceChildren(el('p','detail-placeholder','Nenhuma ficha autorizada neste contexto.'));return;}
  const identity=el('p','bank-context',item.name+' · caso '+item.id+' · '+getShop(item.shopId).name);
  const consultation=renderRegistration(item);
  const banking=renderBankStatus(item);
  target.replaceChildren(identity,consultation,banking);
}
function renderAiCommunications(item){
  const section=detailSection('COMUNICAÇÕES DAS IAs');section.id='ai-communications';
  section.append(el('p','detail-small','Histórico acumulativo fictício. Resultados da F03 não são mensagens ao cliente.'));
  const entries=aiCommunicationsFor(item,state.cases,state.actorId,state.shopId);
  for(const entry of entries){
    const details=el('details','ai-communication');details.dataset.source=entry.source;
    details.append(el('summary','',entry.source+' · '+entry.time),el('p','',entry.content));
    section.append(details);
  }
  if(!entries.length)section.append(el('p','detail-small','Nenhuma comunicação autorizada disponível.'));
  if(state.processing[item.id]){
    const feedback=projectDemoOperationFeedback(state.processing[item.id].kind);
    section.append(callout(feedback.title,feedback.description,'warning'));
  }
  const bank=el('button','btn btn-light','Consultar ficha e processamento em Banco');bank.type='button';bank.id='open-bank-case';
  bank.addEventListener('click',()=>openBank(item.id,'open-bank-case'));section.append(bank);
  return section;
}
function renderOperationalHistory(item){
  const activity=detailSection('HISTÓRICO OPERACIONAL · DADOS FICTÍCIOS');activity.id='relationship-history';
  const view=operationalHistoryFor(item,state.cases,state.actorId,state.shopId,state.processing[item.id],state.followupRequests[item.id]);
  const completed=el('div','timeline-events');completed.setAttribute('aria-label','Acontecimentos e estados técnicos');
  const addEntry=(entry,container,future=false)=>{
    const card=el('div','activity-item'+(future?' future-event':'')+' event-'+entry.state);
    card.dataset.state=entry.state;card.dataset.kind=entry.kind;
    card.append(el('strong','',entry.label),el('span','event-state',entry.statusLabel),el('span','',entry.time));container.append(card);
  };
  for(const entry of view.events)addEntry(entry,completed);
  if(!view.events.length)completed.append(el('p','detail-small','Nenhum acontecimento autorizado informado.'));
  activity.append(completed);
  if(item.postmarkProjection)activity.append(renderContinuity(item));
  if(view.future.length){
    const future=el('section','timeline-future');future.id='future-attempts';
    future.setAttribute('aria-label','Tentativas futuras planejadas, ainda não realizadas');
    future.append(el('h3','detail-label','PLANEJAMENTO F02 · AINDA NÃO REALIZADO'));
    for(const entry of view.future)addEntry(entry,future,true);
    activity.append(future);
  }
  if(item.followupProjection || state.followupRequests[item.id])activity.append(renderFollowupSummary(item));
  activity.append(el('p','detail-small','Somente projeções fictícias. A linha de acontecimentos não se prolonga sobre o planejamento futuro.'));
  return activity;
}
function renderDetails() {
  const target=$('detail-content');const item=selectedCase();
  if(!item){target.replaceChildren(el('p','detail-placeholder','Selecione uma conversa para ver informações do caso.'));return;}
  const context=el('p','case-context','Caso '+item.id+' · '+item.status+' · fictício');
  const tabs=el('div','detail-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Detalhes do caso fictício');
  for(const tab of DETAIL_TABS){
    const button=el('button','detail-tab'+(state.detailTab===tab.id?' active':''),tab.title);
    button.type='button';button.id='case-tab-'+tab.id;
    button.setAttribute('role','tab');button.setAttribute('aria-selected',String(state.detailTab===tab.id));
    button.setAttribute('aria-controls','case-tab-panel');
    button.setAttribute('tabindex',state.detailTab===tab.id?'0':'-1');
    button.addEventListener('click',()=>{state.detailTab=tab.id;renderDetails();
      target.querySelector('.detail-tab.active')?.focus();});
    button.addEventListener('keydown',e=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
      e.preventDefault();
      const i=DETAIL_TABS.findIndex(x=>x.id===tab.id);
      const next=e.key==='Home'?0:e.key==='End'?DETAIL_TABS.length-1:
        (i+(e.key==='ArrowRight'?1:DETAIL_TABS.length-1))%DETAIL_TABS.length;
      state.detailTab=DETAIL_TABS[next].id;
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
    if(item.reassignmentProjection==='protected_queue') group.append(callout('Acesso operacional protegido','A S1-002 decidirá o remanejamento real; não há escolha de Consultor pelo frontend.','warning'));
    if(isSyntheticBankProtected(item)) group.append(callout('Marco bancário protegido','Silêncio de cliente ou janela Meta expirada não representa negativa da instituição financeira.','warning'));
    group.append(prop('Caso fictício',item.id));
    content.append(group,renderAiCommunications(item));
  } else if(state.detailTab==='activity'){
    content.append(renderOperationalHistory(item));
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
      textarea.value=state.noteDrafts[noteDraftKey(item)]??'';
      textarea.addEventListener('input',()=>{state.noteDrafts[noteDraftKey(item)]=textarea.value;});
      const add=el('button','btn btn-primary','Adicionar nota');add.type='submit';
      form.append(label,textarea,add);
      form.addEventListener('submit',e=>{e.preventDefault();const text=textarea.value.trim();
        if(!text || selectedCase()?.id!==item.id || !postmarkContextValid(item) || !canWriteNote(item,state.actorId,state.shopId) || !isInActiveInbox(item))return;
        delete state.noteDrafts[noteDraftKey(item)];
        item.notes??=[];item.notes.push({id:'n-'+(item.notes.length+1),text,actorId:state.actorId,time:'Agora · fictício'});
        // FV-UI-031: o formulário anterior deixa o DOM; devolver foco ao novo campo
        // somente após gravação demonstrativa elegível no mesmo caso.
        renderDetails();target.querySelector('#note-text')?.focus();
        showToast('Nota adicionada somente à memória do navegador.');
      });notes.append(form);
    }else notes.append(el('p','detail-small','Adição de nota não disponível neste perfil ou caso de demonstração.'));
    content.append(notes);
  }
  // FV-UI-051: o alcance fictício também é explícito no painel de detalhes.
  const guidance=el('p','detail-small detail-demo-guidance','Dados fictícios. Este painel não executa operações externas.');
  guidance.id='case-demo-guidance';guidance.setAttribute('role','note');
  content.setAttribute('aria-describedby','case-demo-guidance');content.append(guidance);
  target.replaceChildren(context,tabs,content);
}

function renderRegistration(item){
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
      const scenario=projectDemoOperationFeedback(proc.kind);
      extract.append(callout(scenario.title,scenario.description,'warning'));
      extract.append(el('p','detail-small',scenario.nextStep));
      extract.append(el('p','detail-small',
        'Nenhum efeito técnico/comercial foi confirmado: não há correção manual ou retentativa automática nesta demonstração.'));
      if(proc.kind==='partial'){
        const example=el('div','detail-row');example.append(el('strong','','Campo ilustrativo A'),el('span','','Proposta sintética · não persistida'));
        const missing=el('div','detail-row');missing.append(el('strong','','Campo ilustrativo B'),el('span','','Sem fonte suficiente · pendente'));
        extract.append(example,missing);
      }
      if(canSimulateCompletion(item,state.actorId,state.shopId) && state.processing[item.id] && humanCompletion(item)==='pending'){
        const actions=el('div','scenario-options');
        for(const [kind,label] of [
          ['partial','Retorno parcial'],['failed','Falha técnica'],
          ['stale','Versão obsoleta'],['uncertain','Confirmação incerta'],
          ['denied','Permissão negada'],['unavailable','Serviço indisponível']
        ]){
          const button=el('button','btn btn-light',label);button.type='button';
          button.addEventListener('click',()=>{if(!canSimulateCompletion(bankSelectedCase(),state.actorId,state.shopId))return;
            if(bankSelectedCase()?.id!==item.id)return;
            state.processing[item.id]={...state.processing[item.id],kind};render();renderBank();
            focusExtractionAfterRerender(item.id,'Resultado técnico fictício '+label+' do caso '+item.id);
            showToast(projectDemoOperationFeedback(kind).title+'. Nenhuma API foi chamada.');});actions.append(button);
        }extract.append(actions);
      }
    }
    // Linha do tempo CONFIRMADA apenas na fixture, não inferida do estado atual.
    const cycles=projectMockHumanCycleHistory(item,state.actorId,state.shopId);
    if(cycles.visibility==='detail' && cycles.events.length){
      const history=detailSection('CONCLUSÕES E EXECUÇÕES F03 · FICTÍCIAS');
      for(const event of cycles.events){
        const line=el('div','detail-row');
        line.append(el('strong','',event.completionId+' · '+event.requestId),
          el('span','','Cutoff selado na fixture: '+event.cutoffMessageRef+
            ' · versão '+event.cutoffVersionRef+' · resultado '+event.resultVersionRef));
        history.append(line);
      }
      extract.append(history);
    }
    const dossier=projectMockCustomerDossier(item,state.actorId,state.shopId);
    if(dossier.visibility==='detail'){
      const versioned=detailSection('FICHA VIVA POR CLIENTE E CONCESSIONÁRIA');
      versioned.append(prop('Concessionária da ficha',getShop(item.shopId).name),
        prop('Versão atual confirmada no cenário',dossier.liveFormVersionRef));
      for(const entry of dossier.formHistory){
        versioned.append(el('div','detail-row',
          'Versão preservada: '+entry.versionRef+' · corte '+entry.cutoffRef));
      }
      if(dossier.bankSnapshots.length){
        const banking=detailSection('REMESSAS ANTERIORES · SNAPSHOTS IMUTÁVEIS');
        for(const snap of dossier.bankSnapshots){
          banking.append(el('div','detail-row',
            'Caso '+snap.submissionCaseRef+' · remessa '+snap.bankSubmissionVersionRef+
            ' · snapshot preservado (somente fixture)'));
        }
        versioned.append(banking);
      }else versioned.append(el('p','detail-small','Nenhuma remessa bancária vinculada nesta projeção.'));
      versioned.append(el('p','detail-small',
        'Identidade e vínculos já vêm projetados da mesma loja: navegador não associa clientes por CPF, telefone ou nome.'));
      extract.append(versioned);
    }
    if(item.reviewSceneVersion){
      extract.append(callout('Esclarecimento em cenário alternativo',
        'O S0 fictício autorizou este retrato da conversa. A ficha anterior continua intacta e nenhuma IA foi acionada.'));
    }else{
      const alternate=projectMockClarificationScene(item,state.actorId,state.shopId);
      if(alternate && !state.processing[item.id]){
        extract.append(callout('Lacuna para esclarecer com o cliente',
          'Somente o titular pode visualizar o retorno fictício. Não há editor cadastral ou campanha F02 automática.','warning'));
        const button=el('button','btn btn-light','Visualizar retorno fictício de esclarecimento');
        button.type='button';button.id='show-clarification-demo';
        button.addEventListener('click',()=>{
          const current=bankSelectedCase();
          if(!current || current.id!==item.id || state.reviewScenes[item.id])return;
          const candidate=projectMockClarificationScene(current,state.actorId,state.shopId);
          if(!candidate)return;
          closeTransientDialogs();
          state.reviewScenes[item.id]=candidate;
          renderBank();render();
          focusExtractionAfterRerender(item.id,'Cenário de esclarecimento fictício do caso '+item.id);
          showToast('Cenário alternativo exibido; NÃO houve reabertura S0 nem extração F03.');
        });
        extract.append(button);
      }
    }
    if(proc && proc.candidateCutoffRef){
      extract.append(callout('Segunda solicitação · corte apenas candidato',
        'Pedido local '+proc.requestId+' · referência '+proc.candidateCutoffRef+
        '. Não é evento S0 confirmado, nem execução/persistência F03.','warning'));
    }
    extract.append(el('p','detail-small','Ficha somente leitura. Nenhum Consultor corrige campos; somente S0 pode validar e persistir propostas F03.'));
    return extract;
}
function renderBankStatus(item){
    const bank=detailSection('REMESSA E RETORNO BANCÁRIO · O4');
    const projection=bankProjectionFor(item,state.actorId,state.shopId);
    const copy=bankPhaseCopy(projection);
    bank.append(callout(copy.title,copy.description,
      projection.submissionConfirmed?'':'warning'));
    bank.append(prop('Estado comercial (somente leitura)',item.status));
    const readyConfirmed=bankReadinessFor(item,state.cases,state.actorId,state.shopId);
    bank.append(prop('Aptidão para remessa',readyConfirmed?'Confirmada apenas na fixture · sem remessa iniciada':'Não confirmada nesta projeção'));
    bank.append(prop('Preparação / solicitação',projection.phase==='submission_requested'?
      'Solicitação projetada · não comprova remessa':'Sem preparação ou solicitação confirmada'));
    bank.append(el('p','detail-small','Integração pendente: nenhuma ação de remessa é habilitada sem capacidade e contrato ratificados.'));

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
    return bank;
}
function renderContinuity(item){
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
          $('search-input').value='';state.selectedId=target.id;state.detailTab='activity';
          goto('thread');updateSelectors();render();
          // FV-UI-032: o botão de vínculo saiu do DOM; focar o caso de destino.
          if(window.matchMedia('(max-width:760px)').matches)$('thread-back').focus();
          else $('thread-pane').focus();
          announceCurrentContext('Caso '+target.id+' aberto por vínculo fictício autorizado');
        });
        contact.append(open);
      }
    }else{
      contact.append(el('p','detail-small',
        'Nenhum ciclo é criado por esta tela. Vínculo ausente, divergente ou fora do escopo não concede acesso nem revela outro atendimento.'));
    }
    contact.append(el('p','detail-small',
      'Somente navegação sobre casos fictícios já projetados. A S0 decide criação, roteamento, versão, permissão e histórico. Não existe comando C14 nem reativação da IA Vendedora neste browser.'));
    return contact;
}
function renderFollowupSummary(item){
    const followup=detailSection('RECONTATOS CONTEXTUAIS · CF-OP-02');
    const local=state.followupRequests[item.id]??null;
    const projection=projectedFollowupState(item,local);
    followup.append(callout('Janela, conclusão e resultado são independentes',
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
      followup.append(prop('Template final efetivamente enviado',projection.finalSentConfirmed?'Confirmado apenas no cenário fictício':'Não confirmado'));
      followup.append(prop('Silêncio pós-final',projection.silenceResolution==='confirmed_eligible'?
        'Perda já representada pelo S0 fictício': 'Prazo não iniciado/sem decisão'));
    }
    if(isSyntheticBankProtected(item)) followup.append(callout('Sem perda por silêncio bancário','Remessa ao banco e vendido não são estados elegíveis para perda automática C09.','warning'));
    followup.append(el('p','detail-small','Não há templates reais, relógio local de 24h, chamada OpenAI nem envio WhatsApp. Fonte futura: projeções autorizadas pelo S0.'));
    return followup;
}

function render(){renderList();renderThread();renderDetails();app.dataset.mobileView=state.mobileView;}
function changeActor(actorId){
  const actor=getActor(actorId);if(!actor)return;
  closeTransientDialogs();
  state.listLoading=false;$('demo-list-state').value='ready';
  if($('team-dialog').open)$('team-dialog').close();
  // Não deixar carteira do gestor anterior, nem mesmo oculta no DOM da demo.
  $('team-list').replaceChildren();$('team-monitor').replaceChildren();$('team-batches').replaceChildren();$('team-queue').replaceChildren();
  // FVA-02: pedido local de template/cadeia nunca atravessa perfil fictício.
  state.teamRequests={};state.queueRequests={};state.followupRequests={};state.reviewScenes={};state.processing={};state.teamPanel='members';
  state.noteDrafts={};state.bankCaseId=null;
  if($('bank-dialog').open)$('bank-dialog').close();$('bank-content').replaceChildren();$('bank-case-select').replaceChildren();
  state.actorId=actor.id;state.shopId=actor.shops[0];state.selectedId=null;state.detailTab='overview';state.statusFilter='all';state.inboxView='all';
  state.filter='all';state.query='';$('search-input').value='';goto('list');updateSelectors();render();announceCurrentContext('Perfil alterado');
}
$('actor-select').addEventListener('change',event=>changeActor(event.target.value));
$('shop-select').addEventListener('change',event=>{
  const actor=getActor(state.actorId);
  if(!visibleMockShops(state.cases,state.actorId).includes(event.target.value))return;
  state.listLoading=false;$('demo-list-state').value='ready';
  closeTransientDialogs();
  // FVA-02: solicitação ainda não confirmada por serviço pertence à loja anterior.
  state.noteDrafts={};state.bankCaseId=null;if($('bank-dialog').open)$('bank-dialog').close();$('bank-content').replaceChildren();$('bank-case-select').replaceChildren();
  state.queueRequests={};state.followupRequests={};state.reviewScenes={};state.shopId=event.target.value;state.selectedId=null;state.detailTab='overview';state.statusFilter='all';state.inboxView='all';$('status-filter').value='all';state.query='';$('search-input').value='';goto('list');render();announceCurrentContext('Concessionária alterada');
});
$('search-input').addEventListener('input',event=>{state.query=event.target.value;renderList();});
$('clear-list-filters').addEventListener('click',resetListRefinements);
$('status-filter').addEventListener('change',event=>{state.statusFilter=event.target.value;renderList();});
document.querySelectorAll('[data-inbox]').forEach(button=>button.addEventListener('click',()=>{
 closeTransientDialogs();state.inboxView=button.dataset.inbox;state.selectedId=null;goto('list');render();
 announceCurrentContext({all:'Todos os atendimentos',active:'Atendimentos ativos',history:'Histórico'}[state.inboxView]);
}));
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{state.filter=button.dataset.filter;renderList();}));
/** Mesmo retorno por botão e por Escape: não deixar foco em painel oculto.
 * Apenas navegação; não altera caso, leitura, autorização ou ações.
 */
function mobileBackNavigation(){
  if(!window.matchMedia('(max-width:760px)').matches)return false;
  if(state.mobileView==='detail'){
    return closeFloatingDetails();
  }
  if(state.mobileView==='thread'){
    goto('list');$('search-input').focus();return true;
  }
  return false;
}
$('thread-back').addEventListener('click',()=>{mobileBackNavigation();});
$('detail-back').addEventListener('click',()=>{mobileBackNavigation();});
$('theme-light').addEventListener('click',()=>{state.themeOverride=true;applyTheme('light');});
$('theme-dark').addEventListener('click',()=>{state.themeOverride=true;applyTheme('dark');});
// Fechamento de configurações por teclado e clique fora, sem roubar foco.
$('ui-settings').addEventListener('keydown',event=>{
  if(event.key==='Escape' && $('ui-settings').open){
    event.preventDefault();event.stopPropagation?.();$('ui-settings').open=false;
    $('ui-settings').querySelector('summary')?.focus();
  }
});
document.addEventListener('click',event=>{
  for(const id of ['ui-settings','list-extra'])
    if($(id).open && !$(id).contains(event.target))$(id).open=false;
});
document.addEventListener('focusin',event=>{
  if($('list-extra').open && !$('list-extra').contains(event.target))$('list-extra').open=false;
});
$('list-extra').addEventListener('keydown',event=>{
  if(event.key==='Escape' && $('list-extra').open){
    event.preventDefault();event.stopPropagation?.();$('list-extra').open=false;$('filter-toggle').focus();
  }
});
let detailOpener='detail-toggle';
function setDetailsExpanded(expanded){
  for(const id of ['detail-toggle','thread-title']) $(id).setAttribute('aria-expanded',String(expanded));
}
function openDetails(opener){
  if(!selectedCase())return;
  detailOpener=opener;
  app.classList.remove('details-hidden');
  const mobile=window.matchMedia('(max-width:760px)').matches;
  if(mobile)goto('detail');
  setDetailsExpanded(true);
  if(mobile)$('detail-back').focus();
  else $('detail-content').querySelector('.detail-tab.active')?.focus();
}
$('thread-title').addEventListener('click',()=>openDetails('thread-title'));
$('detail-toggle').addEventListener('click',()=>{
  const mobile=window.matchMedia('(max-width:760px)').matches;
  if(!mobile && !app.classList.contains('details-hidden')){detailOpener='detail-toggle';closeFloatingDetails();}
  else openDetails('detail-toggle');
});
/** Close is navigation only in every viewport. No render/reset/operation cancellation. */
function closeFloatingDetails(){
  if(document.querySelector('dialog[open]'))return false;
  const mobile=window.matchMedia('(max-width:760px)').matches;
  if(mobile ? state.mobileView!=='detail' : app.classList.contains('details-hidden'))return false;
  app.classList.add('details-hidden');
  if(mobile)goto('thread');
  setDetailsExpanded(false);
  $(detailOpener).focus();
  return true;
}
$('detail-close').addEventListener('click',()=>{closeFloatingDetails();});
$('demo-open').addEventListener('click',()=>{communication.reset();$('demo-dialog').showModal();});
$('demo-list-state').addEventListener('change',event=>{
  state.listLoading=event.target.value==='loading';renderList();
});
$('demo-close').addEventListener('click',()=>{$('demo-dialog').close();});
$('demo-dialog').addEventListener('close',()=>{$('demo-open').focus();});
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
    `Consultores supervisionados: ${view.summary.operatorCount} · Entrada de leads pausada: ${view.summary.intakePausedCount} · Conta indisponível: ${view.summary.intakeUnavailableCount} · Casos no histórico: ${view.summary.historicalCases} · Casos ativos autoatribuídos ao gestor: ${view.summary.managerOwnedCases}`);
  section.append(states);
  const stageHeader=el('h4','team-monitor-subheading','Etapas comerciais canônicas — casos ativos');
  section.append(stageHeader);
  const stageList=el('div','team-monitor-stages');
  for(const entry of view.commercialStages.filter(entry=>entry.count>0)){
    const line=el('div','team-monitor-stage');
    line.append(el('span','',entry.status),el('strong','',String(entry.count)));
    stageList.append(line);
  }
  if(!stageList.children.length)stageList.append(el('span','detail-small','Nenhum caso ativo nesta projeção.'));
  section.append(stageList);
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
    if(member.intake==='paused_confirmed') card.append(el('span','',
      'Pausa da entrada confirmada somente na fixture; redistribuição de casos NÃO comprovada.'));
    card.append(el('span','',`Concessionárias concedidas pelo Diretor (somente leitura): ${member.shops.map(id=>getShop(id)?.name??id).join(', ')}`));
    const preview=projectManagerPausePreview(state.actorId,member.id,state.cases);
    if(preview.visibility==='ready'){
      const details=el('details','team-pause-preview');
      details.append(el('summary','','Prévia da carteira durante pausa · '+preview.summary.total+' caso(s)'));
      const indicators=el('p','team-pause-counts',
        `Mantidos após contato: ${preview.summary.started} · Sem substituto: ${preview.summary.noRecipient} · Sem prova: ${preview.summary.unverified} · Ciclos protegidos: ${preview.summary.protected} · Candidatos à transferência: ${preview.summary.candidates}`);
      const rows=el('ul','team-pause-cases');
      for(const item of preview.cases){
        const line=el('li','',item.caseId+' · '+item.shopName+' · '+item.label);
        rows.append(line);
      }
      details.append(indicators,rows,el('p','team-hint',
        'Somente prévia fictícia. Nenhuma atribuição, conta ou concessão é alterada.'));
      card.append(details);
    }
    const requested=state.teamRequests[member.id];
    if(requested){
      card.append(el('span','',`SOLICITADO LOCALMENTE: ${requested.action==='pause'?'pausar novos leads':'retomar novos leads'} em todas as lojas concedidas. NÃO aplicado; redistribuição NÃO executada.`));
    }else if(member.teamState==='active' && ['receiving','paused_confirmed'].includes(member.intake)){
      const action=member.intake==='receiving'?'pause':'resume';
      const button=el('button','btn btn-light',action==='pause'?'Solicitar pausa de novos leads':'Solicitar retomada de novos leads');
      button.type='button';button.setAttribute('aria-label',`${action==='pause'?'Solicitar pausa':'Solicitar retomada'} de novos leads para ${member.name}, todas as concessionárias concedidas`);
      button.addEventListener('click',()=>{
        if(state.teamRequests[member.id])return;
        // UI confirma a INTENÇÃO. Não aplica pausa nem move caso em JS.
        try {
          requestMockIntake(state.actorId,member.id,action);
          state.intakeDialogContext={actorId:state.actorId,operatorId:member.id,action};
          $('intake-dialog-title').textContent=action==='pause'?
            'Confirmar pausa de novos leads':'Confirmar retomada de novos leads';
          $('intake-dialog-copy').textContent=`${member.name} · todas as concessionárias concedidas. Sem bloquear conta ou alterar a carteira. Somente demonstração local.`;
          $('intake-dialog').returnValue='';
          $('intake-dialog').showModal();
        } catch {showToast('Ação indisponível para este Gestor e Consultor.');}
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
    ['Consultores da equipe',data.teamMembers],
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
  // Conciliação: preservar o quadro de oito etapas comerciais e indicadores
  // agregado G3, acrescentando sinais técnicos explícitos do S0 fictício.
  renderTeamMonitoring();
  // UX: indicadores e alertas primeiro; o quadro canônico/comercial continua
  // completo logo abaixo, sem multiplicar conteúdo ou alterar autorização.
  const commercialSummary=target.children[0];
  target.replaceChildren(title,note,indicators,workload,signals,
    el('p','team-hint','Sinais técnicos não são estados comerciais novos. '+
      'A S0 define prazos, prioridades, distribuição, permissões e confirmação de eventos.'),
    commercialSummary);
}
function renderTeamBatches(){
  const target=$('team-batches'),projection=projectManagerBatches(state.actorId);
  if(projection.visibility!=='ready'){
    target.replaceChildren(el('p','detail-small','Lotes indisponíveis para este perfil fictício.'));
    return;
  }
  const title=el('h3','detail-label','G4 · LOTES AUTORIZADOS DA PRÓPRIA EQUIPE');
  const note=el('p','team-hint',
    'Projeções fictícias por equipe e concessionária concedida. Não há importação, distribuição ou alteração de permissões. Consultores e lojas elegíveis são definidos pelo Diretor.');
  const totals=projection.totals,summary=el('div','team-batch-summary');
  summary.append(el('span','',totals.visibleBatches+' lote(s) visíveis'),
    el('span','',totals.confirmedBatches+' com contagem validada na fixture'),
    el('span','',totals.distributionBlocked+' distribuição(ões) bloqueada(s)'));
  const list=el('div','team-batch-list');
  if(!projection.batches.length)list.append(el('p','detail-small','Sem lote autorizado na equipe nesta demonstração.'));
  for(const batch of projection.batches){
    const card=el('div','team-batch-card');
    card.append(el('strong','',batch.id+' · '+batch.shopName),
      el('span','',batch.label));
    if(batch.countsConfirmed){
      card.append(el('span','',`Versão fictícia: ${batch.versionRef} · ${batch.received} recebido(s) · ${batch.eligible} elegível(is) na projeção · ${batch.quarantined} em conferência`));
    }else card.append(el('span','', 'Contagens não confirmadas pelo processamento fictício.'));
    card.append(el('span','',batch.qualityNote));
    list.append(card);
  }
  target.replaceChildren(title,note,summary,list,
    el('p','team-hint','Somente leitura. Upload, aceitação de linhas, roteamento, pausa e concessões de concessionárias pertencem aos comandos futuros S0/S1-002.'));
}

function renderSharedQueue(){
  const target=$('team-queue');
  const view=projectSharedNewLeadQueue(state.actorId,state.shopId);
  if(view.visibility!=='shared_queue_demo'){
    target.replaceChildren(el('p','detail-small','Fila indisponível neste perfil ou concessionária.'));return;
  }
  const title=el('h3','detail-label','LEADS SEM TITULAR · FILA COMPARTILHADA');
  const description=el('p','team-hint','Fotografia sintética alternativa da fila por concessionária, NÃO carteira da equipe. Assunção, concessões e distribuição requerem confirmação atômica S0/S1.');
  const totals=el('p','team-hint',
    'Sem titular: '+view.summary.unassigned+' · Já assumidos: '+view.summary.claimed+' · Redistribuídos: '+view.summary.redistributed+' (estados projetados, não calculados)');
  const list=el('div','team-queue-list');
  if(!view.available.length)list.append(el('p','detail-small','Nenhum lead sem titular nesta projeção fictícia.'));
  for(const row of view.available){
    const card=el('div','team-queue-item');
    card.append(el('strong','',row.name),el('span','',row.id+' · versão '+row.versionRef+' · fictício'));
    const key=row.shopId+'|'+row.id;
    if(state.queueRequests[key]){
      card.append(el('span','', 'SOLICITADO LOCALMENTE · NÃO ATRIBUÍDO, S0 NÃO CONSULTADO'));
    }else{
      for(const [action,label] of [['claim','Solicitar assunção'],['assign_team','Solicitar atribuição à equipe']]){
        if(!row.actions.includes(action))continue;
        const button=el('button','btn btn-light',label);button.type='button';
        button.addEventListener('click',()=>{
          const current=projectSharedNewLeadQueue(state.actorId,state.shopId)
            .available.find(item=>item.id===row.id && item.versionRef===row.versionRef);
          if(!current || !current.actions.includes(action) || state.queueRequests[key])return;
          closeTransientDialogs();
          state.queueDialogContext={actorId:state.actorId,shopId:state.shopId,
            caseId:row.id,versionRef:row.versionRef,action};
          $('queue-action-title').textContent=action==='claim'?'Solicitar assunção fictícia':'Solicitar atribuição fictícia';
          $('queue-action-copy').textContent=row.id+' · '+getShop(row.shopId).name+
            ' · confirmação exclusivamente local, sem titular ou grant aplicado.';
          const candidates=ACTORS.filter(person=>person.role==='operador' &&
            person.teamState==='active' && person.managerId===state.actorId);
          $('queue-assignee-area').hidden=action!=='assign_team';
          $('queue-assignee').replaceChildren(...candidates.map(person=>{
            const option=el('option','',person.name+' · somente o caso se S0 confirmar');
            option.value=person.id;return option;
          }));
          if(action==='assign_team' && !candidates.length){state.queueDialogContext=null;return;}
          const dialog=$('queue-action-dialog');dialog.returnValue='';dialog.showModal();
        });
        card.append(button);
      }
    }
    list.append(card);
  }
  target.replaceChildren(title,description,totals,list);
}
/** FV-UI-029: confirmação substitui o botão de ação da equipe no DOM.
 * Restaurar foco em aba persistente, não no botão descartado; nunca fazer isso
 * quando a janela de equipe estiver fechada ou o perfil for inelegível.
 */
function announceTeamActionAndRestoreFocus(tabId,announcement){
  if(!$('team-dialog').open || !canSeeTeamSummary(state.actorId,state.shopId))return;
  $('team-action-announcement').textContent=announcement;
  $(tabId).focus();
}
function switchTeamPanel(panel){
  if(!canSeeTeamSummary(state.actorId,state.shopId))return;
  state.teamPanel=['monitor','batches','queue'].includes(panel)?panel:'members';
  const monitoring=state.teamPanel==='monitor',batches=state.teamPanel==='batches',
    queue=state.teamPanel==='queue';
  $('team-list').hidden=monitoring||batches||queue;
  $('team-monitor').hidden=!monitoring;
  $('team-batches').hidden=!batches;
  $('team-queue').hidden=!queue;
  $('team-show-members').setAttribute('aria-pressed',String(!monitoring&&!batches&&!queue));
  $('team-show-monitor').setAttribute('aria-pressed',String(monitoring));
  $('team-show-batches').setAttribute('aria-pressed',String(batches));
  $('team-show-queue').setAttribute('aria-pressed',String(queue));
  if(queue)renderSharedQueue();
  else if(batches)renderTeamBatches();
  else if(monitoring)renderTeamMonitor();
  else renderTeamSummary();
}
$('team-show-members').addEventListener('click',()=>switchTeamPanel('members'));
$('team-show-monitor').addEventListener('click',()=>switchTeamPanel('monitor'));
$('team-show-batches').addEventListener('click',()=>switchTeamPanel('batches'));
$('team-show-queue').addEventListener('click',()=>switchTeamPanel('queue'));
$('queue-action-dialog').addEventListener('close',()=>{
  const confirmed=$('queue-action-dialog').returnValue==='confirm';
  $('queue-action-dialog').returnValue='';
  const ctx=state.queueDialogContext;state.queueDialogContext=null;
  if(!confirmed || !ctx || ctx.actorId!==state.actorId || ctx.shopId!==state.shopId ||
    state.teamPanel!=='queue')return;
  const key=ctx.shopId+'|'+ctx.caseId;
  if(state.queueRequests[key])return;
  try{
    const request=requestMockQueueAction(ctx.actorId,ctx.shopId,ctx.caseId,
      ctx.versionRef,ctx.action,ctx.action==='assign_team' ? $('queue-assignee').value : null);
    state.queueRequests[key]=request;renderSharedQueue();
    announceTeamActionAndRestoreFocus('team-show-queue',
      'Intenção registrada apenas localmente. Nenhuma atribuição ou permissão aplicada.');
    showToast('Intenção fictícia registrada. Nenhuma atribuição ou permissão aplicada.');
  }catch{showToast('Solicitação inelegível ou desatualizada nesta projeção.');}
});

function openTeamSummary(){
  if(!canSeeTeamSummary(state.actorId,state.shopId)){
    showToast('A visão da equipe está disponível somente no perfil fictício de gestor.');return;
  }
  communication.reset();
  switchTeamPanel('members');
  $('team-action-announcement').textContent='';
  const dialog=$('team-dialog');dialog.returnValue='';dialog.showModal();
}
$('bank-nav').addEventListener('click',()=>openBank());
$('bank-nav-mobile').addEventListener('click',()=>openBank());
$('conversations-nav').addEventListener('click',()=>{$('search-input').focus();});
$('bank-case-select').addEventListener('change',event=>{
  if(!accessible().some(row=>row.id===event.target.value))return;
  state.bankCaseId=event.target.value;renderBank();$('bank-case-select').focus();
});
$('bank-close').addEventListener('click',()=>$('bank-dialog').close());
$('bank-dialog').addEventListener('close',()=>{
  const target=document.getElementById(bankOpener);
  if(!document.querySelector('dialog[open]'))(target??$('bank-nav-mobile')).focus();
});
$('team-nav').addEventListener('click',openTeamSummary);
$('team-nav-mobile').addEventListener('click',openTeamSummary);
$('team-close').addEventListener('click',()=>$('team-dialog').close());
$('intake-dialog').addEventListener('close',()=>{
  const confirm=$('intake-dialog').returnValue==='confirm';
  $('intake-dialog').returnValue='';
  const ctx=state.intakeDialogContext;state.intakeDialogContext=null;
  if(!confirm || !ctx || ctx.actorId!==state.actorId || state.teamRequests[ctx.operatorId])return;
  try{
    const requestedNow=requestMockIntake(state.actorId,ctx.operatorId,ctx.action);
    state.teamRequests[ctx.operatorId]=requestedNow;
    renderTeamSummary();
    announceTeamActionAndRestoreFocus('team-show-members',
      'Pedido fictício registrado. Pausa ou retomada ainda não aplicada no S0/S1.');
    showToast('Pedido fictício registrado. Pausa/retomada ainda NÃO aplicada no S0/S1.');
  }catch{showToast('Ação indisponível para este Gestor e Consultor.');}
});
document.addEventListener('keydown',event=>{
  // Não deslocar o foco para trás de um diálogo modal nativo.
  if(document.querySelector('dialog[open]'))return;
  const inField=['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName);
  // FV-UI-058: a seta para baixo foca o primeiro caso visível sem selecioná-lo.
  if(event.key==='ArrowDown' && document.activeElement===$('search-input') &&
     !event.ctrlKey && !event.metaKey && !event.altKey && !event.isComposing){
    const first=$('conversation-items').children[0];
    if(first?.classList.contains('conversation-card')){
      event.preventDefault();first.focus();
      return;
    }
  }
  // FV-UI-057: Esc na busca apaga somente a consulta, sem retirar chips,
  // etapa comercial, perfil, loja ou aba selecionada. Modais têm prioridade.
  if(event.key==='Escape' && document.activeElement===$('search-input') &&
     !event.ctrlKey && !event.metaKey && !event.altKey && state.query!==''){
    event.preventDefault();
    state.query='';$('search-input').value='';renderList();
    return;
  }
  // FV-UI-034: Escape atua somente quando o foco está no painel
  // flutuante de Detalhes; nunca fecha diálogos nem editor de nota.
  if(event.key==='Escape'&&!inField &&
     $('detail-pane').contains(document.activeElement) &&
     closeFloatingDetails()){
    event.preventDefault();
    return;
  }
  if(event.key==='Escape'&&!inField&&!document.querySelector('dialog[open]')&&
     window.matchMedia('(max-width:760px)').matches &&
     ['thread','detail'].includes(state.mobileView)){
    event.preventDefault();
    mobileBackNavigation();
  }
});
$('reset-app').addEventListener('click',()=>{
  state.cases=withRevisionScenes(copyCFDemoFixtures());state.processing={};state.reviewScenes={};state.followupRequests={};changeActor(initialDemoActor);showToast('Dados de demonstração restaurados.');
});
$('composer').addEventListener('submit',event=>{
  event.preventDefault();
  const item=selectedCase(),input=$('message-input');
  if(!item || !canMockMessage(item))return;
  const candidate=stageHumanMessagePreview(getActor(state.actorId),input.value);
  if(!candidate)return;
  captureDialogContext('message');
  state.dialogContext.message={...state.dialogContext.message,...candidate};
  $('message-preview-body').textContent=candidate.previewBody;
  const dialog=$('message-preview-dialog');dialog.returnValue='';dialog.showModal();
});
$('message-preview-dialog').addEventListener('close',()=>{
  const confirmed=$('message-preview-dialog').returnValue==='confirm';
  $('message-preview-dialog').returnValue='';
  const draft=state.dialogContext.message;
  const sameContext=consumeDialogContext('message');
  $('message-preview-body').textContent='';
  const item=selectedCase(),input=$('message-input');
  const validDraft=Boolean(sameContext && item && canMockMessage(item));
  if(!confirmed){
    // Escape/Cancelar preserva o rascunho SOMENTE no mesmo caso/titular.
    if(validDraft && !document.querySelector('dialog[open]'))input.focus();
    return;
  }
  if(!validDraft || !draft || draft.rawText!==input.value)return;
  const current=stageHumanMessagePreview(getActor(state.actorId),input.value);
  if(!current || current.previewBody!==draft.previewBody || current.authorId!==draft.authorId)return;
  item.messages.push({
    id:`demo-${item.messages.length+1}`,side:'out',body:current.previewBody,
    time:'Agora · fictício',authorId:current.authorId,deliveryState:'local_demo_not_sent'
  });
  item.updatedAt='Agora · fictício';input.value='';render();
  if(!document.querySelector('dialog[open]') && canMockMessage(selectedCase()))
    $('message-input').focus();
  showToast('Texto inserido somente na demonstração. NÃO enviado via WhatsApp.');
});
$('completion-dialog').addEventListener('close',()=>{
  const isConfirm=$('completion-dialog').returnValue==='confirm';
  $('completion-dialog').returnValue='';
  const sameContext=consumeDialogContext('completion');
  if(!isConfirm || !sameContext)return;
  const item=selectedCase(); if(!item || !canMockClose(item))return;
  state.processing[item.id]=item.reviewSceneVersion
    ? stageMockRepeatCompletion(item,state.actorId,state.shopId) : {kind:'accepted'};
  if(!state.processing[item.id])return;
  state.detailTab='overview';
  render();openBank(item.id,'thread-title');showToast('Solicitação de conclusão simulada. Nenhuma API foi chamada.');
});
$('template-dialog').addEventListener('close',()=>{
  const isConfirm=$('template-dialog').returnValue==='confirm';
  $('template-dialog').returnValue='';
  const sameContext=consumeDialogContext('template');
  if(!isConfirm || !sameContext)return;
  const item=selectedCase();if(!item || !postmarkContextValid(item))return;
  const template=DEMO_TEMPLATES.find(x=>x.id===$('template-select').value);
  try {state.followupRequests[item.id]=applyLocalFollowupRequest(item,state.actorId,state.shopId,'single_template',template);
    state.detailTab='activity';render();showToast('Pedido fictício de template recebido. Envio não confirmado.');}
  catch(error){showToast('Template indisponível neste contexto.');}
});
// FV-UI-033: zoom/reflow pode atravessar o breakpoint com foco no painel de detalhes.
// Registrar o último controle útil antes de o navegador ocultá-lo por CSS; não
// restaurar foco de diálogos ou de outro contexto ao redimensionar.
let wasMobileViewport=window.matchMedia('(max-width:760px)').matches;
let lastResponsiveFocus={region:null,node:null};
document.addEventListener('focusin',event=>{
  if(document.querySelector('dialog[open]'))return;
  const node=event.target;
  const region=$('detail-pane').contains(node)?'detail':
    $('thread-pane').contains(node)?'thread':
    $('conversation-list').contains(node)?'list':null;
  lastResponsiveFocus={region,node:region?node:null};
});
window.addEventListener('resize',()=>{
  const isMobile=window.matchMedia('(max-width:760px)').matches;
  if(isMobile===wasMobileViewport)return;
  wasMobileViewport=isMobile;
  if(!isMobile){
    // FV-UI-035: os botões mobile Voltar deixam de existir visualmente ao
    // ampliar para tablet/desktop. Não restaurar foco em um botão oculto.
    // Guardar a região do mesmo caso e orientar o teclado para destino visível.
    const dialogOpen=Boolean(document.querySelector('dialog[open]'));
    const lastMobileBack=lastResponsiveFocus.node?.id;
    if(state.mobileView==='detail' && selectedCase()){
      app.classList.remove('details-hidden');
      setDetailsExpanded(true);
      if(!dialogOpen &&
         (lastMobileBack==='detail-back' ||
          !$('detail-pane').contains(document.activeElement))){
        const remembered=lastResponsiveFocus.region==='detail'?lastResponsiveFocus.node:null;
        const destination=lastMobileBack==='detail-back'?
          $('detail-content').querySelector('.detail-tab.active') ?? $('detail-toggle'):
          remembered?.isConnected && $('detail-pane').contains(remembered)?
            remembered:$('detail-toggle');
        destination.focus();
      }
    }else if(!dialogOpen && state.mobileView==='thread' && selectedCase() &&
             lastMobileBack==='thread-back'){
      // A região de conversa já possui tabindex=-1 e nome acessível.
      $('thread-pane').focus();
    }
    return;
  }
  const dialog=document.querySelector('dialog[open]');
  if(dialog){
    // Modais continuam com foco próprio; só preparar o painel subjacente.
    goto(['team-dialog','intake-dialog','queue-action-dialog'].includes(dialog.id)?'list':'thread');
    return;
  }
  const current=document.activeElement;
  const region=$('detail-pane').contains(current)?'detail':
    $('thread-pane').contains(current)?'thread':
    $('conversation-list').contains(current)?'list':lastResponsiveFocus.region;
  const canShowDetail=region==='detail' && selectedCase() &&
    !app.classList.contains('details-hidden');
  const targetView=canShowDetail?'detail':
    region==='thread' && selectedCase()?'thread':'list';
  goto(targetView);
  const pane=targetView==='detail'?$('detail-pane'):
    targetView==='thread'?$('thread-pane'):$('conversation-list');
  // A troca de display pode fazer o browser zerar activeElement para BODY.
  const remembered=lastResponsiveFocus.region===targetView ? lastResponsiveFocus.node:null;
  const destination=remembered?.isConnected && pane.contains(remembered)?remembered:
    targetView==='detail' ? $('detail-back'):
    targetView==='thread' ? $('thread-back'):$('search-input');
  if(!pane.contains(document.activeElement) || document.activeElement!==destination)
    destination.focus();
});

if(window.matchMedia('(max-width:1040px)').matches){app.classList.add('details-hidden');setDetailsExpanded(false);}
applyTheme(state.theme);
updateSelectors();render();announceCurrentContext('Demonstração local iniciada');
