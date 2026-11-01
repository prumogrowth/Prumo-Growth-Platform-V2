import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectWa18DispatchOffline as inspect,
 recheckWa18DispatchOffline as recheck,
 classifyWa18GraphMockOffline as classify}
 from './wa18-dispatch-boundary-offline.ts';
const NOW=1800000000000,SHOP='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const other='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const base=()=>({
 contract_version:'wa18-dispatch-intent.lab.v0.1',
 selection_ref:'SELECTION_1',attempt_ref:'ATTEMPT_1',intent_ref:'INTENT_1',
 concessionaria_id:SHOP,app_ref:'APP_A',waba_id:'WABA_A',
 phone_number_id:'1000001',case_ref:'CASE_A',service_ref:'SERVICE_A',
 template_ref:'TPL_A',template_version_ref:'TPL_V2',
 template_purpose_ref:'RECONTACT',consent_purpose_ref:'SERVICE',
 campaign_ref:'CAMPAIGN_A',plan_revision:4,
 case_revision:7,assignment_revision:5,policy_revision:12,
 suppression_revision:8,consent_revision:9,template_revision:3,
 campaign_revision:6,grant_revision:4,registry_revision:10,
 content_sha256:'a'.repeat(64),recipient_sha256:'b'.repeat(64),
 now_ms:NOW,max_age_ms:60000,
});
const s0=()=>({
 contract_version:'prumo.s0.pre-dispatch.pg17/0.1-lab-only',
 decision:'LAB_RESERVATION_RECORDED_NO_DISPATCH',
 reason:null,lab_reservation_recorded:true,
 send_authorized:false,graph_authorized:false,
 credential_resolution_authorized:false,
 pre_dispatch_operationally_authorized:false,
 provider_approval_verified:false,consent_proven_from_real_source:false,
 external_http_ack:false,production_authorized:false,
 commercial_transition_authorized:false,
});
const binding=(i=base())=>{
 const {now_ms,max_age_ms,contract_version,...rest}=i;
 return {...rest,contract_version:'wa18-s0-binding-claim.lab.v0.1',
  reservation_state:'LAB_HELD_NO_DISPATCH',
  commit_state:'LAB_COMMIT_CLAIMED',observed_at_ms:NOW-1000};
};
const rate=()=>({
 contract_version:'wa18-rate-budget.lab.v0.1',
 concessionaria_id:SHOP,app_ref:'APP_A',phone_number_id:'1000001',
 rate_revision:8,observed_at_ms:NOW-1000,
 available_slots:3,throttled_until_ms:null,budget_state:'LAB_AVAILABLE',
});
const run=(i:unknown=base(),s:unknown=s0(),b:unknown=binding(),q:unknown=rate())=>
 inspect(i,s,b,q);
