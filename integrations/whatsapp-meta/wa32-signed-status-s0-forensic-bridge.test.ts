import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectWa32SignedStatusForensicFixture as inspect,
 type Wa32AttemptLookup,type Wa32S0FixturePort} from './wa32-signed-status-s0-forensic-bridge.ts';
import type {TrustedRoutingPorts} from './routed-webhook.ts';
import type {TrustedMetaRegistry,TrustedMetaScope} from './credential-routing.ts';

const CLOCK=1792320000000;
const SECRET='WA32_FAKE_LOCAL_ONLY_SECRET';
const route={route_ref:'WA32_ROUTE',expected_revision:9};
const app={
 app_ref:'WA32_APP',route_ref:route.route_ref,concessionaria_id:'SHOP_A',
 revision:9,active:true,valid_from_ms:CLOCK-1000,valid_until_ms:CLOCK+1000,
 secret_slots:{get_verify_token:'WA32_SLOT_GET',
 post_app_secret:'WA32_SLOT_POST',graph_access_token:'WA32_SLOT_GRAPH'},
 channels:[
  {canal_id:'CHANNEL_A',waba_id:'101010',phone_number_id:'1234567890',active:true},
  {canal_id:'CHANNEL_A2',waba_id:'202020',phone_number_id:'1234567891',active:true},
 ],
};
const appB={
 ...app,app_ref:'WA32_APP_B',route_ref:'WA32_ROUTE_B',
 concessionaria_id:'SHOP_B',revision:12,
 secret_slots:{get_verify_token:'WA32_B_GET',post_app_secret:'WA32_B_POST',
 graph_access_token:'WA32_B_GRAPH'},
 channels:[{canal_id:'CHANNEL_B',waba_id:'303030',phone_number_id:'9876543210',active:true}],
};
const reg:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[app,appB],
};
const scope:TrustedMetaScope={
 app_ref:app.app_ref,concessionaria_id:app.concessionaria_id,
 canal_id:'CHANNEL_A',waba_id:'101010',phone_number_id:'1234567890',
};
const reference=(s:TrustedMetaScope=scope,
  message='wamid.WA32_1',recipient='5581900000000'):Wa32AttemptLookup=>({
 ...s,provider_message_id:message,recipient_verified:recipient,
 case_ref:'CASE_A',attempt_ref:'ATTEMPT_A',binding_revision:2,
 claim_state:'LAB_CLAIMED',
});
function routing(options:{registry?:()=>TrustedMetaRegistry,
 secret?:()=>string|undefined,now?:()=>number}={}):TrustedRoutingPorts{
 return {
  currentRegistry:async()=>options.registry?options.registry():reg,
  resolveSecret:async()=>options.secret?options.secret():SECRET,
  nowMs:options.now??(()=>CLOCK),
 };
}
function s0(options:{lookup?:(s:Readonly<TrustedMetaScope>,m:string,
 phase:'LOOKUP'|'RECHECK')=>Promise<readonly Wa32AttemptLookup[]>}={}):
 Wa32S0FixturePort{
 return {lookupExactAttempt:options.lookup??(async(s,m)=>[reference(s,m)])};
}
function status(message='wamid.WA32_1',recipient='5581900000000',
 kind='delivered'){
 return {id:message,recipient_id:recipient,status:kind,timestamp:'1792320000'};
}
function entry(waba='101010',phone='1234567890',
 list:unknown[]=[status()]){
 return {id:waba,changes:[{field:'messages',
  value:{metadata:{phone_number_id:phone},statuses:list}}]};
}
async function signed(entries:unknown[]=[entry()],secret=SECRET){
 const raw_body=new TextEncoder().encode(JSON.stringify({
   object:'whatsapp_business_account',entry:entries,
 }));
 const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),
  {name:'HMAC',hash:'SHA-256'},false,['sign']);
 const bytes=new Uint8Array(await crypto.subtle.sign('HMAC',key,raw_body));
 return {route,raw_body,
  signature_header:'sha256='+Array.from(bytes,x=>x.toString(16).padStart(2,'0')).join('')};
}
const safe=(r:Awaited<ReturnType<typeof inspect>>)=>{
 for(const k of ['ack_allowed','retry_external','send_authorized',
  'production_authorized','delivery_confirmed','definitive_failure_count_increment',
  'case_transition_authorized'] as const)assert.equal(r[k],false);
 assert.equal(Object.keys(r).length,10);
 assert.equal(Object.isFrozen(r),true);
 const json=JSON.stringify(r);
 for(const x of ['wamid.','SHOP_A','CHANNEL_A','5581900000000','CASE_A',
  'ATTEMPT_A','raw_body','access_token'])assert.equal(json.includes(x),false);
};
const expectDecision=async(req:Awaited<ReturnType<typeof signed>>,
 desired:string,p:Wa32S0FixturePort=s0(),ports=routing())=>{
 const result=await inspect(req,ports,p);
 assert.equal(result.decision,desired);safe(result);return result;
};

