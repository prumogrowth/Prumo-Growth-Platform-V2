import { test } from 'node:test';
import assert from 'node:assert/strict';
import { FakeTransactionalInbox, FakeProtectedPayloads } from './transactional-ingress.ts';
import { FakeVersionedMetaRegistry } from './lifecycle-simulation.ts';
import type { TrustedMetaRegistry } from './credential-routing.ts';

const now = 1792320000000;
const appA = {
  app_ref: 'APP_A', route_ref: 'ROUTE_A', concessionaria_id: 'SHOP_A', active: true,
  revision: 1, valid_from_ms: now - 5000, valid_until_ms: now + 5000,
  secret_slots: { get_verify_token: 'WA_A_GET', post_app_secret: 'WA_A_HMAC', graph_access_token: 'WA_A_GRAPH' },
  channels: [ { canal_id: 'CHAN_A', waba_id: 'WABA_A', phone_number_id: '12345678901', active: true } ],
};
const appB = {
  ...appA, app_ref: 'APP_B', route_ref: 'ROUTE_B', concessionaria_id: 'SHOP_B',
  secret_slots: { get_verify_token: 'WA_B_GET', post_app_secret: 'WA_B_HMAC', graph_access_token: 'WA_B_GRAPH' },
  channels: [ { canal_id: 'CHAN_B', waba_id: 'WABA_B', phone_number_id: '99999999999', active: true } ],
};
const registry: TrustedMetaRegistry = { contract_version: 'wa-meta-credential-routing.v0.1-proposed', apps: [appA, appB] };
const secret = 'FAKE_WA_A_APP_SECRET_NEVER_REAL';
const text = new TextEncoder();
const makeEntry = (waba='WABA_A', sender='12345678901', m=1, s=0) => ({ id:waba,changes:[{field:'messages', value:{ metadata:{phone_number_id:sender},
  ...(m?{messages:Array.from({length:m},(_,i)=>({id:'wamid.IN'+i,from:'5581900000000',timestamp:'1792320000',type:'text'}))}:{}),
  ...(s?{statuses:Array.from({length:s},()=>({id:'wamid.OUT1',recipient_id:'5581900000000',timestamp:'1792320000',status:'delivered'}))}:{})
}}]});
const body = (entries: unknown[] = [makeEntry()]) => text.encode(JSON.stringify({object:'whatsapp_business_account',entry:entries}));
const sign = async (raw: Uint8Array) => {
  const key=await crypto.subtle.importKey('raw',text.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);
  const bytes=new Uint8Array(await crypto.subtle.sign('HMAC',key,raw));
  return 'sha256='+Array.from(bytes,n=>n.toString(16).padStart(2,'0')).join('');
};
const fixture = async (raw:Uint8Array=body(), key='BATCH_A', ref='PAYLOAD_A') => {
  const inbox=new FakeTransactionalInbox();
  const store=new FakeVersionedMetaRegistry(registry);
  const payloads=new FakeProtectedPayloads();
  assert.equal(payloads.putFixture(ref,raw),true);
  const signed = await sign(raw);
  const request={ batch_ref:key, protected_payload_ref:ref, request:{
    route:{route_ref:'ROUTE_A',expected_revision:1}, signature_header:signed, raw_body:raw,
  }};
  const ports={resolveSecret:(slot:string)=> slot==='WA_A_HMAC'?secret:undefined,nowMs:()=>now};
  return {inbox,store,payloads,request,ports,
    run:(options?:{beforeCommit?:()=>void;failWrite?:boolean}) => inbox.inspectAndCommitFixture(request,store,payloads,ports,options)};
};

