import test from 'node:test';
import assert from 'node:assert/strict';
import {FakeAttemptCommitBoundary} from './attempt-commit-simulation.ts';
import {FakeAttemptBindingLedger, snapshotAttemptIdentity} from './attempt-binding.ts';
const a={app_ref:'APP_A',concessionaria_id:'SHOP_A',canal_id:'CHANNEL_A',
  waba_id:'WABA_A',phone_number_id:'12345678901',intent_id:'INTENT_A',
  attempt_id:'ATTEMPT_A',correlation_id:'CORR_A',recipient_verified:'5581900000000',
  provider_message_id:'wamid.OUT_A'};
const g={attempt_id:'ATTEMPT_A',correlation_id:'CORR_A',send_state:'API_ACCEPTED',
  api_accepted:true,http_status:200,provider_message_id:'wamid.OUT_A',
  meta_error_code:null,meta_error_subcode:null,retry_automatically:false};
const unsafe=(result:unknown)=>{
  const text=JSON.stringify(result);
  for(const sensitive of ['wamid.',a.recipient_verified,a.app_ref,'access_token','http_status','commercial_status'])
    assert.equal(text.includes(sensitive),false);
  assert.equal((result as {retry_external:boolean}).retry_external,false);
  assert.equal((result as {ack_allowed:boolean}).ack_allowed,false);
  assert.equal((result as {production_authorized:boolean}).production_authorized,false);
};
test('WA12-01: accepted Graph binding is LAB only, with no delivery or ACK',()=>{
  const x=new FakeAttemptCommitBoundary();const result=x.recordAcceptedFixture(a,g);
  assert.equal(result.decision,'LAB_COMMITTED');assert.equal(x.bindingCount,1);unsafe(result);
  assert.equal(x.recoverExactFixture(a).decision,'LAB_FOUND_EXACT');
});
test('WA12-02: post-commit response loss is UNKNOWN to caller, read-only query finds binding',()=>{
  const x=new FakeAttemptCommitBoundary();const result=x.recordAcceptedFixture(a,g,'after_commit_response_lost');
  assert.equal(result.decision,'LAB_COMMIT_UNKNOWN');assert.equal(x.bindingCount,1);
  assert.equal(x.recoverExactFixture(a).decision,'LAB_FOUND_EXACT');unsafe(result);
});
test('WA12-03: pre-commit response loss is equally UNKNOWN, query returns ABSENT, no retry',()=>{
  const x=new FakeAttemptCommitBoundary();const result=x.recordAcceptedFixture(a,g,'before_commit_response_lost');
  assert.equal(result.decision,'LAB_COMMIT_UNKNOWN');assert.equal(x.bindingCount,0);
  assert.equal(x.recoverExactFixture(a).decision,'LAB_ABSENT');unsafe(result);
});
test('WA12-04: recovery is truly read-only even when records do not exist',()=>{
  const x=new FakeAttemptCommitBoundary();
  for(let i=0;i<10;i++)assert.equal(x.recoverExactFixture(a).decision,'LAB_ABSENT');
  assert.equal(x.bindingCount,0);
});
test('WA12-05: idempotent same observation never creates extra binding',()=>{
  const x=new FakeAttemptCommitBoundary();
  assert.equal(x.recordAcceptedFixture(a,g).decision,'LAB_COMMITTED');
  assert.equal(x.recordAcceptedFixture(a,g).decision,'LAB_COMMITTED');
  assert.equal(x.bindingCount,1);
});
test('WA12-06: conflicting wamid for same attempt is rejected, no new record',()=>{
  const x=new FakeAttemptCommitBoundary();x.recordAcceptedFixture(a,g);
  const b={...a,provider_message_id:'wamid.OTHER'};
  assert.equal(x.recordAcceptedFixture(b,{...g,provider_message_id:'wamid.OTHER'}).decision,'LAB_CONFLICT');
  assert.equal(x.recoverExactFixture(b).decision,'LAB_CONFLICT');
  assert.equal(x.bindingCount,1);
});
test('WA12-07: two attempts on same scoped wamid conflict without mutation',()=>{
  const x=new FakeAttemptCommitBoundary();x.recordAcceptedFixture(a,g);
  const b={...a,attempt_id:'ATTEMPT_B'};
  assert.equal(x.recordAcceptedFixture(b,{...g,attempt_id:'ATTEMPT_B'}).decision,'LAB_CONFLICT');
  assert.equal(x.recoverExactFixture(b).decision,'LAB_CONFLICT');
  assert.equal(x.bindingCount,1);
});
test('WA12-08: isolated App scopes may use equal wamids but cannot exchange references',()=>{
  const x=new FakeAttemptCommitBoundary();x.recordAcceptedFixture(a,g);
  const b={...a,app_ref:'APP_B',concessionaria_id:'SHOP_B',attempt_id:'ATTEMPT_B'};
  assert.equal(x.recordAcceptedFixture(b,{...g,attempt_id:'ATTEMPT_B'}).decision,'LAB_COMMITTED');
  assert.equal(x.bindingCount,2);
  assert.equal(x.recoverExactFixture({...a,app_ref:'APP_B'}).decision,'LAB_CONFLICT');
});
test('WA12-09: Graph HTTP 2xx is necessary; false, uncertain, or errored is rejected',()=>{
  const x=new FakeAttemptCommitBoundary();
  for(const ev of [{...g,http_status:500},{...g,api_accepted:false},
   {...g,send_state:'UNCERTAIN_EXTERNAL'}, {...g,provider_message_id:null},
   {...g,meta_error_code:100}, {...g,retry_automatically:true}]){
    assert.equal(x.recordAcceptedFixture(a,ev).decision,'LAB_REJECTED');
  }
  assert.equal(x.bindingCount,0);
});
test('WA12-10: mismatched outcome attempt, correlation and wamid refuse association',()=>{
  const x=new FakeAttemptCommitBoundary();
  for(const ev of [{...g,attempt_id:'ATTEMPT_X'}, {...g,correlation_id:'CORR_X'},
    {...g,provider_message_id:'wamid.X'}])
    assert.equal(x.recordAcceptedFixture(a,ev).decision,'LAB_REJECTED');
  assert.equal(x.bindingCount,0);
});
test('WA12-11: getter and additional keys on Graph record are rejected',()=>{
  const x=new FakeAttemptCommitBoundary();const getter={...g};
  Object.defineProperty(getter,'http_status',{get(){throw Error('GETTER');}});
  for(const ev of [getter,{...g,access_token:'SECRET'},null,[]])
    assert.equal(x.recordAcceptedFixture(a,ev).decision,'LAB_REJECTED');
  assert.equal(x.bindingCount,0);
});
test('WA12-12: adversarial Proxy getter cannot alter observed accepted message ID',()=>{
  const x=new FakeAttemptCommitBoundary();
  const hostile=new Proxy({...g},{get(target,key,receiver){
    if(key==='provider_message_id')return 'wamid.HOSTILE';
    return Reflect.get(target,key,receiver);
  }});
  assert.equal(x.recordAcceptedFixture(a,hostile).decision,'LAB_COMMITTED');
  assert.equal(x.recoverExactFixture(a).decision,'LAB_FOUND_EXACT');
});
test('WA12-13: no supported failure mode converts unknown into retry permission',()=>{
  const x=new FakeAttemptCommitBoundary();
  for(const fault of ['before_commit_response_lost','after_commit_response_lost'] as const){
    const r=x.recordAcceptedFixture(a,g,fault);unsafe(r);assert.equal(r.decision,'LAB_COMMIT_UNKNOWN');
  }
});
test('WA12-14: invalid inputs fail closed and never alter the ledger',()=>{
  const x=new FakeAttemptCommitBoundary();
  for(const value of [{...a,attempt_id:123},{...a,recipient_verified:'BAD'},
    {...a,extra:'FIELD'},null,[], {...a,provider_message_id:'x'}]){
    assert.equal(x.recordAcceptedFixture(value,g).decision,'LAB_REJECTED');
    assert.equal(x.recoverExactFixture(value).decision,'LAB_INVALID');
  }
  assert.equal(x.recordAcceptedFixture(a,g,'INVALID' as 'none').decision,'LAB_REJECTED');
  assert.equal(x.bindingCount,0);
});
test('WA12-15: direct ledger lookup preserves WA-11 bidirectional invariants',()=>{
  const j=new FakeAttemptBindingLedger();
  assert.equal(j.lookup(a),'ABSENT');assert.equal(j.size,0);
  assert.equal(j.claim(a),'NEW');assert.equal(j.lookup(a),'SAME');
  assert.equal(j.lookup({...a,attempt_id:'OTHER'}),'CONFLICT');
  assert.equal(j.lookup({...a,provider_message_id:'wamid.OTHER'}),'CONFLICT');
  assert.equal(j.size,1);
});
test('WA12-16: validated identity is immutable independent of mutable caller object',()=>{
  const raw={...a};const frozen=snapshotAttemptIdentity(raw);
  assert.ok(frozen);assert.equal(Object.isFrozen(frozen),true);
  raw.attempt_id='ATTEMPT_CHANGED';
  assert.equal(frozen.attempt_id,'ATTEMPT_A');
});
test('WA12-17: new fixture instance has no durable state and cannot attest old writes',()=>{
  const x=new FakeAttemptCommitBoundary();x.recordAcceptedFixture(a,g,'after_commit_response_lost');
  const restarted=new FakeAttemptCommitBoundary();
  assert.equal(restarted.recoverExactFixture(a).decision,'LAB_ABSENT');
  assert.equal(x.recoverExactFixture(a).decision,'LAB_FOUND_EXACT');
});
