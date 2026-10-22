import test from 'node:test';
import assert from 'node:assert/strict';
import {classifyWa31LateEvidence as classify} from './wa31-late-evidence-classifier.ts';
const fake=(outcome:unknown)=>({
 outcome,retry_external:false,send_authorized:false,ack_allowed:false,
 production_authorized:false,delivery_confirmed:false,
 definitive_failure_count_increment:false,case_transition_authorized:false,
});
const flags=(d:ReturnType<typeof classify>)=>{
 assert.equal(Object.isFrozen(d),true);
 assert.equal(Object.keys(d).length,8);
 for(const k of ['retry_external','send_authorized','ack_allowed',
  'production_authorized','delivery_confirmed','definitive_failure_count_increment',
  'case_transition_authorized'] as const)assert.equal(d[k],false);
};
const cases=[
 ['LAB_EMPTY_CLAIM','LAB_NO_OBSERVATIONS'],
 ['LAB_ACTIVE_OBSERVATION','LAB_ACTIVE_EVIDENCE_UNVERIFIED'],
 ['LAB_INVALIDATED_EMPTY','LAB_INVALIDATED_NO_OBSERVATIONS'],
 ['LAB_INVALIDATED_HISTORICAL','LAB_INVALIDATED_HISTORICAL_UNVERIFIED'],
 ['LAB_LATE_OBSERVATION','LAB_POST_REVOCATION_UNVERIFIED'],
 ['LAB_KIND_CONFLICT','LAB_QUARANTINE_CONFLICT'],
 ['LAB_NO_CLAIM','LAB_ABSENT_OR_WRONG_SCOPE'],
] as const;
for(const [i,[raw,decision]] of cases.entries()){
 test('WA31-'+String(i+1).padStart(2,'0')+' '+raw,()=>{
  const d=classify(fake(raw));assert.equal(d.decision,decision);flags(d);
 });
}
test('WA31-08 incorrect evidence cannot become a Graph or delivery fact',()=>{
 for(const x of ['sent','delivered','API_ACCEPTED','GRAPH_OK',
   'LAB_ALREADY_CLAIMED_NO_RETRY','DEFINITIVE_FAILURE','']) {
  const d=classify(fake(x));assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');flags(d);
 }
});
test('WA31-09 reject nonobjects and absent envelope',()=>{
 for(const x of [null,undefined,0,42,'LAB_LATE_OBSERVATION',[],false,{}]){
  const d=classify(x);assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');flags(d);
 }
});
test('WA31-10 reject every missing field',()=>{
 for(const key of Object.keys(fake('LAB_LATE_OBSERVATION'))){
  const x={...fake('LAB_LATE_OBSERVATION')};
  delete (x as Record<string,unknown>)[key];
  assert.equal(classify(x).decision,'LAB_UNTRUSTED_SNAPSHOT');
 }
});
test('WA31-11 reject extra IDs/tokens/client-supplied metadata',()=>{
 for(const key of ['wamid','receipt_id','case_ref','shop_ref','access_token','actor_ref']){
  const d=classify({...fake('LAB_LATE_OBSERVATION'),[key]:'fake'});
  assert.equal(d.decision,'LAB_UNTRUSTED_SNAPSHOT');flags(d);
 }
});
test('WA31-12 reject each elevated flag for any allowed outcome',()=>{
 for(const key of ['retry_external','send_authorized','ack_allowed',
   'production_authorized','delivery_confirmed','definitive_failure_count_increment',
   'case_transition_authorized'])for(const [o] of cases){
   assert.equal(classify({...fake(o),[key]:true}).decision,'LAB_UNTRUSTED_SNAPSHOT');
 }
});
test('WA31-13 reject false-like flags',()=>{
 for(const bad of [null,0,'false',undefined]){
  assert.equal(classify({...fake('LAB_LATE_OBSERVATION'),retry_external:bad}).decision,
    'LAB_UNTRUSTED_SNAPSHOT');
 }
});
test('WA31-14 forged getters, proxy and non-plain prototypes cannot bypass',()=>{
 const x=fake('LAB_LATE_OBSERVATION');
 Object.defineProperty(x,'outcome',{get(){throw Error('GETTER')}});
 assert.equal(classify(x).decision,'LAB_UNTRUSTED_SNAPSHOT');
 const px=new Proxy(fake('LAB_LATE_OBSERVATION'),{ownKeys(){throw Error('PROXY')}});
 assert.equal(classify(px).decision,'LAB_UNTRUSTED_SNAPSHOT');
 const inherited=Object.assign(Object.create({role:'director'}),fake('LAB_LATE_OBSERVATION'));
 assert.equal(classify(inherited).decision,'LAB_UNTRUSTED_SNAPSHOT');
});
test('WA31-15 symbol field cannot hide extra privileges',()=>{
 const x=Object.assign(fake('LAB_LATE_OBSERVATION'),{[Symbol('auth')]:true});
 assert.equal(classify(x).decision,'LAB_UNTRUSTED_SNAPSHOT');
});
test('WA31-16 frozen output cannot reveal provider content or case identifiers',()=>{
 const s=JSON.stringify(classify(fake('LAB_LATE_OBSERVATION')));
 for(const token of ['wamid','access_token','shop_ref','case_ref','recipient','message_body'])
  assert.equal(s.includes(token),false);
});
test('WA31-17 late report cannot undo revocation or count failure streak',()=>{
 const d=classify(fake('LAB_LATE_OBSERVATION'));
 assert.equal(d.decision,'LAB_POST_REVOCATION_UNVERIFIED');
 flags(d);
});
test('WA31-18 null-prototype plain value may be safely interpreted',()=>{
 const raw=Object.assign(Object.create(null),fake('LAB_NO_CLAIM'));
 const d=classify(raw);assert.equal(d.decision,'LAB_ABSENT_OR_WRONG_SCOPE');flags(d);
});
