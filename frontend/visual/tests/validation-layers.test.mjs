/** FV-UI-030: separa diagnósticos de regra, UI, contratos e navegador.
 * Redesign NÃO dispensa regressão de tudo antes da homologação.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
import {spawnSync} from 'node:child_process';

const here=dirname(fileURLToPath(import.meta.url));
const manifest=JSON.parse(readFileSync(join(here,'validation-layers.json'),'utf8'));
const layers=manifest.layers;
const groups=['domain','interaction','source'];
const all=groups.flatMap(k=>layers[k].node_tests);
const suites=readdirSync(here).filter(s=>s.endsWith('.test.mjs')).sort();

test('FV-UI-030: toda suíte Node tem uma única classificação diagnóstica',()=>{
  assert.equal(manifest.schema,'frontend-validation-layers/1');
  assert.equal(manifest.scope,'synthetic_frontend_only');
  assert.equal(manifest.full_acceptance,false);
  assert.equal(new Set(all).size,all.length,'suíte presente em mais de uma camada');
  assert.deepEqual([...all].sort(),suites,'suíte ausente/extra na matriz');
  assert.equal(layers.browser.python_script,'browser.smoke.py');
});

test('FV-UI-030: comportamento fica distinguível de CSS e smoke continua obrigatório',()=>{
  for(const group of groups){
    assert.ok(layers[group].node_tests.length>0,group);
    for(const file of layers[group].node_tests)
      assert.match(file,/^[a-z0-9]+(?:[.-][a-z0-9]+)*\.test\.mjs$/);
  }
  for(const file of ['app.dom.test.mjs','app.mobile.dom.test.mjs','attention-integration.test.mjs'])
    assert.ok(layers.interaction.node_tests.includes(file),file);
  for(const file of ['source-contract.test.mjs','source-module-graph.test.mjs','offline-export-manifest.test.mjs'])
    assert.ok(layers.source.node_tests.includes(file),file);
  assert.ok(!layers.interaction.node_tests.includes('source-contract.test.mjs'));
  assert.ok(!layers.domain.node_tests.includes('source-contract.test.mjs'));
  assert.match(layers.browser.description,/depois de mudar o layout/);
});

test('FV-UI-030: executor recusa camada não mapeada sem disparar testes',()=>{
  const run=spawnSync(process.execPath,[join(here,'run_validation_layers.mjs'),'unknown'],{
    encoding:'utf8',timeout:7000
  });
  assert.equal(run.status,2,run.stderr);
  assert.match(run.stderr,/Camada desconhecida/);
  const help=spawnSync(process.execPath,[join(here,'run_validation_layers.mjs'),'--help'],{
    encoding:'utf8',timeout:7000
  });
  assert.equal(help.status,0,help.stderr);
  assert.match(help.stdout,/não equivale a homologação/);
});
