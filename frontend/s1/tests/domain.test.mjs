import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  STATUS, ACTORS, SHOPS, initialState, getActor, operatorsOf,
  visibleLeads, canExecute, execute, countsByStatus
} from "../domain.mjs";

const act = (state, actorId, leadId, type, extras={}) =>
  execute(state, actorId, {
    leadId, type, expectedVersion: state.leads.find(l => l.id === leadId).version, ...extras
  }, "2026-10-18T12:00:00.000Z");

test("S1-001: preserva exatamente os oito estados comerciais canônicos", () => {
  assert.deepEqual(STATUS, [
    "aguardando primeiro disparo", "primeiro disparo enviado",
    "em atendimento pela IA", "em atendimento pelo operador",
    "cadastro enviado ao operador", "cadastro enviado ao banco", "vendido", "perdido"
  ]);
  assert.equal(new Set(STATUS).size, 8);
  assert.ok(initialState().leads.every(l => STATUS.includes(l.status)));
});

test("S1-002: dados fictícios repetem telefone em lojas diferentes sem compartilhar lead", () => {
  const s=initialState(), a=s.leads.find(l=>l.id==="A-101"), b=s.leads.find(l=>l.id==="B-201");
  assert.equal(a.phone,b.phone);
  assert.notEqual(a.id,b.id); assert.notEqual(a.shopId,b.shopId);
  assert.notStrictEqual(a.history,b.history);
});

test("S1-003: gestor só enxerga registros da própria loja", () => {
  const s=initialState();
  assert.ok(visibleLeads(s,"gestor-aurora").every(l=>l.shopId==="aurora"));
  assert.equal(visibleLeads(s,"gestor-aurora").length,5);
  assert.equal(visibleLeads(s,"gestor-horizonte").length,2);
  assert.throws(()=>act(s,"gestor-aurora","B-201","note",{text:"Nota inválida entre lojas"}),/ACESSO_NEGADO/);
});

test("S1-004: operador só vê os casos atualmente atribuídos", () => {
  const s=initialState();
  assert.deepEqual(visibleLeads(s,"operador-aurora-1").map(l=>l.id),["A-102","A-105"]);
  assert.deepEqual(visibleLeads(s,"operador-aurora-2").map(l=>l.id),["A-103"]);
  assert.deepEqual(visibleLeads(s,"operador-horizonte").map(l=>l.id),["B-201"]);
  assert.throws(()=>act(s,"operador-aurora-1","A-101","note",{text:"Acesso sem atribuição"}),/ACESSO_NEGADO/);
});

test("S1-005: gestor atribui somente operador da mesma concessionária e congela IA", () => {
  const s=initialState();
  assert.throws(()=>act(s,"gestor-aurora","A-101","assign",{operatorId:"operador-horizonte"}),/OPERADOR_FORA_DA_LOJA/);
  const after=act(s,"gestor-aurora","A-101","assign",{operatorId:"operador-aurora-2"});
  const l=after.leads.find(l=>l.id==="A-101");
  assert.equal(l.assignedTo,"operador-aurora-2");
  assert.equal(l.aiSuspended,true);
  assert.equal(l.status,"em atendimento pela IA"); // atribuição não falsifica transição
  assert.ok(visibleLeads(after,"operador-aurora-2").some(x=>x.id==="A-101"));
  assert.equal(s.leads.find(x=>x.id==="A-101").assignedTo,null); // reducer imutável
  assert.equal(l.version,2);
});

test("S1-006: transferência humana suspende IA e operador pode assumir", () => {
  let s=act(initialState(),"gestor-aurora","A-101","assign",{operatorId:"operador-aurora-1"});
  s=act(s,"operador-aurora-1","A-101","start_human");
  const l=s.leads.find(x=>x.id==="A-101");
  assert.equal(l.status,"em atendimento pelo operador");
  assert.equal(l.aiSuspended,true);
  assert.equal(canExecute(s,"gestor-aurora","A-101","simulate_ai"),false);
});

test("S1-007: simulação do primeiro disparo e da IA jamais envia mensagem externa", () => {
  let s=act(initialState(),"gestor-aurora","A-104","simulate_first");
  assert.equal(s.leads.find(x=>x.id==="A-104").status,STATUS[1]);
  s=act(s,"gestor-aurora","A-104","simulate_ai");
  assert.equal(s.leads.find(x=>x.id==="A-104").status,STATUS[2]);
  assert.match(s.leads.find(x=>x.id==="A-104").history.at(-1).text,/SIMULADA/);
});

test("S1-008: operador não consegue avançar etapa de caso não atribuído", () => {
  const s=initialState();
  assert.throws(()=>act(s,"operador-aurora-2","A-101","submit_bank"),/ACESSO_NEGADO/);
  assert.equal(canExecute(s,"operador-aurora-1","A-102","submit_bank"),true);
});

test("S1-009: remessa ao banco é apenas estado simulado, não venda automática", () => {
  const s=act(initialState(),"operador-aurora-1","A-102","submit_bank");
  const l=s.leads.find(x=>x.id==="A-102");
  assert.equal(l.status,STATUS[5]);
  assert.equal(l.evidence,null);
  assert.equal(l.aiSuspended,true);
  assert.match(l.history.at(-1).text,/SOMENTE NA SIMULAÇÃO/);
});

