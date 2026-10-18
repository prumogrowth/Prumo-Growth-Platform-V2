import { test } from 'node:test';
import assert from 'node:assert/strict';
import { FakeVersionedMetaRegistry } from './lifecycle-simulation.ts';
import { selectMetaCredential, type TrustedMetaRegistry } from './credential-routing.ts';
import { inspectRoutedMetaPost, type TrustedRoutingPorts } from './routed-webhook.ts';
const at=1792320000000;
const app={app_ref:'APP_A',route_ref:'ROUTE_A',concessionaria_id:'STORE_A',active:true,
  revision:1,valid_from_ms:at-10000,valid_until_ms:at+10000,
  secret_slots:{get_verify_token:'APP_A_GET',post_app_secret:'APP_A_POST',graph_access_token:'APP_A_GRAPH'},
  channels:[{canal_id:'CH_A',waba_id:'WABA_A',phone_number_id:'1234567890',active:true}]};
const appB={...app,app_ref:'APP_B',route_ref:'ROUTE_B',concessionaria_id:'STORE_B',
  secret_slots:{get_verify_token:'APP_B_GET',post_app_secret:'APP_B_POST',graph_access_token:'APP_B_GRAPH'},
  channels:[{canal_id:'CH_B',waba_id:'WABA_B',phone_number_id:'9999999990',active:true}]};
const source:TrustedMetaRegistry={contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[app,appB]};
const req={app_ref:'APP_A',concessionaria_id:'STORE_A',at_ms:at,expected_revision:1,operation_ref:'OP_A'};
const body=new TextEncoder().encode(JSON.stringify({object:'whatsapp_business_account',entry:[{
  id:'WABA_A',changes:[{field:'messages',value:{metadata:{phone_number_id:'1234567890'},
    messages:[{id:'wamid.IN',from:'5581900000000',timestamp:'1792320000',type:'text'}]}}],
}]}));
const key='SYNTHETIC_HMAC_A';
const sign=async()=>{
 const k=await crypto.subtle.importKey('raw',new TextEncoder().encode(key),{name:'HMAC',hash:'SHA-256'},false,['sign']);
 const digest=new Uint8Array(await crypto.subtle.sign('HMAC',k,body));
 return 'sha256='+Array.from(digest,x=>x.toString(16).padStart(2,'0')).join('');
};
const post=async (store:FakeVersionedMetaRegistry, p?:Partial<TrustedRoutingPorts>)=>inspectRoutedMetaPost({
 route:{route_ref:'ROUTE_A',expected_revision:1},raw_body:body,signature_header:await sign(),
},{currentRegistry:()=>store.snapshot(),resolveSecret:()=>key,nowMs:()=>at,...p});

