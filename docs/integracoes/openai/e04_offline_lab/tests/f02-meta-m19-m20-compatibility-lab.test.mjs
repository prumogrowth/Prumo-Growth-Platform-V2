import test from 'node:test';
import assert from 'node:assert/strict';
import {WA39_LAB_INPUT,previewWa39F02Projection}
 from '../f02-wa39-consumer-lab.mjs';
import {OFF22_INPUT,OFF22_RESULT,reviewF02MetaM19M20Compatibility as review}
 from '../f02-meta-m19-m20-compatibility-lab.mjs';
const HASH='a'.repeat(64);
function wa39(){
 return previewWa39F02Projection({
  schemaVersion:WA39_LAB_INPUT,
  expected:{storeRef:'shop1',caseRef:'case1',flowRef:'flow1',planRevision:2,
    minEvidenceRevision:4,attempts:[{attemptRef:'attempt1',templateVersionRef:'tplv1',isFinalTemplate:true}]},
  snapshot:{storeRef:'shop1',caseRef:'case1',flowRef:'flow1',planRevision:2,evidenceRevision:4,
    events:[{eventRef:'event1',sequence:1,attemptRef:'attempt1',templateVersionRef:'tplv1',
      phase:'S0_RECONCILED',correlationState:'CORRELATED_SENT',providerErrorCode:null}]}
 });
}
function m19graph(){
 return {
  contract_version:'wa19-graph-status-snapshot.lab.v0.2',snapshot_sha256:HASH,
  decision:'LAB_OBSERVATION_UNVERIFIED',progress:'SENT_OBSERVED',
  unique_occurrences:1,exact_replays:0,conflict_occurrences:0,
  sent_observed_lab:true,delivered_observed_lab:false,read_observed_lab:false,
  failed_observed_lab:false,api_accepted_lab:true,
  source_authenticated:false,attempt_correlation_verified:false,
  sent_verified:false,delivered_verified:false,read_verified:false,
  definitive_failure_verified:false,retry_external:false,send_authorized:false,
  production_authorized:false,ack_allowed:false,case_transition_authorized:false,
  wdc13_increment_authorized:false,c09_window_authorized:false
 };
}
function m19binding(){
 return {
  contract_version:'wa19-status-snapshot.lab.v0.2',snapshot_sha256:HASH,
  observation_count:1,duplicate_count:0,saw_explicit_sent:true,
  saw_delivered:false,saw_read:false,saw_failed:false,
  status:'LAB_SENT_OBSERVED_UNVERIFIED',quarantine_required:false,
  requires_s0_recheck:true,s0_source_authenticated:false,
  callback_hmac_verified:false,attempt_correlation_verified:false,
  durable_persistence_verified:false,sent_verified:false,delivered_verified:false,
  read_verified:false,definitive_failure_verified:false,
  definitive_failure_count_increment:false,case_transition_authorized:false,
  commercial_transition_authorized:false,retry_external:false,
  ack_allowed:false,production_authorized:false
 };
}
function m20(){
 return {
  contract_version:'wa20-wdc13-snapshot.lab.v0.2',snapshot_sha256:HASH,
  decision:'LAB_BELOW_TWO_UNVERIFIED',attempts_examined:1,
  consecutive_failure_claims_at_tail:0,claimed_sent_reset_count:0,
  unknown_or_conflict_seen:false,two_consecutive_failure_claims_at_tail:false,
  requires_s0_recheck:true,requires_authenticated_evidence:true,
  s0_source_authenticated:false,attempt_correlation_verified:false,
  definitive_classification_verified:false,sent_verified:false,
  failure_verified:false,wdc13_increment_authorized:false,
  wdc13_transition_authorized:false,c09_window_authorized:false,
  f02_replan_authorized:false,automatic_retry_authorized:false,
  send_authorized:false,production_authorized:false
 };
}
const fixture=()=>({schemaVersion:OFF22_INPUT,wa39Preview:wa39(),
  m19GraphSnapshot:m19graph(),m19S0BindingSnapshot:m19binding(),m20CadenceSnapshot:m20()});
const forbidden=['shop1','case1','flow1','attempt1','event1','tplv1',HASH,
 'snapshot_sha256','observations','saw_explicit_sent','phone_number_id','wamid'];
