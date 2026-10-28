import test from 'node:test';
import assert from 'node:assert/strict';
import {createHmac,createHash} from 'node:crypto';
import {inspectSignedMetaBatchChannelScope as inspect}
 from './cloud-batch-scope-preflight.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';
import type {TrustedRoutingPorts} from './routed-webhook.ts';

const KEY='SYNTHETIC_APP_SCOPE_NOT_META';
const NOW=1792320000000;
const A='123456789012',B='123456789013',C='123456789014';
const P='987654321098',Q='987654321099',R='987654321097';
const app={
 app_ref:'APP_A',route_ref:'ROUTE_A',concessionaria_id:'SHOP_A',
 active:true,revision:7,valid_from_ms:NOW-1000,valid_until_ms:NOW+1000,
 secret_slots:{get_verify_token:'APP_GET',post_app_secret:'APP_POST',graph_access_token:'APP_GRAPH'},
 channels:[
  {canal_id:'CH_A',waba_id:A,phone_number_id:P,active:true},
  {canal_id:'CH_B',waba_id:B,phone_number_id:Q,active:true},
  {canal_id:'CH_C',waba_id:A,phone_number_id:R,active:true},
 ],
};
const registry:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',
 apps:[app],
};
const ports=(reg:TrustedMetaRegistry=registry):TrustedRoutingPorts=>({
 currentRegistry:()=>reg,
 resolveSecret:(s)=>s==='APP_POST'?KEY:undefined,
 nowMs:()=>NOW,
});
const message=(id='wamid.M1')=>({
 id,from:'5581888800000',type:'text',timestamp:'1792320000',
 text:{body:'NEVER_EXPOSE_CUSTOMER_TEXT'},
});
const status=(id='wamid.S1')=>({
 id,recipient_id:'5581888800000',status:'delivered',timestamp:'1792320000',
});
const entry=(waba=A,phone=P,messages:unknown[]=[message()],
 statuses:unknown[]=[])=>({
 id:waba,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:phone},
  messages,statuses,
 }}],
});
const payload=(entries:unknown[]=[entry()])=>({
 object:'whatsapp_business_account',entry:entries,
});
const bytes=(v:unknown)=>Buffer.from(JSON.stringify(v),'utf8');
const sig=(b:Uint8Array,secret=KEY)=>
 'sha256='+createHmac('sha256',secret).update(b).digest('hex');
