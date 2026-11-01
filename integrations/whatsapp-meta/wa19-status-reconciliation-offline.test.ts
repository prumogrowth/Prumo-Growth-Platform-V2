import test from 'node:test';
import assert from 'node:assert/strict';
import {reconcileWa19StatusOffline as reconcile,
 recheckWa19StatusOffline as recheck}
 from './wa19-status-reconciliation-offline.ts';

const NOW=1800000000000,SHOP='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
 OTHER='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const scope=()=>({
 contract_version:'wa19-status-request.lab.v0.1',
 selection_ref:'SELECTION_A',concessionaria_id:SHOP,app_ref:'APP_A',
 waba_id:'WABA_A',phone_number_id:'10000001',canal_ref:'CHANNEL_A',
 case_ref:'CASE_A',intent_ref:'INTENT_A',attempt_ref:'ATTEMPT_A',
 provider_message_id:'wamid.SYNTHETIC123',
 recipient_sha256:'a'.repeat(64),now_ms:NOW,max_age_ms:60000,
});
const binding=(s=scope())=>({
 contract_version:'wa19-s0-binding-claim.lab.v0.1',
 selection_ref:s.selection_ref,concessionaria_id:s.concessionaria_id,
 app_ref:s.app_ref,waba_id:s.waba_id,
 phone_number_id:s.phone_number_id,canal_ref:s.canal_ref,
 case_ref:s.case_ref,intent_ref:s.intent_ref,attempt_ref:s.attempt_ref,
 provider_message_id:s.provider_message_id,
 recipient_sha256:s.recipient_sha256,binding_revision:4,
 claim_state:'LAB_CLAIMED',observed_at_ms:NOW-1000,
});
const occurrence=(kind='sent',ref='EVENT_A',s=scope())=>({
 contract_version:'wa19-status-occurrence.lab.v0.1',
 selection_ref:s.selection_ref,concessionaria_id:s.concessionaria_id,
 app_ref:s.app_ref,waba_id:s.waba_id,phone_number_id:s.phone_number_id,
 canal_ref:s.canal_ref,provider_message_id:s.provider_message_id,
 recipient_sha256:s.recipient_sha256,occurrence_ref:ref,
 body_sha256:'b'.repeat(64),position_index:0,
 provider_kind:kind,provider_timestamp:'2026-11-01T15:00:00.000Z',
 meta_error_code:null,meta_error_subcode:null,
 hmac_verified:false,s0_source_authenticated:false,durably_persisted:false,
});
const run=(s=scope(),b=binding(s),events:any[]=[])=>reconcile(s,b,events);
const denied=(x:ReturnType<typeof run>,reason?:string)=>{
 assert.equal(x.decision,'DENIED');
 if(reason)assert.equal(x.reason,reason);
 assert.equal(x.snapshot,null);
 assert.equal(Object.isFrozen(x),true);
};
const safe=(x:ReturnType<typeof run>,status?:string)=>{
 assert.equal(x.decision,'LAB_STATUS_RECONCILED_UNVERIFIED');
 const p=x.snapshot!;
 assert.ok(p);assert.equal(Object.isFrozen(p),true);
 assert.equal(Object.isFrozen(x),true);
 if(status)assert.equal(p.status,status);
 for(const flag of ['s0_source_authenticated','callback_hmac_verified',
  'attempt_correlation_verified','durable_persistence_verified',
  'sent_verified','delivered_verified','read_verified',
  'definitive_failure_verified','definitive_failure_count_increment',
  'case_transition_authorized','commercial_transition_authorized',
  'retry_external','ack_allowed','production_authorized'] as const)
  assert.equal(p[flag],false,flag);
 for(const flag of ['callback_hmac_verified','s0_source_authenticated',
  'sent_verified','delivered_verified','read_verified',
  'definitive_failure_count_increment','case_transition_authorized',
  'retry_external','ack_allowed','production_authorized'] as const)
  assert.equal(x[flag],false,flag);
 const encoded=JSON.stringify(x);
 for(const item of ['SELECTION_A','ATTEMPT_A','INTENT_A','CASE_A',
  'WABA_A','CHANNEL_A','wamid.','10000001',SHOP])
  assert.equal(encoded.includes(item),false,item);
 assert.match(p.snapshot_sha256,/^[a-f0-9]{64}$/);
 return p;
};
test('M19-01 no observations remain unverified',()=>{
 const x=safe(run(),'LAB_NO_OBSERVATIONS');
 assert.equal(x.observation_count,0);
});
test('M19-02 a sent callback claim never proves sent',()=>{
 const p=safe(run(scope(),binding(),[occurrence()]),'LAB_SENT_OBSERVED_UNVERIFIED');
 assert.equal(p.saw_explicit_sent,true);assert.equal(p.sent_verified,false);
});
test('M19-03 API_ACCEPTED is not an input to this callback module',()=>{
 const s:any=scope();s.graph_api_accepted=true;
 denied(run(s),'INVALID_INPUT');
});
test('M19-04 delivered alone does NOT infer sent',()=>{
 const p=safe(run(scope(),binding(),[occurrence('delivered')]),
  'LAB_DELIVERED_OBSERVED_UNVERIFIED');
 assert.equal(p.saw_explicit_sent,false);
});
test('M19-05 read alone does NOT infer sent',()=>{
 const p=safe(run(scope(),binding(),[occurrence('read')]),
  'LAB_READ_OBSERVED_UNVERIFIED');
 assert.equal(p.saw_explicit_sent,false);
});
test('M19-06 failure alone is unverified, not definitive',()=>{
 const p=safe(run(scope(),binding(),[occurrence('failed')]),
  'LAB_FAILURE_OBSERVED_UNVERIFIED');
 assert.equal(p.saw_failed,true);assert.equal(p.definitive_failure_verified,false);
});
test('M19-07 read before sent is preserved without inferred order',()=>{
 const xs=[occurrence('read','EVT_R'),occurrence('sent','EVT_S')];
 const p=safe(run(scope(),binding(),xs),'LAB_READ_OBSERVED_UNVERIFIED');
 assert.equal(p.saw_explicit_sent,true);assert.equal(p.observation_count,2);
});
test('M19-08 permutations of same events are stable',()=>{
 const xs=[occurrence('read','EVT_R'),occurrence('sent','EVT_S'),
  occurrence('delivered','EVT_D')];
 const a=safe(run(scope(),binding(),xs));
 const b=safe(run(scope(),binding(),xs.slice().reverse()));
 assert.equal(a.snapshot_sha256,b.snapshot_sha256);
});
test('M19-09 identical physical occurrence dedupes once',()=>{
 const e=occurrence();
 const p=safe(run(scope(),binding(),[e,{...e}]),'LAB_SENT_OBSERVED_UNVERIFIED');
 assert.equal(p.observation_count,1);assert.equal(p.duplicate_count,1);
});
test('M19-10 same occurrence id different status quarantined',()=>{
 const p=safe(run(scope(),binding(),[
  occurrence('sent','EVT_A'),occurrence('failed','EVT_A'),
 ]),'LAB_CONFLICT_QUARANTINED');
 assert.equal(p.quarantine_required,true);
});
test('M19-11 same occurrence id other body hash quarantined',()=>{
 const a=occurrence(),z={...a,body_sha256:'c'.repeat(64)};
 const p=safe(run(scope(),binding(),[a,z]),'LAB_CONFLICT_QUARANTINED');
 assert.equal(p.quarantine_required,true);
});
test('M19-12 same occurrence id other timestamp quarantined',()=>{
 const a=occurrence(),z={...a,provider_timestamp:'2026-11-01T15:01:00.000Z'};
 safe(run(scope(),binding(),[a,z]),'LAB_CONFLICT_QUARANTINED');
});
test('M19-13 distinct sent and failed status conflict quarantined',()=>{
 safe(run(scope(),binding(),[
  occurrence('failed','EVT_F'),occurrence('sent','EVT_S'),
 ]),'LAB_CONFLICT_QUARANTINED');
});
test('M19-14 delivered plus failed quarantined',()=>{
 safe(run(scope(),binding(),[
  occurrence('failed','EVT_F'),occurrence('delivered','EVT_D'),
 ]),'LAB_CONFLICT_QUARANTINED');
});
test('M19-15 read plus failed quarantined',()=>{
 safe(run(scope(),binding(),[
  occurrence('failed','EVT_F'),occurrence('read','EVT_R'),
 ]),'LAB_CONFLICT_QUARANTINED');
});
test('M19-16 invalidated attempt with late callback quarantined',()=>{
 const b=binding();b.claim_state='LAB_INVALIDATED';
 const p=safe(run(scope(),b,[occurrence('sent')]),
  'LAB_INVALIDATED_OBSERVATION_HOLD');
 assert.equal(p.quarantine_required,true);assert.equal(p.sent_verified,false);
});
test('M19-17 invalidated empty attempt stays empty',()=>{
 const b=binding();b.claim_state='LAB_INVALIDATED';
 safe(run(scope(),b,[]),'LAB_NO_OBSERVATIONS');
});
test('M19-18 a second physical occurrence same status is not same event',()=>{
 const p=safe(run(scope(),binding(),[
  occurrence('sent','EVT_A'),occurrence('sent','EVT_B')]),
 'LAB_SENT_OBSERVED_UNVERIFIED');
 assert.equal(p.observation_count,2);
});
test('M19-19 unknown status fails entire batch',()=>{
 const e=occurrence('acknowledged');
 denied(run(scope(),binding(),[occurrence(),e]),'EVENT_SCOPE_DENIED');
});
test('M19-20 malformed timestamp fails whole batch',()=>{
 const e=occurrence();e.provider_timestamp='2026-02-30T15:00:00.000Z';
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-21 failed error 131049 stays diagnostic',()=>{
 const e=occurrence('failed');e.meta_error_code=131049;
 const p=safe(run(scope(),binding(),[e]),'LAB_FAILURE_OBSERVED_UNVERIFIED');
 assert.equal(p.definitive_failure_count_increment,false);
});
const cross=[
 ['selection_ref','SELECTION_B'],['concessionaria_id',OTHER],
 ['app_ref','APP_B'],['waba_id','WABA_B'],
 ['phone_number_id','10000002'],['canal_ref','CHANNEL_B'],
 ['case_ref','CASE_B'],['attempt_ref','ATTEMPT_B'],
 ['intent_ref','INTENT_B'],['provider_message_id','wamid.OTHER_123'],
 ['recipient_sha256','f'.repeat(64)],
] as const;
cross.forEach(([key,val],i)=>test('M19-'+String(i+22).padStart(2,'0')+
 ' binding mismatch '+key+' fails closed',()=>{
 const b:any=binding();b[key]=val;
 denied(run(scope(),b),'BINDING_SCOPE_DENIED');
}));
test('M19-33 different callback WABA denied',()=>{
 const e=occurrence();e.waba_id='WABA_B';
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-34 different callback shop denied',()=>{
 const e=occurrence();e.concessionaria_id=OTHER;
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-35 different callback wamid denied',()=>{
 const e=occurrence();e.provider_message_id='wamid.DIFFERENT';
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-36 callback forged authenticated flag denied',()=>{
 const e=occurrence();e.hmac_verified=true;
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-37 callback forged persisted flag denied',()=>{
 const e=occurrence();e.durably_persisted=true;
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-38 callback forged S0 source flag denied',()=>{
 const e=occurrence();e.s0_source_authenticated=true;
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-39 no partial batch with extra status authority',()=>{
 const e:any=occurrence();e.delivered_verified=true;
 denied(run(scope(),binding(),[occurrence(),e]),'EVENT_SCOPE_DENIED');
});
test('M19-40 sparse event array rejected',()=>{
 const xs:any[]=Array(2);xs[0]=occurrence();
 denied(run(scope(),binding(),xs),'INVALID_INPUT');
});
test('M19-41 malicious occurrence getter not invoked',()=>{
 const e:any=occurrence();let calls=0;
 Object.defineProperty(e,'provider_kind',{enumerable:true,
  get(){calls++;return 'sent';}});
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
 assert.equal(calls,0);
});
test('M19-42 malicious source getter not invoked',()=>{
 const s:any=scope();let calls=0;
 Object.defineProperty(s,'app_ref',{enumerable:true,
  get(){calls++;return 'APP_A';}});
 denied(run(s,binding(),[]),'INVALID_INPUT');assert.equal(calls,0);
});
test('M19-43 stale attempt binding denied',()=>{
 const b=binding();b.observed_at_ms=NOW-60001;
 denied(run(scope(),b),'SNAPSHOT_STALE_OR_FUTURE');
});
test('M19-44 future attempt binding denied',()=>{
 const b=binding();b.observed_at_ms=NOW+1;
 denied(run(scope(),b),'SNAPSHOT_STALE_OR_FUTURE');
});
test('M19-45 valid identical replay rechecks without authority',()=>{
 const p=safe(run(scope(),binding(),[occurrence()]));
 const v=recheck(p,scope(),binding(),[occurrence()]);
 assert.equal(v.decision,'LAB_RECHECKED_UNVERIFIED');
 assert.equal(v.snapshot?.snapshot_sha256,p.snapshot_sha256);
});
test('M19-46 any new status occurrence denies original snapshot',()=>{
 const p=safe(run(scope(),binding(),[occurrence()]));
 denied(recheck(p,scope(),binding(),[
  occurrence(),occurrence('delivered','EVT_2')]),
 'SNAPSHOT_OR_CONTEXT_CHANGED');
});
test('M19-47 changed binding revision denies original snapshot',()=>{
 const p=safe(run());
 const b=binding();b.binding_revision=5;
 denied(recheck(p,scope(),b,[]),'SNAPSHOT_OR_CONTEXT_CHANGED');
});
test('M19-48 changed claimed observation time denies original',()=>{
 const p=safe(run());
 const b=binding();b.observed_at_ms=NOW-2000;
 denied(recheck(p,scope(),b,[]),'SNAPSHOT_OR_CONTEXT_CHANGED');
});
test('M19-49 old snapshot cannot assert verified sent',()=>{
 const p=safe(run(scope(),binding(),[occurrence()]));
 denied(recheck({...p,sent_verified:true},scope(),binding(),[occurrence()]),
  'PREVIOUS_SNAPSHOT_INVALID');
});
test('M19-50 forged digest cannot pass recheck',()=>{
 const p=safe(run());
 denied(recheck({...p,snapshot_sha256:'f'.repeat(64)},scope(),binding(),[]),
 'SNAPSHOT_OR_CONTEXT_CHANGED');
});
test('M19-51 request clock drift denies recheck',()=>{
 const p=safe(run()),s=scope();s.now_ms=NOW+1000;
 denied(recheck(p,s,binding(s),[]),'SNAPSHOT_OR_CONTEXT_CHANGED');
});
test('M19-52 observation append on invalidated claim stays quarantined',()=>{
 const b=binding();b.claim_state='LAB_INVALIDATED';
 const p=safe(run(scope(),b,[occurrence('read')]),
  'LAB_INVALIDATED_OBSERVATION_HOLD');
 assert.equal(p.read_verified,false);
});


test('M19-53 future provider timestamp rejected rather than reordered',()=>{
 const e=occurrence();e.provider_timestamp='2027-02-10T00:00:00.000Z';
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-54 successful status with contradictory error code denied',()=>{
 const e=occurrence('sent');e.meta_error_code=131049;
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-55 read status with erroneous failure subcode denied',()=>{
 const e=occurrence('read');e.meta_error_subcode=1;
 denied(run(scope(),binding(),[e]),'EVENT_SCOPE_DENIED');
});
test('M19-56 invalidated claim cannot assert callback occurred after revocation',()=>{
 const b=binding();b.claim_state='LAB_INVALIDATED';
 const p=safe(run(scope(),b,[occurrence('sent')]),
  'LAB_INVALIDATED_OBSERVATION_HOLD');
 assert.equal(p.quarantine_required,true);
 assert.equal(p.sent_verified,false);
});
test('M19-57 failed with unknown error code is still unverified',()=>{
 const e=occurrence('failed');e.meta_error_code=999999999;
 const p=safe(run(scope(),binding(),[e]),
 'LAB_FAILURE_OBSERVED_UNVERIFIED');
 assert.equal(p.definitive_failure_count_increment,false);
});
