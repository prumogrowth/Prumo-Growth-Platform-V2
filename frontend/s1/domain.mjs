// S1-001 — Demonstrador local. Não confere autenticação nem autoriza operações reais.
export const STATUS = Object.freeze([
  "aguardando primeiro disparo",
  "primeiro disparo enviado",
  "em atendimento pela IA",
  "em atendimento pelo operador",
  "cadastro enviado ao operador",
  "cadastro enviado ao banco",
  "vendido",
  "perdido"
]);

export const SHOPS = Object.freeze([
  { id: "aurora", name: "Concessionária Aurora", region: "Loja fictícia · Caruaru" },
  { id: "horizonte", name: "Concessionária Horizonte", region: "Loja fictícia · Recife" }
]);

export const ACTORS = Object.freeze([
  { id: "gestor-aurora", name: "Marina Costa", role: "gestor", shopId: "aurora" },
  { id: "operador-aurora-1", name: "Rafael Lima", role: "operador", shopId: "aurora" },
  { id: "operador-aurora-2", name: "Bianca Rocha", role: "operador", shopId: "aurora" },
  { id: "gestor-horizonte", name: "Paulo Nunes", role: "gestor", shopId: "horizonte" },
  { id: "operador-horizonte", name: "Lia Martins", role: "operador", shopId: "horizonte" }
]);

const BASE_TIME = "2026-10-18T11:00:00.000Z";
const sampleMessage = (author, text, at) => ({ author, text, at });
const sampleEvent = (text, at=BASE_TIME) => ({ text, at, kind: "sistema" });

function lead({ id, shopId, name, phone, source, status, assignedTo=null,
                 messages=[], history=[], updatedAt=BASE_TIME, evidence=null }) {
  const handoff = Boolean(assignedTo) || status === "em atendimento pelo operador" ||
    status === "cadastro enviado ao operador" || status === "cadastro enviado ao banco";
  return {
    id, shopId, name, phone, source,
    status, version: 1, assignedTo, caseId: assignedTo ? "caso-"+id : null,
    aiSuspended: handoff, evidence, updatedAt, messages,
    history: history.length ? history : [sampleEvent("Lead fictício registrado na loja")],
    notes: []
  };
}

export function initialState() {
  return {
    mode: "DEMONSTRACAO_LOCAL",
    leads: [
      lead({ id: "A-101", shopId: "aurora", name: "Cliente Exemplo 01",
        phone: "(81) 9 9000-0101", source: "Importação C01 fictícia",
        status: "em atendimento pela IA",
        messages: [
          sampleMessage("cliente", "Gostaria de entender as opções disponíveis.", "2026-10-18T09:10:00Z"),
          sampleMessage("IA (simulada)", "Vamos organizar as informações iniciais.", "2026-10-18T09:12:00Z")
        ]}),
      lead({ id: "A-102", shopId: "aurora", name: "Cliente Exemplo 02",
        phone: "(81) 9 9000-0102", source: "Entrada C02 fictícia",
        status: "em atendimento pelo operador", assignedTo: "operador-aurora-1",
        messages: [
          sampleMessage("cliente", "Já falei com a loja e preciso continuar.", "2026-10-18T09:22:00Z"),
          sampleMessage("operador (simulado)", "Vou acompanhar o seu caso.", "2026-10-18T09:26:00Z")
        ]}),
      lead({ id: "A-103", shopId: "aurora", name: "Cliente Exemplo 03",
        phone: "(81) 9 9000-0103", source: "Importação C01 fictícia",
        status: "cadastro enviado ao operador", assignedTo: "operador-aurora-2",
        messages: [sampleMessage("sistema", "Encaminhado à equipe humana (simulação).", "2026-10-18T10:00:00Z")]}),
      lead({ id: "A-104", shopId: "aurora", name: "Cliente Exemplo 04",
        phone: "(81) 9 9000-0104", source: "Importação C01 fictícia",
        status: "aguardando primeiro disparo" }),
      lead({ id: "A-105", shopId: "aurora", name: "Cliente Exemplo 05",
        phone: "(81) 9 9000-0105", source: "Operação fictícia",
        status: "cadastro enviado ao banco", assignedTo: "operador-aurora-1",
        messages: [sampleMessage("sistema", "Remessa bancária apenas simulada.", "2026-10-18T10:22:00Z")]}),
      lead({ id: "B-201", shopId: "horizonte", name: "Cliente Exemplo 01",
        phone: "(81) 9 9000-0101", source: "Importação C01 fictícia",
        status: "em atendimento pelo operador", assignedTo: "operador-horizonte",
        messages: [sampleMessage("cliente", "Preciso de informações da minha concessionária.", "2026-10-18T09:30:00Z")]}),
      lead({ id: "B-202", shopId: "horizonte", name: "Cliente Exemplo 06",
        phone: "(81) 9 9000-0202", source: "Operação fictícia",
        status: "primeiro disparo enviado" })
    ]
  };
}