const noAuthority=(x:any)=>{
 assert.equal(x.send_authorized,false);
 assert.equal(x.graph_dispatch_authorized,false);
 assert.equal(x.production_authorized,false);
 assert.equal(x.automatic_retry_authorized,false);
 assert.equal(Object.isFrozen(x),true);
};
function valid(x:any,decision='LAB_DISPATCH_COHERENT_NOT_AUTHORIZED'){
 noAuthority(x);assert.equal(x.decision,decision);assert.equal(x.reason,null);
 assert.ok(x.candidate);
 assert.equal(Object.isFrozen(x.candidate),true);
 for(const p of ['send_authorized','graph_dispatch_authorized',
  'production_authorized','automatic_retry_authorized',
  'ack_allowed','reservation_committed_verified','s0_source_authenticated',
  'credential_resolution_authorized'])assert.equal(x.candidate[p],false,p);
 assert.equal(x.candidate.requires_independent_commit_readback,true);
 assert.match(x.candidate.candidate_sha256,/^[0-9a-f]{64}$/);
 for(const token of [SHOP,'1000001','ATTEMPT_1','CASE_A','CAMPAIGN_A',
  'TPL_A','INTENT_1','SELECTION_1'])assert.equal(JSON.stringify(x).includes(token),false,token);
 return x.candidate;
}
function denied(x:any,why?:string){
 noAuthority(x);assert.equal(x.decision,'DENIED');
 if(why)assert.equal(x.reason,why);
 assert.equal(x.candidate,null);
}
const withOne=(mut:(i:any,b:any,s:any,q:any)=>void)=>{
 const i=base(),b=binding(i),s=s0(),q=rate();
 mut(i,b,s,q);return run(i,s,b,q);
};
test('M18-01 S0 LAB reservation means coherent preview, never permission',()=>{
 const c=valid(run());assert.equal(c.reservation_claim_coherent,true);
});
test('M18-02 stable fresh snapshot recheck is still not authority',()=>{
 const old=valid(run());valid(recheck(old,base(),s0(),binding(),rate()),
  'LAB_RECHECKED_NOT_AUTHORIZED');
});
test('M18-03 denied S0 reservation cannot be upgraded to dispatch',()=>{
 denied(withOne((_i,_b,s)=>{s.decision='DENIED';s.reason='POLICY_DENIED';
  s.lab_reservation_recorded=false;}),'S0_LAB_NOT_ACCEPTABLE');
});
test('M18-04 unavailable S0 cannot authorize Graph',()=>{
 denied(withOne((_i,_b,s)=>{s.decision='UNAVAILABLE';s.reason='UNAVAILABLE';
  s.lab_reservation_recorded=false;}),'S0_LAB_NOT_ACCEPTABLE');
});
test('M18-05 forged S0 send_authorized true rejected',()=>{
 denied(withOne((_i,_b,s)=>{s.send_authorized=true;}),'INVALID_INPUT');
});
test('M18-06 forged S0 graph_authorized true rejected',()=>{
 denied(withOne((_i,_b,s)=>{s.graph_authorized=true;}),'INVALID_INPUT');
});
test('M18-07 S0 commit acknowledgment omitted rejected',()=>{
 denied(withOne((_i,_b,s)=>{s.lab_reservation_recorded=false;}),'INVALID_INPUT');
});
test('M18-08 S0 extra operational lease rejected',()=>{
 denied(withOne((_i,_b,s)=>{s.lease='TOKEN';}),'INVALID_INPUT');
});
test('M18-09 cross-shop binding rejected',()=>{
 denied(withOne((_i,b)=>{b.concessionaria_id=other;}),'BINDING_SCOPE_CHANGED');
});
test('M18-10 different App binding rejected',()=>{
 denied(withOne((_i,b)=>{b.app_ref='APP_B';}),'BINDING_SCOPE_CHANGED');
});
test('M18-11 different WABA binding rejected',()=>{
 denied(withOne((_i,b)=>{b.waba_id='WABA_B';}),'BINDING_SCOPE_CHANGED');
});
test('M18-12 different sender phone binding rejected',()=>{
 denied(withOne((_i,b)=>{b.phone_number_id='1000002';}),'BINDING_SCOPE_CHANGED');
});
test('M18-13 different case binding rejected',()=>{
 denied(withOne((_i,b)=>{b.case_ref='CASE_B';}),'BINDING_SCOPE_CHANGED');
});
test('M18-14 different attempt binding rejected',()=>{
 denied(withOne((_i,b)=>{b.attempt_ref='ATTEMPT_B';}),'BINDING_SCOPE_CHANGED');
});
test('M18-15 cross-intent binding rejected',()=>{
 denied(withOne((_i,b)=>{b.intent_ref='INTENT_B';}),'BINDING_SCOPE_CHANGED');
});
test('M18-16 wrong template version rejected',()=>{
 denied(withOne((_i,b)=>{b.template_version_ref='TPL_V3';}),'BINDING_SCOPE_CHANGED');
});
test('M18-17 wrong consent purpose rejected',()=>{
 denied(withOne((_i,b)=>{b.consent_purpose_ref='MARKETING';}),'BINDING_SCOPE_CHANGED');
});
test('M18-18 changed plan revision rejected',()=>{
 denied(withOne((_i,b)=>{b.plan_revision=5;}),'BINDING_SCOPE_CHANGED');
});
test('M18-19 changed policy revision rejected',()=>{
 denied(withOne((_i,b)=>{b.policy_revision=13;}),'BINDING_SCOPE_CHANGED');
});
test('M18-20 changed registry revision rejected',()=>{
 denied(withOne((_i,b)=>{b.registry_revision=11;}),'BINDING_SCOPE_CHANGED');
});
test('M18-21 changed recipient fingerprint rejected',()=>{
 denied(withOne((_i,b)=>{b.recipient_sha256='c'.repeat(64);}),
 'BINDING_SCOPE_CHANGED');
});
test('M18-22 content changes without template version change rejected',()=>{
 denied(withOne((_i,b)=>{b.content_sha256='c'.repeat(64);}),
 'BINDING_SCOPE_CHANGED');
});
test('M18-23 throttled/429 style budget rejects preview',()=>{
 denied(withOne((_i,_b,_s,q)=>{q.budget_state='LAB_THROTTLED';
  q.throttled_until_ms=NOW+20000;}),'RATE_LIMIT_OR_UNKNOWN');
});
test('M18-24 zero available slots rejects preview',()=>{
 denied(withOne((_i,_b,_s,q)=>{q.available_slots=0;}),
 'RATE_LIMIT_OR_UNKNOWN');
});
test('M18-25 unknown rate state rejects preview',()=>{
 denied(withOne((_i,_b,_s,q)=>{q.budget_state='LAB_UNKNOWN';}),
 'RATE_LIMIT_OR_UNKNOWN');
});
test('M18-26 stale rate budget rejected',()=>{
 denied(withOne((_i,_b,_s,q)=>{q.observed_at_ms=NOW-60001;}),
 'SNAPSHOT_STALE_OR_FUTURE');
});
test('M18-27 future-dated reservation rejected',()=>{
 denied(withOne((_i,b)=>{b.observed_at_ms=NOW+1;}),
 'SNAPSHOT_STALE_OR_FUTURE');
});
test('M18-28 changed rate revision blocks recheck',()=>{
 const old=valid(run()),q=rate();q.rate_revision=9;
 denied(recheck(old,base(),s0(),binding(),q),'REVISION_OR_CONTEXT_CHANGED');
});
test('M18-29 changed rate slots blocks recheck even same revision',()=>{
 const old=valid(run()),q=rate();q.available_slots=2;
 denied(recheck(old,base(),s0(),binding(),q),'REVISION_OR_CONTEXT_CHANGED');
});
test('M18-30 changed content digest blocks recheck',()=>{
 const old=valid(run()),i=base(),b=binding();i.content_sha256='f'.repeat(64);
 b.content_sha256='f'.repeat(64);
 denied(recheck(old,i,s0(),b,rate()),'REVISION_OR_CONTEXT_CHANGED');
});
test('M18-31 recheck on changed attempt blocks continuation',()=>{
 const old=valid(run()),i=base(),b=binding();
 i.attempt_ref='ATTEMPT_NEW';b.attempt_ref='ATTEMPT_NEW';
 denied(recheck(old,i,s0(),b,rate()),'REVISION_OR_CONTEXT_CHANGED');
});
test('M18-32 previously forged candidate authority denied',()=>{
 const old=valid(run());
 denied(recheck({...old,graph_dispatch_authorized:true},
  base(),s0(),binding(),rate()),'PREVIOUS_CANDIDATE_INVALID');
});
test('M18-33 tampered candidate digest is not accepted',()=>{
 const old=valid(run());
 denied(recheck({...old,candidate_sha256:'f'.repeat(64)},
  base(),s0(),binding(),rate()),'REVISION_OR_CONTEXT_CHANGED');
});
test('M18-34 malicious request getter never invoked',()=>{
 const i:any=base();let calls=0;
 Object.defineProperty(i,'attempt_ref',{get(){calls++;return 'ATTEMPT_1';},
  enumerable:true});
 denied(run(i),'INVALID_INPUT');assert.equal(calls,0);
});
test('M18-35 malicious S0 getter never invoked',()=>{
 const s:any=s0();let calls=0;
 Object.defineProperty(s,'decision',{get(){calls++;return 'DENIED';},
  enumerable:true});
 denied(run(base(),s),'INVALID_INPUT');assert.equal(calls,0);
});
test('M18-36 explicit S0 authority escalation is never inferred',()=>{
 const c=valid(run());assert.equal(c.reservation_committed_verified,false);
 assert.equal(c.credential_resolution_authorized,false);
});
const accepted={kind:'http_response',http_status:200,
 response_json:{messages:[{id:'wamid.SYNTHETIC_1'}]}};
