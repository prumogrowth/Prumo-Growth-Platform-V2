// Smoke test de montagem da interface sem navegador ou bibliotecas externas.
// Não equivale a homologação visual/acessibilidade em navegador real.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
const appSource = readFileSync(new URL("../app.mjs", import.meta.url), "utf8");
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
const references = [...appSource.matchAll(/\$\("#([\w-]+)"\)/g)].map(match => match[1]);

class MockElement {
  constructor(tagName="div") {
    this.tagName=tagName; this.children=[]; this.listeners={}; this.attributes={};
    this.textContent=""; this.className=""; this.value=""; this.hidden=false;
    this.type=""; this.disabled=false;
  }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children=[...items]; }
  setAttribute(k,v) { this.attributes[k]=v; }
  addEventListener(name,handler) { this.listeners[name]=handler; }
  trigger(name,value) {
    if(value!==undefined) this.value=value;
    const fn=this.listeners[name];
    assert.equal(typeof fn,"function");
    fn({target:this,preventDefault(){}});
  }
}

const elements = new Map(ids.map(id=>[id,new MockElement()]));
elements.get("filter").value="todos";
globalThis.document = {
  querySelector(selector) {
    const item = elements.get(selector.slice(1));
    if (!item) throw new Error("ID ausente: "+selector);
    return item;
  },
  createElement(tag) { return new MockElement(tag); }
};
globalThis.window = {
  confirm() { return true; },
  prompt() { return "Evidência fictícia SIM-TESTE"; }
};

await import("../app.mjs");
const element = id => elements.get(id);

test("S1-UI-01: todos os identificadores usados no app existem na página", () => {
  assert.equal(new Set(ids).size,ids.length,"IDs HTML não podem se repetir");
  for(const name of references) assert.ok(elements.has(name),"ID ausente: "+name);
  assert.ok(references.length>20);
});

test("S1-UI-02: interface inicial monta os casos do gestor Aurora", () => {
  assert.equal(element("metric-total").textContent,"05");
  assert.equal(element("actor-name").textContent,"Marina Costa");
  assert.equal(element("detail-name").textContent,"Cliente Exemplo 01");
  assert.equal(element("lead-list").children.length,5);
  assert.equal(element("detail-empty").hidden,true);
  assert.equal(element("status-steps").children.length,8);
});

test("S1-UI-03: alternar para operador reduz fila e escopo do detalhe", () => {
  element("profile").trigger("change","operador-aurora-2");
  assert.equal(element("metric-total").textContent,"01");
  assert.equal(element("lead-list").children.length,1);
  assert.equal(element("detail-id").textContent,"A-103 · versão 1");
  assert.match(element("mode-caption").textContent,/somente casos atualmente atribuídos/);
});

test("S1-UI-04: alternar para outra concessionária não conserva detalhe anterior", () => {
  element("profile").trigger("change","gestor-horizonte");
  assert.equal(element("metric-total").textContent,"02");
  assert.equal(element("lead-list").children.length,2);
  assert.equal(element("detail-id").textContent,"B-201 · versão 1");
  assert.equal(element("shop-name").textContent,"Concessionária Horizonte");
});

test("S1-UI-05: pesquisa sem resultados mostra estado vazio", () => {
  element("search").trigger("input","qualquer-id-inexistente-100000");
  assert.equal(element("lead-list").children.length,1);
  assert.equal(element("lead-list").children[0].className,"empty-state");
  assert.equal(element("detail-empty").hidden,false);
  assert.equal(element("detail-filled").hidden,true);
});

test("S1-UI-06: restaurar demonstração reconstrói a fila local", () => {
  element("reset").trigger("click");
  assert.equal(element("metric-total").textContent,"02"); // mesmo perfil Horizonte
  assert.equal(element("lead-list").children.length,2);
  assert.equal(element("detail-empty").hidden,true);
  assert.match(element("notice").textContent,/restaurada/i);
  assert.equal(element("search").value,"");
});
