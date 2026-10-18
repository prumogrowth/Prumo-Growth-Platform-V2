import assert from 'node:assert/strict';
import {createHash,createHmac} from 'node:crypto';
import {test} from 'node:test';
import {canonicalizeInternalProofV1,WA06B_PROOF_VERSION,WA06B_CANONICAL_VERSION} from './internal-proof-wire-v1.ts';

const hex=(bytes:Uint8Array)=>Buffer.from(bytes).toString('hex');
const fingerprint=(bytes:Uint8Array)=>createHash('sha256').update(bytes).digest('hex');
const mac=(bytes:Uint8Array)=>createHmac('sha256','lab-only-not-a-prod-key').update(bytes).digest('hex');
function fixture() {
  const claims={proof_version:WA06B_PROOF_VERSION,canonicalization_version:WA06B_CANONICAL_VERSION,
    service_ref:'meta_ingestor',request_ref:'req_1',nonce_ref:'nonce_1',key_epoch:1,
    purpose:'meta_s0.ingest',audience:'s0_internal_ingress',issued_at_ms:1000,expires_at_ms:2000};
  const occurrence={position:{entry_index:0,change_index:0,array_kind:'statuses',item_index:0},
    event_kind:'status_callback',app_ref:'app_a',concessionaria_id:'loja_a',canal_id:'canal_a',
    waba_id:'waba_a',phone_number_id:'phone_a',provider_message_id:'wamid.ID=',
    provider_timestamp:'2026-10-18T12:00:00.000Z',provider_kind:'delivered'};
  const candidate={contract_version:'meta-s0-handoff.v0.1-proposed',batch_ref:'batch_1',route_ref:'route_1',
    route_revision:1,app_ref:'app_a',protected_payload_ref:'payload_1',payload_sha256:'a'.repeat(64),
    scope_sha256:'b'.repeat(64),event_count:1,occurrences:[occurrence],ack_allowed:false,
    production_authorized:false};
  return {claims,candidate};
}
const bytes=(v:ReturnType<typeof fixture>)=>canonicalizeInternalProofV1(v.claims,v.candidate);
const cloned=()=>structuredClone(fixture());
const changed=(fn:(v:ReturnType<typeof fixture>)=>void)=>{const x=cloned();fn(x);return x;};

