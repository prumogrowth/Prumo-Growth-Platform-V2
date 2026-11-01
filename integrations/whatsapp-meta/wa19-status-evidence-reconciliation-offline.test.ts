import test from 'node:test';
import assert from 'node:assert/strict';
import {reconcileWa19StatusOffline as reconcile,
 recheckWa19StatusOffline as recheck}
 from './wa19-status-evidence-reconciliation-offline.ts';

const NOW=1800000000000;
const SHOP='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',OTHER='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const q=()=>({
 contract_version:'wa19-graph-status-request.lab.v0.1',
 concessionaria_id:SHOP,app_ref:'APP_A',waba_id:'WABA_A',
 phone_number_id:'10000001',attempt_ref:'ATTEMPT_A',intent_ref:'INTENT_A',
 case_ref:'CASE_A',template_ref:'TPL_A',template_version_ref:'TPL_V2',
 provider_message_id:'wamid.ABC_01',
 case_revision:2,template_revision:3,assignment_revision:4,
 consent_revision:5,now_ms:NOW,max_age_ms:60000,
 authority_state:'LAB_ACTIVE',revoked_at_ms:null,
});
const graph=(request=q())=>{
 const {now_ms,max_age_ms,authority_state,revoked_at_ms,
  case_revision,template_revision,assignment_revision,consent_revision,
  contract_version,...scope}=request;
 return {...scope,contract_version:'wa19-graph-claim.lab.v0.1',
  graph_state:'API_ACCEPTED',observed_at_ms:NOW-500,
  source_authenticated:false,attempt_binding_verified:false,
 };
};
const item=(request=q(),status='sent',n=0)=>{
 const {now_ms,max_age_ms,authority_state,revoked_at_ms,
  case_revision,template_revision,assignment_revision,consent_revision,
  contract_version,...scope}=request;
 return {...scope,contract_version:'wa19-callback-event.lab.v0.1',
  source_boundary:'LAB_UNAUTHENTICATED_POST',occurrence_ref:'EVENT_'+n,
  batch_ref:'BATCH_1',entry_index:0,change_index:0,item_index:n,
  body_sha256:'a'.repeat(64),provider_status:status,
  provider_timestamp_ms:NOW-2000+n,observed_at_ms:NOW-1000,
  error_code:status==='failed'?131049:null,
 };
};
const batch=(entries:any[]=[])=>({
 contract_version:'wa19-status-batch.lab.v0.1',events:entries,
});
const run=(request:any=q(),graphClaim:any=graph(request),entries:any[]=[])=>
 reconcile(request,graphClaim,batch(entries));