export function getActor(actorId) { return ACTORS.find(a => a.id === actorId) ?? null; }
export function operatorsOf(shopId) {
  return ACTORS.filter(a => a.shopId === shopId && a.role === "operador");
}
export function canReadLead(actor, leadRecord) {
  return Boolean(actor && leadRecord && actor.shopId === leadRecord.shopId &&
    (actor.role === "gestor" ||
      (actor.role === "operador" && leadRecord.assignedTo === actor.id && Boolean(leadRecord.caseId))));
}
export function visibleLeads(state, actorId) {
  const actor = getActor(actorId);
  return state.leads.filter(l => canReadLead(actor, l));
}
export function isTerminal(status) { return status === "vendido" || status === "perdido"; }
export function canExecute(state, actorId, leadId, type) {
  const actor = getActor(actorId);
  const leadRecord = state.leads.find(l => l.id === leadId);
  if (!canReadLead(actor, leadRecord)) return false;
  if (type === "note") return true;
  if (isTerminal(leadRecord.status)) return false;
  const manager = actor.role === "gestor";
  const operator = actor.role === "operador" && leadRecord.assignedTo === actor.id;
  switch (type) {
    case "assign": return manager;
    case "simulate_first": return manager && leadRecord.status === STATUS[0];
    case "simulate_ai": return manager && leadRecord.status === STATUS[1] && !leadRecord.aiSuspended;
    case "route_operator": return manager && Boolean(leadRecord.assignedTo) &&
      [STATUS[1], STATUS[2]].includes(leadRecord.status);
    case "start_human": return operator && [STATUS[1], STATUS[2], STATUS[4]].includes(leadRecord.status);
    case "submit_bank": return operator && [STATUS[3], STATUS[4]].includes(leadRecord.status);
    case "sell": return manager && leadRecord.status === STATUS[5];
    case "lose": return manager;
    default: return false;
  }
}
function guard(condition, code) {
  if (!condition) throw new Error(code);
}
function requiredText(value, min=3, max=240) {
  guard(typeof value === "string", "TEXTO_INVALIDO");
  const clean = value.trim();
  guard(clean.length >= min && clean.length <= max, "TEXTO_INVALIDO");
  return clean;
}

/** Pure state reducer. Optimistic versions and permissions are for the demo only. */
export function execute(state, actorId, command, now=new Date().toISOString()) {
  guard(state?.mode === "DEMONSTRACAO_LOCAL", "ESTADO_INVALIDO");
  const actor = getActor(actorId);
  const { leadId, type, expectedVersion } = command ?? {};
  const current = state.leads.find(l => l.id === leadId);
  guard(canReadLead(actor, current), "ACESSO_NEGADO");
  guard(Number.isInteger(expectedVersion) && current.version === expectedVersion, "VERSAO_DESATUALIZADA");
  guard(canExecute(state, actorId, leadId, type), "OPERACAO_NAO_PERMITIDA");

  const changed = { ...current, messages: [...current.messages], notes: [...current.notes],
    history: [...current.history] };
  let description = "";
  switch (type) {
    case "assign": {
      const operator = getActor(command.operatorId);
      guard(operator?.role === "operador" && operator.shopId === actor.shopId, "OPERADOR_FORA_DA_LOJA");
      changed.assignedTo = operator.id;
      changed.caseId ??= "caso-"+changed.id;
      changed.aiSuspended = true; // Atribuição/handoff humano nunca retoma IA automaticamente.
      description = "Caso atribuído a "+operator.name+"; IA automática suspensa";
      break;
    }
    case "simulate_first":
      changed.status = STATUS[1];
      description = "Primeiro disparo SIMULADO — nenhum WhatsApp enviado";
      break;
    case "simulate_ai":
      guard(!changed.aiSuspended, "IA_SUSPENSA");
      changed.status = STATUS[2];
      description = "Triagem IA SIMULADA — nenhum modelo conectado";
      break;
    case "route_operator":
      changed.status = STATUS[4]; changed.aiSuspended = true;
      description = "Cadastro encaminhado ao operador (simulação)";
      break;
    case "start_human":
      changed.status = STATUS[3]; changed.aiSuspended = true;
      description = "Atendimento assumido pelo operador; IA permanece suspensa";
      break;
    case "submit_bank":
      changed.status = STATUS[5]; changed.aiSuspended = true;
      description = "Cadastro enviado ao banco SOMENTE NA SIMULAÇÃO";
      break;
    case "sell":
      changed.evidence = requiredText(command.evidence, 12, 180);
      changed.status = STATUS[6];
      description = "Venda registrada manualmente com evidência FICTÍCIA: "+changed.evidence;
      break;
    case "lose":
      changed.status = STATUS[7];
      description = "Perda registrada manualmente: "+requiredText(command.reason, 8, 180);
      break;
    case "note": {
      const note = requiredText(command.text);
      changed.notes.push({ text: note, author: actor.name, at: now });
      description = "Nota interna registrada por "+actor.name;
      break;
    }
    default: throw new Error("OPERACAO_NAO_PERMITIDA");
  }

  changed.version += 1;
  changed.updatedAt = now;
  changed.history.push({ kind: "simulacao", actorId: actor.id, text: description,
    at: now, version: changed.version });
  return {
    ...state,
    leads: state.leads.map(l => l.id === leadId ? changed : l)
  };
}

export function countsByStatus(state, actorId) {
  const leads = visibleLeads(state, actorId);
  return {
    total: leads.length,
    human: leads.filter(l => Boolean(l.assignedTo)).length,
    bank: leads.filter(l => l.status === STATUS[5]).length,
    completed: leads.filter(l => isTerminal(l.status)).length
  };
}
