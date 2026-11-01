import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {inspectS0V02ForM18Offline as adapt,VERSION}
 from './adapter.mjs';
const v='prumo.s0.pre-dispatch.readback/0.2-lab';
const flags={
 lab_only:true,host_authenticated:false,consent_source_authenticated:false,
 m09_host_authenticated:false,provider_approval_verified:false,
 external_lease_issued:false,graph_dispatch_authorized:false,
 send_authorized:false,automatic_retry_authorized:false,ack_allowed:false,
 production_authorized:false,commercial_transition_authorized:false};
const stage=()=>({contract_version:v,status:'LAB_RESERVATION_STAGED_BEFORE_COMMIT',
 reason:'READBACK_REQUIRED',...flags,commit_verified:false,
 quota_slot_recorded_lab_only:1});
const read=()=>({contract_version:v,status:'LAB_COMMITTED_RECEIPT_NO_DISPATCH',
 reason:'DURABLE_PG17_LAB_ONLY_NOT_REDEEMABLE',...flags,
 commit_verified:true,quota_slot_recorded_lab_only:1});
const unknown=()=>({contract_version:v,status:'LAB_COMMIT_UNKNOWN',
 reason:'NO_DURABLE_RECEIPT',...flags,commit_verified:false,
 external_retry_suppressed:true});
function safe(x,reason,committed){
 assert.equal(x.contract_version,VERSION);
 assert.equal(x.decision,'LAB_HOLD_NO_DISPATCH');
 assert.equal(x.reason,reason);
 assert.equal(x.durable_lab_observed,committed);
 assert.equal(x.unbound_to_meta_attempt,true);
 assert.equal(x.wa18_v01_compatible,false);
 assert.equal(x.m18_dispatch_candidate,null);
 for(const k of ['lease_usable','s0_source_authenticated',
  'send_authorized','graph_dispatch_authorized','automatic_retry_authorized',
  'ack_allowed','production_authorized'])
  assert.equal(x[k],false,k);
 assert.ok(Object.isFrozen(x));
}
function denied(x){assert.equal(x.decision,'DENIED');assert.equal(x.m18_dispatch_candidate,null);
 assert.equal(x.send_authorized,false);assert.equal(x.lease_usable,false);}