test('WIRE-01 same candidate yields deterministic bytes; canonical hash fixture',()=>{
  const a=fixture(),b=cloned();
  assert.equal(hex(bytes(a)),hex(bytes(b)));
  assert.equal(fingerprint(bytes(a)),'c94993710cfc4a90d41314c89026385e7cbd446753b2fa7d0ec0cc7f65083209');
});
test('WIRE-02 service/request/nonce/key epoch all bind distinct bytes',()=>{
  const b=bytes(fixture());
  for (const change of [
    (x:any)=>x.claims.service_ref='other', (x:any)=>x.claims.request_ref='other',
    (x:any)=>x.claims.nonce_ref='other',(x:any)=>x.claims.key_epoch=2,
    (x:any)=>x.claims.issued_at_ms=1001,(x:any)=>x.claims.expires_at_ms=2001
  ]) assert.notEqual(hex(b),hex(bytes(changed(change))));
});
test('WIRE-03 route/app/payload/digest and occurrences bind distinct MACs',()=>{
  const baseline=mac(bytes(fixture()));
  for(const change of [(x:any)=>x.candidate.route_ref='other',
    (x:any)=>x.candidate.app_ref=x.candidate.occurrences[0].app_ref='other',
    (x:any)=>x.candidate.protected_payload_ref='payload_2',
    (x:any)=>x.candidate.payload_sha256='c'.repeat(64),
    (x:any)=>x.candidate.scope_sha256='d'.repeat(64),
    (x:any)=>x.candidate.occurrences[0].provider_kind='read',
    (x:any)=>x.candidate.occurrences[0].provider_timestamp='2026-10-18T12:01:00.000Z'])
    assert.notEqual(mac(bytes(changed(change))),baseline);
});
test('WIRE-04 rejects purpose/audience downgrade and unknown versions',()=>{
  for(const change of [(x:any)=>x.claims.purpose='C07',
    (x:any)=>x.claims.audience='graph',(x:any)=>x.claims.proof_version='old',
    (x:any)=>x.claims.canonicalization_version='old',
    (x:any)=>x.candidate.contract_version='old'])
    assert.throws(()=>bytes(changed(change)),/INVALID_WA06B_PROOF_ENVELOPE/);
});
test('WIRE-05 rejects unexpected PII/secret fields anywhere',()=>{
  for(const change of [(x:any)=>x.claims.token='secret',
    (x:any)=>x.candidate.customer_number='5581000000',
    (x:any)=>x.candidate.occurrences[0].message_text='PII',
    (x:any)=>x.candidate.occurrences[0].position.raw_phone='PII'])
    assert.throws(()=>bytes(changed(change)),/INVALID_WA06B_PROOF_ENVELOPE/);
});
test('WIRE-06 reject accessor fields without calling hostile getters',()=>{
  const a:any=fixture();let called=false;
  Object.defineProperty(a.claims,'service_ref',{enumerable:true,get(){called=true;throw Error('secret');}});
  assert.throws(()=>bytes(a),/INVALID_WA06B_PROOF_ENVELOPE/);assert.equal(called,false);
});
test('WIRE-07 reject array getters, holes and custom members',()=>{
  const a:any=fixture();let called=false;
  Object.defineProperty(a.candidate.occurrences,'0',{get(){called=true;throw Error('leak');}});
  assert.throws(()=>bytes(a),/INVALID_WA06B_PROOF_ENVELOPE/);assert.equal(called,false);
  const b:any=fixture();delete b.candidate.occurrences[0];
  assert.throws(()=>bytes(b),/INVALID_WA06B_PROOF_ENVELOPE/);
  const c:any=fixture();c.candidate.occurrences.extra='secret';
  assert.throws(()=>bytes(c),/INVALID_WA06B_PROOF_ENVELOPE/);
});
test('WIRE-08 rejects malformed numeric, scope count, flags',()=>{
  for(const change of [(x:any)=>x.claims.key_epoch=0,
    (x:any)=>x.claims.issued_at_ms=1.1,
    (x:any)=>x.claims.expires_at_ms=0,
    (x:any)=>x.candidate.event_count=2,
    (x:any)=>x.candidate.ack_allowed=true,
    (x:any)=>x.candidate.production_authorized=true])
    assert.throws(()=>bytes(changed(change)),/INVALID_WA06B_PROOF_ENVELOPE/);
});
test('WIRE-09 rejects duplicate occurrence positions and binds order',()=>{
  const a:any=fixture();a.candidate.occurrences.push(structuredClone(a.candidate.occurrences[0]));a.candidate.event_count=2;
  assert.throws(()=>bytes(a),/INVALID_WA06B_PROOF_ENVELOPE/);
  const b:any=fixture();const second=structuredClone(b.candidate.occurrences[0]);second.position.item_index=1;
  b.candidate.occurrences.push(second);b.candidate.event_count=2;
  const v1=hex(bytes(b));b.candidate.occurrences.reverse();assert.notEqual(v1,hex(bytes(b)));
});
test('WIRE-10 allows same WAMID callback occurrences in distinct positions',()=>{
  const a:any=fixture(),o=structuredClone(a.candidate.occurrences[0]);o.position.item_index=1;
  a.candidate.occurrences.push(o);a.candidate.event_count=2;
  assert.ok(bytes(a).byteLength>0);
});
test('WIRE-11 allows same App with two distinct channels, rejects other App',()=>{
  const a:any=fixture(),o=structuredClone(a.candidate.occurrences[0]);
  o.position.item_index=1;o.canal_id='canal_b';o.phone_number_id='phone_b';
  a.candidate.occurrences.push(o);a.candidate.event_count=2;
  assert.ok(bytes(a).byteLength>0);
  o.app_ref='app_b';
  assert.throws(()=>bytes(a),/INVALID_WA06B_PROOF_ENVELOPE/);
});
test('WIRE-12 validates dates, WAMID, array/event-kind combinations',()=>{
  for(const change of [(x:any)=>x.candidate.occurrences[0].provider_timestamp='2026-02-31T12:00:00.000Z',
    (x:any)=>x.candidate.occurrences[0].provider_message_id='bad',
    (x:any)=>x.candidate.occurrences[0].position.array_kind='messages',
    (x:any)=>x.candidate.occurrences[0].event_kind='inbound_message'])
    assert.throws(()=>bytes(changed(change)),/INVALID_WA06B_PROOF_ENVELOPE/);
});
test('WIRE-13 emits sanitized errors without customer/secret content',()=>{
  const a:any=fixture();a.candidate.occurrences[0].message_text='CUSTOMER PRIVATE';
  try{bytes(a);assert.fail('expected rejection');}catch(e){
    assert.equal((e as Error).message,'INVALID_WA06B_PROOF_ENVELOPE');
    assert.doesNotMatch(String(e),/CUSTOMER PRIVATE/);
  }
});
test('WIRE-14 rejects non-ASCII lookalikes and unsafe field lengths',()=>{
  for(const change of [(x:any)=>x.claims.service_ref='servíço',
    (x:any)=>x.candidate.route_ref='r'.repeat(129),
    (x:any)=>x.candidate.occurrences[0].provider_kind='💬'])
    assert.throws(()=>bytes(changed(change)),/INVALID_WA06B_PROOF_ENVELOPE/);
});
test('WIRE-15 length prefixes separate field boundaries',()=>{
  const a:any=fixture(),b:any=fixture();
  a.claims.request_ref='ab';a.claims.nonce_ref='c';
  b.claims.request_ref='a';b.claims.nonce_ref='bc';
  assert.notEqual(hex(bytes(a)),hex(bytes(b)));
});
