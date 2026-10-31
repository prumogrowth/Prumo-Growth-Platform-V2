/** Signed synthetic Meta/S0 trust-boundary tests; NO HTTP, DB or Graph. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac} from 'node:crypto';
import {auditHttpAckClaimsOffline as audit}
 from './cloud-http-ack-authority-audit.ts';
import {inspectSignedMetaBatchChannelScope as preflight}
 from './cloud-batch-scope-preflight.ts';
import {prepareS0HandoffFixture}
 from './s0-handoff-contract.ts';
import {decideBatchAck} from './durable-receipt.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';
import type {TrustedRoutingPorts} from './routed-webhook.ts';

const SECRET='OFFLINE_ACK_PERIMETER_SYNTHETIC';
const NOW=1792320000000, W1='123456789012',P1='987654321098';
const W2='123456789013',P2='987654321099';
const app={app_ref:'APP_A',route_ref:'ROUTE_A',concessionaria_id:'SHOP_A',
 active:true,revision:7,valid_from_ms:NOW-1000,valid_until_ms:NOW+1000,
 secret_slots:{get_verify_token:'APP_GET',post_app_secret:'APP_POST',
  graph_access_token:'APP_GRAPH'},
 channels:[{canal_id:'CH_A',waba_id:W1,phone_number_id:P1,active:true},
  {canal_id:'CH_B',waba_id:W2,phone_number_id:P2,active:true}],
};
const registry:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',
 apps:[app],
};
const ports=():TrustedRoutingPorts=>({
 currentRegistry:()=>registry,resolveSecret:s=>s==='APP_POST'?SECRET:undefined,
 nowMs:()=>NOW,
});
const message=(id:string)=>({id,from:'5581888800000',type:'text',
 timestamp:'1792320000',text:{body:'CUSTOMER_PRIVATE_ABC'}});
const entry=(waba=W1,phone=P1,id='wamid.INPUT')=>({
 id:waba,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:phone},
  messages:[message(id)],
 }}],
});
const body=(entries:unknown[]=[entry()])=>({
 object:'whatsapp_business_account',entry:entries,
});
const encode=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const signed=(b:Uint8Array)=>
 'sha256='+createHmac('sha256',SECRET).update(b).digest('hex');
const route=Object.freeze({route_ref:'ROUTE_A',expected_revision:7});
async function fixture(entries:unknown[]=[entry()]){
 const b=encode(body(entries));
 const q={raw_body:b,signature_header:signed(b),route};
 const [s,r]=await Promise.all([preflight(q,ports()),
  prepareS0HandoffFixture({
   request:q,batch_ref:'BATCH_HTTP_AUDIT',protected_payload_ref:'PAYLOAD_HTTP_AUDIT',
  },ports())]);
 assert.notEqual(s.decision,'DENIED');
 assert.equal(r.ok,true);
 if(r.ok===false||s.decision==='DENIED')throw Error('fixture');
 const c=r.candidate;
 const alleged={
  contract_version:'meta-s0-receipt.v0.1-proposed',batch_ref:c.batch_ref,
  app_ref:c.app_ref,protected_payload_ref:c.protected_payload_ref,
  payload_sha256:c.payload_sha256,scope_sha256:c.scope_sha256,
  route_ref:c.route_ref,route_revision:c.route_revision,
  total:c.event_count,accepted:c.event_count,duplicates:0,quarantined:0,
  outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',
 };
 return {s,c,alleged};
}
async function input(p:Record<string,unknown>={}){
 const f=await fixture();
 return {signed_batch:f.s,s0_handoff_candidate:f.c,
  alleged_receipt:f.alleged,trusted_route:route,
  alleged_m2m_proof:null,alleged_http_decision:null,...p};
}
function closed(v:ReturnType<typeof audit>){
 assert.equal(v.disposition,'NO_HTTP_ACTION_AUTHORIZED');
 assert.equal(Object.isFrozen(v),true);
 assert.equal('status' in v,false);
 assert.equal('action' in v,false);
 assert.equal('http_status' in v,false);
 for(const [k,x] of Object.entries(v))
  if(k.endsWith('_allowed')||k.endsWith('_authorized')||
     k.endsWith('_verified')||k==='deduplicated'||k==='retry_external')
   assert.equal(x,false,k);
 const str=JSON.stringify(v);
 for(const secret of ['CUSTOMER_PRIVATE_ABC','5581888800000','wamid.INPUT',SECRET])
  assert.equal(str.includes(secret),false);
 return v;
}
test('ACK-PERIMETER-01 perfect forged COMMITTED receipt still cannot authorize HTTP',async()=>{
 const v=closed(audit(await input()));
 assert.equal(v.reason,'S0_COMMIT_AUTHORITY_NOT_VERIFIED');
 assert.equal(v.receipt_shape,'MATCHES_UNVERIFIED');
 assert.equal(v.scope_shape,'SINGLE_CHANNEL');
});
test('ACK-PERIMETER-02 missing receipt means unknown result, never rollback/ACK',async()=>{
 const v=closed(audit(await input({alleged_receipt:null})));
 assert.equal(v.reason,'CLAIMED_RECEIPT_ABSENT');
 assert.equal(v.receipt_shape,'ABSENT');
});
test('ACK-PERIMETER-03 legacy helper is now closed and forged ACK200 refused',async()=>{
 const old=decideBatchAck(1,{outcome:'ACCEPTED_DURABLE',
  commit_state:'COMMITTED',total:1,accepted:1,duplicates:0,quarantined:0});
 assert.equal(old.decision,'DENIED_NO_HTTP_AUTHORITY');
 assert.equal('status' in old,false);
 assert.equal('action' in old,false);
 const v=closed(audit(await input({alleged_http_decision:{
  status:200,action:'ACK',reason:'ALL_ITEMS_DURABLE'}})));
 assert.equal(v.reason,'UNTRUSTED_HTTP_ACTION');
});
test('ACK-PERIMETER-04 arbitrary HTTP503 is not a transport policy either',async()=>{
 const v=closed(audit(await input({alleged_http_decision:{
  status:503,action:'RETRY'}})));
 assert.equal(v.reason,'UNTRUSTED_HTTP_ACTION');
});
test('ACK-PERIMETER-05 plain status=200 injection refused',async()=>{
 const v=closed(audit(await input({alleged_http_decision:200})));
 assert.equal(v.reason,'UNTRUSTED_HTTP_ACTION');
});
test('ACK-PERIMETER-06 HTML-like HTTP status claim cannot leak',async()=>{
 const v=closed(audit(await input({alleged_http_decision:'HTTP/1.1 200 OK'})));
 assert.equal(v.reason,'UNTRUSTED_HTTP_ACTION');
});
test('ACK-PERIMETER-07 apparent M2M HMAC does not prove issuer',async()=>{
 const v=closed(audit(await input({alleged_m2m_proof:{
  kind:'LAB_M2M_HMAC',key_id:'SERVICE_A',
  mac_sha256:'a'.repeat(64)}})));
 assert.equal(v.reason,'M2M_CLAIM_NOT_VERIFIED');
 assert.equal(v.receipt_shape,'MATCHES_UNVERIFIED');
});
test('ACK-PERIMETER-08 JWT-shaped bearer is not ingress M2M evidence',async()=>{
 const v=closed(audit(await input({alleged_m2m_proof:'header.payload.signature'})));
 assert.equal(v.reason,'M2M_CLAIM_NOT_VERIFIED');
});
test('ACK-PERIMETER-09 truthy service authorized flag cannot grant ACK',async()=>{
 const v=closed(audit(await input({alleged_m2m_proof:{
  verified:true,active:true,role:'director'}})));
 assert.equal(v.reason,'M2M_CLAIM_NOT_VERIFIED');
});
test('ACK-PERIMETER-10 unknown proof URL is not a readback',async()=>{
 const v=closed(audit(await input({alleged_m2m_proof:{
  receipt_url:'https://invalid.example/claimed'}})));
 assert.equal(v.reason,'M2M_CLAIM_NOT_VERIFIED');
});
test('ACK-PERIMETER-11 missing technical signed evidence fails first',async()=>{
 const v=closed(audit(await input({signed_batch:null})));
 assert.equal(v.reason,'SIGNED_ENVELOPE_NOT_CONFIRMED');
});
test('ACK-PERIMETER-12 forged positive signature verdict with no field provenance fails',async()=>{
 const v=closed(audit(await input({signed_batch:{
  decision:'SIGNED_SINGLE_CHANNEL_TECHNICAL',event_count:1}})));
 assert.equal(v.reason,'SIGNED_ENVELOPE_NOT_CONFIRMED');
});
test('ACK-PERIMETER-13 escalated production flag rejects signed-shape claim',async()=>{
 const x=await input();
 const v=closed(audit({...x,signed_batch:{
  ...(x.signed_batch as object),production_authorized:true}}));
 assert.equal(v.reason,'SIGNED_ENVELOPE_NOT_CONFIRMED');
});
test('ACK-PERIMETER-14 escalated ACK flag rejects signed-shape claim',async()=>{
 const x=await input();
 const v=closed(audit({...x,signed_batch:{
  ...(x.signed_batch as object),ack_allowed:true}}));
 assert.equal(v.reason,'SIGNED_ENVELOPE_NOT_CONFIRMED');
});
test('ACK-PERIMETER-15 escalated M2M flag rejects signed-shape claim',async()=>{
 const x=await input();
 const v=closed(audit({...x,signed_batch:{
  ...(x.signed_batch as object),m2m_verified:true}}));
 assert.equal(v.reason,'SIGNED_ENVELOPE_NOT_CONFIRMED');
});
test('ACK-PERIMETER-16 no S0 candidate cannot authorize anything',async()=>{
 const v=closed(audit(await input({s0_handoff_candidate:null})));
 assert.equal(v.reason,'S0_CANDIDATE_NOT_CONFIRMED');
});
test('ACK-PERIMETER-17 wrong candidate raw digest is inconsistent',async()=>{
 const x=await input();
 const altered={...(x.s0_handoff_candidate as object),
  payload_sha256:'b'.repeat(64)};
 const v=closed(audit({...x,s0_handoff_candidate:altered}));
 assert.equal(v.reason,'CLAIMED_RECEIPT_INCONSISTENT');
});
test('ACK-PERIMETER-18 wrong trusted route revision invalidates structural match',async()=>{
 const v=closed(audit(await input({trusted_route:{
  route_ref:'ROUTE_A',expected_revision:8}})));
 assert.equal(v.reason,'CLAIMED_RECEIPT_INCONSISTENT');
});
test('ACK-PERIMETER-19 wrong trusted route name invalidates structural match',async()=>{
 const v=closed(audit(await input({trusted_route:{
  route_ref:'ROUTE_B',expected_revision:7}})));
 assert.equal(v.reason,'CLAIMED_RECEIPT_INCONSISTENT');
});
test('ACK-PERIMETER-20 malformed trusted route fails closed before receipt',async()=>{
 const v=closed(audit(await input({trusted_route:{
  route_ref:'../no',expected_revision:7}})));
 assert.equal(v.reason,'INVALID_BOUNDARY_INPUT');
});
test('ACK-PERIMETER-21 missing trusted route fails closed',async()=>{
 const v=closed(audit(await input({trusted_route:null})));
 assert.equal(v.reason,'INVALID_BOUNDARY_INPUT');
});
test('ACK-PERIMETER-22 extra root field is never silently trusted',async()=>{
 const v=closed(audit({...await input(),s0_authorized:true}));
 assert.equal(v.reason,'INVALID_BOUNDARY_INPUT');
});
test('ACK-PERIMETER-23 proxy/getter input fails without throwing secrets',async()=>{
 const x=await input();
 Object.defineProperty(x,'signed_batch',{get(){
  throw Error('SECRET_THROUGH_GETTER');},enumerable:true});
 const v=closed(audit(x));
 assert.equal(v.reason,'INVALID_BOUNDARY_INPUT');
});
test('ACK-PERIMETER-24 array or primitive input cannot grant authority',()=>{
 for(const x of [null,undefined,[],42,'APPROVED',true]){
  const v=closed(audit(x));assert.equal(v.reason,'INVALID_BOUNDARY_INPUT');
 }
});
test('ACK-PERIMETER-25 claimed receipt batch_ref mismatch stays invalid',async()=>{
 const x=await input();
 const v=closed(audit({...x,alleged_receipt:{
  ...(x.alleged_receipt as object),batch_ref:'BATCH_DIFFERENT'}}));
 assert.equal(v.reason,'CLAIMED_RECEIPT_INCONSISTENT');
});
test('ACK-PERIMETER-26 simulated ALREADY_ACCEPTED not replay authority',async()=>{
 const x=await input();
 const v=closed(audit({...x,alleged_receipt:{
  ...(x.alleged_receipt as object),outcome:'ALREADY_ACCEPTED',
  accepted:0,duplicates:1}}));
 assert.equal(v.reason,'S0_COMMIT_AUTHORITY_NOT_VERIFIED');
 assert.equal(v.durable_receipt_verified,false);
 assert.equal(v.replay_suppression_authorized,false);
});
test('ACK-PERIMETER-27 quarantine is not permission to ACK',async()=>{
 const x=await input();
 const v=closed(audit({...x,alleged_receipt:{
  ...(x.alleged_receipt as object),outcome:'QUARANTINED_DURABLE',
  accepted:0,quarantined:1}}));
 assert.equal(v.reason,'CLAIMED_RECEIPT_INCONSISTENT');
});
test('ACK-PERIMETER-28 mixed-channel signed batch requires separate ratification',async()=>{
 const f=await fixture([entry(W1,P1,'wamid.A'),
  entry(W2,P2,'wamid.B')]);
 const v=closed(audit({
  signed_batch:f.s,s0_handoff_candidate:f.c,
  alleged_receipt:f.alleged,trusted_route:route,
  alleged_m2m_proof:null,alleged_http_decision:null,
 }));
 assert.equal(v.reason,'MULTICHANNEL_POLICY_NOT_RATIFIED');
 assert.equal(v.scope_shape,'MULTICHANNEL_UNRATIFIED');
 assert.equal(v.receipt_shape,'MATCHES_UNVERIFIED');
});
test('ACK-PERIMETER-29 signed multi-channel with forged M2M still unrated',async()=>{
 const f=await fixture([entry(W1,P1,'wamid.A'),
  entry(W2,P2,'wamid.B')]);
 const v=closed(audit({
  signed_batch:f.s,s0_handoff_candidate:f.c,
  alleged_receipt:f.alleged,trusted_route:route,
  alleged_m2m_proof:{verified:true},alleged_http_decision:null,
 }));
 assert.equal(v.reason,'MULTICHANNEL_POLICY_NOT_RATIFIED');
 assert.equal(v.m2m_verified,false);
});
test('ACK-PERIMETER-30 deterministic no-authority verdict for repeated claim',async()=>{
 const x=await input();
 const a=closed(audit(x)),b=closed(audit(x));
 assert.deepEqual(a,b);
 assert.equal(Object.keys(a).includes('status'),false);
});