test('S0-M18-V02-01 durable receipt remains deliberately unbound to Meta',()=>{
 safe(adapt(stage(),read()),'COMMITTED_PG17_BUT_NO_AUTHENTICATED_ATTEMPT_BINDING',true);
});
test('S0-M18-V02-02 no durable event is unknown, never retry',()=>{
 safe(adapt(stage(),unknown()),'COMMIT_UNKNOWN_NO_EXTERNAL_RETRY',false);
});
test('S0-M18-V02-03 stale physical receipt is no-dispatch',()=>{
 safe(adapt(stage(),{...read(),status:'LAB_STALE_NO_DISPATCH',
  reason:'CONSENT_STALE_OR_REVOKED'}),'S0_POLICY_OR_REGISTRY_STALE',true);
});
test('S0-M18-V02-04 cancelled physical receipt is no-dispatch',()=>{
 safe(adapt(stage(),{...read(),status:'LAB_CANCELLED_NO_DISPATCH',
  reason:'CANCELLED_OR_REVOKED'}),'CANCELLED_NO_DISPATCH',true);
});
test('S0-M18-V02-05 expired physical receipt is no-dispatch',()=>{
 safe(adapt(stage(),{...read(),status:'LAB_EXPIRED_NO_DISPATCH',
  reason:'DEADLINE_PASSED'}),'EXPIRED_NO_DISPATCH',true);
});
test('S0-M18-V02-06 invalidated prior receipt is no-dispatch',()=>{
 safe(adapt(stage(),{...read(),status:'LAB_INVALIDATED_NO_DISPATCH',
  reason:'MISSING_OR_REVOKED_BASE'}),'ORIGINAL_RESERVATION_INVALIDATED',true);
});
test('S0-M18-V02-07 exact replay stage cannot become a lease',()=>{
 safe(adapt({...stage(),status:'LAB_REPLAY_REQUIRES_READBACK',
  reason:'NO_COMMIT_ASSERTION',original_attempt_ref:'attempt_A'},read()),
  'COMMITTED_PG17_BUT_NO_AUTHENTICATED_ATTEMPT_BINDING',true);
});
test('S0-M18-V02-08 cancel staged followed by cancelled',()=>{
 safe(adapt({...stage(),status:'LAB_CANCEL_STAGED_BEFORE_COMMIT',
 reason:'READBACK_REQUIRED',quota_slot_recorded_lab_only:undefined},
 {...read(),status:'LAB_CANCELLED_NO_DISPATCH',
 reason:'CANCELLED_OR_REVOKED'}),'CANCELLED_NO_DISPATCH',true);
});
test('S0-M18-V02-09 forged true send_authorized is rejected',()=>{
 denied(adapt(stage(),{...read(),send_authorized:true}));
});
test('S0-M18-V02-10 forged operational host authentication rejected',()=>{
 denied(adapt(stage(),{...read(),host_authenticated:true}));
});
test('S0-M18-V02-11 forged operational lease rejected',()=>{
 denied(adapt(stage(),{...read(),external_lease_issued:true}));
});
test('S0-M18-V02-12 forged commit on stage rejected',()=>{
 denied(adapt({...stage(),commit_verified:true},read()));
});
test('S0-M18-V02-13 forged commit on unknown rejected',()=>{
 denied(adapt(stage(),{...unknown(),commit_verified:true}));
});
test('S0-M18-V02-14 false committed flag on success rejected',()=>{
 denied(adapt(stage(),{...read(),commit_verified:false}));
});
test('S0-M18-V02-15 arbitrary response field cannot claim lease',()=>{
 denied(adapt(stage(),{...read(),sendToken:'FAKE'}));
});
test('S0-M18-V02-16 legacy v0.1 is never accepted as v0.2',()=>{
 denied(adapt(stage(),{...read(),contract_version:
 'prumo.s0.pre-dispatch.pg17/0.1-lab-only'}));
});
test('S0-M18-V02-17 missing commit proof denied',()=>{
 const x={...read()};delete x.commit_verified;
 denied(adapt(stage(),x));
});
test('S0-M18-V02-18 malicious getter never invoked',()=>{
 let n=0;const x=read();
 Object.defineProperty(x,'status',{enumerable:true,get(){n++;return 'LAB_COMMITTED_RECEIPT_NO_DISPATCH'}});
 denied(adapt(stage(),x));assert.equal(n,0);
});
test('S0-M18-V02-19 missing stage is not proof for M18',()=>{
 denied(adapt(null,read()));
});
test('S0-M18-V02-20 missing readback never produces preview',()=>{
 denied(adapt(stage(),null));
});
test('S0-M18-V02-21 rollback stage cannot be inferred committed',()=>{
 safe(adapt(stage(),unknown()),'COMMIT_UNKNOWN_NO_EXTERNAL_RETRY',false);
});
test('S0-M18-V02-22 noncanonical output status denied',()=>{
 denied(adapt(stage(),{...read(),status:'GRAPH_AUTHORIZED'}));
});
test('S0-M18-V02-23 readback source DENIED remains hold',()=>{
 safe(adapt(stage(),{contract_version:v,status:'DENIED',
 reason:'INVALID_REQUEST',...flags}),'SOURCE_DENIED_OR_UNAVAILABLE',false);
});
test('S0-M18-V02-24 readback source UNAVAILABLE remains hold',()=>{
 safe(adapt(stage(),{contract_version:v,status:'UNAVAILABLE',
 reason:'DEPENDENCY_UNAVAILABLE',...flags}),'SOURCE_DENIED_OR_UNAVAILABLE',false);
});
const artifactPath=process.env.M18_V02_PG17_FIXTURE;
let artifact=null;
if(artifactPath)artifact=JSON.parse(readFileSync(artifactPath,'utf8'));
test('S0-M18-V02-25 actual PG17 success after independent COMMIT is no-send',
 {skip:!artifact},()=>{
 safe(adapt(artifact.positive.stage,artifact.positive.readback),
 'COMMITTED_PG17_BUT_NO_AUTHENTICATED_ATTEMPT_BINDING',true);
});
test('S0-M18-V02-26 actual PG17 exact replay cannot become lease',
 {skip:!artifact},()=>{
 safe(adapt(artifact.positive.replay,artifact.positive.readback),
 'COMMITTED_PG17_BUT_NO_AUTHENTICATED_ATTEMPT_BINDING',true);
});
test('S0-M18-V02-27 actual PG17 rollback is unknown',
 {skip:!artifact},()=>{
 safe(adapt(artifact.rollback.stage,artifact.rollback.readback),
 'COMMIT_UNKNOWN_NO_EXTERNAL_RETRY',false);
});
test('S0-M18-V02-28 actual PG17 consent revoked invalidates receipt',
 {skip:!artifact},()=>{
 safe(adapt(artifact.stale.stage,artifact.stale.readback),
 'S0_POLICY_OR_REGISTRY_STALE',true);
});
test('S0-M18-V02-29 actual PG17 cancelled receipt remains no-send',
 {skip:!artifact},()=>{
 safe(adapt(artifact.cancelled.stage,artifact.cancelled.readback),
 'CANCELLED_NO_DISPATCH',true);
});
test('S0-M18-V02-30 actual PG17 expired receipt remains no-send',
 {skip:!artifact},()=>{
 safe(adapt(artifact.expired.stage,artifact.expired.readback),
 'EXPIRED_NO_DISPATCH',true);
});
test('S0-M18-V02-31 actual PG17 status injection rejected',
 {skip:!artifact},()=>{
 denied(adapt(artifact.positive.stage,
 {...artifact.positive.readback,graph_dispatch_authorized:true}));
});
let wa18=null;
if(process.env.M18_META_PIN){
 const uri=pathToFileURL(resolve(process.env.M18_META_PIN,
  'integrations/whatsapp-meta/wa18-dispatch-boundary-offline.ts')).href;
 wa18=await import(uri);
}
// Independently valid synthetic M18 consumer inputs: NOT a conversion of
// store-A / WABA physical PG17. Proves the original Meta interface refuses
// the actual v0.2 response type rather than silently aliasing it to v0.1.
function metaIntent(){
 return {
 contract_version:'wa18-dispatch-intent.lab.v0.1',
 selection_ref:'selection_A',attempt_ref:'attempt_A',intent_ref:'intent_A',
 concessionaria_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
 app_ref:'APP_A',waba_id:'100001',phone_number_id:'200001',
 case_ref:'case_A',service_ref:'M09_KEY_A',
 template_ref:'tpl_A',template_version_ref:'ver_1',
 template_purpose_ref:'followup_message',consent_purpose_ref:'lead_followup',
 campaign_ref:'camp_A',plan_revision:1,case_revision:1,
 assignment_revision:1,policy_revision:1,suppression_revision:1,
 consent_revision:1,template_revision:1,campaign_revision:1,
 grant_revision:1,registry_revision:1,
 content_sha256:'b'.repeat(64),recipient_sha256:'a'.repeat(64),
 now_ms:1800000000000,max_age_ms:60000};
}
function metaBinding(i){
 const {contract_version,now_ms,max_age_ms,...scoped}=i;
 return {...scoped,contract_version:'wa18-s0-binding-claim.lab.v0.1',
  reservation_state:'LAB_HELD_NO_DISPATCH',commit_state:'LAB_COMMIT_CLAIMED',
  observed_at_ms:i.now_ms-1000};
}
function metaRate(i){
 return {contract_version:'wa18-rate-budget.lab.v0.1',
  concessionaria_id:i.concessionaria_id,app_ref:i.app_ref,
  phone_number_id:i.phone_number_id,
  rate_revision:1,observed_at_ms:i.now_ms-1000,
  available_slots:1,throttled_until_ms:null,budget_state:'LAB_AVAILABLE'};
}
test('S0-M18-V02-32 pinned Meta M18 directly rejects positive S0 v0.2',
 {skip:!wa18||!artifact},()=>{
 const i=metaIntent();
 const v02=artifact.positive.readback;
 const x=wa18.inspectWa18DispatchOffline(i,v02,metaBinding(i),metaRate(i));
 assert.equal(x.decision,'DENIED');assert.equal(x.reason,'INVALID_INPUT');
 assert.equal(x.graph_dispatch_authorized,false);
 assert.equal(x.send_authorized,false);
});
test('S0-M18-V02-33 pinned Meta M18 directly rejects S0 unknown v0.2',
 {skip:!wa18||!artifact},()=>{
 const i=metaIntent();
 const x=wa18.inspectWa18DispatchOffline(i,artifact.rollback.readback,
  metaBinding(i),metaRate(i));
 assert.equal(x.decision,'DENIED');assert.equal(x.reason,'INVALID_INPUT');
});
test('S0-M18-V02-34 original Meta M18 positive lab model is still no authority',
 {skip:!wa18},()=>{
 const i=metaIntent(),s={
  contract_version:'prumo.s0.pre-dispatch.pg17/0.1-lab-only',
  decision:'LAB_RESERVATION_RECORDED_NO_DISPATCH',reason:null,
  lab_reservation_recorded:true,send_authorized:false,
  graph_authorized:false,credential_resolution_authorized:false,
  pre_dispatch_operationally_authorized:false,
  provider_approval_verified:false,consent_proven_from_real_source:false,
  external_http_ack:false,production_authorized:false,
  commercial_transition_authorized:false};
 const o=wa18.inspectWa18DispatchOffline(i,s,metaBinding(i),metaRate(i));
 assert.equal(o.decision,'LAB_DISPATCH_COHERENT_NOT_AUTHORIZED');
 assert.equal(o.candidate.reservation_committed_verified,false);
 assert.equal(o.candidate.requires_independent_commit_readback,true);
 assert.equal(o.graph_dispatch_authorized,false);
 assert.equal(o.send_authorized,false);
});