const req=(b:Uint8Array,signature:string|null=sig(b),
 route_ref='ROUTE_A',expected_revision=7)=>({
 raw_body:b,signature_header:signature,
 route:{route_ref,expected_revision},
});
const run=(v:unknown=payload(),port=ports(),key=KEY)=>{
 const b=bytes(v);return inspect(req(b,sig(b,key)),port);
};
type Result=Awaited<ReturnType<typeof inspect>>;
function noRights(r:Result){
 assert.equal(Object.isFrozen(r),true);
 for(const name of [
  'ack_allowed','partial_ack_allowed','send_authorized','s0_write_authorized',
  'production_authorized','commercial_effect_authorized','delivery_confirmed',
  'consent_verified','service_identity_verified','m2m_verified','persisted',
  'durable_receipt_verified','batch_partition_authorized',
  'channel_policy_ratified','automatic_retry_authorized','deduplicated',
 ] as const)assert.equal(r[name],false,name);
}
function allowed(r:Result,decision:'SIGNED_SINGLE_CHANNEL_TECHNICAL'|
 'SIGNED_MULTI_CHANNEL_UNRATIFIED'){
 noRights(r);assert.equal(r.decision,decision);
 if(r.decision==='DENIED')throw Error('denied');
 assert.equal(r.reason,null);
 assert.equal(r.scope_count,r.channels.length);
 assert.equal(r.event_count,r.channels.reduce((n,c)=>n+c.occurrence_count,0));
 assert.match(r.raw_sha256,/^[a-f0-9]{64}$/);
 assert.ok(Object.isFrozen(r.channels));
 return r;
}
function denied(r:Result,reason?:string){
 noRights(r);assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('accepted');
 if(reason)assert.equal(r.reason,reason);
 assert.equal(r.event_count,0);
 assert.equal(r.scope_count,0);
 assert.deepEqual(r.channels,[]);
 assert.equal(r.raw_sha256,null);
}
test('PREFLIGHT-01 single signed channel is technical only; no ACK/partition',async()=>{
 const v=allowed(await run(), 'SIGNED_SINGLE_CHANNEL_TECHNICAL');
 assert.equal(v.scope_count,1);assert.equal(v.event_count,1);
 assert.equal(v.channels[0].canal_id,'CH_A');
 assert.deepEqual([v.channels[0].inbound_message_count,
  v.channels[0].status_callback_count],[1,0]);
});
test('PREFLIGHT-02 same App multi-WABA batch is visible but UNRATIFIED',async()=>{
 const v=allowed(await run(payload([entry(),entry(B,Q,[message('wamid.M2')])])),
  'SIGNED_MULTI_CHANNEL_UNRATIFIED');
 assert.equal(v.scope_count,2);
 assert.equal(v.event_count,2);
 assert.deepEqual(v.channels.map(x=>x.canal_id),['CH_A','CH_B']);
 assert.ok(v.channels.every(x=>x.app_ref==='APP_A'&&x.concessionaria_id==='SHOP_A'));
});
test('PREFLIGHT-03 mixed message and status aggregate without collapsing either',async()=>{
 const v=allowed(await run(payload([
  entry(A,P,[message('wamid.1'),message('wamid.2')],[status('wamid.OUT')]),
  entry(B,Q,[],[status('wamid.OUT2')]),
 ])), 'SIGNED_MULTI_CHANNEL_UNRATIFIED');
 assert.deepEqual(v.channels.map(x=>[x.inbound_message_count,x.status_callback_count]),
  [[2,1],[0,1]]);
 assert.equal(v.event_count,4);
});
test('PREFLIGHT-04 repeated wamid is NOT deduped across positions',async()=>{
 const m=message(),v=allowed(await run(payload([
  entry(A,P,[m,{...m}])])), 'SIGNED_SINGLE_CHANNEL_TECHNICAL');
 assert.equal(v.event_count,2);
 assert.equal(v.deduplicated,false);
});
test('PREFLIGHT-05 same WABA distinct registered sender phones are distinct channels',async()=>{
 const v=allowed(await run(payload([
  entry(A,P,[message('wamid.FIRST')]),
  entry(A,R,[message('wamid.SECOND')]),
 ])),'SIGNED_MULTI_CHANNEL_UNRATIFIED');
 assert.deepEqual(v.channels.map(x=>x.canal_id),['CH_A','CH_C']);
});
test('PREFLIGHT-06 same channel across multiple entries coalesces counters only',async()=>{
 const v=allowed(await run(payload([
  entry(A,P,[message('wamid.ONE')]),
  entry(A,P,[message('wamid.TWO')],[status()]),
 ])), 'SIGNED_SINGLE_CHANNEL_TECHNICAL');
 assert.equal(v.event_count,3);
 assert.equal(v.scope_count,1);
 assert.equal(v.channels[0].occurrence_count,3);
});
test('PREFLIGHT-07 raw SHA covers FULL physical POST and is not a receipt',async()=>{
 const p=payload([entry(),entry(B,Q)]),b=bytes(p);
 const r=allowed(await inspect(req(b),ports()),'SIGNED_MULTI_CHANNEL_UNRATIFIED');
 assert.equal(r.raw_sha256,createHash('sha256').update(b).digest('hex'));
 assert.equal(r.persisted,false);assert.equal(r.durable_receipt_verified,false);
});
test('PREFLIGHT-08 tampered HMAC denies whole mixed batch, no channel leak',async()=>{
 const b=bytes(payload([entry(),entry(B,Q)]));
 denied(await inspect(req(b,sig(b,'OTHER_KEY')),ports()),
  'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-09 no signature denies whole batch',async()=>{
 const b=bytes(payload([entry(),entry(B,Q)]));
 denied(await inspect(req(b,null),ports()),'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-10 unmapped WABA in a validly signed batch denies all',async()=>{
 denied(await run(payload([entry(),entry(C,Q)])),
  'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-11 unmapped phone within known WABA denies all',async()=>{
 denied(await run(payload([entry(),entry(A,Q)])),
  'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-12 App from separate route cannot be smuggled in by event',async()=>{
 const extra={
  ...app,app_ref:'APP_B',route_ref:'ROUTE_B',concessionaria_id:'SHOP_B',
  secret_slots:{get_verify_token:'B_GET',post_app_secret:'B_POST',
   graph_access_token:'B_GRAPH'},
  channels:[{canal_id:'CH_Z',waba_id:C,phone_number_id:Q,active:true}],
 };
 const multi={...registry,apps:[app,extra]};
 denied(await run(payload([entry(),entry(C,Q)]),ports(multi)),
  'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-13 revoked App or revoked channel blocks entire signed view',async()=>{
 const inactive={...registry,apps:[{...app,active:false}]};
 denied(await run(payload(),ports(inactive)),'SIGNATURE_OR_ROUTING_DENIED');
 const reg={...registry,apps:[{...app,channels:app.channels.map(c=>
  c.canal_id==='CH_B'?{...c,active:false}:c)}]};
 denied(await run(payload([entry(),entry(B,Q)]),ports(reg)),
  'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-14 stale revision fails before distribution',async()=>{
 const b=bytes(payload());
 denied(await inspect(req(b,sig(b),'ROUTE_A',8),ports()),
  'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-15 missing registry/secret denies before exposure',async()=>{
 denied(await run(payload(),{...ports(),resolveSecret:()=>undefined}),
  'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-16 malformed signed sibling denies all, no partial counts',async()=>{
 const bad={...message('wamid.BAD'),timestamp:'NOT_TIMESTAMP'};
 denied(await run(payload([entry(),entry(B,Q,[bad])])),
  'SIGNATURE_OR_ROUTING_DENIED');
});
test('PREFLIGHT-17 original byte mutation after call is isolated',async()=>{
 const b=bytes(payload([entry(),entry(B,Q)]));
 const task=inspect(req(b),ports());
 b.fill(0);
 const r=allowed(await task,'SIGNED_MULTI_CHANNEL_UNRATIFIED');
 assert.equal(r.event_count,2);
});
test('PREFLIGHT-18 caller route mutation after call cannot rebind App',async()=>{
 const b=bytes(payload([entry(),entry(B,Q)]));
 const request=req(b);
 const task=inspect(request,ports());
 request.route.route_ref='ROUTE_B';
 request.route.expected_revision=999;
 const r=allowed(await task,'SIGNED_MULTI_CHANNEL_UNRATIFIED');
 assert.equal(r.scope_count,2);
});
test('PREFLIGHT-19 invalid input and over-size fail before HMAC',async()=>{
 const b=bytes(payload());
 denied(await inspect(req(b,sig(b),'../bad'),ports()),'INVALID_INPUT');
 const huge=Buffer.alloc(256*1024+1,65);
 denied(await inspect(req(huge,sig(huge)),ports()),'INVALID_INPUT');
});
test('PREFLIGHT-20 no events cannot be promoted to a signed distribution',async()=>{
 denied(await run(payload([entry(A,P,[],[])])));
});
test('PREFLIGHT-21 one hundred events stay counted by channel',async()=>{
 const many=Array.from({length:100},(_,i)=>message('wamid.M'+i));
 const r=allowed(await run(payload([entry(A,P,many)])),
  'SIGNED_SINGLE_CHANNEL_TECHNICAL');
 assert.equal(r.event_count,100);
});
test('PREFLIGHT-22 one hundred and one events refuse all',async()=>{
 const many=Array.from({length:101},(_,i)=>message('wamid.M'+i));
 denied(await run(payload([entry(A,P,many)])));
});
test('PREFLIGHT-23 report is technical only: never expose participant, wamid, content',async()=>{
 const v=allowed(await run(payload([entry(A,P,[message('wamid.VERY_SECRET')])])),
  'SIGNED_SINGLE_CHANNEL_TECHNICAL');
 const s=JSON.stringify(v);
 for(const token of ['wamid.VERY_SECRET','5581888800000',
  'NEVER_EXPOSE_CUSTOMER_TEXT','APP_POST',KEY])
  assert.equal(s.includes(token),false,token);
});
test('PREFLIGHT-24 mutable trusted registry revocation after HMAC must deny',async()=>{
 let count=0;
 const revoked={...registry,apps:[{...app,active:false}]};
 const dynamic:TrustedRoutingPorts={
  ...ports(),
  currentRegistry:()=>{count++;return count>=2?revoked:registry;},
 };
 denied(await run(payload(),dynamic),'SIGNATURE_OR_ROUTING_DENIED');
 assert.ok(count>=2);
});
