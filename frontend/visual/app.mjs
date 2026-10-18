/** FV-UI-001. Navegação e demonstração em memória; NÃO é frontend autenticado.
 * Não chamar backend, OpenAI, Meta, Banco, storage ou permitir efeito comercial.
 */
import {
  ACTORS, getActor, getShop, copyFixtures, visibleConversations,
  canSimulateCompletion, statusTone
} from './fixtures.mjs';

const $ = id => document.getElementById(id);
const app = $('visual-app');
const list = $('conversation-items');
const state = {
  actorId: 'rafael', shopId: 'aurora', filter: 'all', query: '',
  selectedId: 'A-102', cases: copyFixtures(), processing: {},
  mobileView: 'list'
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
  let items = accessible();
  if (state.filter === 'unread') items = items.filter(x => x.unread > 0);
  if (state.filter === 'mine') items = items.filter(x => x.assignedTo === state.actorId);
  const query = state.query.toLocaleLowerCase('pt-BR').trim();
  if (query) items = items.filter(x => [x.name, x.id, x.tag, x.status].some(v => v.toLocaleLowerCase('pt-BR').includes(query)));
  return items;
}
function canMockMessage(record) {
  const actor = getActor(state.actorId);
  return Boolean(actor && record && actor.shops.includes(state.shopId) &&
    record.shopId === state.shopId && record.assignedTo === actor.id &&
    record.status !== 'vendido' && record.status !== 'perdido' &&
    record.status !== 'em atendimento pela IA');
}
function canMockClose(record) {
  return canSimulateCompletion(record, state.actorId, state.shopId) && !state.processing[record.id];
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
  const shopSelect = $('shop-select');
  shopSelect.replaceChildren(...actor.shops.map(id => {
    const shop = getShop(id); const o = el('option', '', `${shop.name} · fictícia`); o.value = id; return o;
  }));
  shopSelect.value = state.shopId;
}
function renderList() {
  const items = filtered();
  const total = accessible().length;
  $('list-count').textContent = `${total} ${total === 1 ? 'atendimento' : 'atendimentos'}`;
  $('list-context').textContent = getActor(state.actorId).role === 'gestor' ? 'Visão de supervisão' : 'Atribuídos a mim';
  const nodes = items.map((item, idx) => {
    const card = el('button', 'conversation-card' + (item.id === state.selectedId ? ' is-selected' : ''));
    card.type = 'button'; card.setAttribute('aria-pressed', String(item.id === state.selectedId));
    card.setAttribute('aria-label', `Abrir conversa ${item.name}, ${item.status}, ${item.unread} não lidas`);
    const avatar = el('div', 'avatar a' + (idx%4+1), item.initials); avatar.setAttribute('aria-hidden','true');
    const center = el('div','item-center');
    const row = el('div','item-title-row'); row.append(el('span','item-title',item.name),el('span','item-time',item.updatedAt));
    const preview = item.messages.at(-1)?.body ?? 'Sem mensagens';
    const foot = el('div', 'item-foot'); foot.append(el('span','micro-tag',item.tag));
    if (item.unread > 0) foot.append(el('span','unread',item.unread));
    center.append(row, el('div','item-preview',preview),foot);
    card.append(avatar,center);
    card.addEventListener('click', () => {
      state.selectedId = item.id; item.unread = 0;
      goto('thread'); render();
    });
    return card;
  });
  if (!nodes.length) {
    const box = el('div','no-results');
    box.append(el('strong','', 'Nenhuma conversa neste filtro'),el('span','', 'Altere a busca, o filtro ou o perfil fictício.'));
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
  $('thread-meta').textContent = item ? `${getShop(item.shopId).name} · Caso ${item.id} · atendimento fictício` : 'Nenhum atendimento selecionado';
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
  if (canMockClose(item)) {
    const close = el('button', 'btn btn-primary', 'Concluir atendimento');
    close.type = 'button'; close.id='request-completion';
    close.addEventListener('click', () => $('completion-dialog').showModal());
    bar.append(close);
  } else if (state.processing[item.id]) {
    const label = state.processing[item.id].kind === 'accepted' ? 'Solicitação simulada' : 'Resultado fictício';
    bar.append(el('span','status-indicator human',label));
  }
  const composeAllowed = canMockMessage(item) && !state.processing[item.id];
  input.disabled = !composeAllowed;
  button.disabled = !composeAllowed;
  input.placeholder = composeAllowed ? 'Escrever mensagem de demonstração…' : 'Visualização somente leitura neste contexto';
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
  if(!item){ target.replaceChildren(el('p','detail-placeholder','Selecione uma conversa para ver informações do caso.'));return;}
  const profile=el('div','profile-detail');const avatar=el('div','avatar',item.initials);
  profile.append(avatar,el('strong','',item.name),el('span','',`Caso ${item.id} · exemplo fictício`));
  const group=detailSection('CONTEXTO DO ATENDIMENTO');
  const actor=ACTORS.find(a=>a.id===item.assignedTo);
  group.append(prop('Concessionária',getShop(item.shopId).name),prop('Profissional atribuído',actor?.name??'Sem atribuição'),prop('Estado comercial',item.status));
  const extract=detailSection('FICHA E EXTRAÇÃO · FV-02');
  const proc=state.processing[item.id];
  if(!proc){
    extract.append(callout('Ainda não solicitada', 'Após a conclusão humana, a futura S0 poderá solicitar extração à OpenAI. Nenhum dado foi processado aqui.'));
  } else if(proc.kind==='accepted'){
    extract.append(callout('Solicitação registrada — simulação', 'Demonstra apenas o estado de interface. Não existe chamada à OpenAI nem gravação de ficha.','warning'));
    if (canSimulateCompletion(item,state.actorId,state.shopId)) {
      const box=el('div','detail-actions'); const btn=el('button','btn btn-light','Simular retorno com pendências');btn.type='button';
      btn.addEventListener('click',()=>{state.processing[item.id]={kind:'partial'};renderDetails();renderThread();showToast('Resultado fictício exibido. Nenhuma informação foi gravada.');});
      box.append(btn);extract.append(box);
    }
  } else {
    extract.append(callout('Resultado ilustrativo com pendências','Exemplo visual de como o frontend apresentará uma extração parcial. Nenhuma ficha foi gravada.','warning'));
    const example=el('div','detail-row');example.append(el('strong','','Campo demonstrativo 01'),el('span','','Proposta fictícia · fonte simulada da conversa'));
    const missing=el('div','detail-row');missing.append(el('strong','','Campo demonstrativo 02'),el('span','','Sem evidência suficiente · revisão pendente'));
    extract.append(example,missing);
  }
  extract.append(el('p','detail-small','O catálogo real de campos e a persistência dependem da S0 e de validações. Não há formulário de preenchimento manual habitual.'));
  const conditions=detailSection('REGRAS DA EXPERIÊNCIA');
  conditions.append(callout('Atendimento humano independente', 'Concluir a conversa não envia cadastro ao banco, não marca vendido ou perdido e não reativa a IA Vendedora.'));
  conditions.append(el('p','detail-small', 'Gestão acessa conversas D2 no escopo concedido. Campos D3/D4 reais não são carregados neste protótipo.'));
  target.replaceChildren(profile,group,extract,conditions);
}
function render(){renderList();renderThread();renderDetails();app.dataset.mobileView=state.mobileView;}
function changeActor(actorId){
  const actor=getActor(actorId);if(!actor)return;
  state.actorId=actor.id;state.shopId=actor.shops[0];state.selectedId=null;
  state.filter='all';state.query='';$('search-input').value='';goto('list');updateSelectors();render();
}
$('actor-select').addEventListener('change',event=>changeActor(event.target.value));
$('shop-select').addEventListener('change',event=>{
  const actor=getActor(state.actorId);
  if(!actor.shops.includes(event.target.value))return;
  state.shopId=event.target.value;state.selectedId=null;state.query='';$('search-input').value='';goto('list');render();
});
$('search-input').addEventListener('input',event=>{state.query=event.target.value;renderList();});
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{state.filter=button.dataset.filter;renderList();}));
$('thread-back').addEventListener('click',()=>goto('list'));
$('detail-back').addEventListener('click',()=>goto('thread'));
$('detail-toggle').addEventListener('click',()=>{
  if (window.matchMedia('(max-width:760px)').matches) {goto('detail');return;}
  const hidden=app.classList.toggle('details-hidden');$('detail-toggle').setAttribute('aria-expanded',String(!hidden));
});
$('detail-close').addEventListener('click',()=>{app.classList.add('details-hidden');$('detail-toggle').setAttribute('aria-expanded','false');});
$('team-nav').addEventListener('click',()=>showToast('A visão de equipe será desenhada em uma etapa posterior.'));
$('reset-app').addEventListener('click',()=>{
  state.cases=copyFixtures();state.processing={};changeActor('rafael');showToast('Dados de demonstração restaurados.');
});
$('composer').addEventListener('submit',event=>{
  event.preventDefault();const item=selectedCase();const input=$('message-input');const text=input.value.trim();
  if(!text || !item || !canMockMessage(item) || state.processing[item.id]) return;
  item.messages.push({id:`demo-${item.messages.length+1}`,side:'out',body:text,time:'Agora · fictício'});
  item.updatedAt='Agora';input.value='';render();showToast('Mensagem adicionada apenas à simulação local.');
});
$('completion-dialog').addEventListener('close',()=>{
  if($('completion-dialog').returnValue!=='confirm')return;
  const item=selectedCase(); if(!item || !canMockClose(item))return;
  state.processing[item.id]={kind:'accepted'};
  render();showToast('Solicitação de conclusão simulada. Nenhuma API foi chamada.');
});
if(window.matchMedia('(max-width:1040px)').matches){app.classList.add('details-hidden');$('detail-toggle').setAttribute('aria-expanded','false');}
updateSelectors();render();