const fail=(x:any,why?:string)=>{
 assert.equal(x.decision,'DENIED');
 if(why)assert.equal(x.reason,why);
 assert.equal(x.snapshot,null);
 for(const key of ['source_authenticated','attempt_correlation_verified',
 'sent_verified','delivered_verified','read_verified',
 'definitive_failure_verified','retry_external','send_authorized',
 'production_authorized','ack_allowed','case_transition_authorized',
 'wdc13_increment_authorized','c09_window_authorized'])
  assert.equal(x[key],false,key);
 assert.equal(Object.isFrozen(x),true);
};
const good=(x:any,decision:string,progress:string)=>{
 assert.equal(x.decision,decision);assert.equal(x.reason,null);
 assert.ok(x.snapshot);assert.equal(x.snapshot.decision,decision);
 assert.equal(x.snapshot.progress,progress);
 assert.equal(Object.isFrozen(x),true);
 assert.equal(Object.isFrozen(x.snapshot),true);
 assert.match(x.snapshot.snapshot_sha256,/^[a-f0-9]{64}$/);
 for(const key of ['source_authenticated','attempt_correlation_verified',
 'sent_verified','delivered_verified','read_verified',
 'definitive_failure_verified','retry_external','send_authorized',
 'production_authorized','ack_allowed','case_transition_authorized',
 'wdc13_increment_authorized','c09_window_authorized']){
  assert.equal(x[key],false,key);
  assert.equal(x.snapshot[key],false,key);
 }
 const wire=JSON.stringify(x);
 for(const hidden of [SHOP,'WABA_A','APP_A','ATTEMPT_A',
  'CASE_A','INTENT_A','wamid.ABC_01','10000001','a'.repeat(64)])
  assert.equal(wire.includes(hidden),false,hidden);
 return x.snapshot;
};
test('M19-01 empty accepted API claim is not SENT',()=>{
 const s=good(run(),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
 assert.equal(s.api_accepted_lab,true);assert.equal(s.sent_observed_lab,false);
});
test('M19-02 unknown Graph state without callback remains unverified',()=>{
 const g:any=graph();g.graph_state='EXTERNAL_UNKNOWN';
 const s=good(run(q(),g),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
 assert.equal(s.api_accepted_lab,false);
});
test('M19-03 mock Graph rejected without callback does not count failure',()=>{
 const g:any=graph();g.graph_state='PROVIDER_REJECTED';
 const s=good(run(q(),g),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
 assert.equal(s.failed_observed_lab,false);
});
test('M19-04 single sent observation remains LAB only',()=>{
 const s=good(run(q(),graph(),[item()]),
  'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
 assert.equal(s.sent_observed_lab,true);assert.equal(s.unique_occurrences,1);
});
test('M19-05 delivered without sent does not create sent',()=>{
 const s=good(run(q(),graph(),[item(q(),'delivered')]),
  'LAB_OBSERVATION_UNVERIFIED','DELIVERED_OBSERVED');
 assert.equal(s.sent_observed_lab,false);assert.equal(s.delivered_observed_lab,true);
});
test('M19-06 read without sent does not create sent',()=>{
 const s=good(run(q(),graph(),[item(q(),'read')]),
  'LAB_OBSERVATION_UNVERIFIED','READ_OBSERVED');
 assert.equal(s.sent_observed_lab,false);assert.equal(s.read_observed_lab,true);
});
test('M19-07 failed without sent is not definitive correlated failure',()=>{
 const s=good(run(q(),graph(),[item(q(),'failed')]),
  'LAB_OBSERVATION_UNVERIFIED','FAILED_OBSERVED');
 assert.equal(s.failed_observed_lab,true);
 assert.equal(s.definitive_failure_verified,false);
});
test('M19-08 ordinary sent then delivered then read no commercial effect',()=>{
 const a=[item(q(),'sent',0),item(q(),'delivered',1),item(q(),'read',2)];
 const s=good(run(q(),graph(),a),'LAB_OBSERVATION_UNVERIFIED','READ_OBSERVED');
 assert.equal(s.unique_occurrences,3);
 assert.equal(s.sent_observed_lab,true);
});
test('M19-09 read before sent is not reordered into inferred callback',()=>{
 const a=[item(q(),'read',2),item(q(),'sent',0)];
 const s=good(run(q(),graph(),a),'LAB_OBSERVATION_UNVERIFIED','READ_OBSERVED');
 assert.equal(s.sent_observed_lab,true);
 assert.equal(s.unique_occurrences,2);
});
test('M19-10 exact duplicate physical occurrence counts once',()=>{
 const a=item(),s=good(run(q(),graph(),[a,{...a}]),
  'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
 assert.equal(s.unique_occurrences,1);assert.equal(s.exact_replays,1);
});
test('M19-11 exact duplicate with reordered list same digest',()=>{
 const a=item(q(),'sent',0),b=item(q(),'read',1);
 const x=good(run(q(),graph(),[a,b]),'LAB_OBSERVATION_UNVERIFIED','READ_OBSERVED');
 const y=good(run(q(),graph(),[b,a]),'LAB_OBSERVATION_UNVERIFIED','READ_OBSERVED');
 assert.equal(x.snapshot_sha256,y.snapshot_sha256);
});
test('M19-12 identical replay count contributes to snapshot fingerprint',()=>{
 const a=item(),one=good(run(q(),graph(),[a]),
 'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
 const two=good(run(q(),graph(),[a,a]),
 'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
 assert.notEqual(one.snapshot_sha256,two.snapshot_sha256);
});
test('M19-13 same position with different status quarantines',()=>{
 const a=item(),b={...a,provider_status:'failed',error_code:131049};
 const s=good(run(q(),graph(),[a,b]),
 'LAB_QUARANTINED_CONFLICT','CONFLICT');
 assert.equal(s.conflict_occurrences,1);
});
test('M19-14 same occurrence ref with different physical position quarantines',()=>{
 const a=item(),b={...item(q(),'delivered',1),occurrence_ref:'EVENT_0'};
 const s=good(run(q(),graph(),[a,b]),
 'LAB_QUARANTINED_CONFLICT','CONFLICT');
 assert.equal(s.conflict_occurrences,1);
});
test('M19-15 same position different body digest quarantines',()=>{
 const a=item(),b={...a,body_sha256:'b'.repeat(64)};
 good(run(q(),graph(),[a,b]),'LAB_QUARANTINED_CONFLICT','CONFLICT');
});
test('M19-16 same occurrence ref different event timestamp quarantines',()=>{
 const a=item(),b={...a,provider_timestamp_ms:a.provider_timestamp_ms+1};
 good(run(q(),graph(),[a,b]),'LAB_QUARANTINED_CONFLICT','CONFLICT');
});
test('M19-17 same wamid across statuses is not dedupe',()=>{
 const a=item(q(),'sent',0),b=item(q(),'read',1);
 const s=good(run(q(),graph(),[a,b]),'LAB_OBSERVATION_UNVERIFIED','READ_OBSERVED');
 assert.equal(s.unique_occurrences,2);
});
test('M19-18 failed plus sent is conflict',()=>{
 good(run(q(),graph(),[item(q(),'sent'),item(q(),'failed',1)]),
 'LAB_QUARANTINED_CONFLICT','CONFLICT');
});
test('M19-19 failed plus delivered is conflict',()=>{
 good(run(q(),graph(),[item(q(),'delivered'),item(q(),'failed',1)]),
 'LAB_QUARANTINED_CONFLICT','CONFLICT');
});
test('M19-20 failed plus read is conflict',()=>{
 good(run(q(),graph(),[item(q(),'read'),item(q(),'failed',1)]),
 'LAB_QUARANTINED_CONFLICT','CONFLICT');
});
test('M19-21 Graph rejected plus sent callback quarantined',()=>{
 const g:any=graph();g.graph_state='PROVIDER_REJECTED';
 good(run(q(),g,[item()]),'LAB_QUARANTINED_CONFLICT','CONFLICT');
});
test('M19-22 Graph unknown plus sent callback never grants correlation',()=>{
 const g:any=graph();g.graph_state='EXTERNAL_UNKNOWN';
 good(run(q(),g,[item()]),'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
});
test('M19-23 active policy cannot hide revoked callback time',()=>{
 const req:any=q();req.authority_state='LAB_REVOKED';req.revoked_at_ms=NOW-2500;
 const s=good(run(req,graph(req),[item(req)]),
  'LAB_QUARANTINED_CONFLICT','CONFLICT');
 assert.equal(s.sent_verified,false);
});
test('M19-24 historical callback for revoked context remains unverified',()=>{
 const req:any=q();req.authority_state='LAB_REVOKED';req.revoked_at_ms=NOW-1000;
 const ev=item(req);ev.provider_timestamp_ms=NOW-2000;
 good(run(req,graph(req),[ev]),'LAB_LATE_HISTORICAL_UNVERIFIED','SENT_OBSERVED');
});
test('M19-25 no callbacks with revoked case never grants sent',()=>{
 const req:any=q();req.authority_state='LAB_REVOKED';req.revoked_at_ms=NOW-100;
 good(run(req,graph(req),[]),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
});
test('M19-26 foreign shop callback blocked',()=>{
 const a=item();a.concessionaria_id=OTHER;
 fail(run(q(),graph(),[a]),'SCOPE_MISMATCH');
});
test('M19-27 foreign App callback blocked',()=>{
 const a=item();a.app_ref='APP_OTHER';
 fail(run(q(),graph(),[a]),'SCOPE_MISMATCH');
});
test('M19-28 foreign WABA callback blocked',()=>{
 const a=item();a.waba_id='WABA_OTHER';
 fail(run(q(),graph(),[a]),'SCOPE_MISMATCH');
});
test('M19-29 foreign sender phone blocked',()=>{
 const a=item();a.phone_number_id='10000002';
 fail(run(q(),graph(),[a]),'SCOPE_MISMATCH');
});
test('M19-30 foreign case callback blocked',()=>{
 const a=item();a.case_ref='CASE_OTHER';
 fail(run(q(),graph(),[a]),'SCOPE_MISMATCH');
});
test('M19-31 foreign attempt callback blocked',()=>{
 const a=item();a.attempt_ref='ATTEMPT_OTHER';
 fail(run(q(),graph(),[a]),'SCOPE_MISMATCH');
});
test('M19-32 foreign wamid callback blocked',()=>{
 const a=item();a.provider_message_id='wamid.FOREIGN';
 fail(run(q(),graph(),[a]),'SCOPE_MISMATCH');
});
test('M19-33 foreign template version callback blocked',()=>{
 const a=item();a.template_version_ref='TPL_V9';
 fail(run(q(),graph(),[a]),'SCOPE_MISMATCH');
});
test('M19-34 Graph bound to another attempt denied',()=>{
 const g=graph();g.attempt_ref='ATTEMPT_OTHER';
 fail(run(q(),g,[]),'SCOPE_MISMATCH');
});
test('M19-35 Graph claimed HMAC validity true denied',()=>{
 const g:any=graph();g.source_authenticated=true;
 fail(run(q(),g,[]),'OBSERVATION_UNTRUSTED');
});
test('M19-36 Graph claimed S0 binding verified true denied',()=>{
 const g:any=graph();g.attempt_binding_verified=true;
 fail(run(q(),g,[]),'OBSERVATION_UNTRUSTED');
});
test('M19-37 webhook claimed authenticated source rejected',()=>{
 const a=item();a.source_boundary='HMAC_VERIFIED';
 fail(run(q(),graph(),[a]),'OBSERVATION_UNTRUSTED');
});
test('M19-38 unsupported status does not become failed',()=>{
 const a=item();a.provider_status='unknown';
 fail(run(q(),graph(),[a]),'OBSERVATION_UNTRUSTED');
});
test('M19-39 failed event error 131049 only diagnostic',()=>{
 const ev=item(q(),'failed');ev.error_code=131049;
 const s=good(run(q(),graph(),[ev]),'LAB_OBSERVATION_UNVERIFIED','FAILED_OBSERVED');
 assert.equal(s.wdc13_increment_authorized,false);
});
test('M19-40 malformed success with code denied',()=>{
 const ev=item(q(),'sent');ev.error_code=131049;
 fail(run(q(),graph(),[ev]),'OBSERVATION_UNTRUSTED');
});
test('M19-41 stale callback observation denied',()=>{
 const ev=item();ev.observed_at_ms=NOW-60001;
 fail(run(q(),graph(),[ev]),'OBSERVATION_UNTRUSTED');
});
test('M19-42 future provider event denied',()=>{
 const ev=item();ev.provider_timestamp_ms=NOW+1;
 fail(run(q(),graph(),[ev]),'OBSERVATION_UNTRUSTED');
});
test('M19-43 stale Graph snapshot denied',()=>{
 const g=graph();g.observed_at_ms=NOW-60001;
 fail(run(q(),g,[]),'OBSERVATION_UNTRUSTED');
});
test('M19-44 event getter never executed',()=>{
 const ev=item();let hits=0;
 Object.defineProperty(ev,'provider_status',{enumerable:true,get(){
  hits++;return 'sent';
 }});
 fail(run(q(),graph(),[ev]),'INVALID_INPUT');assert.equal(hits,0);
});
test('M19-45 sparse callback array denied',()=>{
 const x=[item()];x.length=2;
 fail(reconcile(q(),graph(),batch(x)),'INVALID_INPUT');
});
test('M19-46 batch over 80 events refused',()=>{
 const arr=Array.from({length:81},(_,i)=>item(q(),'sent',i));
 fail(run(q(),graph(),arr),'CAPACITY_REACHED');
});
test('M19-47 unexpected callback authority fields denied',()=>{
 const ev:any=item();ev.sent_verified=true;
 fail(run(q(),graph(),[ev]),'INVALID_INPUT');
});
test('M19-48 unexpected Graph access token denied',()=>{
 const g:any=graph();g.access_token='TOKEN';
 fail(run(q(),g,[]),'INVALID_INPUT');
});
test('M19-49 recheck exact stable snapshot passes LAB only',()=>{
 const e=[item(q(),'sent')],first=good(run(q(),graph(),e),
 'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
 good(recheck(first,q(),graph(),batch([item(q(),'sent')])),
 'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
});
test('M19-50 recheck new callback denies stale snapshot',()=>{
 const old=good(run(q(),graph(),[]),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
 fail(recheck(old,q(),graph(),batch([item()])), 'SNAPSHOT_CHANGED');
});
test('M19-51 recheck event timestamp changed denies',()=>{
 const ev=item(),old=good(run(q(),graph(),[ev]),
 'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
 const later={...ev,provider_timestamp_ms:ev.provider_timestamp_ms+1};
 fail(recheck(old,q(),graph(),batch([later])),'SNAPSHOT_CHANGED');
});
test('M19-52 recheck Graph state changed denies',()=>{
 const old=good(run(q(),graph(),[]),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
 const g:any=graph();g.graph_state='EXTERNAL_UNKNOWN';
 fail(recheck(old,q(),g,batch([])),'SNAPSHOT_CHANGED');
});
test('M19-53 recheck authority revocation denies',()=>{
 const old=good(run(q(),graph(),[]),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
 const req:any=q();req.authority_state='LAB_REVOKED';req.revoked_at_ms=NOW-100;
 fail(recheck(old,req,graph(req),batch([])),'SNAPSHOT_CHANGED');
});
test('M19-54 forged old candidate with commercial flag denied',()=>{
 const old=good(run(q(),graph(),[]),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
 fail(recheck({...old,case_transition_authorized:true},
  q(),graph(),batch([])),'INVALID_PREVIOUS');
});
test('M19-55 forged old sent flag denied',()=>{
 const old=good(run(q(),graph(),[]),'LAB_NO_CALLBACK_UNVERIFIED','NONE');
 fail(recheck({...old,sent_verified:true},
  q(),graph(),batch([])),'INVALID_PREVIOUS');
});
test('M19-56 no claim is proof of HMAC or durable receipt',()=>{
 const s=good(run(q(),graph(),[item()]),
  'LAB_OBSERVATION_UNVERIFIED','SENT_OBSERVED');
 assert.equal(s.source_authenticated,false);
 assert.equal(s.attempt_correlation_verified,false);
 assert.equal(s.ack_allowed,false);
});
