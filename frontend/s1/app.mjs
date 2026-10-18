import {
  STATUS, SHOPS, ACTORS, initialState, getActor, operatorsOf,
  visibleLeads, canExecute, execute, countsByStatus
} from "./domain.mjs";

let state = initialState();
let activeActorId = "gestor-aurora";
let selectedLeadId = "A-101";
let query = "";
let statusFilter = "todos";

const $ = (s) => document.querySelector(s);
const node = (tag, className, text) => {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text;
  return e;
};
const formatTime = (value) => new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
}).format(new Date(value));
const actor = () => getActor(activeActorId);
const shop = () => SHOPS.find(s => s.id === actor().shopId);
const leadById = id => visibleLeads(state, activeActorId).find(l => l.id === id) ?? null;
const allVisible = () => visibleLeads(state, activeActorId);
const initials = label => label.split(" ").slice(0, 2).map(x => x[0]).join("").toUpperCase();
const ownerName = id => getActor(id)?.name ?? "Aguardando atribuição";
const statusClass = value => {
  if (value === "vendido") return "status-success";
  if (value === "perdido") return "status-muted";
  if (value === "cadastro enviado ao banco") return "status-bank";
  if (value.includes("operador")) return "status-human";
  if (value.includes("IA")) return "status-ai";
  return "status-neutral";
};

