import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,createHmac} from 'node:crypto';
import {inspectWa12PhysicalIngressBarrier as inspect}
 from './wa12-physical-ingress-barrier.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';
import type {TrustedRoutingPorts} from './routed-webhook.ts';

const NOW=1792320000000;
const KEY='WA12_SYNTHETIC_HMAC_A_ONLY';
const appA={
 app_ref:'APP_A',route_ref:'ROUTE_A',concessionaria_id:'SHOP_A',
 active:true,revision:7,valid_from_ms:NOW-10000,valid_until_ms:NOW+10000,
 secret_slots:{get_verify_token:'WA12_GET_A',post_app_secret:'WA12_POST_A',
  graph_access_token:'WA12_GRAPH_A'},
 channels:[
  {canal_id:'CANAL_A1',waba_id:'100001',phone_number_id:'200001',active:true},
  {canal_id:'CANAL_A2',waba_id:'100002',phone_number_id:'200002',active:true},
 ],
};
const appB={
 app_ref:'APP_B',route_ref:'ROUTE_B',concessionaria_id:'SHOP_B',
 active:true,revision:3,valid_from_ms:NOW-10000,valid_until_ms:NOW+10000,
 secret_slots:{get_verify_token:'WA12_GET_B',post_app_secret:'WA12_POST_B',
  graph_access_token:'WA12_GRAPH_B'},
 channels:[
  {canal_id:'CANAL_B1',waba_id:'300001',phone_number_id:'400001',active:true},
 ],
};
const registry:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',
 apps:[appA,appB],
};
const ports=(opts:{registry?:()=>TrustedMetaRegistry;
 resolve?:(name:string)=>string|undefined;calls?:string[]}={}):TrustedRoutingPorts=>({
 currentRegistry:opts.registry??(()=>registry),
 resolveSecret:(name)=>{
  opts.calls?.push(name);
  return opts.resolve?opts.resolve(name):
   name==='WA12_POST_A'?KEY:undefined;
 },
 nowMs:()=>NOW,
});
const msg=(id='wamid.INPUT_A')=>({id,from:'5581900000000',
 type:'text',timestamp:'1792320000',text:{body:'REDACTED'},
});
const entry=(waba='100001',phone='200001',id='wamid.INPUT_A')=>({
 id:waba,changes:[{field:'messages',value:{
  messaging_product:'whatsapp',metadata:{phone_number_id:phone},
  messages:[msg(id)],
 }}],
});
const statusEntry=()=>({id:'100001',changes:[{field:'messages',
 value:{messaging_product:'whatsapp',metadata:{phone_number_id:'200001'},
  statuses:[{id:'wamid.OUT',recipient_id:'5581900000000',
   status:'delivered',timestamp:'1792320000'}]}}]});
const raw=(entries:unknown[]=[entry()])=>Buffer.from(JSON.stringify({
 object:'whatsapp_business_account',entry:entries,
}),'utf8');
const digest=(v:Uint8Array)=>createHash('sha256').update(v).digest('hex');
const signature=(data:Uint8Array,secret=KEY)=>
 'sha256='+createHmac('sha256',secret).update(data).digest('hex');
