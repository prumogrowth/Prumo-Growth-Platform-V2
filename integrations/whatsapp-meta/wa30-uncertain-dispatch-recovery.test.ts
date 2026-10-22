import test from 'node:test';
import assert from 'node:assert/strict';
import {classifyWa30RecoverySnapshot as classify} from './wa30-uncertain-dispatch-recovery.ts';

const row=(outcome:unknown)=>({
  outcome, retry_external:false,send_authorized:false,ack_allowed:false,
  production_authorized:false,delivery_confirmed:false,
  definitive_failure_count_increment:false,case_transition_authorized:false,
});
const safe=(r:ReturnType<typeof classify>)=>{
  for(const k of ['retry_external','send_authorized','ack_allowed',
    'production_authorized','delivery_confirmed','definitive_failure_count_increment',
    'case_transition_authorized'] as const)assert.equal(r[k],false);
  assert.equal(Object.isFrozen(r),true);
  assert.equal(Object.keys(r).length,8);
};
const cases=[
 ['LAB_CLAIM_UNRESOLVED','LAB_HOLD_UNRESOLVED'],
 ['LAB_ABSENT_UNKNOWN','LAB_ABSENT_STILL_UNCERTAIN'],
 ['LAB_PROVIDER_ACCEPTED_UNVERIFIED','LAB_ACCEPTED_NOT_SENT'],
 ['LAB_SENT_UNVERIFIED','LAB_SENT_REPORTED_UNVERIFIED'],
 ['LAB_FAILURE_UNVERIFIED','LAB_FAILURE_REPORTED_UNVERIFIED'],
 ['LAB_INVALIDATED','LAB_INVALIDATED_HOLD'],
 ['LAB_CONFLICT','LAB_CONFLICT_QUARANTINE'],
] as const;
for(const [i,[x,y]] of cases.entries()){
 test('WA30-'+String(i+1).padStart(2,'0')+' '+x+' cannot authorize Graph/cadence',()=>{
   const decision=classify(row(x)); assert.equal(decision.decision,y);safe(decision);
 });
}
test('WA30-08 no evidence, partial evidence and nonobjects fail closed',()=>{
 for(const x of [null,undefined,{},[],false,42,'LAB_SENT_UNVERIFIED',
    {outcome:'LAB_SENT_UNVERIFIED'},Object.create(null)]){
   const d=classify(x);assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');safe(d);
 }
});
test('WA30-09 forbid all extra keys including provider message identifier',()=>{
 for(const key of ['wamid','recipient','shop_ref','access_token','commercial_state']){
  const d=classify({...row('LAB_SENT_UNVERIFIED'),[key]:'simulated'});
  assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');safe(d);
 }
});
test('WA30-10 forbid missing keys even when sent is claimed',()=>{
 for(const key of Object.keys(row('LAB_SENT_UNVERIFIED'))){
  const x={...row('LAB_SENT_UNVERIFIED')};
  delete (x as Record<string,unknown>)[key];
  assert.equal(classify(x).decision,'LAB_UNTRUSTED_SNAPSHOT');
 }
});
test('WA30-11 reject any positive authority flag regardless of evidence state',()=>{
 for(const key of ['retry_external','send_authorized','ack_allowed',
 'production_authorized','delivery_confirmed','definitive_failure_count_increment',
 'case_transition_authorized']){
  for(const outcome of cases.map(x=>x[0]))
   assert.equal(classify({...row(outcome),[key]:true}).decision,'LAB_UNTRUSTED_SNAPSHOT');
 }
});
test('WA30-12 nonboolean false-like flags cannot bypass schema',()=>{
 for(const value of ['false',0,null,undefined]){
  assert.equal(classify({...row('LAB_SENT_UNVERIFIED'),ack_allowed:value}).decision,
    'LAB_UNTRUSTED_SNAPSHOT');
 }
});
test('WA30-13 no invented outcome can upgrade an unverified signal',()=>{
 for(const x of ['SENT','delivered','API_ACCEPTED','COMMIT_UNKNOWN','DEFINITIVE_FAILURE',
  'LAB_FOUND_EXACT','LAB_ALREADY_CLAIMED_NO_RETRY','GRAPH_POST_OK']){
  assert.equal(classify(row(x)).decision,'LAB_UNTRUSTED_SNAPSHOT');
 }
});
test('WA30-14 hostile accessors, proxies and custom prototypes are denied',()=>{
 const accessor=row('LAB_SENT_UNVERIFIED');
 Object.defineProperty(accessor,'outcome',{get(){throw Error('LEAK')}});
 assert.equal(classify(accessor).decision,'LAB_UNTRUSTED_SNAPSHOT');
 const trapped=new Proxy(row('LAB_SENT_UNVERIFIED'),{ownKeys(){throw Error('PROXY')}});
 assert.equal(classify(trapped).decision,'LAB_UNTRUSTED_SNAPSHOT');
 assert.equal(classify(Object.assign(Object.create({fake:1}),row('LAB_SENT_UNVERIFIED'))).decision,
   'LAB_UNTRUSTED_SNAPSHOT');
});
test('WA30-15 accepted does not become Meta sent or increase technical-failure streak',()=>{
 const d=classify(row('LAB_PROVIDER_ACCEPTED_UNVERIFIED'));
 assert.equal(d.decision,'LAB_ACCEPTED_NOT_SENT');safe(d);
});
test('WA30-16 same for reported failure: zero definitive failure cadence increments',()=>{
 const d=classify(row('LAB_FAILURE_UNVERIFIED'));safe(d);
 assert.equal(d.definitive_failure_count_increment,false);
});
test('WA30-17 no field exposes a provider receipt or token',()=>{
 const s=JSON.stringify(classify(row('LAB_CLAIM_UNRESOLVED')));
 for(const name of ['wamid','receipt','access_token','case_ref','shop_ref','Graph','sent_at'])
   assert.equal(s.includes(name),false);
});
test('WA30-18 exotic unknown symbol keys cannot hide extra authority',()=>{
 const x=Object.assign(row('LAB_SENT_UNVERIFIED'),{[Symbol('private')]:true});
 assert.equal(classify(x).decision,'LAB_UNTRUSTED_SNAPSHOT');
});
