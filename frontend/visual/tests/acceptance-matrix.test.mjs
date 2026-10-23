import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';

const here=dirname(fileURLToPath(import.meta.url));
const manifest=JSON.parse(readFileSync(join(here,'acceptance-matrix.json'),'utf8'));
const expected=Array.from({length:16},(_,i)=>'FV-22-'+String(i+1).padStart(2,'0'));

test('FV-UI-020: matriz contém os dezesseis critérios, sem lacunas',()=>{
  assert.equal(manifest.schema,'frontend-fv22-acceptance-evidence/0.1');
  assert.deepEqual(manifest.criteria.map(c=>c.id),expected);
  assert.equal(manifest.homologated,false);
  assert.equal(manifest.scope,'synthetic_frontend_only');
});

test('FV-UI-020: matriz aponta para testes reais e somente da frente',()=>{
  for(const c of manifest.criteria){
    assert.ok(['prototype_only','partial','external_blocked'].includes(c.coverage),c.id);
    assert.ok(Array.isArray(c.tests) && c.tests.length>0,c.id);
    assert.equal(new Set(c.tests).size,c.tests.length);
    for(const filename of c.tests){
      assert.match(filename,/^[a-z0-9]+(?:[.-][a-z0-9]+)*\.test\.mjs$/);
      assert.ok(existsSync(join(here,filename)),c.id+' missing '+filename);
    }
  }
});

test('FV-UI-020: rastreabilidade não se confunde com homologação',()=>{
  assert.ok(manifest.criteria.some(c=>c.coverage==='external_blocked'));
  assert.ok(manifest.criteria.some(c=>c.coverage==='partial'));
  for(const forbidden of ['complete','homologated','production'])
    assert.equal(manifest.criteria.some(c=>c.coverage===forbidden),false);
});
