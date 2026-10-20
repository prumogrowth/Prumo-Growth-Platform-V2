import assert from 'node:assert/strict';
import test from 'node:test';
import {HUMAN_COMMAND_IDS,S0_COMMAND_RESULT_PROPOSAL,S0_COMMAND_OUTCOMES,
  stageCandidateCommandResult} from '../s0-command-result.mjs';

const expected=(id='C11')=>({contract_id:id,contract_version:'proposal-1',
  request_id:'request-fake',correlation_id:'corr-fake',
  actor_id:'actor-fake',scope_ref:'scope-fake',
  aggregate_ref:'case-fake',expected_version:'before-fake'});
const response=(status='APPLIED',context=expected())=>({...context,
  schema_version:S0_COMMAND_RESULT_PROPOSAL,
  outcome:{status,reason_code:null,
    ...(status==='APPLIED'||status==='ALREADY_APPLIED'?{
      confirmed_persisted:true,effect_id:'event-fake',source_of_truth_version:'after-fake'
    }:{})}});
const denied=(r,e=expected())=>{
  const v=stageCandidateCommandResult(r,e);
  assert.equal(v.accepted,false);assert.equal(v.hasVerifiedEffect,false);
  assert.equal(v.canRefresh,false);assert.equal(v.displayState,'untrusted');
  assert.equal(JSON.stringify(v).includes('case-fake'),false);
};

test('somente IDs de comandos humanos explicitamente candidatos',()=>{
  assert.deepEqual(HUMAN_COMMAND_IDS,['C11','C12','C13','C15','C16','C17','C18']);
  for(const id of HUMAN_COMMAND_IDS){
    const v=stageCandidateCommandResult(response('APPLIED',expected(id)),expected(id));
    assert.equal(v.displayState,'claimed_applied');
    assert.equal(v.hasVerifiedEffect,false);
  }
  denied(response('APPLIED',expected('C14')),expected('C14'));
  denied(response('APPLIED',expected('C21')),expected('C21'));
});

test('aceito para processamento ou dependente de fornecedor nunca é aplicado',()=>{
  for(const status of ['ACCEPTED_FOR_PROCESSING','PENDING_EXTERNAL','UNCERTAIN_EXTERNAL']){
    const v=stageCandidateCommandResult(response(status),expected());
    assert.equal(v.accepted,true);assert.equal(v.displayState,'pending');
    assert.equal(v.hasVerifiedEffect,false);assert.equal(v.canRefresh,true);
  }
  assert.deepEqual(S0_COMMAND_OUTCOMES,['APPLIED','ALREADY_APPLIED','ACCEPTED_FOR_PROCESSING',
    'PENDING_EXTERNAL','UNCERTAIN_EXTERNAL','REJECTED']);
});

test('APPLIED e ALREADY_APPLIED demandam marcador de persistência, versão e efeito',()=>{
  for(const status of ['APPLIED','ALREADY_APPLIED']){
    const x=response(status);
    for(const outcome of [
      {...x.outcome,confirmed_persisted:false},
      {...x.outcome,effect_id:null},
      {...x.outcome,source_of_truth_version:''},
      {...x.outcome,reason_code:'PROOF_REQUIRED'}
    ])denied({...x,outcome});
    const v=stageCandidateCommandResult(x,expected());
    assert.equal(v.displayState,'claimed_applied');
    assert.equal(v.hasVerifiedEffect,false,'Fronteira de apresentação não autentica efeito');
  }
});

test('REJECTED só classifica recusa com motivo, sem vazamento do payload bruto',()=>{
  const base=response('REJECTED');
  base.outcome.reason_code='CONFLICT_VERSION';
  base.secret='must-not-leak';
  const v=stageCandidateCommandResult(base,expected());
  assert.equal(v.displayState,'rejected');
  assert.equal(JSON.stringify(v).includes('must-not-leak'),false);
  denied({...base,outcome:{status:'REJECTED',reason_code:null}});
  denied({...base,outcome:{...base.outcome,effect_id:'some-effect'}});
});

test('nunca misturar ator, loja, comando, versão, objeto ou request/correlation',()=>{
  const ctx=expected(),ok=response('APPLIED',ctx);
  for(const k of Object.keys(ctx)){
    denied({...ok,[k]:'forged-other'},ctx);
    denied({...ok,[k]:null},ctx);
    denied(ok,{...ctx,[k]:null});
  }
  denied({...ok,schema_version:'legacy'},ctx);
});

test('resultados e contextos malformados sempre falham fechados',()=>{
  for(const bad of [null,undefined,false,123,'APPLIED',[],new Date(),new Map()]){
    denied(bad);
    if(bad===undefined) assert.equal(stageCandidateCommandResult(response('APPLIED'),undefined).accepted,false);
    else denied(response('APPLIED'),bad);
  }
  for(const bad of [null,[],{status:'APPLIED'},'APPLIED',
    {status:'SOLD',reason_code:null},{status:'ALREADY_APPLIED',effect_id:'x'}])
    denied({...response('APPLIED'),outcome:bad});
});

test('status pendente não pode carregar efeito já confirmado sem prova',()=>{
  for(const state of ['PENDING_EXTERNAL','UNCERTAIN_EXTERNAL','ACCEPTED_FOR_PROCESSING']){
    const ok=response(state);
    denied({...ok,outcome:{...ok.outcome,effect_id:'claimed-effect'}});
    denied({...ok,outcome:{...ok.outcome,confirmed_persisted:true}});
    denied({...ok,outcome:{...ok.outcome,source_of_truth_version:'next'}});
    denied({...ok,outcome:{...ok.outcome,reason_code:'FORBIDDEN'}});
  }
});

test('a classificação não muta o recebimento nem cria status comercial',()=>{
  const r=response('ALREADY_APPLIED');
  const original=structuredClone(r);
  const value=stageCandidateCommandResult(r,expected());
  assert.deepEqual(r,original);
  assert.equal('commercial_status' in value,false);
  assert.equal('bank_approved' in value,false);
  assert.equal('actor_id' in value,false);
});
