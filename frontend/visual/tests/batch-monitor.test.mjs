import test from 'node:test';
import assert from 'node:assert/strict';
import { DEMO_BATCHES, BATCH_PHASES, batchPhaseCopy, projectManagerBatches } from '../batch-monitor.mjs';

test('G4-01: Marina só consulta lotes de sua própria equipe mesmo na mesma loja',()=>{
  const p=projectManagerBatches('marina');
  assert.equal(p.visibility,'ready');
  assert.deepEqual(p.batches.map(x=>x.id),['L-G4-01','L-G4-02']);
  assert.equal(p.batches.some(x=>x.id==='L-G4-03'),false);
  assert.equal(p.totals.confirmedBatches,1);
});
test('G4-02: Daniel não vê lotes de Marina e usa somente suas lojas elegíveis',()=>{
  const p=projectManagerBatches('daniel');
  assert.deepEqual(p.batches.map(x=>x.id),['L-G4-03','L-G4-04']);
  assert.equal(p.totals.distributionBlocked,1);
});
test('G4-03: operador, suspenso e gestor desconhecido não recebem projeção',()=>{
  for(const id of ['rafael','bianca','otavio','inexistente']){
    const p=projectManagerBatches(id);
    assert.equal(p.visibility,'forbidden');
    assert.equal(p.totals,null);
    assert.deepEqual(p.batches,[]);
  }
});
test('G4-04: contagens precisam de confirmação, versão e consistência aritmética',()=>{
  const valid=DEMO_BATCHES[0];
  const invalid=[
    {...valid,dataVersion:' '},{...valid,countsConfirmed:false},
    {...valid,received:9},{...valid,quarantined:-1},{...valid,eligible:'10'},
    {...valid,phase:'under_review'}
  ];
  for(const batch of invalid){
    const p=projectManagerBatches('marina',[batch]).batches[0];
    assert.equal(p.countsConfirmed,false);
    assert.equal(p.received,null);
    assert.equal(p.versionRef,null);
    assert.equal(p.quarantined,null);
  }
});
test('G4-05: condição recebida/revisão não significa lote validado',()=>{
  const p=projectManagerBatches('marina');
  const row=p.batches.find(x=>x.id==='L-G4-02');
  assert.equal(row.countsConfirmed,false);
  assert.equal(row.received,null);
  assert.match(row.label,/Conferência pendente/);
});
test('G4-06: gestor não herda lote apenas porque tem concessionária em comum',()=>{
  const all=DEMO_BATCHES.map(x=>({...x}));
  const first=projectManagerBatches('marina',all);
  const second=projectManagerBatches('daniel',all);
  assert.equal(first.batches.some(x=>x.id==='L-G4-03'),false);
  assert.equal(second.batches.some(x=>x.id==='L-G4-01'),false);
});
test('G4-07: loja fora de concessão não libera lote mesmo com gestor indicado',()=>{
  const forged={...DEMO_BATCHES[0],shopId:'nao_concedida'};
  const p=projectManagerBatches('marina',[forged]);
  assert.deepEqual(p.batches,[]);
});
test('G4-08: gerente não consegue associar lote à loja sem operador elegível da equipe',()=>{
  const injected={...DEMO_BATCHES[0],managerId:'marina',shopId:'horizonte'};
  const p=projectManagerBatches('marina',[injected]);
  assert.equal(p.batches.length,1); // Lia está concedida a Horizonte pelo responsável.
  const invalid={...injected,shopId:'loja_c'};
  assert.equal(projectManagerBatches('marina',[invalid]).batches.length,0);
});
test('G4-09: projeção nunca expõe nomes de clientes, linhas CSV nem documentos',()=>{
  const data=JSON.stringify(projectManagerBatches('marina'));
  for(const secret of ['Cliente Exemplo','cpf','phone','rowContent','documentBytes']){
    assert.equal(data.includes(secret),false);
  }
});
test('G4-10: processamento de lotes é somente leitura e não altera fixtures',()=>{
  const snapshot=JSON.stringify(DEMO_BATCHES);
  projectManagerBatches('marina');
  projectManagerBatches('daniel');
  assert.equal(JSON.stringify(DEMO_BATCHES),snapshot);
  assert.equal(projectManagerBatches('marina').batches[0].actionAvailable,false);
});
test('G4-11: fases são técnicas, não criam status de venda/perda',()=>{
  assert.equal(BATCH_PHASES.includes('vendido'),false);
  assert.equal(BATCH_PHASES.includes('perdido'),false);
  assert.match(batchPhaseCopy('BAD'),/sem confirmação/);
});