test('WA32-01 correct signed POST and exact scoped S0 attempt returns ONLY counters',async()=>{
 let phases:string[]=[];
 const p=s0({lookup:async(s,m,phase)=>{phases.push(phase);return [reference(s,m)]}});
 const r=await expectDecision(await signed(),'LAB_FORENSIC_SCOPED',p);
 assert.equal(r.scoped_event_count,1);assert.equal(r.invalidated_attempts,0);
 assert.deepEqual(phases,['LOOKUP','RECHECK']);
});
test('WA32-02 previously revoked attempt is retainable for forensic scope only',async()=>{
 const p=s0({lookup:async(s,m)=>[{...reference(s,m),claim_state:'LAB_INVALIDATED'}]});
 const r=await expectDecision(await signed(),'LAB_FORENSIC_SCOPED',p);
 assert.equal(r.invalidated_attempts,1);
});
test('WA32-03 wrong HMAC is refused before S0 lookup',async()=>{
 let calls=0;const p=s0({lookup:async()=>{calls++;return []}});
 await expectDecision(await signed(undefined,'WRONG_FAKE_KEY'),'LAB_ROUTING_DENIED',p);
 assert.equal(calls,0);
});
test('WA32-04 missing HMAC is refused before lookup',async()=>{
 let calls=0;const req={...await signed(),signature_header:null};
 const p=s0({lookup:async()=>{calls++;return []}});
 await expectDecision(req,'LAB_ROUTING_DENIED',p);assert.equal(calls,0);
});
test('WA32-05 signed App A batch cannot smuggle Shop B WABA',async()=>{
 let calls=0;const p=s0({lookup:async()=>{calls++;return []}});
 await expectDecision(await signed([entry(),entry('303030','9876543210')]),
  'LAB_ROUTING_DENIED',p);
 assert.equal(calls,0);
});
test('WA32-06 inbound messages in otherwise-valid signed POST are NOT status receipts',async()=>{
 const incoming={id:'wamid.INBOUND',from:'5581900000000',
  timestamp:'1792320000',type:'text'};
 const e={id:'101010',changes:[{field:'messages',value:{
   metadata:{phone_number_id:'1234567890'},messages:[incoming]}}]};
 let calls=0;const p=s0({lookup:async()=>{calls++;return []}});
 await expectDecision(await signed([e]),'LAB_UNSUPPORTED_BATCH',p);
 assert.equal(calls,0);
});
test('WA32-07 mixed signed status/inbound batch denies all, not partial',async()=>{
 const incoming={id:'wamid.INBOUND',from:'5581900000000',
  timestamp:'1792320000',type:'text'};
 const e={id:'101010',changes:[{field:'messages',value:{
   metadata:{phone_number_id:'1234567890'},messages:[incoming]}}]};
 await expectDecision(await signed([entry(),e]),'LAB_UNSUPPORTED_BATCH');
});
test('WA32-08 absent S0 binding cannot be inferred from wamid alone',async()=>{
 await expectDecision(await signed(),'LAB_S0_BINDING_DENIED',
  s0({lookup:async()=>[]}));
});
test('WA32-09 duplicate S0 binding is ambiguous and denied',async()=>{
 await expectDecision(await signed(),'LAB_S0_BINDING_DENIED',
  s0({lookup:async(s,m)=>[reference(s,m),reference(s,m)]}));
});
test('WA32-10 wrong shop, channel, App, WABA or sender cannot match',async()=>{
 for(const field of ['concessionaria_id','canal_id','app_ref','waba_id','phone_number_id'] as const){
  const p=s0({lookup:async(s,m)=>[{...reference(s,m),[field]:'OTHER'}]});
  await expectDecision(await signed(),'LAB_S0_BINDING_DENIED',p);
 }
});
test('WA32-11 recipient is exact, never 8/9-digit-normalized or guessed',async()=>{
 for(const other of ['5581990000000','5581900000001','+5581900000000']){
  const p=s0({lookup:async(s,m)=>[{...reference(s,m),recipient_verified:other}]});
  await expectDecision(await signed(),'LAB_S0_BINDING_DENIED',p);
 }
});
test('WA32-12 provider wamid cannot cross attempts under same App/channel',async()=>{
 const p=s0({lookup:async(s,m)=>[{...reference(s,m),provider_message_id:'wamid.FORGED'}]});
 await expectDecision(await signed(),'LAB_S0_BINDING_DENIED',p);
});
test('WA32-13 S0 binding change between two distinct reads prevents handoff',async()=>{
 const p=s0({lookup:async(s,m,phase)=>[{
   ...reference(s,m),binding_revision:phase==='LOOKUP'?2:3,
 }]});
 await expectDecision(await signed(),'LAB_STALE_OR_CHANGED',p);
});
test('WA32-14 switching case, attempt or state during verification is stale',async()=>{
 for(const change of [{case_ref:'CASE_B'},{attempt_ref:'ATTEMPT_B'},
  {claim_state:'LAB_INVALIDATED' as const}]){
  const p=s0({lookup:async(s,m,phase)=>[{
   ...reference(s,m),...(phase==='RECHECK'?change:{}),
  }]});
  await expectDecision(await signed(),'LAB_STALE_OR_CHANGED',p);
 }
});
test('WA32-15 S0 recheck missing, ambiguous or malformed refuses',async()=>{
 for(const bad of [[],[null],[reference(scope),reference(scope)]]){
  const p=s0({lookup:async(s,m,phase)=>
   phase==='LOOKUP'?[reference(s,m)]:bad as readonly Wa32AttemptLookup[]});
  await expectDecision(await signed(),'LAB_STALE_OR_CHANGED',p);
 }
});
test('WA32-16 S0 port error is UNAVAILABLE not a forged absence',async()=>{
 const p=s0({lookup:async()=>{throw Error('test port unreachable')}});
 await expectDecision(await signed(),'LAB_PORT_UNAVAILABLE',p);
});
test('WA32-17 HMAC route revision revoked during privileged lookup denies',async()=>{
 let disabled=false;
 const port=routing({registry:()=>({...reg,
   apps:[{...app,active:!disabled},appB]})});
 const p=s0({lookup:async(s,m,phase)=>{
   if(phase==='RECHECK')disabled=true;return [reference(s,m)];
 }});
 await expectDecision(await signed(),'LAB_STALE_OR_CHANGED',p,port);
});
test('WA32-18 HMAC registry channel changes after lookup deny same revision',async()=>{
 let swapped=false;
 const port=routing({registry:()=>({...reg,apps:[{
  ...app,channels:swapped?
    [{...app.channels[0],canal_id:'CHANGED'},app.channels[1]]:app.channels,
 },appB]})});
 const p=s0({lookup:async(s,m,phase)=>{
  if(phase==='RECHECK')swapped=true;return [reference(s,m)];
 }});
 await expectDecision(await signed(),'LAB_STALE_OR_CHANGED',p,port);
});
test('WA32-19 multiple statuses on same case remain classified as observations only',async()=>{
 const r=await expectDecision(await signed([entry(undefined,undefined,
   [status('wamid.WA32_1'),status('wamid.WA32_1','5581900000000','read')])]),
   'LAB_FORENSIC_SCOPED');
 assert.equal(r.scoped_event_count,2);assert.equal(r.invalidated_attempts,0);
});
test('WA32-20 different valid channels within same signed App can be bound separately',async()=>{
 const p=s0({lookup:async(s,m)=>[reference(s,m)]});
 const r=await expectDecision(await signed([
  entry(),entry('202020','1234567891',[status('wamid.WA32_2')]),
 ]),'LAB_FORENSIC_SCOPED',p);
 assert.equal(r.scoped_event_count,2);
});
test('WA32-21 signed batch with unknown status is rejected, never counted as failure',async()=>{
 await expectDecision(await signed([entry(undefined,undefined,
 [status('wamid.WA32_1','5581900000000','unknown')])]),'LAB_UNSUPPORTED_BATCH');
});
test('WA32-22 invalid or hostile S0 record shape denied and causes no partial result',async()=>{
 const bad={...reference(scope)};
 Object.defineProperty(bad,'case_ref',{get(){throw Error('getter')}});
 for(const entry of [bad,{...reference(scope),access_token:'fake'},
  Object.assign(Object.create({injected:true}),reference(scope)),
  {...reference(scope),binding_revision:0},
  {...reference(scope),case_ref:'../unsafe'},
  {...reference(scope),claim_state:'UNKNOWN'},
 ])await expectDecision(await signed(),'LAB_S0_BINDING_DENIED',
 s0({lookup:async()=>[entry as Wa32AttemptLookup]}));
});
test('WA32-23 absent S0 injected port refuses even correctly verified HMAC',async()=>{
 const r=await inspect(await signed(),routing(),{} as Wa32S0FixturePort);
 assert.equal(r.decision,'LAB_PORT_UNAVAILABLE');safe(r);
});
test('WA32-24 S0 forged positive authorization fields are prohibited',async()=>{
 const p=s0({lookup:async(s,m)=>[{
  ...reference(s,m),send_authorized:true,
 } as Wa32AttemptLookup]});
 await expectDecision(await signed(),'LAB_S0_BINDING_DENIED',p);
});