function toast(text, isError=false) {
  const region = $("#notice");
  region.textContent = text;
  region.className = "toast"+(isError ? " toast-error" : "");
  region.hidden = false;
  // No timers: the message remains visible until the next action.
}
function clearToast() { $("#notice").hidden = true; }
function button(label, onClick, className="btn btn-secondary", disabled=false) {
  const b = node("button", className, label);
  b.type = "button"; b.disabled = disabled; b.addEventListener("click", onClick);
  return b;
}
function statusPill(value) {
  return node("span", "status "+statusClass(value), value);
}
function commit(command) {
  try {
    const leadRecord = leadById(command.leadId);
    if (!leadRecord) throw new Error("ACESSO_NEGADO");
    state = execute(state, activeActorId, {
      ...command, expectedVersion: leadRecord.version
    });
    toast("Alteração registrada apenas na demonstração. Nenhum serviço externo foi acionado.");
    render();
  } catch (error) {
    const label = {
      ACESSO_NEGADO: "Este caso não está acessível neste perfil.",
      VERSAO_DESATUALIZADA: "Este registro mudou. Atualize a seleção.",
      OPERACAO_NAO_PERMITIDA: "A ação não é permitida neste estágio.",
      OPERADOR_FORA_DA_LOJA: "Escolha um operador da mesma concessionária.",
      TEXTO_INVALIDO: "Preencha o texto exigido dentro do limite informado."
    }[error.message] ?? "Não foi possível executar esta ação simulada.";
    toast(label, true);
  }
}
function renderPersona() {
  const sel = $("#profile");
  sel.replaceChildren();
  ACTORS.forEach(a => {
    const option = node("option", "", a.name+" · "+(a.role === "gestor" ? "Gestor" : "Operador")+" da Prumo | Escopo: "+SHOPS.find(s => s.id === a.shopId).name);
    option.value = a.id; sel.append(option);
  });
  sel.value = activeActorId;
  $("#current-role").textContent = actor().role === "gestor" ? "Visão do gestor" : "Minha carteira de casos";
  $("#shop-name").textContent = shop().name;
  $("#shop-region").textContent = shop().region;
  $("#avatar").textContent = initials(actor().name);
  $("#actor-name").textContent = actor().name;
  $("#actor-role").textContent = actor().role === "gestor" ? "Gestor da Prumo • simulado" : "Operador da Prumo • simulado";
}
function renderMetrics() {
  const m = countsByStatus(state, activeActorId);
  [["metric-total",m.total],["metric-human",m.human],
   ["metric-bank",m.bank],["metric-done",m.completed]]
    .forEach(([id,value])=>{ $("#"+id).textContent = String(value).padStart(2,"0"); });
  $("#total-label").textContent = actor().role === "gestor" ? "Leads da loja" : "Casos atribuídos a mim";
}
function filteredLeads() {
  const raw = query.trim().toLocaleLowerCase("pt-BR");
  return allVisible().filter(l =>
    (statusFilter === "todos" || l.status === statusFilter) &&
    (!raw || [l.id, l.name, l.phone, l.source, l.status].some(x =>
      x.toLocaleLowerCase("pt-BR").includes(raw))));
}
function renderList() {
  const list = $("#lead-list");
  list.replaceChildren();
  const records = filteredLeads();
  $("#lead-count").textContent = records.length+" "+(records.length===1?"registro":"registros");
  if (!records.length) {
    const empty = node("div","empty-state");
    empty.append(node("strong","","Nenhum caso nesta seleção"),
      node("p","","Altere a pesquisa, o filtro ou o perfil simulado."));
    list.append(empty);return;
  }
  records.forEach(l => {
    const card = button("",()=>{selectedLeadId=l.id;clearToast();render();},"lead-card"+(selectedLeadId===l.id?" is-selected":""));
    card.setAttribute("aria-current",selectedLeadId===l.id?"true":"false");
    const row=node("div","lead-card-top");
    row.append(node("strong","",l.name),node("small","lead-id",l.id));
    const foot=node("div","lead-card-foot");
    foot.append(statusPill(l.status));
    const sub=node("p","lead-card-sub",""+l.phone+" · "+ownerName(l.assignedTo));
    card.append(row,sub,foot);
    list.append(card);
  });
}
function renderJourney(leadRecord) {
  const container=$("#status-steps");
  container.replaceChildren();
  STATUS.forEach((s,i)=>{
    const item=node("div","step"+(s===leadRecord.status?" active":""));
    item.append(node("span","step-index",String(i+1)),node("span","step-name",s));
    if(s===leadRecord.status) item.setAttribute("aria-current","step");
    container.append(item);
  });
}
function renderHistory(leadRecord) {
  const thread=$("#conversation");
  thread.replaceChildren();
  if (!leadRecord.messages.length) {
    thread.append(node("p","thread-empty","Nenhuma mensagem fictícia cadastrada neste caso."));
  }
  leadRecord.messages.forEach(m=>{
    const card=node("div","bubble"+(m.author.toLowerCase().includes("cliente")?" inbound":" outbound"));
    card.append(node("span","bubble-by",m.author),node("p","",m.text),
      node("time","",formatTime(m.at)));
    thread.append(card);
  });
  const history=$("#history");
  history.replaceChildren();
  [...leadRecord.history].reverse().forEach(ev=>{
    const item=node("li","timeline-item");
    item.append(node("span","timeline-dot"),node("span","timeline-text",ev.text),
      node("time","",formatTime(ev.at)));
    history.append(item);
  });
  const notes=$("#notes");
  notes.replaceChildren();
  if(!leadRecord.notes.length) notes.append(node("p","small-muted","Nenhuma nota interna."));
  [...leadRecord.notes].reverse().forEach(n=>{
    const item=node("div","note");
    item.append(node("strong","",n.author+" · "+formatTime(n.at)),node("p","",n.text));
    notes.append(item);
  });
}
function renderActions(l) {
  const area=$("#actions");area.replaceChildren();
  const operator = actor().role==="operador";
  const action=(type,label,primary=false)=> {
    if (canExecute(state,activeActorId,l.id,type))
      area.append(button(label,()=>commit({type,leadId:l.id}),primary?"btn btn-primary":"btn btn-secondary"));
  };
  if(!operator && canExecute(state,activeActorId,l.id,"assign")) {
    const field=node("label","assignment-label","Atribuir caso à equipe");
    const select=node("select","assignment-select");
    select.setAttribute("aria-label","Operador da concessionária");
    const initial=node("option","","Escolher operador");
    initial.value="";select.append(initial);
    operatorsOf(l.shopId).forEach(op=>{
      const option=node("option","",op.name);
      option.value=op.id;select.append(option);
    });
    select.value=l.assignedTo??"";
    const assignRow=node("div","assignment-row");
    assignRow.append(select,button("Atribuir",()=>{
      if (!select.value) return toast("Selecione um operador da loja.",true);
      commit({type:"assign",leadId:l.id,operatorId:select.value});
    },"btn btn-secondary"));
    area.append(field,assignRow);
  }
  action("simulate_first","Simular primeiro disparo");
  action("simulate_ai","Simular triagem IA");
  action("route_operator","Encaminhar cadastro ao operador",true);
  action("start_human","Assumir atendimento humano",true);
  action("submit_bank","Simular envio ao banco",true);
  if (canExecute(state,activeActorId,l.id,"sell")) {
    area.append(button("Registrar venda fictícia",()=>{
      const evidence=window.prompt("Informe evidência FICTÍCIA de confirmação manual (mínimo 12 caracteres). Não insira dados reais:");
      if(evidence!==null) commit({type:"sell",leadId:l.id,evidence});
    },"btn btn-primary"));
  }
  if (canExecute(state,activeActorId,l.id,"lose")) {
    area.append(button("Registrar perda",()=>{
      const reason=window.prompt("Informe motivo fictício da perda (mínimo 8 caracteres):");
      if(reason!==null) commit({type:"lose",leadId:l.id,reason});
    },"btn btn-ghost"));
  }
  if (!area.children.length) {
    area.append(node("p","small-muted","Sem transições disponíveis para este perfil e estágio."));
  }
  const noteForm=$("#note-form");
  noteForm.hidden=!canExecute(state,activeActorId,l.id,"note");
  $("#note-body").value="";
}
function renderDetail() {
  const l=leadById(selectedLeadId);
  $("#detail-empty").hidden=Boolean(l);
  $("#detail-filled").hidden=!l;
  if (!l) return;
  $("#detail-name").textContent=l.name;
  $("#detail-id").textContent=l.id+" · versão "+l.version;
  $("#detail-phone").textContent=l.phone+" (fictício)";
  $("#detail-source").textContent=l.source;
  $("#detail-owner").textContent=ownerName(l.assignedTo);
  $("#detail-handoff").textContent=l.aiSuspended
    ?"IA automática suspensa neste caso desde a transferência humana"
    :"Sem transferência humana registrada";
  $("#detail-handoff").className="handoff"+(l.aiSuspended?" is-paused":"");
  const pill=$("#detail-status");pill.replaceChildren(statusPill(l.status));
  $("#bank-disclaimer").hidden=l.status!==STATUS[5]&&l.status!==STATUS[6];
  renderJourney(l);renderHistory(l);renderActions(l);
}
function render() {
  const matching=filteredLeads();
  if(!matching.some(l=>l.id===selectedLeadId)) selectedLeadId=matching[0]?.id??null;
  renderPersona();renderMetrics();renderList();renderDetail();
  $("#mode-caption").textContent=actor().role==="gestor"
    ?"Acesso de demonstração: somente registros fictícios da concessionária selecionada."
    :"Acesso de demonstração: somente casos atualmente atribuídos a este operador.";
}
$("#profile").addEventListener("change",event=>{
  activeActorId=event.target.value;selectedLeadId=null;clearToast();render();
});
$("#search").addEventListener("input",event=>{query=event.target.value;render();});
$("#filter").addEventListener("change",event=>{statusFilter=event.target.value;render();});
$("#reset").addEventListener("click",()=>{
  if(!window.confirm("Restaurar todos os dados fictícios da demonstração?"))return;
  state=initialState();query="";statusFilter="todos";$("#search").value="";$("#filter").value="todos";
  selectedLeadId=null;toast("Demonstração restaurada. Nenhum dado externo foi alterado.");render();
});
$("#note-form").addEventListener("submit",event=>{
  event.preventDefault();
  if(!selectedLeadId)return;
  const text=$("#note-body").value;
  commit({type:"note",leadId:selectedLeadId,text});
});
STATUS.forEach(s=>{
  const option=node("option","",s);option.value=s;$("#filter").append(option);
});
render();