test("S1-010: registrar venda exige gestor e evidência manual fictícia", () => {
  const s=initialState();
  assert.throws(()=>act(s,"operador-aurora-1","A-105","sell",{evidence:"Prova fictícia detalhada"}),/OPERACAO_NAO_PERMITIDA/);
  assert.throws(()=>act(s,"gestor-aurora","A-105","sell",{evidence:"curta"}),/TEXTO_INVALIDO/);
  const done=act(s,"gestor-aurora","A-105","sell",{evidence:"Comprovante sintético SIM-105"});
  assert.equal(done.leads.find(x=>x.id==="A-105").status,"vendido");
  assert.match(done.leads.find(x=>x.id==="A-105").history.at(-1).text,/FICTÍCIA/);
  assert.equal(canExecute(done,"gestor-aurora","A-105","sell"),false);
});

test("S1-011: perda manual não pode ser atribuída ao operador e encerra transições", () => {
  const s=initialState();
  assert.throws(()=>act(s,"operador-aurora-1","A-102","lose",{reason:"Motivo fictício"}),/OPERACAO_NAO_PERMITIDA/);
  const done=act(s,"gestor-aurora","A-102","lose",{reason:"Desistência em cenário de laboratório"});
  assert.equal(done.leads.find(x=>x.id==="A-102").status,"perdido");
  assert.equal(canExecute(done,"gestor-aurora","A-102","assign"),false);
  assert.equal(canExecute(done,"gestor-aurora","A-102","note"),true);
});

test("S1-012: controle otimista impede comando com versão anterior", () => {
  const s=initialState();
  const version=s.leads.find(l=>l.id==="A-104").version;
  const after=act(s,"gestor-aurora","A-104","simulate_first");
  assert.throws(()=>execute(after,"gestor-aurora",{
    leadId:"A-104",type:"simulate_ai",expectedVersion:version
  }),/VERSAO_DESATUALIZADA/);
});

test("S1-013: notas internas de operador têm autor, sem mensagem de saída", () => {
  const s=initialState(), before=s.leads.find(l=>l.id==="A-102").messages.length;
  const after=act(s,"operador-aurora-1","A-102","note",{text:"  Continuidade sob atendimento humano  "});
  const l=after.leads.find(x=>x.id==="A-102");
  assert.equal(l.notes.length,1);
  assert.equal(l.notes[0].text,"Continuidade sob atendimento humano");
  assert.equal(l.notes[0].author,"Rafael Lima");
  assert.equal(l.messages.length,before);
});

test("S1-014: atribuição posterior revoga visibilidade do operador anterior", () => {
  const s=act(initialState(),"gestor-aurora","A-102","assign",{operatorId:"operador-aurora-2"});
  assert.equal(visibleLeads(s,"operador-aurora-1").some(x=>x.id==="A-102"),false);
  assert.equal(visibleLeads(s,"operador-aurora-2").some(x=>x.id==="A-102"),true);
  assert.throws(()=>act(s,"operador-aurora-1","A-102","note",{text:"Não tenho mais esse caso"}),/ACESSO_NEGADO/);
});

test("S1-015: encaminhamento ao operador exige atribuição anterior", () => {
  const s=initialState();
  assert.equal(canExecute(s,"gestor-aurora","A-101","route_operator"),false);
  const a=act(s,"gestor-aurora","A-101","assign",{operatorId:"operador-aurora-1"});
  const b=act(a,"gestor-aurora","A-101","route_operator");
  assert.equal(b.leads.find(x=>x.id==="A-101").status,STATUS[4]);
});

test("S1-016: filtros por perfil não confundem nomes com permissões", () => {
  const s=initialState();
  assert.notEqual(getActor("gestor-horizonte"),null);
  assert.equal(getActor("inexistente"),null);
  assert.deepEqual(operatorsOf("horizonte").map(x=>x.id),["operador-horizonte"]);
  assert.ok(ACTORS.every(a=>SHOPS.some(s=>s.id===a.shopId)));
  assert.equal(countsByStatus(s,"operador-aurora-2").total,1);
  assert.equal(countsByStatus(s,"gestor-aurora").total,5);
});

test("S1-017: demonstrador não usa rede, tokens, armazenamento nem HTML dinâmico não escapado", () => {
  const js=readFileSync(new URL("../app.mjs",import.meta.url),"utf8");
  const html=readFileSync(new URL("../index.html",import.meta.url),"utf8");
  assert.ok(!/\b(fetch|XMLHttpRequest|WebSocket|localStorage|sessionStorage)\s*\(/.test(js));
  assert.ok(!/\.innerHTML\s*=|insertAdjacentHTML\s*\(/.test(js));
  assert.ok(!/<script[^>]+src=["']https?:\/\//.test(html));
  assert.match(html,/type="module" src="\.\/app\.mjs"/);
  assert.match(html,/id="profile"/);
  assert.match(html,/id="note-form"/);
});

test("S1-018: fixture é reconstruída em memória, sem mutar estado inicial", () => {
  const first=initialState();
  const after=act(first,"gestor-aurora","A-104","simulate_first");
  const second=initialState();
  assert.notDeepEqual(after,first);
  assert.deepEqual(second,first);
});
