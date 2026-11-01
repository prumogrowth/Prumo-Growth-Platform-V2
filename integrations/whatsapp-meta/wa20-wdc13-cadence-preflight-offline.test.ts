import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectWa20Wdc13Offline as inspect,
 recheckWa20Wdc13Offline as recheck}
 from './wa20-wdc13-cadence-preflight-offline.ts';

const NOW=1800000000000,SHOP='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const context=()=>({
 contract_version:'wa20-cadence-claim.lab.v0.1',
 concessionaria_id:SHOP,app_ref:'APP_A',waba_ref:'WABA_A',
 phone_number_id:'10000001',case_ref:'CASE_A',flow_ref:'FLOW_A',
 plan_ref:'PLAN_A',cadence_ref:'CADENCE_A',plan_revision:7,
 case_revision:9,evidence_revision:11,observed_at_ms:NOW-1000,
 now_ms:NOW,max_age_ms:60000,cadence_state:'LAB_ACTIVE',
 s0_source_authenticated:false,attempt_correlation_verified:false,
 definitive_classification_verified:false,durable_evidence_verified:false,
});
const attempt=(status='LAB_DEFINITIVE_FAILURE_CLAIM',n=1)=>({
 contract_version:'wa20-attempt-claim.lab.v0.1',
 concessionaria_id:SHOP,app_ref:'APP_A',waba_ref:'WABA_A',
 phone_number_id:'10000001',case_ref:'CASE_A',
 flow_ref:'FLOW_A',plan_ref:'PLAN_A',cadence_ref:'CADENCE_A',
 attempt_ref:'ATTEMPT_'+n,intent_ref:'INTENT_'+n,sequence_no:n,
 template_ref:'TPL_A',template_version_ref:'TPL_V1',
 is_final_template:false,event_ref:'EVT_'+n,
 event_sha256:'a'.repeat(64),provider_error_code:
  status==='LAB_DEFINITIVE_FAILURE_CLAIM'?131049:null,
 status_claim:status,observed_at_ms:NOW-1000,
});
const fail=()=>attempt();
const sent=(n=1)=>attempt('LAB_SENT_CLAIM',n);
const unknown=(n=1)=>attempt('LAB_UNKNOWN_CLAIM',n);
const conflict=(n=1)=>attempt('LAB_CONFLICT_CLAIM',n);
const pending=(n=1)=>attempt('LAB_PENDING_CLAIM',n);
const run=(ctx:unknown=context(),arr:unknown[]=[])=>inspect(ctx,arr);
type Outcome=ReturnType<typeof run>;
function safe(x:Outcome,decision?:string){
 assert.equal(x.reason,null);
 if(decision)assert.equal(x.decision,decision);
 assert.ok(x.snapshot);assert.equal(Object.isFrozen(x),true);
 assert.equal(Object.isFrozen(x.snapshot),true);
 assert.equal(x.snapshot!.requires_s0_recheck,true);
 assert.equal(x.snapshot!.requires_authenticated_evidence,true);
 assert.match(x.snapshot!.snapshot_sha256,/^[a-f0-9]{64}$/);
 for(const k of ['s0_source_authenticated','attempt_correlation_verified',
  'definitive_classification_verified','sent_verified','failure_verified',
  'wdc13_increment_authorized','wdc13_transition_authorized',
  'c09_window_authorized','f02_replan_authorized',
  'automatic_retry_authorized','send_authorized',
  'production_authorized'] as const){
  assert.equal(x[k],false,k);
  assert.equal(x.snapshot![k],false,k);
 }
 const wire=JSON.stringify(x);
 for(const v of [SHOP,'ATTEMPT_','INTENT_','APP_A','CASE_A','FLOW_A','CADENCE_A'])
  assert.equal(wire.includes(v),false,v);
 return x.snapshot!;
}
function denied(x:Outcome,reason?:string){
 assert.equal(x.decision,'DENIED');assert.equal(x.snapshot,null);
 if(reason)assert.equal(x.reason,reason);
 assert.equal(x.production_authorized,false);
 assert.equal(x.wdc13_transition_authorized,false);
 assert.equal(Object.isFrozen(x),true);
}
test('M20-01 no attempts means insufficient unverified evidence',()=>{
 const s=safe(run(),'LAB_NO_ATTEMPTS_UNVERIFIED');
 assert.equal(s.attempts_examined,0);
});
test('M20-02 one LAB definitive failure is below threshold',()=>{
 const s=safe(run(context(),[fail()]),'LAB_BELOW_TWO_UNVERIFIED');
 assert.equal(s.consecutive_failure_claims_at_tail,1);
});
test('M20-03 two consecutive LAB definitive failure claims candidate only',()=>{
 const s=safe(run(context(),[fail(),fail2()]),
  'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED');
 assert.equal(s.two_consecutive_failure_claims_at_tail,true);
});
function fail2(){return attempt('LAB_DEFINITIVE_FAILURE_CLAIM',2);}
test('M20-04 three LAB failure claims remain nonauthorizing',()=>{
 const s=safe(run(context(),[fail(),fail2(),attempt('LAB_DEFINITIVE_FAILURE_CLAIM',3)]),
  'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED');
 assert.equal(s.consecutive_failure_claims_at_tail,3);
});
test('M20-05 sent claim resets prior single failure',()=>{
 const s=safe(run(context(),[fail(),sent(2)]),'LAB_BELOW_TWO_UNVERIFIED');
 assert.equal(s.consecutive_failure_claims_at_tail,0);
});
test('M20-06 sent between failures breaks consecutiveness',()=>{
 const s=safe(run(context(),[fail(),sent(2),attempt('LAB_DEFINITIVE_FAILURE_CLAIM',3)]),
 'LAB_BELOW_TWO_UNVERIFIED');
 assert.equal(s.consecutive_failure_claims_at_tail,1);
});
test('M20-07 sent after two failures clears current threshold',()=>{
 const s=safe(run(context(),[fail(),fail2(),sent(3)]),
 'LAB_BELOW_TWO_UNVERIFIED');
 assert.equal(s.two_consecutive_failure_claims_at_tail,false);
});
test('M20-08 new two failures after sent create new candidate only',()=>{
 const s=safe(run(context(),[fail(),sent(2),
  attempt('LAB_DEFINITIVE_FAILURE_CLAIM',3),
  attempt('LAB_DEFINITIVE_FAILURE_CLAIM',4)]),
  'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED');
 assert.equal(s.consecutive_failure_claims_at_tail,2);
});
test('M20-09 no customer reply required for claimed sent reset',()=>{
 const s=safe(run(context(),[fail(),sent(2)]),'LAB_BELOW_TWO_UNVERIFIED');
 assert.equal(s.claimed_sent_reset_count,1);
});
test('M20-10 API_ACCEPTED cannot be treated as sent',()=>{
 const a=attempt('API_ACCEPTED');
 denied(run(context(),[a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-11 Graph timeout cannot be definitive failure claim by default',()=>{
 const a=attempt('TIMEOUT');
 denied(run(context(),[a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-12 HTTP ACK cannot count as status evidence',()=>{
 const a=attempt('HTTP_ACK');
 denied(run(context(),[a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-13 UNKNOWN between failures holds the cadence',()=>{
 safe(run(context(),[fail(),unknown(2),
  attempt('LAB_DEFINITIVE_FAILURE_CLAIM',3)]),
  'LAB_HOLD_UNCERTAIN_OR_CONFLICT');
});
test('M20-14 two post-unknown failures without sent still hold',()=>{
 const s=safe(run(context(),[unknown(),fail2(),
  attempt('LAB_DEFINITIVE_FAILURE_CLAIM',3)]),
  'LAB_HOLD_UNCERTAIN_OR_CONFLICT');
 assert.equal(s.two_consecutive_failure_claims_at_tail,false);
});
test('M20-15 later claimed sent can end historical hold in lab',()=>{
 const s=safe(run(context(),[unknown(),sent(2),attempt('LAB_DEFINITIVE_FAILURE_CLAIM',3)]),
  'LAB_BELOW_TWO_UNVERIFIED');
 assert.equal(s.unknown_or_conflict_seen,true);
});
test('M20-16 PENDING holds and never increments WDC-13',()=>{
 safe(run(context(),[fail(),pending(2)]),
  'LAB_HOLD_UNCERTAIN_OR_CONFLICT');
});
test('M20-17 CONFLICT holds even if two failure claims follow',()=>{
 safe(run(context(),[conflict(),fail2(),attempt('LAB_DEFINITIVE_FAILURE_CLAIM',3)]),
  'LAB_HOLD_UNCERTAIN_OR_CONFLICT');
});
test('M20-18 conflict after two failures prevents candidate',()=>{
 safe(run(context(),[fail(),fail2(),conflict(3)]),
  'LAB_HOLD_UNCERTAIN_OR_CONFLICT');
});
test('M20-19 invalidated cadence never yields candidate',()=>{
 const c=context();c.cadence_state='LAB_REVOKED';
 safe(run(c,[fail(),fail2()]),'LAB_INACTIVE_HOLD');
});
test('M20-20 paused cadence never yields candidate',()=>{
 const c=context();c.cadence_state='LAB_PAUSED';
 safe(run(c,[fail(),fail2()]),'LAB_INACTIVE_HOLD');
});
test('M20-21 a single status diagnostic code 131049 is not WDC-13 authority',()=>{
 const s=safe(run(context(),[fail()]),'LAB_BELOW_TWO_UNVERIFIED');
 assert.equal(s.wdc13_increment_authorized,false);
});
test('M20-22 failed claim without an error code is still LAB-only',()=>{
 const a=fail();a.provider_error_code=null;
 safe(run(context(),[a]),'LAB_BELOW_TWO_UNVERIFIED');
});
test('M20-23 sent with failure error code is internally contradictory',()=>{
 const a=sent();a.provider_error_code=131049;
 denied(run(context(),[a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-24 duplicate attempt ID cannot double count',()=>{
 const a=fail(),b=fail2();b.attempt_ref=a.attempt_ref;
 denied(run(context(),[a,b]),'SEQUENCE_GAP_OR_DUPLICATE');
});
test('M20-25 duplicate intent cannot be mistaken for two separate attempts',()=>{
 const a=fail(),b=fail2();b.intent_ref=a.intent_ref;
 denied(run(context(),[a,b]),'SEQUENCE_GAP_OR_DUPLICATE');
});
test('M20-26 duplicate sequence index rejected',()=>{
 const a=fail(),b=fail2();b.sequence_no=1;
 denied(run(context(),[a,b]),'SEQUENCE_GAP_OR_DUPLICATE');
});
test('M20-27 missing first attempt in claimed history refused',()=>{
 denied(run(context(),[fail2()]),'SEQUENCE_GAP_OR_DUPLICATE');
});
test('M20-28 missing middle attempt refused',()=>{
 const xs=[fail(),attempt('LAB_DEFINITIVE_FAILURE_CLAIM',3)];
 denied(run(context(),xs),'SEQUENCE_GAP_OR_DUPLICATE');
});
test('M20-29 unordered but complete sequence canonicalizes',()=>{
 const a=safe(run(context(),[fail(),fail2()]),
  'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED');
 const b=safe(run(context(),[fail2(),fail()]),
  'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED');
 assert.equal(a.snapshot_sha256,b.snapshot_sha256);
});
test('M20-30 changed failed event digest changes snapshot',()=>{
 const x=safe(run(context(),[fail(),fail2()]),
 'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED');
 const b=fail2();b.event_sha256='b'.repeat(64);
 const y=safe(run(context(),[fail(),b]),
 'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED');
 assert.notEqual(x.snapshot_sha256,y.snapshot_sha256);
});
test('M20-31 changed plan revision changes snapshot',()=>{
 const x=safe(run(context(),[fail()]));
 const c=context();c.plan_revision++;
 const y=safe(run(c,[fail()]));
 assert.notEqual(x.snapshot_sha256,y.snapshot_sha256);
});
test('M20-32 changed evidence revision changes snapshot',()=>{
 const x=safe(run(context(),[fail()]));
 const c=context();c.evidence_revision++;
 const y=safe(run(c,[fail()]));
 assert.notEqual(x.snapshot_sha256,y.snapshot_sha256);
});
test('M20-33 changed template final bit changes snapshot but never opens C09',()=>{
 const x=safe(run(context(),[sent()]));
 const a=sent();a.is_final_template=true;
 const y=safe(run(context(),[a]));
 assert.notEqual(x.snapshot_sha256,y.snapshot_sha256);
 assert.equal(y.c09_window_authorized,false);
});
test('M20-34 stale S0 claim is refused',()=>{
 const c=context();c.observed_at_ms=NOW-60001;
 denied(run(c,[]),'SNAPSHOT_STALE_OR_FUTURE');
});
test('M20-35 future S0 claim is refused',()=>{
 const c=context();c.observed_at_ms=NOW+1;
 denied(run(c,[]),'SNAPSHOT_STALE_OR_FUTURE');
});
test('M20-36 stale attempt claim refused',()=>{
 const a=fail();a.observed_at_ms=NOW-60001;
 denied(run(context(),[a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-37 future attempt claim refused',()=>{
 const a=fail();a.observed_at_ms=NOW+1;
 denied(run(context(),[a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-38 caller declaring S0 source authenticated is refused',()=>{
 const c=context();c.s0_source_authenticated=true;
 denied(run(c,[fail()]),'INVALID_INPUT');
});
test('M20-39 caller declaring definitive verified is refused',()=>{
 const c=context();c.definitive_classification_verified=true;
 denied(run(c,[fail()]),'INVALID_INPUT');
});
test('M20-40 caller declaring attempt correlation verified is refused',()=>{
 const c=context();c.attempt_correlation_verified=true;
 denied(run(c,[fail()]),'INVALID_INPUT');
});
test('M20-41 hidden commercial override in input refused',()=>{
 const c:any=context();c.close_case=true;
 denied(run(c,[fail(),fail2()]),'INVALID_INPUT');
});
test('M20-42 extra attempt proof-of-send field refused',()=>{
 const a:any=sent();a.sent_verified=true;
 denied(run(context(),[a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-43 context getter not executed',()=>{
 const c:any=context();let hits=0;
 Object.defineProperty(c,'cadence_state',{enumerable:true,
  get(){hits++;return 'LAB_ACTIVE';}});
 denied(run(c,[]),'INVALID_INPUT');assert.equal(hits,0);
});
test('M20-44 attempt getter not executed',()=>{
 const a:any=fail();let hits=0;
 Object.defineProperty(a,'status_claim',{enumerable:true,
  get(){hits++;return 'LAB_DEFINITIVE_FAILURE_CLAIM';}});
 denied(run(context(),[a]),'ATTEMPT_SCOPE_DENIED');assert.equal(hits,0);
});
test('M20-45 sparse attempt array refused',()=>{
 const a:any[]=[fail()];a.length=2;
 denied(run(context(),a),'INVALID_INPUT');
});
test('M20-46 array exceeding 40 is refused before computation',()=>{
 const xs=Array.from({length:41},(_,i)=>attempt('LAB_SENT_CLAIM',i+1));
 denied(run(context(),xs),'INVALID_INPUT');
});
test('M20-47 stable recheck preserves LAB-only analysis',()=>{
 const old=safe(run(context(),[fail(),fail2()]),
 'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED');
 const y=recheck(old,context(),[fail2(),fail()]);
 safe(y,'LAB_RECHECKED_UNVERIFIED');
});
test('M20-48 changed status between snapshots fails recheck',()=>{
 const old=safe(run(context(),[fail(),fail2()]));
 denied(recheck(old,context(),[fail(),sent(2)]),
  'SNAPSHOT_OR_CONTEXT_CHANGED');
});
test('M20-49 changed time but same revisions fails recheck',()=>{
 const old=safe(run(context(),[fail()]));
 const c=context();c.now_ms=NOW+1;
 denied(recheck(old,c,[fail()]),'SNAPSHOT_OR_CONTEXT_CHANGED');
});
test('M20-50 forged positive authority on old candidate denied',()=>{
 const old=safe(run(context(),[fail(),fail2()]));
 denied(recheck({...old,wdc13_transition_authorized:true},
  context(),[fail(),fail2()]),'INVALID_PREVIOUS');
});
test('M20-51 previous output digest tampering denied',()=>{
 const old=safe(run(context(),[fail(),fail2()]));
 denied(recheck({...old,snapshot_sha256:'f'.repeat(64)},
  context(),[fail(),fail2()]),'SNAPSHOT_OR_CONTEXT_CHANGED');
});
test('M20-52 claimed sent of final template does not create C09 window',()=>{
 const a=sent();a.is_final_template=true;
 const s=safe(run(context(),[a]),'LAB_BELOW_TWO_UNVERIFIED');
 assert.equal(s.c09_window_authorized,false);
 assert.equal(s.f02_replan_authorized,false);
});


test('M20-53 cross-concessionaria attempt cannot count',()=>{
 const a=fail2();a.concessionaria_id='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
 denied(run(context(),[fail(),a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-54 cross-WABA attempt cannot count',()=>{
 const a=fail2();a.waba_ref='WABA_FOREIGN';
 denied(run(context(),[fail(),a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-55 cross-sender attempt cannot count',()=>{
 const a=fail2();a.phone_number_id='10000009';
 denied(run(context(),[fail(),a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-56 cross-case attempt cannot count',()=>{
 const a=fail2();a.case_ref='CASE_OTHER';
 denied(run(context(),[fail(),a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-57 cross-cadence attempt cannot count',()=>{
 const a=fail2();a.cadence_ref='CADENCE_OTHER';
 denied(run(context(),[fail(),a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-58 cross-plan attempt cannot count',()=>{
 const a=fail2();a.plan_ref='PLAN_OTHER';
 denied(run(context(),[fail(),a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-59 cross-flow attempt cannot count',()=>{
 const a=fail2();a.flow_ref='FLOW_OTHER';
 denied(run(context(),[fail(),a]),'ATTEMPT_SCOPE_DENIED');
});
test('M20-60 cross-App attempt cannot count',()=>{
 const a=fail2();a.app_ref='APP_OTHER';
 denied(run(context(),[fail(),a]),'ATTEMPT_SCOPE_DENIED');
});
