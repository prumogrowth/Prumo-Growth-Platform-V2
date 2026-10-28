/**
 * OFFLINE synthetic forensic audit of physical signed callbacks / claimed S0 receipts.
 * No HTTP ACK or write. S0 sources imported READ-ONLY and left unchanged.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {
 compareSignedMetaPhysicalDeliveries as compare,
 reviewAllegedS0ReceiptWithoutAck as reviewRaw,
} from './cloud-physical-replay-receipt-audit.ts';
import {inspectSignedMetaBatchChannelScope as preflight}
 from './cloud-batch-scope-preflight.ts';
import {prepareS0HandoffFixture}
 from './s0-handoff-contract.ts';
import {decideBatchAck} from './durable-receipt.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';
import type {TrustedRoutingPorts} from './routed-webhook.ts';

const APP_SECRET='SYNTHETIC_PHYSICAL_REPLAY_APP_SECRET';
const NOW=1792320000000;
const W1='123456789012',P1='987654321098';
const W2='123456789013',P2='987654321099';
const app={app_ref:'APP_A',route_ref:'ROUTE_A',concessionaria_id:'SHOP_A',
 active:true,revision:7,valid_from_ms:NOW-1000,valid_until_ms:NOW+1000,
 secret_slots:{
  get_verify_token:'APP_GET',post_app_secret:'APP_POST',
  graph_access_token:'APP_GRAPH',
 },
 channels:[
  {canal_id:'CH_A',waba_id:W1,phone_number_id:P1,active:true},
  {canal_id:'CH_B',waba_id:W2,phone_number_id:P2,active:true},
 ]};
const registry:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',
 apps:[app],
};
const ports=():TrustedRoutingPorts=>({
 currentRegistry:()=>registry,
 resolveSecret:s=>s==='APP_POST'?APP_SECRET:undefined,
 nowMs:()=>NOW,
});
const msg=(id:string)=>({
 id,from:'5581888800000',timestamp:'1792320000',type:'text',
 text:{body:'PRIVATE_FIXTURE_CONTENT_NEVER_IN_RESULT'},
});
const status=(id:string)=>({
 id,recipient_id:'5581888800000',timestamp:'1792320001',status:'sent',
});
const entry=(waba=W1,phone=P1,messages:unknown[]=[msg('wamid.M1')],
 statuses:unknown[]=[])=>({
 id:waba,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:phone},
  messages,statuses,
 }}],
});
const body=(entries:unknown[]=[entry()])=>({
 object:'whatsapp_business_account',entry:entries,
});
const raw=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const signature=(b:Uint8Array,secret=APP_SECRET)=>
 'sha256='+createHmac('sha256',secret).update(b).digest('hex');
const request=(payload:unknown=body())=>{
 const b=raw(payload);
 return {raw_body:b,signature_header:signature(b),
  route:{route_ref:'ROUTE_A',expected_revision:7}};
};
const trustedRoute={route_ref:'ROUTE_A',expected_revision:7};
const review=(
 signed:Parameters<typeof reviewRaw>[0],
 candidate:Parameters<typeof reviewRaw>[1],
 alleged:unknown,
)=>reviewRaw(signed,candidate,alleged,trustedRoute);
const receipt=(c:object)=> {
 const v=c as Record<string,unknown>;
 return {
  contract_version:'meta-s0-receipt.v0.1-proposed',
  batch_ref:v.batch_ref,app_ref:v.app_ref,
  protected_payload_ref:v.protected_payload_ref,
  payload_sha256:v.payload_sha256,scope_sha256:v.scope_sha256,
  route_ref:v.route_ref,route_revision:v.route_revision,
  total:v.event_count,accepted:v.event_count,
  duplicates:0,quarantined:0,
  outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',
 };
};
async function pair(a=body(),b=body()){
 return compare(request(a),request(b),ports());
}
async function triple(payload:unknown=body()){
 const q=request(payload),trusted=ports();
 const [signed,s0]=await Promise.all([
  preflight(q,trusted),
  prepareS0HandoffFixture({
   request:q,batch_ref:'BATCH_S0_LAB',
   protected_payload_ref:'PAYLOAD_S0_LAB',
  },trusted),
 ]);
 assert.equal(signed.decision==='DENIED',false);
 assert.equal(s0.ok,true);
 if(s0.ok===false)throw Error('not a synthetic S0 candidate');
 return {signed,c:s0.candidate};
}
function noRights(x:Record<string,unknown>){
 for(const name of ['ack_allowed','partial_ack_allowed',
  'http_response_authorized','send_authorized','s0_write_authorized',
  'production_authorized','retry_external','automatic_retry_authorized',
  'replay_suppression_authorized','deduplicated','durable_receipt_verified',
  'commit_verified','service_identity_verified','m2m_verified',
  'commercial_effect_authorized','channel_policy_ratified'])
  assert.equal(x[name],false,name);
}
function yes(r:Awaited<ReturnType<typeof compare>>,decision:string){
 noRights(r);assert.equal(r.decision,decision);
 if(r.decision==='DENIED')throw Error('denied');
 assert.match(r.prior_raw_sha256,/^[a-f0-9]{64}$/);
 assert.match(r.current_raw_sha256,/^[a-f0-9]{64}$/);
 return r;
}
function no(r:Awaited<ReturnType<typeof compare>>,reason?:string){
 noRights(r);assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('allowed');
 if(reason)assert.equal(r.reason,reason);
 assert.equal(r.prior_raw_sha256,null);
 assert.equal(r.current_raw_sha256,null);
}
test('REPLAY-01 same signed physical bytes: identity without dedupe/ACK',async()=>{
 const x=yes(await pair(),'EXACT_SIGNED_RAW_BYTES_UNVERIFIED');
 assert.equal(x.same_raw_bytes,true);
 assert.equal(x.same_scope,true);
 assert.equal(x.prior_event_count,1);
});
test('REPLAY-02 same message replayed in new physical POST remains unproven',async()=>{
 const b=body([entry(W1,P1,[msg('wamid.M1')])]);
 const x=yes(await pair(b,b),'EXACT_SIGNED_RAW_BYTES_UNVERIFIED');
 assert.equal(x.replay_suppression_authorized,false);
 assert.equal(x.durable_receipt_verified,false);
});
test('REPLAY-03 reordered entries must not appear byte identical',async()=>{
 const a=entry(W1,P1,[msg('wamid.A')]);
 const b=entry(W2,P2,[msg('wamid.B')]);
 const x=yes(await pair(body([a,b]),body([b,a])),
  'DIFFERENT_SIGNED_RAW_BYTES_UNVERIFIED');
 assert.equal(x.same_raw_bytes,false);
 assert.equal(x.same_scope,true);
 assert.equal(x.prior_event_count,2);
 assert.equal(x.current_event_count,2);
});
test('REPLAY-04 reorder two sibling messages changes physical hash',async()=>{
 const a=entry(W1,P1,[msg('wamid.A'),msg('wamid.B')]);
 const b=entry(W1,P1,[msg('wamid.B'),msg('wamid.A')]);
 const x=yes(await pair(body([a]),body([b])),
  'DIFFERENT_SIGNED_RAW_BYTES_UNVERIFIED');
 assert.equal(x.same_scope,true);
});
test('REPLAY-05 same event counts with changed content must not be equated',async()=>{
 const x=yes(await pair(body([entry(W1,P1,[msg('wamid.A')])]),
  body([entry(W1,P1,[msg('wamid.B')])])),
  'DIFFERENT_SIGNED_RAW_BYTES_UNVERIFIED');
 assert.equal(x.same_raw_bytes,false);
});
test('REPLAY-06 whitespace variations are different physical POSTs',async()=>{
 const original=body(),r=request(original);
 const alt=Buffer.from(JSON.stringify(original,null,2));
 const newReq={...r,raw_body:alt,signature_header:signature(alt)};
 const x=yes(await compare(r,newReq,ports()),
  'DIFFERENT_SIGNED_RAW_BYTES_UNVERIFIED');
 assert.equal(x.same_scope,true);
});
test('REPLAY-07 same bytes with changed trusted route must fail safely',async()=>{
 const first=request(),second=request();
 second.route.expected_revision=8;
 no(await compare(first,second,ports()),'SIGNED_BATCH_DENIED');
});
test('REPLAY-08 altered scope and valid signature yields scope-change category',async()=>{
 const x=yes(await pair(body([entry(W1,P1)]),
  body([entry(W2,P2)])),'SIGNED_SCOPE_CHANGED_UNVERIFIED');
 assert.equal(x.same_scope,false);
});
test('REPLAY-09 mixed channel changed to one channel is scope drift',async()=>{
 const x=yes(await pair(body([entry(),entry(W2,P2)]),
  body([entry()])),'SIGNED_SCOPE_CHANGED_UNVERIFIED');
 assert.equal(x.prior_event_count,2);
 assert.equal(x.current_event_count,1);
});
test('REPLAY-10 invalid second HMAC denies the complete comparison',async()=>{
 const first=request(),second=request();
 second.signature_header='sha256='+'0'.repeat(64);
 no(await compare(first,second,ports()),'SIGNED_BATCH_DENIED');
});
test('REPLAY-11 unmapped second channel denies the entire comparison',async()=>{
 no(await pair(body(),body([entry('777777777777',P1)])),
  'SIGNED_BATCH_DENIED');
});
test('REPLAY-12 hostile input denies without exposing raw hashes',async()=>{
 const first=request(),second=request();
 second.route.route_ref='../bad';
 no(await compare(first,second,ports()),'INVALID_INPUT');
});
test('REPLAY-13 mutation after invocation does not alter either body',async()=>{
 const a=request(),b=request();
 const task=compare(a,b,ports());
 a.raw_body.fill(0);b.raw_body.fill(0);
 const x=yes(await task,'EXACT_SIGNED_RAW_BYTES_UNVERIFIED');
 assert.equal(x.same_raw_bytes,true);
});
test('REPLAY-14 mutation of trusted route after invocation is isolated',async()=>{
 const a=request(),b=request();
 const task=compare(a,b,ports());
 a.route.expected_revision=99;
 b.route.route_ref='INVALID';
 yes(await task,'EXACT_SIGNED_RAW_BYTES_UNVERIFIED');
});
test('RECEIPT-15 missing response is not evidence of failed or successful commit',async()=>{
 const {signed,c}=await triple();
 const r=review(signed,c,null);
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'CLAIMED_RECEIPT_MISSING');
});
test('RECEIPT-16 forged COMMITTED matching shape remains NOT durable proof',async()=>{
 const {signed,c}=await triple();
 const r=review(signed,c,receipt(c));
 noRights(r);
 assert.equal(r.decision,'CLAIMED_RECEIPT_SHAPE_ONLY_UNVERIFIED');
 assert.equal(r.reason,'NO_AUTHENTICATED_DURABLE_EVIDENCE');
 assert.equal(r.event_count,1);
});
test('RECEIPT-17 historical shape-only helper returns 200 for fabricated receipt',()=>{
 // This is not an HTTP endpoint. Prove why its return value cannot be
 // treated as permission to send a transport-level ACK.
 const fabricated={outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',
  total:1,accepted:1,duplicates:0,quarantined:0};
 const old=decideBatchAck(1,fabricated);
 assert.equal(old.action,'ACK');
 assert.equal(old.status,200);
});
test('RECEIPT-18 fabricated matching receipt still denied for mismatched SHA',async()=>{
 const {signed,c}=await triple();
 const fake={...c,payload_sha256:'a'.repeat(64)};
 const r=review(signed,fake,receipt(c));
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'CANDIDATE_SCOPE_MISMATCH');
});
test('RECEIPT-19 swapped channel ownership blocked despite equal total',async()=>{
 const {signed,c}=await triple(body([
  entry(W1,P1,[msg('wamid.X')]),
  entry(W2,P2,[msg('wamid.Y')]),
 ]));
 const altered={...c,occurrences:c.occurrences.map((e,i)=>
  i===0?{...e,canal_id:'CH_B'}:e)};
 const r=review(signed,altered,receipt(altered));
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'CANDIDATE_SCOPE_MISMATCH');
});
test('RECEIPT-20 one duplicated occurrence position is rejected',async()=>{
 const {signed,c}=await triple(body([entry(W1,P1,[
  msg('wamid.M1'),msg('wamid.M2')])])); 
 const altered={...c,occurrences:[c.occurrences[0],c.occurrences[0]]};
 const r=review(signed,altered,receipt(altered));
 noRights(r);assert.equal(r.reason,'CANDIDATE_SCOPE_MISMATCH');
});
test('RECEIPT-21 quarantine cannot be promoted to ACK',async()=>{
 const {signed,c}=await triple();
 const claim={...receipt(c),outcome:'QUARANTINED_DURABLE',
  accepted:0,quarantined:1};
 const r=review(signed,c,claim);
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'QUARANTINE_POLICY_PENDING');
});
test('RECEIPT-22 wrong claimed batch_ref denied even with COMMITTED',async()=>{
 const {signed,c}=await triple();
 const r=review(signed,c,{...receipt(c),batch_ref:'FORGED'});
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'CLAIMED_RECEIPT_REJECTED');
});
test('RECEIPT-23 replay counters cannot exceed batch total',async()=>{
 const {signed,c}=await triple();
 const r=review(signed,c,{...receipt(c),
  outcome:'ALREADY_ACCEPTED',accepted:0,duplicates:2});
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'CLAIMED_RECEIPT_REJECTED');
});
test('RECEIPT-24 claimed ALREADY_ACCEPTED remains shape-only without authority',async()=>{
 const {signed,c}=await triple();
 const r=review(signed,c,{...receipt(c),
  outcome:'ALREADY_ACCEPTED',accepted:0,duplicates:1});
 noRights(r);assert.equal(r.decision,'CLAIMED_RECEIPT_SHAPE_ONLY_UNVERIFIED');
 assert.equal(r.reason,'NO_AUTHENTICATED_DURABLE_EVIDENCE');
});
test('RECEIPT-25 100-event batch and claimed receipt still no ACK',async()=>{
 const many=Array.from({length:100},(_,i)=>msg('wamid.R'+i));
 const {signed,c}=await triple(body([entry(W1,P1,many)]));
 const r=review(signed,c,receipt(c));
 noRights(r);assert.equal(r.event_count,100);
});
test('RECEIPT-26 status and message counts must align exactly',async()=>{
 const {signed,c}=await triple(body([entry(W1,P1,
  [msg('wamid.MSG')],[status('wamid.STATUS')])]));
 const wrong={...c,occurrences:c.occurrences.map((e,i)=>
  i===1?{...e,event_kind:'inbound_message'}:e)};
 const r=review(signed,wrong,receipt(wrong));
 noRights(r);assert.equal(r.reason,'CANDIDATE_SCOPE_MISMATCH');
});

test('RECEIPT-27 wrong candidate route is rejected even if receipt echoes it',async()=>{
 const {signed,c}=await triple();
 const changed={...c,route_ref:'ROUTE_FORGED'};
 const r=review(signed,changed,receipt(changed));
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'CANDIDATE_SCOPE_MISMATCH');
});
test('RECEIPT-28 stale candidate route revision is rejected before receipt',async()=>{
 const {signed,c}=await triple();
 const changed={...c,route_revision:6};
 const r=review(signed,changed,receipt(changed));
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'CANDIDATE_SCOPE_MISMATCH');
});
test('RECEIPT-29 claimed route missing from trusted host input is rejected',async()=>{
 const {signed,c}=await triple();
 const r=reviewRaw(signed,c,receipt(c),{
  route_ref:'ROUTE_B',expected_revision:7,
 });
 noRights(r);assert.equal(r.decision,'DENIED');
 assert.equal(r.reason,'CANDIDATE_SCOPE_MISMATCH');
});