test('LIFE-D-01: versioned fake store applies a revocation to an isolated copy',()=>{
 const s=new FakeVersionedMetaRegistry(source);
 const r=s.proposeAndSwap({...req,action:'REVOKE_APP'});
 assert.equal(r.decision,'APPLIED_SIMULATED');
 assert.equal(s.snapshot().apps[0].active,false);assert.equal(source.apps[0].active,true);
 assert.equal(s.snapshot().apps[1].active,true);
 assert.equal(r.production_authorized,false);
});
test('LIFE-D-02: same operation ref + payload returns idempotent simulated replay',()=>{
 const s=new FakeVersionedMetaRegistry(source), x={...req,action:'REVOKE_APP' as const};
 assert.equal(s.proposeAndSwap(x).decision,'APPLIED_SIMULATED');
 assert.equal(s.proposeAndSwap(x).decision,'REPLAYED_SIMULATED');
 assert.equal(s.appliedOperations,1);
});
test('LIFE-D-03: same operation ID with different request is a conflict',()=>{
 const s=new FakeVersionedMetaRegistry(source);
 s.proposeAndSwap({...req,action:'REVOKE_CHANNEL',canal_id:'CH_A'});
 assert.equal(s.proposeAndSwap({...req,action:'REVOKE_APP'}).decision,'OPERATION_CONFLICT');
 assert.equal(s.snapshot().apps[0].active,true);
});
test('LIFE-D-04: two stale proposals cannot overwrite each other',()=>{
 const s=new FakeVersionedMetaRegistry(source);
 assert.equal(s.proposeAndSwap({...req,action:'REVOKE_CHANNEL',canal_id:'CH_A'}).decision,'APPLIED_SIMULATED');
 assert.equal(s.proposeAndSwap({...req,action:'REVOKE_APP',operation_ref:'OP_B'}).decision,'DENIED');
 assert.equal(s.snapshot().apps[0].revision,2);
});
test('LIFE-D-05: independent shop B is unchanged by shop A revocation',()=>{
 const s=new FakeVersionedMetaRegistry(source);s.proposeAndSwap({...req,action:'REVOKE_APP'});
 assert.deepEqual(s.snapshot().apps[1],source.apps[1]);
});
test('LIFE-D-06: forged shop cannot apply a lifecycle transition',()=>{
 const s=new FakeVersionedMetaRegistry(source);
 assert.equal(s.proposeAndSwap({...req,concessionaria_id:'STORE_B',action:'REVOKE_APP'}).decision,'DENIED');
 assert.equal(s.appliedOperations,0);
});
test('LIFE-D-07: staged rotation remains OFF while third-party token verification is pending',()=>{
 const s=new FakeVersionedMetaRegistry(source);
 const r=s.proposeAndSwap({...req,action:'STAGE_ROTATION',next_secret_slots:{
  get_verify_token:'NEW_A_GET',post_app_secret:'NEW_A_POST',graph_access_token:'NEW_A_GRAPH'}});
 assert.equal(r.decision,'APPLIED_SIMULATED');
 assert.equal(s.snapshot().apps[0].active,false);
 assert.equal(selectMetaCredential(s.snapshot(),{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',at_ms:at,expected_revision:2}).ok,false);
});
test('LIFE-D-08: no returned token, channel, or secret slot in mutation receipt',()=>{
 const s=new FakeVersionedMetaRegistry(source);
 const r=s.proposeAndSwap({...req,action:'REVOKE_APP'});
 assert.equal('candidate_registry' in r,false);
 assert.equal(JSON.stringify(r).includes('APP_A_POST'),false);
 assert.equal(JSON.stringify(r).includes('STORE_A'),false);
});
test('LIFE-D-09: old caller-held snapshot cannot mutate actual fake registry',()=>{
 const s=new FakeVersionedMetaRegistry(source), stale=s.snapshot();
 (stale as unknown as {apps:{channels:{active:boolean}[]}[]}).apps[0].channels[0].active=false;
 assert.equal(s.snapshot().apps[0].channels[0].active,true);
});
test('LIFE-D-10: Graph slot for revoked App cannot be selected',()=>{
 const s=new FakeVersionedMetaRegistry(source);s.proposeAndSwap({...req,action:'REVOKE_APP'});
 const r=selectMetaCredential(s.snapshot(),{purpose:'GRAPH_ACCESS_TOKEN',trusted_scope:{
  app_ref:'APP_A',concessionaria_id:'STORE_A',canal_id:'CH_A',waba_id:'WABA_A',phone_number_id:'1234567890'},
  at_ms:at,expected_revision:2});assert.equal(r.ok,false);
});
test('LIFE-D-11: POST blocked after fake registry has revoked App',async()=>{
 const s=new FakeVersionedMetaRegistry(source);
 assert.equal((await post(s)).ok,true);
 s.proposeAndSwap({...req,action:'REVOKE_APP'});
 assert.equal((await post(s)).ok,false);
});
test('LIFE-D-12: POST blocked after fake channel-only revocation',async()=>{
 const s=new FakeVersionedMetaRegistry(source);
 s.proposeAndSwap({...req,action:'REVOKE_CHANNEL',canal_id:'CH_A'});
 assert.equal((await post(s)).ok,false);
});
test('LIFE-D-13: concurrent revocation during secret lookup fails closed',async()=>{
 const s=new FakeVersionedMetaRegistry(source);
 const r=await post(s,{resolveSecret:()=>{
  s.proposeAndSwap({...req,action:'REVOKE_APP'});return key;
 }});
 assert.equal(r.ok,false);if(!r.ok)assert.equal(r.reason,'ROUTING_CHANGED');
});
test('LIFE-D-14: malformed operation ref is denied with no mutations',()=>{
 const s=new FakeVersionedMetaRegistry(source);
 assert.equal(s.proposeAndSwap({...req,action:'REVOKE_APP',operation_ref:'../not-safe'}).decision,'DENIED');
 assert.equal(s.appliedOperations,0);
});
test('LIFE-D-15: revocation during final channel check cannot release signed batch',async()=>{
 const store=new FakeVersionedMetaRegistry(source);
 let clockCalls=0;
 const r=await post(store,{nowMs:()=>{
  clockCalls++;
  if(clockCalls===4) store.proposeAndSwap({...req,action:'REVOKE_APP'});
  return at;
 }});
 assert.equal(store.snapshot().apps[0].active,false);
 assert.equal(r.ok,false,'stale registry snapshot must not release an App just revoked');
});
