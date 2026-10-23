import test from 'node:test';
import assert from 'node:assert/strict';
import {classifyWa38CallbackAggregate as classify} from './wa38-callback-ambiguity-classifier.ts';

const fixture=(outcome:unknown)=>({
 outcome,retry_external:false,send_authorized:false,ack_allowed:false,
 production_authorized:false,delivery_confirmed:false,
 definitive_failure_count_increment:false,case_transition_authorized:false,
});
const safe=(d:ReturnType<typeof classify>)=>{
 assert.ok(Object.isFrozen(d));assert.equal(Object.keys(d).length,8);
 for(const k of ['retry_external','send_authorized','ack_allowed',
  'production_authorized','delivery_confirmed',
  'definitive_failure_count_increment','case_transition_authorized'] as const)
  assert.equal(d[k],false,k);
 const x=JSON.stringify(d);
 for(const sensitive of ['wamid','recipient','phone_number_id','sha256','shop_ref',
 'case_ref','access_token'])assert.equal(x.includes(sensitive),false);
};
const statuses=[
 ['LAB_NONE','LAB_NO_EVIDENCE'],
 ['LAB_SINGLE_UNVERIFIED','LAB_OBSERVATION_UNVERIFIED'],
 ['LAB_LATE_UNVERIFIED','LAB_LATE_EVIDENCE_UNVERIFIED'],
 ['LAB_MULTIPLE_OR_CONFLICT_QUARANTINED','LAB_QUARANTINE_HOLD'],
] as const;
for(let i=0;i<statuses.length;i++){
 const [status,decision]=statuses[i];
 test('WA38-'+String(i+1).padStart(2,'0')+' '+status,()=>{
  const d=classify(fixture(status));assert.equal(d.decision,decision);safe(d);
 });
}
test('WA38-05 no result can report delivery even for variant hold',()=>{
 for(const [status] of statuses)safe(classify(fixture(status)));
});
test('WA38-06 forged sent, failed, accepted and certified statuses fail closed',()=>{
 for(const status of ['sent','delivered','read','failed',
  'LAB_PROVIDER_ACCEPTED_UNVERIFIED','GRAPH_SENT','LAB_CONFIRMED',''])
  assert.equal(classify(fixture(status)).decision,'LAB_UNTRUSTED_SNAPSHOT');
});
test('WA38-07 reject missing required field',()=>{
 for(const k of Object.keys(fixture('LAB_MULTIPLE_OR_CONFLICT_QUARANTINED'))){
  const f={...fixture('LAB_MULTIPLE_OR_CONFLICT_QUARANTINED')};
  delete (f as Record<string,unknown>)[k];
  const d=classify(f);assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');safe(d);
 }
});
test('WA38-08 reject any asserted authority bit',()=>{
 for(const k of ['retry_external','send_authorized','ack_allowed',
 'production_authorized','delivery_confirmed','definitive_failure_count_increment',
 'case_transition_authorized'])for(const [s] of statuses){
  const d=classify({...fixture(s),[k]:true});
  assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');safe(d);
 }
});
test('WA38-09 strings/zero/null are not false in authority bits',()=>{
 for(const value of ['false',0,null,undefined]){
  const d=classify({...fixture('LAB_SINGLE_UNVERIFIED'),retry_external:value});
  assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');safe(d);
 }
});
test('WA38-10 extra body hash, phone or event attributes denied',()=>{
 for(const field of ['body_sha256','event_ref','app_ref','recipient_ref',
  'access_token','tenant_ref']){
  const d=classify({...fixture('LAB_SINGLE_UNVERIFIED'),[field]:'test'});
  assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');safe(d);
 }
});
test('WA38-11 inherited/array/scalar/null snapshots fail closed',()=>{
 for(const x of [null,undefined,42,'LAB_NONE',[],true,{}])
  assert.equal(classify(x).decision,'LAB_UNTRUSTED_SNAPSHOT');
 const inherited=Object.assign(Object.create({privilege:true}),fixture('LAB_NONE'));
 assert.equal(classify(inherited).decision,'LAB_UNTRUSTED_SNAPSHOT');
});
test('WA38-12 throwing ownKeys and getter snapshots fail closed',()=>{
 const proxy=new Proxy(fixture('LAB_NONE'),{ownKeys(){throw Error('trap')}});
 assert.equal(classify(proxy).decision,'LAB_UNTRUSTED_SNAPSHOT');
 const x=fixture('LAB_NONE');
 Object.defineProperty(x,'outcome',{get(){throw Error('getter')}});
 assert.equal(classify(x).decision,'LAB_UNTRUSTED_SNAPSHOT');
});
test('WA38-13 symbol extra key rejected',()=>{
 const x=Object.assign(fixture('LAB_NONE'),{[Symbol('owner')]:true});
 assert.equal(classify(x).decision,'LAB_UNTRUSTED_SNAPSHOT');
});
test('WA38-14 null-prototype but exact data-only snapshot accepted',()=>{
 const x=Object.assign(Object.create(null),fixture('LAB_SINGLE_UNVERIFIED'));
 const d=classify(x);assert.equal(d.decision,'LAB_OBSERVATION_UNVERIFIED');safe(d);
});
test('WA38-15 hostile objects cannot force side effects',()=>{
 const x=new Proxy(fixture('LAB_NONE'),{getPrototypeOf(){throw Error('bad')}});
 const d=classify(x);assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');safe(d);
});
test('WA38-16 output is separate immutable object, never caller snapshot',()=>{
 const x=fixture('LAB_MULTIPLE_OR_CONFLICT_QUARANTINED');
 const d=classify(x);
 assert.notEqual(d,x);assert.ok(Object.isFrozen(d));
 x.outcome='LAB_NONE';
 assert.equal(d.decision,'LAB_QUARANTINE_HOLD');safe(d);
});