const envelope=(data=raw())=>({
 method:'POST',route:{route_ref:'ROUTE_A',expected_revision:7},
 raw_query:null,raw_body:data,
 headers:[
  ['Content-Type','application/json'],
  ['X-Hub-Signature-256',signature(data)],
  ['Content-Length',String(data.byteLength)],
 ],
});
const capture=(data=raw())=>({
 contract_version:'wa12-host-physical-capture.lab.v0.1',
 route_ref:'ROUTE_A',route_revision:7,raw_sha256:digest(data),
 expected_event_count:1,batch_ref:'LAB_BATCH_1',
 protected_payload_ref:'LAB_PROTECTED_1',
});
const run=(options:{envelope?:unknown;capture?:unknown;
 ports?:TrustedRoutingPorts}={})=>{
 const rawData=raw();
 return inspect(
  Object.hasOwn(options,'envelope')?options.envelope:envelope(rawData),
  Object.hasOwn(options,'capture')?options.capture:capture(rawData),
  options.ports??ports(),
 );
};
type Result=Awaited<ReturnType<typeof run>>;
function noAuthority(r:Result){
 for(const k of ['ack_allowed','http_ack_allowed','http_response_authorized',
  'persisted','durable_receipt_verified','commit_verified','readback_verified',
  'idempotency_verified','replay_suppression_authorized','recovery_authorized',
  'automatic_retry_authorized','partial_ack_allowed','m2m_verified',
  's0_write_authorized','send_authorized','production_authorized',
  'commercial_transition_authorized'] as const)assert.equal(r[k],false,k);
 for(const name of ['status','body','candidate','receipt','events',
  'channels','token','secret','s0_commit'])assert.equal(name in r,false,name);
 assert.equal(Object.isFrozen(r),true);
}
function deny(r:Result,reason?:Result['reason']){
 noAuthority(r);
 assert.equal(r.decision,'DENIED');
 if(reason)assert.equal(r.reason,reason);
 assert.equal(r.event_count,0);
 assert.equal(r.scope_count,0);
 assert.equal(r.raw_sha256,null);
}
function ok(r:Result,count:number,scopes:number){
 noAuthority(r);
 assert.equal(r.decision,'LAB_PHYSICAL_BATCH_COHERENT_UNCOMMITTED');
 assert.equal(r.reason,null);
 assert.equal(r.event_count,count);
 assert.equal(r.scope_count,scopes);
 assert.match(r.raw_sha256!,/^[a-f0-9]{64}$/);
}
test('WA12-01 one signed POST matches host capture, no S0 effects',async()=>{
 ok(await run(),1,1);
});
test('WA12-02 two channels in same App are one physical POST',async()=>{
 const data=raw([entry(),entry('100002','200002','wamid.TWO')]);
 ok(await run({envelope:envelope(data),capture:{
  ...capture(data),expected_event_count:2,
 }}),2,2);
});
test('WA12-03 mixed status and inbound occurrence remain different',async()=>{
 const data=raw([entry(),statusEntry()]);
 ok(await run({envelope:envelope(data),capture:{
  ...capture(data),expected_event_count:2,
 }}),2,1);
});
test('WA12-04 exact repeat does not claim dedupe or replay suppression',async()=>{
 const v1=await run(),v2=await run();
 ok(v1,1,1);ok(v2,1,1);assert.deepEqual(v1,v2);
});
test('WA12-05 host-captured digest mismatching POST denies before secret lookup',async()=>{
 const calls:string[]=[];
 const c={...capture(),raw_sha256:'0'.repeat(64)};
 deny(await run({capture:c,ports:ports({calls})}),'CAPTURE_MISMATCH');
 assert.deepEqual(calls,[]);
});
test('WA12-06 host route mismatch cannot pass via body routing claims',async()=>{
 const c={...capture(),route_ref:'ROUTE_B'};
 deny(await run({capture:c}),'CAPTURE_MISMATCH');
});
test('WA12-07 host revision mismatch fails before HMAC',async()=>{
 deny(await run({capture:{...capture(),route_revision:6}}),
  'CAPTURE_MISMATCH');
});
test('WA12-08 host event count mismatch cannot bless partial S0 handoff',async()=>{
 deny(await run({capture:{...capture(),expected_event_count:2}}),
  'CAPTURE_MISMATCH');
});
test('WA12-09 tampered signature denies before handoff creation',async()=>{
 const e=envelope();e.headers[1][1]='sha256='+('0'.repeat(64));
 deny(await run({envelope:e}),'ENVELOPE_DENIED');
});
test('WA12-10 HTTP GET is not eligible for durable POST barrier',async()=>{
 deny(await run({envelope:{...envelope(),method:'GET',raw_body:null,
  raw_query:'hub.mode=subscribe'}}),'INVALID_INPUT');
});
test('WA12-11 absent signature denies without S0 call',async()=>{
 const e=envelope();e.headers.splice(1,1);
 deny(await run({envelope:e}),'INVALID_INPUT');
});
test('WA12-12 HMAC header duplicate rejected without collapse',async()=>{
 const e=envelope();e.headers.push(['x-hub-signature-256',signature(e.raw_body)]);
 deny(await run({envelope:e}),'INVALID_INPUT');
});
test('WA12-13 Content-Type duplication rejected by WA11',async()=>{
 const e=envelope();e.headers.push(['content-type','application/json']);
 deny(await run({envelope:e}),'ENVELOPE_DENIED');
});
test('WA12-14 Content-Length mismatch rejected without body conversion',async()=>{
 const e=envelope();e.headers[2][1]='0';
 deny(await run({envelope:e}),'ENVELOPE_DENIED');
});
test('WA12-15 unsigned channel from another tenant denied atomically',async()=>{
 const data=raw([entry(),entry('300001','400001','wamid.OTHER')]);
 deny(await run({envelope:envelope(data),capture:{
  ...capture(data),expected_event_count:2,
 }}),'ENVELOPE_DENIED');
});
test('WA12-16 disabled channel refuses physical POST',async()=>{
 const bad={...registry,apps:[{...appA,channels:[
  {...appA.channels[0],active:false},appA.channels[1]]},appB]};
 deny(await run({ports:ports({registry:()=>bad})}),'ENVELOPE_DENIED');
});
test('WA12-17 missing host capture is invalid, not implicitly trusted',async()=>{
 deny(await run({capture:null}),'INVALID_INPUT');
});
test('WA12-18 extra false authority field in capture refuses',async()=>{
 deny(await run({capture:{...capture(),ack_allowed:true}}),'INVALID_INPUT');
});
test('WA12-19 unratified contract version refuses',async()=>{
 deny(await run({capture:{...capture(),contract_version:'productive'}}),
  'INVALID_INPUT');
});
test('WA12-20 malformed sha digest refuses',async()=>{
 deny(await run({capture:{...capture(),raw_sha256:'not-a-sha'}}),
  'INVALID_INPUT');
});
test('WA12-21 getters on capture are never invoked',async()=>{
 let hits=0;const c=capture();
 Object.defineProperty(c,'batch_ref',{configurable:true,enumerable:true,
  get(){hits++;throw Error('GETTER_EXECUTED');}});
 deny(await run({capture:c}),'INVALID_INPUT');
 assert.equal(hits,0);
});
test('WA12-22 getters on envelope array are never invoked',async()=>{
 let hits=0;const e=envelope();const pair=e.headers[0];
 Object.defineProperty(e.headers,'0',{configurable:true,enumerable:true,
  get(){hits++;return pair;}});
 deny(await run({envelope:e}),'INVALID_INPUT');
 assert.equal(hits,0);
});
test('WA12-23 sparse header list fails closed',async()=>{
 const e=envelope();e.headers.length=4;
 deny(await run({envelope:e}),'INVALID_INPUT');
});
test('WA12-24 caller mutating bytes after invocation cannot change digest',async()=>{
 const data=raw(),e=envelope(data),c=capture(data);
 const process=inspect(e,c,ports());
 data.fill(0);
 const r=await process;
 ok(r,1,1);assert.equal(r.raw_sha256,c.raw_sha256);
});
test('WA12-25 caller mutating signature after invocation cannot substitute HMAC',async()=>{
 const e=envelope(),c=capture(e.raw_body);
 const process=inspect(e,c,ports());
 e.headers[1][1]='sha256='+('0'.repeat(64));
 ok(await process,1,1);
});
test('WA12-26 revocation during first routed HMAC rejects',async()=>{
 let revoked=false;
 const p=ports({
  registry:()=>({...registry,apps:[{...appA,active:!revoked},appB]}),
  resolve:(name)=>{revoked=true;return name==='WA12_POST_A'?KEY:undefined;},
 });
 deny(await run({ports:p}),'ENVELOPE_DENIED');
});
test('WA12-27 revocation between WA11 and S0 candidate refuses',async()=>{
 let registryCalls=0;
 const p=ports({registry:()=>({
  ...registry,apps:[{...appA,active:++registryCalls<=4},appB],
 })});
 const r=await run({ports:p});
 noAuthority(r);assert.equal(r.decision,'DENIED');
 assert.ok(['HANDOFF_DENIED','ENVELOPE_DENIED'].includes(r.reason!));
});
test('WA12-28 revocation between candidate and final read refuses',async()=>{
 let registryCalls=0;
 const p=ports({registry:()=>({
  ...registry,apps:[{...appA,active:++registryCalls<=8},appB],
 })});
 const r=await run({ports:p});
 noAuthority(r);assert.equal(r.decision,'DENIED');
 assert.ok(['FINAL_SCOPE_DENIED','HANDOFF_DENIED'].includes(r.reason!));
});
test('WA12-29 malicious secret provider errors never leak',async()=>{
 const p=ports({resolve:()=>{throw Error('PRIVATE_VAULT_KEY_BYTES');}});
 const result=await run({ports:p});
 deny(result,'ENVELOPE_DENIED');
 assert.equal(JSON.stringify(result).includes('PRIVATE_VAULT_KEY_BYTES'),false);
});
test('WA12-30 invalid S0 batch reference denied',async()=>{
 deny(await run({capture:{...capture(),batch_ref:'bad batch'}}),
  'INVALID_INPUT');
});
test('WA12-31 invalid synthetic protection ref denied',async()=>{
 deny(await run({capture:{...capture(),protected_payload_ref:''}}),
  'INVALID_INPUT');
});
test('WA12-32 empty POST refuses even when digest matches empty buffer',async()=>{
 const data=new Uint8Array(0);
 deny(await run({envelope:envelope(data),capture:capture(data)}),
  'INVALID_INPUT');
});
test('WA12-33 signed POST can never declare itself S0 COMMITTED',async()=>{
 const e={...envelope(),commit_state:'COMMITTED',ack_allowed:true};
 deny(await run({envelope:e}),'INVALID_INPUT');
});
test('WA12-34 blocked credential alias from M09/M11 still applies',async()=>{
 const bad={...registry,apps:[{...appA,secret_slots:{
  ...appA.secret_slots,post_app_secret:appA.secret_slots.get_verify_token}},appB]};
 deny(await run({ports:ports({registry:()=>bad})}),'ENVELOPE_DENIED');
});
test('WA12-35 no assumptions about real durability, identity, or production',async()=>{
 const r=await run();ok(r,1,1);
 const serialized=JSON.stringify(r);
 for(const x of ['wamid.INPUT_A','5581900000000','LAB_BATCH_1',
  'LAB_PROTECTED_1','PRIVATE_VAULT','SECRET']){
  assert.equal(serialized.includes(x),false,x);
 }
});
