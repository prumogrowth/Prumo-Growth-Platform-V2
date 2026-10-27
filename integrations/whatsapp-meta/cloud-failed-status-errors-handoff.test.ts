/** Entirely fictional status callbacks. No HTTP/Graph, credentials or S0. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {inspectSignedMetaFailedStatusErrors as inspect}
 from './cloud-failed-status-errors-handoff.ts';
const SECRET='OFFLINE_STATUS_ERRORS_NO_LIVE_SECRET';
const ROUTE={waba_id:'123456789012',phone_number_id:'987654321098',revision:4};
const TS='1761000000';
const failed=(id='wamid.OUT_1')=>({
 id,recipient_id:'5581888800000',status:'failed',timestamp:TS,
 errors:[{code:131026,title:'Message undeliverable',
  message:'Message undeliverable',
  error_data:{details:'Could not be delivered'},
  href:'https://example.invalid/untrusted-help'}],
});
const state=(status:'sent'|'delivered'|'read',id='wamid.OUT_2')=>({
 id,recipient_id:'5581888800000',status,timestamp:TS,
});
const inbound=()=>({
 from:'5581888800003',id:'wamid.IN_1',timestamp:TS,
 type:'unsupported',errors:[{code:131051}],
});
const root=(statuses:unknown[]=[failed()],messages:unknown[]=[])=>({
 object:'whatsapp_business_account',
 entry:[{id:ROUTE.waba_id,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',
  metadata:{phone_number_id:ROUTE.phone_number_id},
  messages,statuses,
 }}]}],
});
const bytes=(value:unknown)=>Buffer.from(JSON.stringify(value),'utf8');
const sig=(bytes:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(bytes).digest('hex');
const run=(value:unknown=root(),route=ROUTE)=>{
 const raw=bytes(value);return inspect(raw,sig(raw),SECRET,route);
};
function safe(v:Awaited<ReturnType<typeof inspect>>){
 assert.equal(Object.isFrozen(v),true);
 for(const key of [
  'ack_allowed','send_authorized','s0_write_authorized',
  'retry_external','production_authorized','delivery_confirmed',
  'case_transition_authorized','commercial_effect_authorized',
  'consent_verified','deduplicated','attempt_correlated',
  'provider_failure_effect_confirmed','definitive_failure_count_increment',
  'automatic_retry_authorized',
 ] as const)assert.equal(v[key],false,key);
}
function accepted(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'SIGNED_FAILED_STATUS_ERRORS_NOT_DURABLE');
 if(r.decision!=='SIGNED_FAILED_STATUS_ERRORS_NOT_DURABLE')throw Error('DENIED');
 return r.observations;
}
function denied(r:Awaited<ReturnType<typeof inspect>>){
 safe(r);assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('expected denied');
 assert.equal(r.raw_sha256,null);
 assert.deepEqual(r.observations,[]);
 return r.reason;
}
test('STATUS-ERR-01 reported 131026 keeps technical code and sent-message id',async()=>{
 const r=await run(),o=accepted(r);
 assert.equal(o.length,1);
 assert.equal(o[0].kind,'provider_reported_failed_status_errors');
 assert.equal(o[0].reported_status,'failed');
 assert.equal(o[0].provider_message_id,'wamid.OUT_1');
 assert.equal(o[0].recipient_identifier,'5581888800000');
 assert.deepEqual(o[0].codes,[{code:131026,error_subcode:null}]);
 assert.equal(o[0].position.array_kind,'statuses');
 assert.equal(o[0].position.item_index,0);
 assert.ok(Object.isFrozen(o[0]));
 assert.ok(Object.isFrozen(o[0].codes));
 assert.ok(Object.isFrozen(o[0].codes[0]));
 assert.match(r.raw_sha256!,/^[a-f0-9]{64}$/);
 assert.equal(JSON.stringify(o).includes('Could not be delivered'),false);
 assert.equal(JSON.stringify(o).includes('example.invalid'),false);
});
test('STATUS-ERR-02 optional subcode and multiple numeric claims preserved inertly',async()=>{
 const v=failed();v.errors=[
  {code:131047,error_subcode:17},{code:131049},
 ] as any;
 assert.deepEqual(accepted(await run(root([v])))[0].codes,[
  {code:131047,error_subcode:17},{code:131049,error_subcode:null},
 ]);
});
test('STATUS-ERR-03 sent delivered read never confer deliveries',async()=>{
 const r=await run(root([state('sent'),state('delivered'),state('read')]));
 assert.deepEqual(accepted(r),[]);
 assert.equal(r.delivery_confirmed,false);
});
test('STATUS-ERR-04 mixed statuses and inbound retain exact status positions',async()=>{
 const r=await run(root([
  state('sent'),failed('wamid.A'),state('read'),failed('wamid.B'),
 ],[inbound()]));
 const observations=accepted(r);
 assert.deepEqual(observations.map(x=>x.position.item_index),[1,3]);
 assert.deepEqual(observations.map(x=>x.provider_message_id),
  ['wamid.A','wamid.B']);
 assert.ok(observations.every(x=>x.position.array_kind==='statuses'));
});
test('STATUS-ERR-05 nonfailed status with any errors is ambiguous and denied',async()=>{
 for(const status of ['sent','delivered','read'] as const){
  const s=state(status);(s as any).errors=[{code:131026}];
  assert.equal(denied(await run(root([failed(),s]))),
   'INCONSISTENT_STATUS_ERRORS');
  const t=state(status);(t as any).errors=[];
  assert.equal(denied(await run(root([t]))),'INCONSISTENT_STATUS_ERRORS');
 }
});
test('STATUS-ERR-06 failed status requires a nonempty bounded errors array',async()=>{
 for(const err of [undefined,null,[],{},9,
  Array.from({length:9},()=>({code:131026}))]){
  const v=failed();
  if(err===undefined)delete (v as any).errors;
  else (v as any).errors=err;
  assert.equal(denied(await run(root([failed('wamid.OK'),v]))),
   'MALFORMED_STATUS_ERRORS');
 }
});
test('STATUS-ERR-07 malformed codes/subcodes denied whole batch',async()=>{
 for(const code of [0,-1,1.5,'131026',null,Number.MAX_SAFE_INTEGER+1]){
  const s=failed();s.errors=[{code}] as any;
  assert.equal(denied(await run(root([s]))),'MALFORMED_STATUS_ERRORS');
 }
 for(const subcode of [0,-5,2.5,'9',null]){
  const s=failed();s.errors=[{code:131026,error_subcode:subcode}] as any;
  assert.equal(denied(await run(root([s]))),'MALFORMED_STATUS_ERRORS');
 }
});
test('STATUS-ERR-08 injection and unknown fields are fail-closed',async()=>{
 for(const field of ['retry_automatically','automatic_reply','token','destination']){
  const v=failed();(v.errors[0] as any)[field]=true;
  assert.equal(denied(await run(root([v]))),'MALFORMED_STATUS_ERRORS');
 }
});
test('STATUS-ERR-09 arbitrary title and message must meet conservative UTF8 bounds',async()=>{
 for(const bad of [null,17,'bad\nnewline','\uD800','x'.repeat(1025)]){
  const v=failed();(v.errors[0] as any).message=bad;
  assert.equal(denied(await run(root([v]))),'MALFORMED_STATUS_ERRORS');
 }
 for(const bad of [null,12,'\n','y'.repeat(513)]){
  const v=failed();(v.errors[0] as any).title=bad;
  assert.equal(denied(await run(root([v]))),'MALFORMED_STATUS_ERRORS');
 }
});
test('STATUS-ERR-10 optional trace, type and href never appear in output',async()=>{
 const v=failed();
 Object.assign(v.errors[0],{
  fbtrace_id:'TRACE_PII_123',type:'OAuthException',
  href:'https://example.invalid?token=DO_NOT_RETURN',
 });
 const r=await run(root([v]));
 const o=accepted(r);
 assert.equal(JSON.stringify(o).includes('TRACE_PII_123'),false);
 assert.equal(JSON.stringify(o).includes('OAuthException'),false);
 assert.equal(JSON.stringify(o).includes('DO_NOT_RETURN'),false);
});
test('STATUS-ERR-11 error_data validates details, product, and rejects extras',async()=>{
 const v=failed();(v.errors[0] as any).error_data={
  details:'Untrusted text',messaging_product:'whatsapp',
 };
 assert.equal(accepted(await run(root([v])))[0].codes[0].code,131026);
 for(const data of [null,[],{foo:'bar'},
  {details:null},{messaging_product:'instagram'},
  {details:'\u0000hidden'}]){
  const x=failed();(x.errors[0] as any).error_data=data;
  assert.equal(denied(await run(root([x]))),'MALFORMED_STATUS_ERRORS');
 }
});
test('STATUS-ERR-12 absent optional titles/details are not fabricated',async()=>{
 const s=failed();s.errors=[{code:131026}] as any;
 assert.deepEqual(accepted(await run(root([s])))[0].codes,
  [{code:131026,error_subcode:null}]);
});
test('STATUS-ERR-13 invalid wamid for failed report denied',async()=>{
 for(const id of ['not-wamid','wamid.BAD ID']){
  const s=failed(id);
  assert.equal(denied(await run(root([s]))),'MALFORMED_STATUS_ERRORS');
 }
 for(const id of ['', 'wamid.'+'x'.repeat(1025)]){
  const s=failed(id);
  assert.equal(denied(await run(root([s]))),'VERIFICATION_DENIED');
 }
});
test('STATUS-ERR-14 invalid or missing HMAC and incorrect App secret reveal no data',async()=>{
 const b=bytes(root());
 for(const result of await Promise.all([
  inspect(b,null,SECRET,ROUTE),
  inspect(b,'sha256='+'0'.repeat(64),SECRET,ROUTE),
  inspect(b,'bogus',SECRET,ROUTE),
  inspect(b,sig(b),'WRONG_SECRET',ROUTE),
  inspect(b,sig(b),'',ROUTE),
 ]))assert.equal(denied(result),'VERIFICATION_DENIED');
});
test('STATUS-ERR-15 WABA and phone cross scope rejected entirely',async()=>{
 const b=bytes(root([failed()]));
 for(const wrong of [
  {...ROUTE,waba_id:'999999999999'},
  {...ROUTE,phone_number_id:'999999999999'},
 ]){
  assert.equal(denied(await inspect(b,sig(b),SECRET,wrong)),
   'VERIFICATION_DENIED');
 }
 const x=root([failed()]);
 x.entry.push({id:'999999999999',changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:ROUTE.phone_number_id},
  messages:[],statuses:[failed('wamid.OTHER')],
 }}]});
 assert.equal(denied(await run(x)),'VERIFICATION_DENIED');
});
test('STATUS-ERR-16 malformed sibling or subscribed field denies entire batch',async()=>{
 const s=state('sent');(s as any).timestamp='invalid';
 assert.equal(denied(await run(root([failed(),s]))),'VERIFICATION_DENIED');
 const x=root([failed()]);
 (x.entry[0].changes[0] as any).field='unexpected_event_field';
 assert.equal(denied(await run(x)),'VERIFICATION_DENIED');
});
test('STATUS-ERR-17 duplicates remain distinct pending S0 deduplication',async()=>{
 const s=failed();
 const r=await run(root([s,{...s}]));
 assert.deepEqual(accepted(r).map(x=>x.position.item_index),[0,1]);
 assert.equal(r.deduplicated,false);
 assert.equal(r.definitive_failure_count_increment,false);
});
test('STATUS-ERR-18 mutation, signed body limit, event cap and invalid UTF8',async()=>{
 const b=bytes(root([failed()]));
 const task=inspect(b,sig(b),SECRET,ROUTE);
 b.fill(0);
 assert.equal(accepted(await task)[0].codes[0].code,131026);
 const v=bytes(root([failed(),failed('wamid.SECOND')]));
 assert.equal(denied(await inspect(v,sig(v),SECRET,ROUTE,
  {maxBodyBytes:v.length-1})),'VERIFICATION_DENIED');
 assert.equal(denied(await inspect(v,sig(v),SECRET,ROUTE,
  {maxEvents:1})),'VERIFICATION_DENIED');
 const invalid=Uint8Array.from([0xff,0xfe]);
 assert.equal(denied(await inspect(invalid,sig(invalid),SECRET,ROUTE)),
  'VERIFICATION_DENIED');
});