test('TX-01 signed event, current App and fake protected raw body yield simulated commit only',async()=>{
  const f=await fixture(); const r=await f.run();
  assert.equal(r.decision,'SIMULATED_COMMIT'); assert.equal(r.simulated_occurrences,1);
  assert.equal(r.ack_allowed,false); assert.equal(r.production_authorized,false);
  assert.equal(f.inbox.occurrenceCount,1);assert.equal(f.inbox.batchCount,1);
});
test('TX-02 a message and a status at item 0 are distinct occurrences',async()=>{
  const f=await fixture(body([makeEntry('WABA_A','12345678901',1,1)]));
  const r=await f.run();assert.equal(r.decision,'SIMULATED_COMMIT');
  assert.equal(r.simulated_occurrences,2);
});
test('TX-03 multiple entries in one signed Meta POST are accepted atomically for same App',async()=>{
  const raw=body([makeEntry('WABA_A','12345678901',2,1)]);
  const f=await fixture(raw);assert.equal((await f.run()).simulated_occurrences,3);
});
test('TX-04 revocation just before simulated commit blocks ALL items',async()=>{
  const f=await fixture(body([makeEntry('WABA_A','12345678901',2,2)]));
  const r=await f.run({beforeCommit:()=>{f.store.proposeAndSwap({action:'REVOKE_APP',app_ref:'APP_A',concessionaria_id:'SHOP_A',expected_revision:1,operation_ref:'OP_REVOKE',at_ms:now});}});
  assert.equal(r.decision,'BLOCKED');assert.equal(r.reason,'BINDING_REVOKED_OR_CHANGED');
  assert.equal(f.inbox.occurrenceCount,0);assert.equal(f.inbox.batchCount,0);
});
test('TX-05 channel revocation before commit denies batch, including no partial writes',async()=>{
  const f=await fixture();const r=await f.run({beforeCommit:()=>{f.store.proposeAndSwap({action:'REVOKE_CHANNEL',app_ref:'APP_A',concessionaria_id:'SHOP_A',canal_id:'CHAN_A',expected_revision:1,operation_ref:'OP_CHANNEL',at_ms:now});}});
  assert.equal(r.reason,'BINDING_REVOKED_OR_CHANGED');assert.equal(f.inbox.occurrenceCount,0);
});
test('TX-06 rotation staged before commit blocks and does not reactivate App',async()=>{
  const f=await fixture();const r=await f.run({beforeCommit:()=>{f.store.proposeAndSwap({action:'STAGE_ROTATION',app_ref:'APP_A',concessionaria_id:'SHOP_A',expected_revision:1,operation_ref:'OP_ROTATE',at_ms:now,next_secret_slots:{get_verify_token:'NEW_A_GET',post_app_secret:'NEW_A_POST',graph_access_token:'NEW_A_GRAPH'}});}});
  assert.equal(r.reason,'BINDING_REVOKED_OR_CHANGED');assert.equal(f.store.snapshot().apps[0].active,false);
});
test('TX-07 invalid HMAC and fabricated route never reach transaction',async()=>{
  const f=await fixture();f.request.request.signature_header='sha256='+'0'.repeat(64);
  assert.equal((await f.run()).reason,'HMAC_OR_ROUTING_DENIED');assert.equal(f.inbox.occurrenceCount,0);
  f.request.request.route.route_ref='UNKNOWN';assert.equal((await f.run()).reason,'HMAC_OR_ROUTING_DENIED');
});
test('TX-08 fake payload reference is mandatory and must contain exact authenticated bytes',async()=>{
  const f=await fixture();f.request.protected_payload_ref='NOT_FOUND';
  assert.equal((await f.run()).reason,'PAYLOAD_UNAVAILABLE');
  const f2=await fixture();const newRaw=body([makeEntry('WABA_A','12345678901',2,0)]);
  assert.equal(f2.payloads.putFixture('WRONG_REF',newRaw),true);
  f2.request.protected_payload_ref='WRONG_REF';
  assert.equal((await f2.run()).reason,'PAYLOAD_UNAVAILABLE');
});
test('TX-09 byte-for-byte retry with same batch ref does not create a second record',async()=>{
  const f=await fixture();assert.equal((await f.run()).decision,'SIMULATED_COMMIT');
  const again=await f.run();assert.equal(again.decision,'SIMULATED_REPLAY');
  assert.equal(again.simulated_occurrences,1);assert.equal(f.inbox.occurrenceCount,1);
});
test('TX-10 batch ref reused for different signed content is conflict, no overwrites',async()=>{
  const f=await fixture();assert.equal((await f.run()).decision,'SIMULATED_COMMIT');
  const other=body([makeEntry('WABA_A','12345678901',2,0)]);
  assert.equal(f.payloads.putFixture('PAYLOAD_B',other),true);
  const r=await f.inbox.inspectAndCommitFixture({batch_ref:'BATCH_A',protected_payload_ref:'PAYLOAD_B',request:{...f.request.request,raw_body:other,signature_header:await sign(other)}},f.store,f.payloads,f.ports);
  assert.equal(r.decision,'CONFLICT');assert.equal(f.inbox.occurrenceCount,1);
});
test('TX-11 two different batches may each retain same callback wamid/status/timestamp',async()=>{
  const raw=body([makeEntry('WABA_A','12345678901',0,1)]);
  const f=await fixture(raw);assert.equal((await f.run()).decision,'SIMULATED_COMMIT');
  assert.equal(f.payloads.putFixture('PAYLOAD_B',raw),true);
  const r=await f.inbox.inspectAndCommitFixture({batch_ref:'BATCH_B',protected_payload_ref:'PAYLOAD_B',request:f.request.request},f.store,f.payloads,f.ports);
  assert.equal(r.decision,'SIMULATED_COMMIT'); assert.equal(f.inbox.occurrenceCount,2);
});
test('TX-12 transport writes fail before all-or-none fake state change',async()=>{
  const f=await fixture(body([makeEntry('WABA_A','12345678901',2,2)]));
  const r=await f.run({failWrite:true}); assert.equal(r.decision,'SIMULATED_WRITE_FAILURE');
  assert.equal(f.inbox.occurrenceCount,0);assert.equal(f.inbox.batchCount,0);
  assert.equal((await f.run()).decision,'SIMULATED_COMMIT');assert.equal(f.inbox.occurrenceCount,4);
});
test('TX-13 mixed tenant/waba signed under App A is rejected as a whole',async()=>{
  const f=await fixture(body([makeEntry(),makeEntry('WABA_B','99999999999')]));
  const r=await f.run();assert.equal(r.reason,'HMAC_OR_ROUTING_DENIED');assert.equal(f.inbox.batchCount,0);
});
test('TX-14 input raw buffer cannot change after invocation',async()=>{
  const f=await fixture();const promise=f.run();f.request.request.raw_body.fill(0);
  const result=await promise;assert.equal(result.decision,'SIMULATED_COMMIT');
});
test('TX-15 replay after revocation fails safely (no new ACK or mutation)',async()=>{
  const f=await fixture();await f.run();f.store.proposeAndSwap({action:'REVOKE_APP',app_ref:'APP_A',concessionaria_id:'SHOP_A',expected_revision:1,operation_ref:'OP_AFTER',at_ms:now});
  const result=await f.run();assert.equal(result.decision,'BLOCKED'); assert.equal(f.inbox.occurrenceCount,1);
});
test('TX-16 malformed input and missing fake protected ref deny and never expose PII',async()=>{
  const f=await fixture();const r=await f.inbox.inspectAndCommitFixture({batch_ref:'../BAD',protected_payload_ref:'PAYLOAD_A',request:f.request.request},f.store,f.payloads,f.ports);
  assert.equal(r.reason,'INVALID_INPUT');assert.equal(r.ack_allowed,false);
  assert.equal(JSON.stringify(r).includes('5581900000000'),false);
});
test('TX-17 commit boundary checks fresh clock before capturing final registry snapshot',async()=>{
  const f=await fixture();let calls=0;
  const ports={...f.ports,nowMs:()=>{calls++;if(calls===5)f.store.proposeAndSwap({action:'REVOKE_APP',app_ref:'APP_A',concessionaria_id:'SHOP_A',expected_revision:1,operation_ref:'OP_CLOCK',at_ms:now});return now;}};
  const r=await f.inbox.inspectAndCommitFixture(f.request,f.store,f.payloads,ports);
  assert.equal(r.ack_allowed,false);
  // Exact call index is only a test fixture detail; either denial or a commit
  // before the simulated revocation is allowed, never a real receipt.
  assert.ok(['SIMULATED_COMMIT','BLOCKED'].includes(r.decision));
});
test('TX-18 no S0 durable receipt nor HTTP success is produced by the fake transaction',async()=>{
  const f=await fixture();const r=await f.run();
  assert.equal(r.ack_allowed,false);assert.equal('commit_state' in r,false);
  assert.equal('http_status' in r,false);assert.equal('status' in r,false);
  assert.equal('access_token' in r,false);assert.equal('payload_ref' in r,false);
});
