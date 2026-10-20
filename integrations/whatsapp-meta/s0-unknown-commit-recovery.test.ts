import test from 'node:test';
import assert from 'node:assert/strict';
import { classifyUnknownCommitRecovery as classify } from './s0-unknown-commit-recovery.ts';
const row=(outcome:string)=>({
  outcome,ack_allowed:false,retry_external:false,production_authorized:false,
});
const flags=(x:ReturnType<typeof classify>)=>{
  assert.deepEqual(
    {retry_external:x.retry_external,ack_allowed:x.ack_allowed,
      production_authorized:x.production_authorized,delivery_confirmed:x.delivery_confirmed},
    {retry_external:false,ack_allowed:false,production_authorized:false,delivery_confirmed:false},
  );
  assert.equal(Object.isFrozen(x),true);
};
test('WA16-01 exact DB lookup after lost commit reply means durable binding, never Graph delivery',()=>{
 const r=classify(row('LAB_FOUND_EXACT'));
 assert.equal(r.decision,'LAB_CONFIRMED_DURABLE');flags(r);
});
test('WA16-02 LAB_ABSENT means COMMIT still externally uncertain, NEVER a resend signal',()=>{
 const r=classify(row('LAB_ABSENT'));
 assert.equal(r.decision,'LAB_ABSENT_STILL_UNCERTAIN');flags(r);
});
test('WA16-03 mismatched attempt or wamid gets quarantine, not retry',()=>{
 const r=classify(row('LAB_CONFLICT'));
 assert.equal(r.decision,'LAB_CONFLICT_QUARANTINE');flags(r);
});
test('WA16-04 lost read response remains unknown, not an invented LAB_ABSENT',()=>{
 for(const x of [null,undefined,{},42,'LAB_FOUND_EXACT',[],false]){
  const r=classify(x);assert.equal(r.decision,'LAB_UNTRUSTED_RECOVERY');flags(r);
 }
});
test('WA16-05 writer outcomes are not recovery evidence',()=>{
 for(const kind of ['LAB_BOUND','LAB_REPLAY','COMMIT_UNKNOWN','API_ACCEPTED','sent','delivered']){
  const r=classify(row(kind));
  assert.equal(r.decision,'LAB_UNTRUSTED_RECOVERY');flags(r);
 }
});
test('WA16-06 forged retry, ACK or production flags disqualify otherwise exact read',()=>{
 for(const key of ['ack_allowed','retry_external','production_authorized'] as const){
  const r=classify({...row('LAB_FOUND_EXACT'),[key]:true});
  assert.equal(r.decision,'LAB_UNTRUSTED_RECOVERY');flags(r);
 }
});
test('WA16-07 missing or extra fields disqualify JSON claimed as S0 row',()=>{
 for(const x of [
  {outcome:'LAB_FOUND_EXACT'},
  {...row('LAB_FOUND_EXACT'),token:'fake'},
  {...row('LAB_FOUND_EXACT'),actor:'postgres'},
  {...row('LAB_FOUND_EXACT'),commercial_status:'vendido'},
 ]){
  assert.equal(classify(x).decision,'LAB_UNTRUSTED_RECOVERY');
 }
});
test('WA16-08 reject accessors, hostile proxies and exotic prototypes',()=>{
 const withGetter=row('LAB_FOUND_EXACT');
 Object.defineProperty(withGetter,'outcome',{get(){throw Error('GETTER');}});
 assert.equal(classify(withGetter).decision,'LAB_UNTRUSTED_RECOVERY');
 const trap=new Proxy(row('LAB_FOUND_EXACT'),{ownKeys(){throw Error('PROXY');}});
 assert.equal(classify(trap).decision,'LAB_UNTRUSTED_RECOVERY');
 assert.equal(classify(Object.assign(Object.create({v:'inherited'}),row('LAB_FOUND_EXACT'))).decision,
   'LAB_UNTRUSTED_RECOVERY');
});
test('WA16-09 reject nonboolean false-like flags, fail closed',()=>{
 for(const bad of [0,'false',null,undefined]){
  assert.equal(classify({...row('LAB_FOUND_EXACT'),retry_external:bad}).decision,
    'LAB_UNTRUSTED_RECOVERY');
 }
});
test('WA16-10 no identifiers or immutable outcome are exposed in decision',()=>{
 const r=classify(row('LAB_FOUND_EXACT'));
 const serialized=JSON.stringify(r);
 for(const token of ['wamid.','concessionaria_id','attempt_id','credential','http_status',
     'commercial_status','access_token'])
   assert.equal(serialized.includes(token),false);
 flags(r);
});