const noGraphAuthority=(x:any,d:string)=>{
 assert.equal(x.decision,d);assert.equal(x.sent_verified,false);
 assert.equal(x.delivered_verified,false);assert.equal(x.read_verified,false);
 assert.equal(x.provider_status_verified,false);
 assert.equal(x.attempt_correlation_valid,false);
 assert.equal(x.retry_external,false);
 assert.equal(x.graph_dispatch_authorized,false);
 assert.equal(x.production_authorized,false);
 assert.equal(x.commercial_transition_authorized,false);
 assert.equal(Object.isFrozen(x),true);
};
test('M18-37 mock Graph 200/wamid means API accept, not sent',()=>{
 noGraphAuthority(classify(base(),accepted),'LAB_API_ACCEPTED_NOT_SENT');
});
test('M18-38 mock Graph timeout never triggers automatic retry',()=>{
 noGraphAuthority(classify(base(),{kind:'transport_error'}),
  'LAB_EXTERNAL_UNCERTAIN');
});
test('M18-39 mock Graph 429 remains uncertain, no auto retry',()=>{
 noGraphAuthority(classify(base(),{kind:'http_response',http_status:429,
  response_json:{error:{code:131049}}}),'LAB_EXTERNAL_UNCERTAIN');
});
test('M18-40 mock Graph 503 remains uncertain, no sent',()=>{
 noGraphAuthority(classify(base(),{kind:'http_response',http_status:503,
  response_json:{}}),'LAB_EXTERNAL_UNCERTAIN');
});
test('M18-41 mock Graph 400 rejection does not count commercial failure',()=>{
 noGraphAuthority(classify(base(),{kind:'http_response',http_status:400,
  response_json:{error:{code:131049}}}),
  'LAB_PROVIDER_REJECTED_UNVERIFIED');
});
test('M18-42 2xx with no wamid is external uncertainty',()=>{
 noGraphAuthority(classify(base(),{kind:'http_response',http_status:200,
  response_json:{messages:[]}}),'LAB_EXTERNAL_UNCERTAIN');
});
test('M18-43 nested hostile Graph getter denied without executing',()=>{
 const p:any={messages:[{id:'wamid.SYNTHETIC_1'}]};
 let calls=0;Object.defineProperty(p.messages[0],'id',
  {enumerable:true,get(){calls++;return 'wamid.SYNTHETIC_1';}});
 noGraphAuthority(classify(base(),{kind:'http_response',http_status:200,
  response_json:p}),'DENIED');assert.equal(calls,0);
});
test('M18-44 mock Graph cannot claim evidence of delivery itself',()=>{
 const o:any={...accepted,send_authorized:true};
 noGraphAuthority(classify(base(),o),'DENIED');
});


