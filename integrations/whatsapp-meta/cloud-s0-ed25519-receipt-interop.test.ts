/** Adversarial S0 PR48 Ed25519 Python↔Node lab receipt interop. NO ACK. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {inspectPinnedS0LabReceipt as inspect} from './cloud-s0-ed25519-receipt-interop.ts';

const fixture=JSON.parse(readFileSync(
 new URL('./cloud-s0-ed25519-receipt-interop.vector.json',import.meta.url),'utf8'));
const bytes=()=>Buffer.from(fixture.raw_base64,'base64');
const key=()=>Buffer.from(fixture.public_key_base64,'base64');
const receipt=()=>structuredClone(fixture.receipt);
const expected=()=>({
 app:'LAB_APP_A',route:'route_A',route_revision:'1',
 instance:'LAB_S0_01',receipt_key_id:'LAB_RECEIPT_1',
 receipt_key_revision:'1',m2m_issuer:'LAB_META_INFRA',
 m2m_key_id:'key_A',m2m_key_revision:'1',expected_item_count:1,
 bindings:[{waba:'100001',phone:'200001',tenant:'tenant_A',
  channel:'channel_A',revision:'1'}],
});
type Result=ReturnType<typeof inspect>;
const validate=(r:Result)=>{
 for(const k of ['ack_allowed','http_ack_allowed','partial_ack_allowed',
  'http_response_authorized','production_authorized',
  'send_authorized','s0_write_authorized','durable_receipt_verified',
  'commit_verified','service_identity_verified','m2m_verified',
  'channel_policy_ratified','commercial_effect_authorized',
  'retry_external','automatic_retry_authorized',
  'replay_suppression_authorized'] as const)assert.equal(r[k],false,k);
 assert.equal(Object.isFrozen(r),true);
 assert.equal('status' in r,false);
 assert.equal('action' in r,false);
 assert.equal(JSON.stringify(r).includes('5500000000000'),false);
};
const run=(r:unknown=receipt(),e=expected(),b=bytes(),pub=key())=>
 inspect(b,r,e,pub);
const ok=(r:Result)=>{
 validate(r);
 assert.equal(r.decision,'S0_LAB_SIGNATURE_AND_CONTEXT_MATCH_UNRATIFIED');
 if(r.decision==='DENIED')throw Error(r.reason);
 assert.equal(r.receipt_signature_matched,true);
 assert.equal(r.physical_bytes_matched,true);
 assert.equal(r.trusted_context_matched,true);
};
const no=(r:Result,reason?:string)=>{
 validate(r);assert.equal(r.decision,'DENIED');
 if(r.decision!=='DENIED')throw Error('accepted');
 if(reason)assert.equal(r.reason,reason);
 assert.equal(r.receipt_signature_matched,false);
 assert.equal(r.physical_bytes_matched,false);
 assert.equal(r.trusted_context_matched,false);
};
test('INTEROP-01 independent Python golden Ed25519 receipt and original UTF8 bytes',()=>{
 ok(run());
});
test('INTEROP-02 positive cryptographic check is explicitly NOT HTTP ACK',()=>{
 const v=run();ok(v);
 assert.equal(v.production_authorized,false);
 assert.equal(v.durable_receipt_verified,false);
});
test('INTEROP-03 changed pinned S0 public key denies',()=>{
 const p=key();p[0]^=1;
 no(run(receipt(),expected(),bytes(),p),
  'UNTRUSTED_OR_MISMATCHED_KEY');
});
test('INTEROP-04 receipt cannot self-select substitute public key',()=>{
 const v=receipt();v.body.receipt_public_key=Buffer.alloc(32,5).toString('base64');
 no(run(v), 'UNTRUSTED_OR_MISMATCHED_KEY');
});
test('INTEROP-05 forged same-length signature fails cryptography',()=>{
 const v=receipt();v.signature=Buffer.alloc(64,65).toString('base64');
 no(run(v),'S0_SIGNATURE_DENIED');
});
test('INTEROP-06 signature with invalid or noncanonical base64 fails',()=>{
 for(const signature of ['','AAA=','@@@',0,null,
  Buffer.alloc(63).toString('base64')]){
  const v=receipt();v.signature=signature;
  no(run(v),'INVALID_RECEIPT_STRUCTURE');
 }
});
test('INTEROP-07 app mismatch denies',()=>{
 const e=expected();e.app='LAB_APP_B';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-08 route mismatch denies',()=>{
 const e=expected();e.route='route_B';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-09 route revision mismatch denies',()=>{
 const e=expected();e.route_revision='2';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-10 S0 instance mismatch denies',()=>{
 const e=expected();e.instance='OTHER_S0';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-11 receipt signer key ID mismatch denies',()=>{
 const e=expected();e.receipt_key_id='OTHER_SIGNER';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-12 receipt signer revision mismatch denies',()=>{
 const e=expected();e.receipt_key_revision='2';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-13 wrong physical bytes deny despite correct S0 signature',()=>{
 const b=bytes();b[b.length-1]^=1;
 no(run(receipt(),expected(),b),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-14 JSON reorder or whitespace changes physical hash',()=>{
 const b=Buffer.concat([bytes(),Buffer.from(' ')]);
 no(run(receipt(),expected(),b),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-15 event count difference denies',()=>{
 const e=expected();e.expected_item_count=2;
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-16 wrong trusted channel denies',()=>{
 const e=expected();e.bindings[0].channel='OTHER_CHANNEL';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-17 wrong tenant denies',()=>{
 const e=expected();e.bindings[0].tenant='OTHER_TENANT';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-18 wrong sender phone denies',()=>{
 const e=expected();e.bindings[0].phone='200999';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-19 stale trusted binding revision denies',()=>{
 const e=expected();e.bindings[0].revision='2';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-20 duplicate expected binding cannot be treated as two authorities',()=>{
 const e=expected();e.bindings.push({...e.bindings[0]});
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-21 forged recorded timestamp fails signature even if format plausible',()=>{
 const v=receipt();v.body.recorded_at='2026-10-28T17:00:00.100000+00:00';
 no(run(v),'S0_SIGNATURE_DENIED');
});
test('INTEROP-22 forged original item digest fails signature',()=>{
 const v=receipt();v.body.items_sha256='a'.repeat(64);
 no(run(v),'S0_SIGNATURE_DENIED');
});
test('INTEROP-23 forged binding digest fails even before crypto check',()=>{
 const v=receipt();v.body.binding_sha256='b'.repeat(64);
 no(run(v),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-24 claimed production permission true cannot pass profile',()=>{
 const v=receipt();v.body.production_authorized=true;
 no(run(v),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-25 claimed commercial permission true cannot pass profile',()=>{
 const v=receipt();v.body.commercial_transition_authorized=true;
 no(run(v),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-26 fake COMMITTED without signed body is denied',()=>{
 no(run({outcome:'ACCEPTED_DURABLE',commit_state:'COMMITTED',
  total:1,accepted:1,duplicates:0,quarantined:0}),
  'INVALID_RECEIPT_STRUCTURE');
});
test('INTEROP-27 extra top-level field or getter denies',()=>{
 const v=receipt();v.ack_allowed=true;
 no(run(v),'INVALID_RECEIPT_STRUCTURE');
 const w=receipt();
 Object.defineProperty(w,'signature',{get(){throw Error('SECRET');},
  enumerable:true});
 no(run(w),'INVALID_RECEIPT_STRUCTURE');
});
test('INTEROP-28 missing/extra body key denies',()=>{
 const v=receipt();delete v.body.audit_id;
 no(run(v),'CONTEXT_OR_BODY_MISMATCH');
 const w=receipt();w.body.verified=true;
 no(run(w),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-29 malformed or empty trust anchor fails input',()=>{
 no(run(receipt(),expected(),bytes(),Buffer.alloc(0)),'INVALID_INPUT');
 no(run(receipt(),expected(),bytes(),null as any),'INVALID_INPUT');
});
test('INTEROP-30 empty/raw oversized body fails before any signature',()=>{
 no(run(receipt(),expected(),Buffer.alloc(0)),'INVALID_INPUT');
 no(run(receipt(),expected(),Buffer.alloc(262145)),'INVALID_INPUT');
});
test('INTEROP-31 noncanonical/unsafe revision cannot be coerced',()=>{
 const e=expected();e.route_revision='01';
 no(run(receipt(),e),'INVALID_INPUT');
 e.route_revision='1.0';
 no(run(receipt(),e),'INVALID_INPUT');
});
test('INTEROP-32 recovery with same receipt does not grant replay suppression',()=>{
 const a=run(),b=run();
 ok(a);ok(b);assert.deepEqual(a,b);
 assert.equal(a.replay_suppression_authorized,false);
});

test('INTEROP-33 mismatched trusted M2M issuer denies signed S0 receipt',()=>{
 const e=expected();e.m2m_issuer='ANOTHER_INGRESSOR';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-34 mismatched trusted M2M key identity denies',()=>{
 const e=expected();e.m2m_key_id='OTHER_M2M_KEY';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-35 mismatched trusted M2M key revision denies',()=>{
 const e=expected();e.m2m_key_revision='2';
 no(run(receipt(),e),'CONTEXT_OR_BODY_MISMATCH');
});
test('INTEROP-36 malformed trusted M2M key revision denies input',()=>{
 const e=expected();e.m2m_key_revision='01';
 no(run(receipt(),e),'INVALID_INPUT');
});
