import test from 'node:test';
import assert from 'node:assert/strict';
import {makeWa35SignedHandoffFixture as make,
 type Wa35SyntheticPorts} from './wa35-signed-ingress-handoff-fixture.ts';
import {verifyWa34SyntheticFixture,type Wa34Scope}
 from './wa34-service-forensic-handoff.ts';
import type {RoutablePost,TrustedRoutingPorts} from './routed-webhook.ts';
import type {TrustedMetaRegistry,TrustedMetaScope}
 from './credential-routing.ts';
import type {Wa32AttemptLookup}
 from './wa32-signed-status-s0-forensic-bridge.ts';

const TIME=1792320000000, APP_SECRET='WA35_LOCAL_ONLY_APP_SECRET';
const KEY=new Uint8Array(48).fill(0x63),nonce='WA35_NONCE_A';
const app={
 app_ref:'WA35_APP_A',route_ref:'WA35_ROUTE_A',
 concessionaria_id:'shop_A',revision:8,active:true,
 valid_from_ms:TIME-100000,valid_until_ms:TIME+120000,
 secret_slots:{get_verify_token:'WA35_GET_A',post_app_secret:'WA35_POST_A',
  graph_access_token:'WA35_GRAPH_A'},
 channels:[{canal_id:'WA35_CHANNEL_A',waba_id:'123456',
  phone_number_id:'1234567890',active:true}],
};
const appB={
 ...app,app_ref:'WA35_APP_B',route_ref:'WA35_ROUTE_B',
 concessionaria_id:'shop_B',secret_slots:{
  get_verify_token:'WA35_GET_B',post_app_secret:'WA35_POST_B',
  graph_access_token:'WA35_GRAPH_B'},
 channels:[{canal_id:'WA35_CHANNEL_B',waba_id:'223456',
  phone_number_id:'2234567890',active:true}],
};
const registry=():TrustedMetaRegistry=>({
 contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[app,appB],
});
const attempt=(s:TrustedMetaScope,m:string):Wa32AttemptLookup=>({
 ...s,provider_message_id:m,recipient_verified:'5581900000000',
 case_ref:'case31_hist',attempt_ref:'attempt31_hist',binding_revision:5,
 claim_state:'LAB_INVALIDATED',
});
function ports(options:{
 registry?:()=>TrustedMetaRegistry;clock?:()=>number;
 lookup?:(scope:TrustedMetaScope,m:string,phase:'LOOKUP'|'RECHECK')=>
  Promise<readonly Wa32AttemptLookup[]>;
 key?:()=>Promise<Uint8Array>;nonce?:()=>Promise<string>;
 secret?:()=>string;
}={}):Wa35SyntheticPorts{
 const routing:TrustedRoutingPorts={
  currentRegistry:async()=>options.registry?.()??registry(),
  resolveSecret:async()=>options.secret?.()??APP_SECRET,
  nowMs:options.clock??(()=>TIME),
 };
 return {routing,s0:{lookupExactAttempt:options.lookup??(async(s,m)=>[attempt(s,m)])},
  internalKey:options.key??(async()=>KEY),
  nonce:options.nonce??(async()=>nonce)};
}
const callback=(kind='delivered',ts='1792320000',
 msg='wamid.WA35_A',recipient='5581900000000')=>({
 id:msg,recipient_id:recipient,status:kind,timestamp:ts,
});
const body=(statuses:unknown[]=[callback()],waba='123456',
 phone='1234567890')=>({
 object:'whatsapp_business_account',
 entry:[{id:waba,changes:[{field:'messages',
  value:{metadata:{phone_number_id:phone},statuses}}]}],
});
async function sign(payload:unknown=body(),secret=APP_SECRET):
 Promise<RoutablePost>{
 const raw_body=new TextEncoder().encode(JSON.stringify(payload));
 const rawKey=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),
  {name:'HMAC',hash:'SHA-256'},false,['sign']);
 const mac=new Uint8Array(await crypto.subtle.sign('HMAC',rawKey,raw_body));
 const signature_header='sha256='+Array.from(mac,
  x=>x.toString(16).padStart(2,'0')).join('');
 return {route:{route_ref:'WA35_ROUTE_A',expected_revision:8},
  raw_body,signature_header};
}
function safe(result:Awaited<ReturnType<typeof make>>){
 for(const key of ['ack_allowed','send_authorized','retry_external',
  'production_authorized','delivery_confirmed',
  'case_transition_authorized','definitive_failure_count_increment'] as const)
  assert.equal(result[key],false);
 assert.equal(Object.isFrozen(result),true);
}
async function expect(req:RoutablePost,want:string,p=ports()){
 const decision=await make(req,p);safe(decision);
 assert.equal(decision.decision,want);
 if(want!=='LAB_TICKET_FOR_S0_RECHECK_ONLY')assert.equal(decision.ticket,null);
 return decision;
}
const issued='LAB_TICKET_FOR_S0_RECHECK_ONLY';
const scopeFromTicket=(t:NonNullable<Awaited<ReturnType<typeof make>>['ticket']>):
 Wa34Scope=>{
 const p=t.payload;
 return {app_ref:p.app_ref,concessionaria_id:p.concessionaria_id,
  canal_id:p.canal_id,waba_id:p.waba_id,
  phone_number_id:p.phone_number_id,provider_message_id:p.provider_message_id,
  recipient_verified:p.recipient_verified,case_ref:p.case_ref,
  attempt_ref:p.attempt_ref,binding_revision:p.binding_revision,
  event_ref:p.event_ref,provider_kind:p.provider_kind,
  meta_body_sha256:p.meta_body_sha256};
};
test('WA35-01 signed Meta POST -> real route -> exact attempt -> signed internal candidate',async()=>{
 const req=await sign();
 const result=await expect(req,issued);
 assert.ok(result.ticket);
 const signed=result.ticket;
 assert.equal(signed.payload.purpose,'FORENSIC_APPEND_ONLY');
 assert.equal(signed.payload.concessionaria_id,'shop_A');
 assert.equal(signed.payload.nonce_ref,nonce);
 assert.equal(signed.payload.issued_at_ms,TIME);
 assert.equal(signed.payload.expires_at_ms,TIME+60000);
 const verified=await verifyWa34SyntheticFixture(signed,
   scopeFromTicket(signed),TIME,KEY);
 assert.equal(verified.decision,'LAB_CONTRACT_PENDING');
 const hash=new Uint8Array(await crypto.subtle.digest('SHA-256',req.raw_body));
 assert.equal(signed.payload.meta_body_sha256,
  Array.from(hash,x=>x.toString(16).padStart(2,'0')).join(''));
});
test('WA35-02 wrong Meta HMAC cannot trigger S0 lookup or signing',async()=>{
 let calls=0,keys=0;
 const p=ports({lookup:async()=>{calls++;return []},
  key:async()=>{keys++;return KEY}});
 await expect(await sign(body(),'wrong-key'),'LAB_ROUTING_DENIED',p);
 assert.equal(calls,0);assert.equal(keys,0);
});
test('WA35-03 malformed signature cannot trigger signing',async()=>{
 const req={...await sign(),signature_header:'sha256=xyz'};
 await expect(req,'LAB_ROUTING_DENIED');
});
test('WA35-04 signed body from another WABA rejected by route binding',async()=>{
 const req=await sign(body([callback()],'223456','2234567890'));
 await expect(req,'LAB_ROUTING_DENIED');
});
test('WA35-05 mixed inbound and status cannot mint packet',async()=>{
 const b={object:'whatsapp_business_account',entry:[
 body().entry[0],{id:'123456',changes:[{field:'messages',
 value:{metadata:{phone_number_id:'1234567890'},
  messages:[{id:'wamid.INBOUND',from:'5581900000000',
   type:'text',timestamp:'1792320000'}]}}]}]};
 await expect(await sign(b),'LAB_UNSUPPORTED_EVENT');
});
test('WA35-06 signed status batch with two callbacks is rejected atomically',async()=>{
 await expect(await sign(body([callback(),callback('read')])),
  'LAB_UNSUPPORTED_EVENT');
});
test('WA35-07 no S0 binding is denied',async()=>{
 await expect(await sign(),'LAB_BINDING_DENIED',ports({lookup:async()=>[]}));
});
test('WA35-08 duplicate S0 binding is ambiguous',async()=>{
 await expect(await sign(),'LAB_BINDING_DENIED',ports({
 lookup:async(s,m)=>[attempt(s,m),attempt(s,m)]}));
});
test('WA35-09 wrong tenant/case sender scope rejected',async()=>{
 for(const key of ['concessionaria_id','app_ref','canal_id','waba_id',
  'phone_number_id'] as const){
  await expect(await sign(),'LAB_BINDING_DENIED',ports({
   lookup:async(s,m)=>[{...attempt(s,m),[key]:'OTHER'}]}));
 }
});
test('WA35-10 exact recipient, not normalized, is required',async()=>{
 await expect(await sign(),'LAB_BINDING_DENIED',ports({
 lookup:async(s,m)=>[{...attempt(s,m),recipient_verified:'5581900000001'}]}));
});
test('WA35-11 wamid from a different attempt cannot receive signed ticket',async()=>{
 await expect(await sign(),'LAB_BINDING_DENIED',ports({
 lookup:async(s,m)=>[{...attempt(s,m),provider_message_id:'wamid.WRONG'}]}));
});
test('WA35-12 revision changed before S0 RECHECK is denied',async()=>{
 await expect(await sign(),'LAB_STALE',ports({
 lookup:async(s,m,phase)=>[{
  ...attempt(s,m),binding_revision:phase==='LOOKUP'?5:6}]}));
});
test('WA35-13 swapped case/attempt and claim state at RECHECK are denied',async()=>{
 for(const changed of [{case_ref:'case_OTHER'},
  {attempt_ref:'attempt_OTHER'},{claim_state:'LAB_CLAIMED' as const}]){
  await expect(await sign(),'LAB_STALE',ports({
   lookup:async(s,m,phase)=>[{
    ...attempt(s,m),...(phase==='RECHECK'?changed:{})}]}));
 }
});
test('WA35-14 invalidated claim remains admissible only for forensics',async()=>{
 const result=await expect(await sign(),issued);
 assert.equal(result.ticket?.payload.case_ref,'case31_hist');
 assert.equal(result.send_authorized,false);
});
test('WA35-15 active claim also never grants sending rights',async()=>{
 const result=await expect(await sign(),issued,ports({
 lookup:async(s,m)=>[{...attempt(s,m),claim_state:'LAB_CLAIMED'}]}));
 assert.equal(result.ticket?.payload.purpose,'FORENSIC_APPEND_ONLY');
 assert.equal(result.ack_allowed,false);
});
test('WA35-16 app revoked while S0 resolver works makes handoff stale',async()=>{
 let off=false;
 await expect(await sign(),'LAB_STALE',ports({
 registry:()=>({...registry(),apps:[{...app,active:!off},appB]}),
 lookup:async(s,m,phase)=>{if(phase==='RECHECK')off=true;return [attempt(s,m)]},
 }));
});
test('WA35-17 app channel revision swapped while keys resolve makes stale',async()=>{
 let swapped=false;
 await expect(await sign(),'LAB_STALE',ports({
 registry:()=>({...registry(),apps:[{...app,
   channels:swapped?[{...app.channels[0],canal_id:'OTHER'}]:app.channels},
   appB]}),
 key:async()=>{swapped=true;return KEY},
 }));
});
test('WA35-18 S0 changed after signing secret lookup still rejected',async()=>{
 let changed=false;
 await expect(await sign(),'LAB_STALE',ports({
 key:async()=>{changed=true;return KEY},
 lookup:async(s,m)=>[{...attempt(s,m),binding_revision:changed?6:5}],
 }));
});
test('WA35-19 invalid, missing or repeated nonce is a future S0 gate',async()=>{
 await expect(await sign(),'LAB_INTERNAL_UNAVAILABLE',ports({
 nonce:async()=>'NO SPACE'}));
 const result=await expect(await sign(),issued);
 const another=await expect(await sign(),issued);
 assert.equal(result.ticket?.payload.nonce_ref,another.ticket?.payload.nonce_ref);
});
test('WA35-20 invalid internal signing key yields no ticket',async()=>{
 await expect(await sign(),'LAB_INTERNAL_UNAVAILABLE',ports({
 key:async()=>new Uint8Array(8)}));
});
test('WA35-21 malformed or evil S0 objects are denied',async()=>{
 const d=attempt({app_ref:app.app_ref,concessionaria_id:'shop_A',
 canal_id:'WA35_CHANNEL_A',waba_id:'123456',phone_number_id:'1234567890'},
 'wamid.WA35_A');
 const getter={...d};
 Object.defineProperty(getter,'case_ref',{get(){throw Error('GETTER')}});
 for(const bad of [getter,{...d,extra:'injected'},
  Object.assign(Object.create({role:'director'}),d),
  {...d,binding_revision:0},{...d,claim_state:'APPROVED'}]){
  await expect(await sign(),'LAB_BINDING_DENIED',ports({
   lookup:async()=>[bad as Wa32AttemptLookup]}));
 }
});
test('WA35-22 caller mutation during await cannot change HMAC-hashed body',async()=>{
 const req=await sign();
 const original=Uint8Array.from(req.raw_body);
 let didMutate=false;
 const p=ports({registry:()=>{
  if(!didMutate){didMutate=true;req.raw_body.fill(0)}
  return registry();
 }});
 const out=await expect(req,issued,p);
 assert.ok(out.ticket);
 const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',original));
 assert.equal(out.ticket.payload.meta_body_sha256,
 Array.from(digest,x=>x.toString(16).padStart(2,'0')).join(''));
});
test('WA35-23 same stable provider status gets same event reference',async()=>{
 const one=await expect(await sign(),issued);
 const two=await expect(await sign(),issued);
 assert.equal(one.ticket?.payload.event_ref,two.ticket?.payload.event_ref);
 assert.match(one.ticket!.payload.event_ref,/^EVT_[0-9a-f]{64}$/);
});
test('WA35-24 status kind or provider timestamp changes event reference',async()=>{
 const first=await expect(await sign(),issued);
 const kind=await expect(await sign(body([callback('read')])),issued);
 const time=await expect(await sign(body([callback('delivered','1792320001')])),issued);
 assert.notEqual(first.ticket?.payload.event_ref,kind.ticket?.payload.event_ref);
 assert.notEqual(first.ticket?.payload.event_ref,time.ticket?.payload.event_ref);
});
test('WA35-25 signed packet tamper fails WA34 reader but not its stateless replay',async()=>{
 const out=await expect(await sign(),issued);
 const w=out.ticket!;
 assert.equal((await verifyWa34SyntheticFixture(w,scopeFromTicket(w),TIME,KEY)).decision,
  'LAB_CONTRACT_PENDING');
 assert.equal((await verifyWa34SyntheticFixture({...w,payload:{...w.payload,
  case_ref:'case_OTHER'}},scopeFromTicket(w),TIME,KEY)).decision,'LAB_DENIED');
 assert.equal((await verifyWa34SyntheticFixture(w,scopeFromTicket(w),TIME,KEY)).decision,
  'LAB_CONTRACT_PENDING');
});
test('WA35-26 synthetic local service secret is not Meta App Secret',async()=>{
 const out=await expect(await sign(),issued);
 const w=out.ticket!;
 const invalid=new TextEncoder().encode(APP_SECRET.padEnd(48,'#'));
 assert.equal((await verifyWa34SyntheticFixture(w,scopeFromTicket(w),TIME,
  invalid)).decision,'LAB_DENIED');
});
