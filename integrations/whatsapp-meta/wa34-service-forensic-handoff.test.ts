import test from 'node:test';
import assert from 'node:assert/strict';
import {issueWa34SyntheticFixture as issue,verifyWa34SyntheticFixture as verify,
  type Wa34Scope,type Wa34SignedPacket} from './wa34-service-forensic-handoff.ts';

const NOW=1792320000000,KEY=new Uint8Array(48).fill(0x45);
const DIFFERENT=new Uint8Array(48).fill(0x46);
const scope=():Wa34Scope=>({
 app_ref:'APP_A',concessionaria_id:'shop_A',canal_id:'CHANNEL_A',
 waba_id:'100001',phone_number_id:'1234567890',
 provider_message_id:'wamid.WA34_FAKE',recipient_verified:'5581900000000',
 case_ref:'case31_hist',attempt_ref:'attempt31_hist',
 binding_revision:8,event_ref:'EVENT_01',provider_kind:'delivered',
 meta_body_sha256:'a'.repeat(64),
});
const wire=async()=> {
 const result=await issue(scope(),'NONCE_WA34_01',NOW,60000,KEY);
 assert.ok(result);return result;
};
const assertSafe=(d:Awaited<ReturnType<typeof verify>>)=>{
 assert.equal(Object.isFrozen(d),true);
 assert.deepEqual(Object.keys(d).sort(),[
  'ack_allowed','case_transition_authorized','decision',
  'definitive_failure_count_increment','production_authorized',
  'retry_external','send_authorized',
 ].sort());
 for(const k of ['ack_allowed','send_authorized','retry_external',
   'production_authorized','case_transition_authorized',
   'definitive_failure_count_increment'] as const)
  assert.equal(d[k],false);
 const json=JSON.stringify(d);
 for(const prohibited of ['wamid.','5581900000000','shop_A','APP_A',
     'attempt31_hist','access_token','mac_sha256'])
  assert.ok(!json.includes(prohibited));
};
const check=async(packet:unknown,expected:unknown=scope(),now=NOW,key=KEY,
 decision='LAB_DENIED')=>{
 const d=await verify(packet,expected,now,key);assert.equal(d.decision,decision);
 assertSafe(d);
};
const tamper=async(k:string,v:unknown)=>{
 const good=await wire();
 return {payload:{...good.payload,[k]:v},mac_sha256:good.mac_sha256};
};
test('WA34-01 correct synthetic internal MAC yields contract pending, never permit',async()=>{
 await check(await wire(),scope(),NOW,KEY,'LAB_CONTRACT_PENDING');
});
test('WA34-02 expires strictly at end of lifetime',async()=>{
 const w=await wire();await check(w,scope(),NOW+59999,KEY,'LAB_CONTRACT_PENDING');
 await check(w,scope(),NOW+60000);
});
test('WA34-03 cannot verify before issued time',async()=>{
 await check(await wire(),scope(),NOW-1);
});
test('WA34-04 issued packet cannot request validity longer than 120 seconds',async()=>{
 await check(await tamper('expires_at_ms',NOW+120001));
 assert.equal(await issue(scope(),'X',NOW,120001,KEY),null);
});
test('WA34-05 independent internal service MAC secret is mandatory',async()=>{
 await check(await wire(),scope(),NOW,DIFFERENT);
});
test('WA34-06 digest of Meta raw signed body must match expected internal source',async()=>{
 await check(await wire(),{...scope(),meta_body_sha256:'b'.repeat(64)});
});
test('WA34-07 cannot carry one dealer grant to another dealer',async()=>{
 await check(await wire(),{...scope(),concessionaria_id:'shop_B'});
});
test('WA34-08 cannot transfer evidence across Apps',async()=>{
 await check(await wire(),{...scope(),app_ref:'APP_B'});
});
test('WA34-09 cannot transfer across WABAs',async()=>{
 await check(await wire(),{...scope(),waba_id:'100002'});
});
test('WA34-10 cannot transfer across sender phone numbers',async()=>{
 await check(await wire(),{...scope(),phone_number_id:'1234567891'});
});
test('WA34-11 cannot transfer across channels even in same WABA',async()=>{
 await check(await wire(),{...scope(),canal_id:'CHANNEL_B'});
});
test('WA34-12 cannot infer recipient using phone variant normalization',async()=>{
 await check(await wire(),{...scope(),recipient_verified:'5581990000000'});
});
test('WA34-13 provider message ID must match exactly',async()=>{
 await check(await wire(),{...scope(),provider_message_id:'wamid.DIFFERENT'});
});
test('WA34-14 mismatched case cannot receive status',async()=>{
 await check(await wire(),{...scope(),case_ref:'case31_late'});
});
test('WA34-15 mismatched attempt cannot receive status',async()=>{
 await check(await wire(),{...scope(),attempt_ref:'attempt31_late'});
});
test('WA34-16 stale binding revision is denied',async()=>{
 await check(await wire(),{...scope(),binding_revision:9});
});
test('WA34-17 same provider message with different event ref is not same status',async()=>{
 await check(await wire(),{...scope(),event_ref:'EVENT_02'});
});
test('WA34-18 a failed callback is not interchangeable with delivery',async()=>{
 await check(await wire(),{...scope(),provider_kind:'failed'});
});
test('WA34-19 changing purpose after signing cannot authorize dispatch',async()=>{
 await check(await tamper('purpose','GRAPH_SEND'));
});
test('WA34-20 audience and issuer may not be replaced by an actor/client',async()=>{
 await check(await tamper('audience','HTTP_CLIENT'));
 await check(await tamper('issuer','FAKE_IA'));
});
test('WA34-21 all positive authorization bits fail before MAC verification',async()=>{
 for(const field of ['ack_allowed','send_authorized','retry_external',
   'production_authorized','case_transition_authorized',
   'definitive_failure_count_increment']){
  await check(await tamper(field,true));
 }
});
test('WA34-22 signed packet tamper and malformed MAC are refused',async()=>{
 const w=await wire();
 await check({...w,mac_sha256:'0'.repeat(64)});
 await check({...w,mac_sha256:'sha256='+w.mac_sha256});
 await check({...w,mac_sha256:'xx'});
});
test('WA34-23 packet rejects unknown or missing fields, including fake bearer token',async()=>{
 const w=await wire();
 await check({...w,access_token:'FAKE'});
 await check({payload:w.payload});
 await check({payload:{...w.payload,actor_ref:'MALLORY'},mac_sha256:w.mac_sha256});
 const tampered={...w.payload} as Record<string,unknown>;
 delete tampered.nonce_ref;
 await check({payload:tampered,mac_sha256:w.mac_sha256});
});
test('WA34-24 accessor/proxy/prototype spoofing fails without execution',async()=>{
 const w=await wire();
 const attacker={...w.payload};
 Object.defineProperty(attacker,'case_ref',{get(){throw Error('NEVER_READ')}});
 await check({payload:attacker,mac_sha256:w.mac_sha256});
 const proxy=new Proxy({...w.payload},{ownKeys(){throw Error('PROXY')}});
 await check({payload:proxy,mac_sha256:w.mac_sha256});
 await check({payload:Object.assign(Object.create({injected:true}),w.payload),
   mac_sha256:w.mac_sha256});
});
test('WA34-25 extra hidden symbol property denied',async()=>{
 const w=await wire();
 const payload=Object.assign({...w.payload},{[Symbol('hidden')]:true});
 await check({payload,mac_sha256:w.mac_sha256});
});
test('WA34-26 unauthenticated or malformed synthetic issuer inputs are refused',async()=>{
 assert.equal(await issue({...scope(),secret:'leak'},'NONCE_A',NOW,30000,KEY),null);
 assert.equal(await issue({...scope(),provider_kind:'delivered?'},'NONCE_A',NOW,30000,KEY),null);
 assert.equal(await issue({...scope(),meta_body_sha256:'BAD'},'NONCE_A',NOW,30000,KEY),null);
});
test('WA34-27 nonce must be syntactically safe and cannot be empty',async()=>{
 for(const nonce of ['','N SPACE','../x','x'.repeat(129)])
   assert.equal(await issue(scope(),nonce,NOW,50000,KEY),null);
});
test('WA34-28 forbidden and empty issuer signing keys return unavailable',async()=>{
 assert.equal(await issue(scope(),'NONCE_A',NOW,10000,new Uint8Array(8)),null);
 await check(await wire(),scope(),NOW,new Uint8Array(8),'LAB_UNAVAILABLE');
});
test('WA34-29 frozen issued copy cannot be changed via original object mutation',async()=>{
 const raw=scope();
 const w=await issue(raw,'NONCE_A',NOW,10000,KEY);
 assert.ok(w);
 (raw as {case_ref:string}).case_ref='CASE_OTHER';
 await check(w,scope(),NOW,KEY,'LAB_CONTRACT_PENDING');
});
test('WA34-30 identical replay passes stateless verification: S0 consume must be atomic',async()=>{
 const w=await wire();
 await check(w,scope(),NOW,KEY,'LAB_CONTRACT_PENDING');
 await check(w,scope(),NOW,KEY,'LAB_CONTRACT_PENDING');
 assert.equal('write_authorized' in w.payload,false);
});
