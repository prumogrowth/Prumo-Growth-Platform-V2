import test from 'node:test';
import assert from 'node:assert/strict';
import {
  PROPOSED_UQ_FAMILIES, S0_READ_PROPOSAL_VERSION,
  stageProposedS0ReadEnvelope
} from '../s0-read-contract.mjs';

const expected = (query_id='UQ01') => ({
  query_id, query_version:'candidate-1', request_id:'request-fixture-01',
  correlation_id:'corr-fixture-01', actor_id:'operator-fixture',
  scope_ref:'opaque-scope-fixture', returned_projection:'minimized-test-view'
});
const envelope = (input=expected()) => ({
  ...input, schema_version:S0_READ_PROPOSAL_VERSION,
  source_of_truth_version:'fixture-version-1', as_of:'T0 fictício',
  leitura_minimizada:true, outcome:{status:'APPLIED',reason_code:null},
  records:[{case_ref:'case-fixture-1',status_comercial:'em atendimento pelo operador'}],
  next_cursor:null
});

const rejects = (response,input=expected()) => {
  const value=stageProposedS0ReadEnvelope(response,input);
  assert.equal(value.accepted,false);
  assert.equal(value.code,'UNTRUSTED_READ_PROJECTION');
  assert.deepEqual(value.records,[]);
  assert.equal(value.nextCursor,null);
  assert.equal(value.sourceVersion,null);
  assert.equal(JSON.stringify(value).includes('case-fixture-1'),false);
};

test('UQ01–UQ09: nove famílias propostas podem receber envelope fictício íntegro',()=>{
  assert.deepEqual(PROPOSED_UQ_FAMILIES, ['UQ01','UQ02','UQ03','UQ04','UQ05','UQ06','UQ07','UQ08','UQ09']);
  for(const query_id of PROPOSED_UQ_FAMILIES){
    const req=expected(query_id),reply=envelope(req);
    const value=stageProposedS0ReadEnvelope(reply,req);
    assert.equal(value.accepted,true,query_id);
    assert.equal(value.records.length,1);
    assert.equal(value.sourceVersion,'fixture-version-1');
  }
});

test('envelope falha fechado com resposta ou contexto malformados',()=>{
  for(const malformed of [null,undefined,'text',true,[],0,new Date(),new Map()]){
    rejects(malformed);
    if (malformed === undefined)
      assert.equal(stageProposedS0ReadEnvelope(envelope(),undefined).accepted,false);
    else rejects(envelope(),malformed);
  }
  rejects(envelope(),{...expected(),query_id:'C19'});
});

test('desvio de ator, escopo, identificador, correlação ou versão é negado',()=>{
  const req=expected(), valid=envelope(req);
  for(const key of ['query_id','query_version','request_id','correlation_id','actor_id','scope_ref','returned_projection']){
    rejects({...valid,[key]:'other-fixture'},req);
    rejects({...valid,[key]:null},req);
    rejects({...valid}, {...req,[key]:null});
  }
  rejects({...valid,schema_version:'unknown'},req);
});

test('resultado negado ou não comprovado não entrega registros nem cursor',()=>{
  const input=expected(), valid=envelope(input);
  for(const status of ['FORBIDDEN_SCOPE','PENDING_EXTERNAL','UNKNOWN','ACCEPTED_FOR_PROCESSING',null]){
    rejects({...valid,outcome:{status,reason_code:'FORBIDDEN_SCOPE'},next_cursor:'private-cursor'},input);
  }
  rejects({...valid,outcome:{status:'APPLIED',reason_code:'PROOF_REQUIRED'}},input);
  rejects({...valid,outcome:{status:'APPLIED',reason_code:null},leitura_minimizada:false},input);
});

test('registros não-array, objetos arbitrários e cursores malformados são negados',()=>{
  const ok=envelope();
  for(const records of [null,'case-fixture-1',{case_ref:'secret'},[null],[123],[[]],[new Date()]])
    rejects({...ok,records});
  for(const next_cursor of [false,1,{},[],'   '])
    rejects({...ok,next_cursor});
  for(const source_of_truth_version of [null,'',false])
    rejects({...ok,source_of_truth_version});
});

test('leitura aceita copia registros; projeção não implementa permissão no S0',()=>{
  const reply=envelope(),value=stageProposedS0ReadEnvelope(reply,expected());
  assert.equal(value.accepted,true);
  assert.notEqual(value.records,reply.records);
  assert.notEqual(value.records[0],reply.records[0]);
  reply.records[0].case_ref='altered-after-handshake';
  assert.equal(value.records[0].case_ref,'case-fixture-1');
  assert.ok(Object.isFrozen(value.records));
});

test('ausência de fonte, data e lista explicitamente minimizada nega por padrão',()=>{
  const base=envelope();
  for(const change of [{as_of:''},{source_of_truth_version:null},
    {leitura_minimizada:undefined},{records:undefined},{outcome:undefined}])
    rejects({...base,...change});
});