function check(mutate,status,reason){
 const x=fixture();if(mutate)mutate(x);
 const before=mutate?null:structuredClone(x);
 const o=review(x);
 assert.equal(o.schemaVersion,OFF22_RESULT);
 assert.equal(o.status,status);
 assert.equal(o.reason,reason);
 assert.equal(Object.isFrozen(o),true);
 for(const k of ['s0SourceAuthenticated','metaProviderAuthenticated','callbackHmacVerified',
  'attemptCorrelationVerified','sentVerified','definitiveFailureVerified',
  'wdc13TransitionAuthorized','c09WindowAuthorized','f02ReplanAuthorized',
  'automaticRetryAuthorized','sendAuthorized','schedulingAuthorized',
  'commercialTransitionAuthorized','productionAuthorized','crossSourceIdentityAttested',
  'rawStatusExposed'])assert.equal(o[k],false,k);
 assert.equal(o.requiresCanonicalS0Wa39Contract,true);
 assert.equal(o.requiresS0TransactionalRecheck,true);
 for(const s of forbidden)assert.ok(!JSON.stringify(o).includes(s),s);
 if(before)assert.deepEqual(x,before);
 return o;
}
const cases=[
 ['three untrusted snapshots never bind to F02',null,'LAB_FINAL_TEMPLATE_HOLD','NO_AUTHENTICATED_C09_SENT'],
 ['M19 sent does not equal verified C09',i=>{i.m19S0BindingSnapshot.saw_explicit_sent=false;},'LAB_FINAL_TEMPLATE_HOLD','NO_AUTHENTICATED_C09_SENT'],
 ['neither M19 snapshot yields sent; remains uncorrelated',i=>{i.m19S0BindingSnapshot.saw_explicit_sent=false;i.m19GraphSnapshot.sent_observed_lab=false;},'LAB_UNCORRELATED_HOLD','NO_SHARED_AUTHENTICATED_ATTEMPT_ID'],
 ['attempt not final cannot authorize any C09',i=>{i.wa39Preview.observations[0].finalTemplateCandidate=false;},'LAB_UNCORRELATED_HOLD','NO_SHARED_AUTHENTICATED_ATTEMPT_ID'],
 ['two alleged failures remain S0-only',i=>{i.m20CadenceSnapshot.decision='LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED';i.m20CadenceSnapshot.consecutive_failure_claims_at_tail=2;i.m20CadenceSnapshot.attempts_examined=2;i.m20CadenceSnapshot.two_consecutive_failure_claims_at_tail=true;},'LAB_WDC13_CANDIDATE_HOLD','S0_EXCLUSIVE_COUNTER'],
 ['M19 graph conflict quarantined',i=>{i.m19GraphSnapshot.decision='LAB_QUARANTINED_CONFLICT';i.m19GraphSnapshot.progress='CONFLICT';i.m19GraphSnapshot.conflict_occurrences=2;},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['M19 graph collision count alone quarantined',i=>{i.m19GraphSnapshot.conflict_occurrences=1;},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['M19 binding quarantine true',i=>{i.m19S0BindingSnapshot.quarantine_required=true;},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['M19 binding conflict status',i=>{i.m19S0BindingSnapshot.status='LAB_CONFLICT_QUARANTINED';},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['M19 binding late invalidation holds',i=>{i.m19S0BindingSnapshot.status='LAB_INVALIDATED_OBSERVATION_HOLD';},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['M20 unknown or conflict holds',i=>{i.m20CadenceSnapshot.decision='LAB_HOLD_UNCERTAIN_OR_CONFLICT';},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['WA39 uncertain holds despite M19 sent',i=>{i.wa39Preview.observations[0].observation='UNCERTAIN_REQUIRES_REVIEW';},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['WA39 quarantined holds',i=>{i.wa39Preview.observations[0].observation='QUARANTINED_REQUIRES_REVIEW';},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['WA39 conflict holds',i=>{i.wa39Preview.observations[0].observation='CONFLICT_REQUIRES_REVIEW';},'LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN'],
 ['M19 graph old version denied',i=>{i.m19GraphSnapshot.contract_version='wa19-graph-status-snapshot.lab.v0.1';},'DENIED','M19_GRAPH_CONTRACT'],
 ['M19 binding old version denied',i=>{i.m19S0BindingSnapshot.contract_version='wa19-status-snapshot.lab.v0.1';},'DENIED','M19_BINDING_CONTRACT'],
 ['M20 old version denied',i=>{i.m20CadenceSnapshot.contract_version='wa20-wdc13-snapshot.lab.v0.1';},'DENIED','M20_CADENCE_CONTRACT'],
 ['WA39 wrong projection version denied',i=>{i.wa39Preview.schemaVersion='other';},'DENIED','WA39_PROJECTION'],
 ['WA39 forged sent verified denied',i=>{i.wa39Preview.observations[0].verified=true;},'DENIED','WA39_PROJECTION'],
 ['WA39 extra authority denied',i=>{i.wa39Preview.wdc13Authorized=true;},'DENIED','WA39_PROJECTION'],
 ['M19 graph forged authenticated source denied',i=>{i.m19GraphSnapshot.source_authenticated=true;},'DENIED','M19_GRAPH_CONTRACT'],
 ['M19 graph forged sent verified denied',i=>{i.m19GraphSnapshot.sent_verified=true;},'DENIED','M19_GRAPH_CONTRACT'],
 ['M19 binding forged callback HMAC denied',i=>{i.m19S0BindingSnapshot.callback_hmac_verified=true;},'DENIED','M19_BINDING_CONTRACT'],
 ['M19 binding forged persistence denied',i=>{i.m19S0BindingSnapshot.durable_persistence_verified=true;},'DENIED','M19_BINDING_CONTRACT'],
 ['M20 forged verified classification denied',i=>{i.m20CadenceSnapshot.definitive_classification_verified=true;},'DENIED','M20_CADENCE_CONTRACT'],
 ['M20 forged transition authorization denied',i=>{i.m20CadenceSnapshot.wdc13_transition_authorized=true;},'DENIED','M20_CADENCE_CONTRACT'],
 ['M19 graph property injection denied',i=>{i.m19GraphSnapshot.phone_number_id='canary';},'DENIED','M19_GRAPH_CONTRACT'],
 ['M20 unexpected event injection denied',i=>{i.m20CadenceSnapshot.attempt_ref='other';},'DENIED','M20_CADENCE_CONTRACT'],
 ['M19 binding invalid hash denied',i=>{i.m19S0BindingSnapshot.snapshot_sha256='zzz';},'DENIED','M19_BINDING_CONTRACT'],
 ['M20 invalid hash denied',i=>{i.m20CadenceSnapshot.snapshot_sha256='zzz';},'DENIED','M20_CADENCE_CONTRACT'],
 ['M19 graph negative count denied',i=>{i.m19GraphSnapshot.conflict_occurrences=-1;},'DENIED','M19_GRAPH_CONTRACT'],
 ['M20 impossible attempt count denied',i=>{i.m20CadenceSnapshot.attempts_examined=41;},'DENIED','M20_CADENCE_CONTRACT'],
 ['input unknown schema denied',i=>{i.schemaVersion='future';},'INVALID_INPUT','ENVELOPE'],
 ['input unknown field denied',i=>{i.send_authorized=true;},'INVALID_INPUT','ENVELOPE'],
 ['M19 graph accessor not invoked',i=>{Object.defineProperty(i.m19GraphSnapshot,'decision',{get(){throw Error('getter should not run');}});},'INVALID_INPUT','ENVELOPE'],
 ['M19 binding accessor not invoked',i=>{Object.defineProperty(i.m19S0BindingSnapshot,'status',{get(){throw Error('getter should not run');}});},'INVALID_INPUT','ENVELOPE'],
 ['M20 accessor not invoked',i=>{Object.defineProperty(i.m20CadenceSnapshot,'decision',{get(){throw Error('getter should not run');}});},'INVALID_INPUT','ENVELOPE'],
 ['recursive nested payload rejected',i=>{i.self=i;},'INVALID_INPUT','ENVELOPE'],
 ['M19 graph unexpected prototype rejected',i=>{Object.setPrototypeOf(i.m19GraphSnapshot,{evil:true});},'INVALID_INPUT','ENVELOPE'],
 ['WA39 projection getter rejected',i=>{Object.defineProperty(i.wa39Preview,'observations',{get(){throw Error('getter');}});},'INVALID_INPUT','ENVELOPE']
];
if(cases.length!==40)throw Error('expected exactly 40 cases, got '+cases.length);
cases.forEach(([name,mutate,status,reason],i)=>{
 test('OFF22-'+String(i+1).padStart(2,'0')+' '+name,()=>check(mutate,status,reason));
});
