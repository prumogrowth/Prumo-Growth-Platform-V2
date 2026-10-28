/**
 * READ-ONLY S0/Meta cross-contract audit; two unrelated OFFLINE inspectors.
 * This test does not import or modify S0 implementation, database, permissions
 * or a real ingress endpoint. One fake trusted registry is shared by fixtures.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac,createHash} from 'node:crypto';
import {inspectSignedMetaComposedWebhook} from './cloud-composed-observation-handoff.ts';
import {prepareS0HandoffFixture,reviewS0ReceiptFixture}
 from './s0-handoff-contract.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';
import type {TrustedRoutingPorts} from './routed-webhook.ts';

const SECRET='META_S0_READONLY_AUDIT_SYNTHETIC_SECRET';
const WHEN=1792320000000,STAMP='1792320000';
const WABA_A='123456789012',PHONE_A='987654321098';
const WABA_B='123456789013',PHONE_B='987654321099';
const APP='APP_A',ROUTE='ROUTE_A';
const CHANNEL_A='CH_A',CHANNEL_B='CH_B',SHOP='SHOP_A';
const app={
 app_ref:APP,route_ref:ROUTE,concessionaria_id:SHOP,active:true,
 revision:7,valid_from_ms:WHEN-1000,valid_until_ms:WHEN+1000,
 secret_slots:{
  get_verify_token:'A_GET',post_app_secret:'A_POST',
  graph_access_token:'A_GRAPH',
 },
 channels:[
  {canal_id:CHANNEL_A,waba_id:WABA_A,phone_number_id:PHONE_A,active:true},
  {canal_id:CHANNEL_B,waba_id:WABA_B,phone_number_id:PHONE_B,active:true},
 ],
};
const registry:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',
 apps:[app],
};
const ports=(reg:TrustedMetaRegistry=registry):TrustedRoutingPorts=>({
 currentRegistry:()=>reg,
 resolveSecret:(slot)=>slot==='A_POST'?SECRET:undefined,
 nowMs:()=>WHEN,
});
const route=(waba_id=WABA_A,phone_number_id=PHONE_A)=>({
 waba_id,phone_number_id,revision:7,
});
const message=(id='wamid.MSG_A',ctx?:unknown)=>({
 id,from:'5581888800000',timestamp:STAMP,type:'text',
 text:{body:'Sensitive fictional text must never be copied into S0 metadata'},
 ...(ctx===undefined?{}:{context:ctx}),
});
const status=(id='wamid.OUT_A',value:'sent'|'failed'='sent')=>({
 id,recipient_id:'5581888800000',timestamp:STAMP,status:value,
 ...(value==='failed'?{errors:[{code:131026}]}:{}),
});
const entry=(waba_id=WABA_A,phone_number_id=PHONE_A,
 messages:unknown[]=[message()],statuses:unknown[]=[])=>({
 id:waba_id,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id},
  messages,statuses,
 }}],
});
const body=(entries:unknown[]=[entry()])=>({
 object:'whatsapp_business_account',entry:entries,
});
const raw=(x:unknown)=>Buffer.from(JSON.stringify(x),'utf8');
const sign=(bytes:Uint8Array,key=SECRET)=>
 'sha256='+createHmac('sha256',key).update(bytes).digest('hex');
const call=async(payload:unknown,scope=route(),reg=registry,key=SECRET)=>{
 const bytes=raw(payload),signature=sign(bytes,key);
 const [meta,s0]=await Promise.all([
  inspectSignedMetaComposedWebhook(bytes,signature,SECRET,scope),
  prepareS0HandoffFixture({
   request:{
    route:{route_ref:ROUTE,expected_revision:7},
    raw_body:bytes,signature_header:signature,
   },
   batch_ref:'BATCH_CROSS_AUDIT',protected_payload_ref:'PAYLOAD_CROSS_AUDIT',
  },ports(reg)),
 ]);
 return {meta,s0,bytes};
};
const safe=(o:object)=>{
 const x=o as Record<string,unknown>;
 assert.equal(x.ack_allowed,false);
 assert.equal(x.production_authorized,false);
};
function bothAccepted(x:Awaited<ReturnType<typeof call>>){
 safe(x.meta);safe(x.s0);
 assert.equal(x.meta.decision,'SIGNED_COMPOSED_NOT_DURABLE');
 assert.equal(x.s0.ok,true);
 if(x.meta.decision!=='SIGNED_COMPOSED_NOT_DURABLE'||!x.s0.ok)
  throw Error('missing synthetic observation');
 return {meta:x.meta,s0:x.s0.candidate};
}
const receipt=(c:ReturnType<typeof bothAccepted>['s0'])=>({
 contract_version:'meta-s0-receipt.v0.1-proposed',
 batch_ref:c.batch_ref,app_ref:c.app_ref,
 protected_payload_ref:c.protected_payload_ref,
 payload_sha256:c.payload_sha256,scope_sha256:c.scope_sha256,
 route_ref:c.route_ref,route_revision:c.route_revision,
 total:c.event_count,accepted:c.event_count,duplicates:0,quarantined:0,
 outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',
});
test('BOUNDARY-01 same signed single-WABA callback is visible technically in both readers',async()=>{
 const result=bothAccepted(await call(body()));
 assert.equal(result.meta.occurrences.length,1);
 assert.equal(result.s0.event_count,1);
 assert.equal(result.meta.occurrences[0].provider_message_id,
  result.s0.occurrences[0].provider_message_id);
 assert.equal(result.s0.occurrences[0].canal_id,CHANNEL_A);
 assert.equal(result.meta.route_revision,result.s0.route_revision);
});
test('BOUNDARY-02 physical raw sha256 agrees, but is not durable receipt',async()=>{
 const x=await call(body());
 const {meta,s0}=bothAccepted(x);
 const hex=createHash('sha256').update(x.bytes).digest('hex');
 assert.equal(meta.raw_sha256,hex);
 assert.equal(s0.payload_sha256,hex);
 assert.equal('commit_state' in s0,false);
 assert.equal('http_status' in s0,false);
 assert.equal('ack_allowed' in s0,true);
 assert.equal(s0.ack_allowed,false);
});
test('BOUNDARY-03 two WABAs SAME App pass S0 candidate but deny single-route Meta reader',async()=>{
 const x=await call(body([
  entry(WABA_A,PHONE_A,[message('wamid.FIRST')]),
  entry(WABA_B,PHONE_B,[message('wamid.SECOND')]),
 ]));
 safe(x.meta);safe(x.s0);
 assert.equal(x.s0.ok,true);
 if(!x.s0.ok)throw Error('S0 synthetic multi-WABA denied');
 assert.equal(x.s0.candidate.event_count,2);
 assert.deepEqual(x.s0.candidate.occurrences.map(e=>e.canal_id),
  [CHANNEL_A,CHANNEL_B]);
 assert.equal(x.meta.decision,'DENIED');
 if(x.meta.decision==='DENIED'){
  assert.equal(x.meta.reason,'VERIFICATION_DENIED');
  assert.deepEqual(x.meta.occurrences,[]);
 }
});
test('BOUNDARY-04 different App not in trusted registry fails atomically in S0',async()=>{
 const x=await call(body([
  entry(WABA_A,PHONE_A,[message('wamid.ONE')]),
  entry('777777777777','777777777778',[message('wamid.SECOND')]),
 ]));
 assert.equal(x.s0.ok,false);
 assert.equal(x.meta.decision,'DENIED');
 safe(x.meta);safe(x.s0);
});
test('BOUNDARY-05 same WABA with wrong phone for second entry never grants S0 scope',async()=>{
 const x=await call(body([
  entry(WABA_A,PHONE_A,[message('wamid.ONE')]),
  entry(WABA_A,PHONE_B,[message('wamid.TWO')]),
 ]));
 assert.equal(x.s0.ok,false);
 assert.equal(x.meta.decision,'DENIED');
 safe(x.meta);safe(x.s0);
});
test('BOUNDARY-06 signed quote remains uncorrelated and omitted from S0 minimal metadata',async()=>{
 const x=await call(body([entry(
  WABA_A,PHONE_A,[message('wamid.REPLY',{
   id:'wamid.ORIGINAL',from:'5581888812345',
   referred_product:{catalog_id:'SYNTHETIC_PRIVATE_CATALOG'},
  })],
 )]));
 const {meta,s0}=bothAccepted(x);
 assert.equal(meta.occurrences[0].quoted_reference?.quoted_provider_message_id,
  'wamid.ORIGINAL');
 const serialized=JSON.stringify(s0);
 assert.equal(serialized.includes('wamid.ORIGINAL'),false);
 assert.equal(serialized.includes('5581888812345'),false);
 assert.equal(serialized.includes('SYNTHETIC_PRIVATE_CATALOG'),false);
 assert.equal(serialized.includes('Sensitive fictional'),false);
});
test('BOUNDARY-07 claimed committed receipt cannot grant HTTP ACK',async()=>{
 const {s0}=bothAccepted(await call(body()));
 const reviewed=reviewS0ReceiptFixture(s0,receipt(s0));
 assert.equal(reviewed.verdict,'STRUCTURE_MATCHES_BUT_UNVERIFIED');
 assert.equal(reviewed.reason,'NEEDS_AUTHENTICATED_S0_COMMIT_EVIDENCE');
 assert.equal(reviewed.ack_allowed,false);
 assert.equal(reviewed.production_authorized,false);
});
test('BOUNDARY-08 fake receipt with partial counters is denied without ACK',async()=>{
 const {s0}=bothAccepted(await call(body()));
 const rejected=reviewS0ReceiptFixture(s0,{...receipt(s0),
  accepted:0,duplicates:0});
 assert.equal(rejected.verdict,'DENIED');
 assert.equal(rejected.ack_allowed,false);
});
test('BOUNDARY-09 invalid HMAC denies both independent readers',async()=>{
 const bytes=raw(body()),signature=sign(bytes,'WRONG_KEY');
 const [meta,s0]=await Promise.all([
  inspectSignedMetaComposedWebhook(bytes,signature,SECRET,route()),
  prepareS0HandoffFixture({request:{
   route:{route_ref:ROUTE,expected_revision:7},
   raw_body:bytes,signature_header:signature,
  },batch_ref:'BATCH_A',protected_payload_ref:'PAYLOAD_A'},ports()),
 ]);
 safe(meta);safe(s0);
 assert.equal(meta.decision,'DENIED');assert.equal(s0.ok,false);
});
test('BOUNDARY-10 signed but malformed sibling refuses whole batch',async()=>{
 const bad={...message('wamid.BAD'),timestamp:'INVALID'};
 const x=await call(body([entry(WABA_A,PHONE_A,[message('wamid.OK'),bad])]));
 assert.equal(x.meta.decision,'DENIED');assert.equal(x.s0.ok,false);
 safe(x.meta);safe(x.s0);
});
test('BOUNDARY-11 duplicate event IDs remain separate positions in both readers',async()=>{
 const dup=message();
 const {meta,s0}=bothAccepted(await call(body([entry(
  WABA_A,PHONE_A,[dup,{...dup}],
 )])));
 assert.equal(meta.occurrences.length,2);
 assert.equal(s0.event_count,2);
 assert.deepEqual(meta.occurrences.map(e=>e.position.item_index),[0,1]);
 assert.deepEqual(s0.occurrences.map(e=>e.position.item_index),[0,1]);
 assert.equal(meta.deduplicated,false);
});
test('BOUNDARY-12 status callback is not a new inbound customer conversation',async()=>{
 const {meta,s0}=bothAccepted(await call(body([entry(
  WABA_A,PHONE_A,[],[status('wamid.OUT','sent')],
 )])));
 assert.equal(meta.occurrences[0].source_kind,'status_callback');
 assert.equal(meta.occurrences[0].kind,'uninterpreted_status');
 assert.equal(s0.occurrences[0].event_kind,'status_callback');
 assert.equal(s0.occurrences[0].provider_message_id,'wamid.OUT');
});
test('BOUNDARY-13 sender binding revocation blocks S0 but does not automatically revoke stateless Meta HMAC',async()=>{
 const revoked:TrustedMetaRegistry={
  ...registry,apps:[{...app,active:false}],
 };
 const x=await call(body(),route(),revoked);
 assert.equal(x.meta.decision,'SIGNED_COMPOSED_NOT_DURABLE');
 assert.equal(x.s0.ok,false);
 safe(x.meta);safe(x.s0);
});
test('BOUNDARY-14 S0 internal proof is a separate security domain from Meta signature',async()=>{
 const {meta,s0}=bothAccepted(await call(body()));
 assert.equal('m2m_proof' in meta,false);
 assert.equal('m2m_proof' in s0,false);
 assert.equal('nonce' in s0,false);
 assert.equal('nonce' in meta,false);
 assert.equal(s0.ack_allowed,false);
 assert.equal(meta.ack_allowed,false);
});