test('AUD-M18-45 snapshot v0.2 binds observation instants',()=>{
 const c=valid(run());
 assert.equal(c.contract_version,'wa18-dispatch-preview.lab.v0.2');
});
test('AUD-M18-46 older v0.1 candidate cannot inherit updated digest rules',()=>{
 const c=valid(run());
 denied(recheck({...c,contract_version:'wa18-dispatch-preview.lab.v0.1'},
  base(),s0(),binding(),rate()),'PREVIOUS_CANDIDATE_INVALID');
});
test('AUD-M18-47 changed fake clock under same revisions rejects recheck',()=>{
 const c=valid(run()),i=base();i.now_ms=NOW+1000;
 denied(recheck(c,i,s0(),binding(i),rate()),'REVISION_OR_CONTEXT_CHANGED');
});
test('AUD-M18-48 changed max-age window under same revisions rejects',()=>{
 const c=valid(run()),i=base();i.max_age_ms=59999;
 denied(recheck(c,i,s0(),binding(i),rate()),'REVISION_OR_CONTEXT_CHANGED');
});
test('AUD-M18-49 changed binding observation within age denies',()=>{
 const c=valid(run()),b=binding();b.observed_at_ms=NOW-2000;
 denied(recheck(c,base(),s0(),b,rate()),'REVISION_OR_CONTEXT_CHANGED');
});
test('AUD-M18-50 changed rate observation within age denies',()=>{
 const c=valid(run()),q=rate();q.observed_at_ms=NOW-2000;
 denied(recheck(c,base(),s0(),binding(),q),'REVISION_OR_CONTEXT_CHANGED');
});
test('AUD-M18-51 unchanged observation age remains safely nonauthorizing',()=>{
 const c=valid(run());
 valid(recheck(c,base(),s0(),binding(),rate()),'LAB_RECHECKED_NOT_AUTHORIZED');
});
test('AUD-M18-52 S0 lab success with arbitrary reason rejected',()=>{
 const z=s0();z.reason='S0_OK';
 denied(run(base(),z,binding(),rate()),'INVALID_INPUT');
});
test('AUD-M18-53 Graph mock HTTP 200 cannot verify S0 attempt correlation',()=>{
 const x=classify(base(),accepted);
 noGraphAuthority(x,'LAB_API_ACCEPTED_NOT_SENT');
 assert.equal(x.attempt_correlation_valid,false);
});
test('AUD-M18-54 Graph mock 400 cannot verify S0 attempt correlation',()=>{
 const x=classify(base(),{kind:'http_response',http_status:400,response_json:{
  error:{code:131049},
 }});
 noGraphAuthority(x,'LAB_PROVIDER_REJECTED_UNVERIFIED');
 assert.equal(x.attempt_correlation_valid,false);
});
test('AUD-M18-55 Graph mock timeout cannot verify S0 attempt correlation',()=>{
 const x=classify(base(),{kind:'transport_error'});
 noGraphAuthority(x,'LAB_EXTERNAL_UNCERTAIN');
 assert.equal(x.attempt_correlation_valid,false);
});
test('AUD-M18-56 mixed mock transport and HTTP fields denied',()=>{
 noGraphAuthority(classify(base(),{
  kind:'transport_error',http_status:200,response_json:accepted.response_json,
 }),'DENIED');
});
test('AUD-M18-57 mock HTTP response without payload denied',()=>{
 noGraphAuthority(classify(base(),{
  kind:'http_response',
 }),'DENIED');
});
test('AUD-M18-58 fake graph HTTP success never allows retry',()=>{
 const x=classify(base(),accepted);
 noGraphAuthority(x,'LAB_API_ACCEPTED_NOT_SENT');
 assert.equal(x.retry_external,false);
});
test('AUD-M18-59 forged new rate source cannot retain candidate',()=>{
 const c=valid(run()),q=rate();q.app_ref='APP_B';
 denied(recheck(c,base(),s0(),binding(),q),'RATE_LIMIT_OR_UNKNOWN');
});
test('AUD-M18-60 fake positive S0 with hidden grant denied',()=>{
 const z:any=s0();z.grant_used=true;
 denied(run(base(),z,binding(),rate()),'INVALID_INPUT');
});
test('AUD-M18-61 future rate observation remains fail closed',()=>{
 const q=rate();q.observed_at_ms=NOW+100;
 denied(run(base(),s0(),binding(),q),'SNAPSHOT_STALE_OR_FUTURE');
});
test('AUD-M18-62 fake Graph message with extra top-level status denied',()=>{
 const obs:any={...accepted,status:'sent'};
 noGraphAuthority(classify(base(),obs),'DENIED');
});
