/** WA10: synthetic M2M metadata, Ed25519 host pin & rotation hardening. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {inspectWa10PinnedS0LabTrust as inspect,
 type Wa10FixtureRegistry} from './wa10-service-trust-pin-audit.ts';
const vector=JSON.parse(readFileSync(
 new URL('./cloud-s0-ed25519-receipt-interop.vector.json',import.meta.url),'utf8'));
const NOW=1792320000000;
const KEY=vector.public_key_base64 as string;
const expected=()=>({
 app:'LAB_APP_A',route:'route_A',route_revision:'1',
 instance:'LAB_S0_01',receipt_key_id:'LAB_RECEIPT_1',
 receipt_key_revision:'1',m2m_issuer:'LAB_META_INFRA',
 m2m_key_id:'key_A',m2m_key_revision:'1',expected_item_count:1,
 bindings:[{waba:'100001',phone:'200001',tenant:'tenant_A',
  channel:'channel_A',revision:'1'}],
});
const registry=():Wa10FixtureRegistry=>({
 contract_version:'wa10-meta-service-trust.lab.v0.1-candidate',
 registry_revision:4,
 receipt_pins:[{
  app_ref:'LAB_APP_A',instance_ref:'LAB_S0_01',
  key_id:'LAB_RECEIPT_1',key_revision:'1',public_key_base64:KEY,
  status:'ACTIVE',not_before_ms:NOW-3000,not_after_ms:NOW+3000,
 }],
 service_principals:[{
  principal_ref:'META_INGRESS_SERVICE_A',app_ref:'LAB_APP_A',
  issuer_ref:'LAB_META_INFRA',m2m_key_id:'key_A',m2m_key_revision:'1',
  audience:'PRUMO_S0_META_INGRESS_LAB',status:'ACTIVE',
  not_before_ms:NOW-3000,not_after_ms:NOW+3000,
 }],
});
const host=()=>({
 principal_ref:'META_INGRESS_SERVICE_A',app_ref:'LAB_APP_A',
 issuer_ref:'LAB_META_INFRA',m2m_key_id:'key_A',
 m2m_key_revision:'1',audience:'PRUMO_S0_META_INGRESS_LAB',
 expected_registry_revision:4,at_ms:NOW,
});
const signed=()=>structuredClone(vector.receipt);
const bytes=()=>Buffer.from(vector.raw_base64,'base64');
const run=(opts:{receipt?:unknown;raw?:Uint8Array;expected?:unknown;
 host?:unknown;registry?:unknown}={})=>inspect(
 opts.raw??bytes(),opts.receipt??signed(),
 (opts.expected??expected()) as ReturnType<typeof expected>,
 opts.host??host(),opts.registry??registry(),
);
const no=(v:ReturnType<typeof run>,reason?:string)=>{
 assert.equal(v.decision,'DENIED');
 if(reason)assert.equal(v.reason,reason);
 assert.equal(v.receipt_signature_matched,false);
 rights(v);
};
const rights=(v:ReturnType<typeof run>)=>{
 for(const k of ['m2m_authenticated','key_custody_verified','pin_authority_ratified',
  'rotation_authorized','ack_allowed','http_ack_allowed','send_authorized',
  'production_authorized','s0_write_authorized','retry_external',
  'commercial_transition_authorized'] as const)assert.equal(v[k],false,k);
 assert.equal('status' in v,false);
 assert.equal('action' in v,false);
 assert.equal('secret_slot' in v,false);
 assert.equal('public_key_base64' in v,false);
 assert.equal(Object.isFrozen(v),true);
};
test('WA10-01 valid independent lab pin + Python Ed25519 receipt remains UNRATIFIED',()=>{
 const x=run();
 assert.equal(x.decision,'LAB_PIN_AND_RECEIPT_MATCHED_UNRATIFIED');
 assert.equal(x.reason,null);assert.equal(x.receipt_signature_matched,true);
 rights(x);
});
test('WA10-02 no registry or self-pinning fallback',()=>{
 no(run({registry:null}),'INVALID_TRUST_REGISTRY');
});
test('WA10-03 untrusted host context missing fails closed',()=>{
 no(run({host:null}),'INVALID_INPUT');
});
test('WA10-04 human principal instead of M2M metadata rejected',()=>{
 no(run({host:{...host(),principal_ref:'HUMAN_DIRECTOR_A'}}),
  'SERVICE_CONTEXT_DENIED');
});
test('WA10-05 cross-App principal denied',()=>{
 no(run({host:{...host(),app_ref:'LAB_APP_B'}}),
  'SERVICE_CONTEXT_DENIED');
});
test('WA10-06 cross-issuer M2M metadata denied',()=>{
 no(run({host:{...host(),issuer_ref:'OTHER_ISSUER'}}),
  'SERVICE_CONTEXT_DENIED');
});
test('WA10-07 stale M2M key revision denied',()=>{
 no(run({host:{...host(),m2m_key_revision:'2'}}),
  'SERVICE_CONTEXT_DENIED');
});
test('WA10-08 wrong audience rejects even if subject same',()=>{
 no(run({host:{...host(),audience:'OPENAI_ASSISTANT'}}),'INVALID_INPUT');
});
test('WA10-09 absent S0 principal in trusted metadata denies',()=>{
 const r=registry();r.service_principals=[];
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
});
test('WA10-10 service revoked denies irrespective of a valid Ed25519 receipt',()=>{
 const r=registry();r.service_principals[0].status='REVOKED';
 no(run({registry:r}),'SERVICE_CONTEXT_DENIED');
});
test('WA10-11 staged M2M service cannot authenticate from metadata',()=>{
 const r=registry();r.service_principals[0].status='STAGED';
 no(run({registry:r}),'SERVICE_CONTEXT_DENIED');
});
test('WA10-12 S0 service expiry or future activation denied',()=>{
 for(const t of [NOW-3001,NOW+3000]){
  no(run({host:{...host(),at_ms:t}}),'SERVICE_CONTEXT_DENIED');
 }
});
test('WA10-13 host trust registry revision must be current',()=>{
 no(run({host:{...host(),expected_registry_revision:3}}),
  'STALE_TRUST_REVISION');
});
test('WA10-14 pin revoked denies valid old signature',()=>{
 const r=registry();r.receipt_pins[0].status='REVOKED';
 no(run({registry:r}),'PIN_REVOKED');
});
test('WA10-15 STAGED pin cannot validate the receipt',()=>{
 const r=registry();r.receipt_pins[0].status='STAGED';
 no(run({registry:r}),'PIN_NOT_CURRENT');
});
test('WA10-16 expired/not-yet-active pin never signs a lab success',()=>{
 for(const t of [NOW-3001,NOW+3000]){
  const r=registry();r.service_principals[0].not_before_ms=0;
  r.service_principals[0].not_after_ms=NOW+10000;
  no(run({host:{...host(),at_ms:t},registry:r}),'PIN_NOT_CURRENT');
 }
});
test('WA10-17 changing host pin ID denies despite matching receipt self-claim',()=>{
 const r=registry();r.receipt_pins[0].key_id='LAB_OTHER_KEY';
 no(run({registry:r}),'PIN_NOT_CURRENT');
});
test('WA10-18 wrong pin bytes cannot be replaced by receipt-embedded key',()=>{
 const r=registry();
 r.receipt_pins[0].public_key_base64=Buffer.alloc(32,3).toString('base64');
 no(run({registry:r}),'RECEIPT_DENIED');
});
test('WA10-19 tampered S0 receipt signature rejects',()=>{
 const rec=signed();
 rec.signature=Buffer.alloc(64,1).toString('base64');
 no(run({receipt:rec}),'RECEIPT_DENIED');
});
test('WA10-20 tampered raw POST original bytes reject',()=>{
 const raw=bytes();raw[0]^=1;
 no(run({raw}),'RECEIPT_DENIED');
});
test('WA10-21 changed S0 binding/context not ratified by trust pins',()=>{
 const e=expected();e.bindings[0].tenant='OTHER_TENANT';
 no(run({expected:e}),'RECEIPT_DENIED');
});
test('WA10-22 receipt issuer fields are not a principal identity source',()=>{
 const rec=signed();
 rec.body.m2m_issuer='OTHER_ISSUER';
 no(run({receipt:rec}),'RECEIPT_DENIED');
});
test('WA10-23 two active pins in deliberate rotation allowed by exact key ID',()=>{
 const r=registry();r.receipt_pins.push({
  ...r.receipt_pins[0],key_id:'NEW_PIN',key_revision:'2',
  public_key_base64:Buffer.alloc(32,4).toString('base64'),
 });
 const x=run({registry:r});
 assert.equal(x.decision,'LAB_PIN_AND_RECEIPT_MATCHED_UNRATIFIED');
 rights(x);
});
test('WA10-24 revoking old pin during new-key overlap denies old receipts',()=>{
 const r=registry();r.receipt_pins.push({
  ...r.receipt_pins[0],key_id:'NEW_PIN',key_revision:'2',
  public_key_base64:Buffer.alloc(32,4).toString('base64')});
 r.receipt_pins[0].status='REVOKED';
 no(run({registry:r}),'PIN_REVOKED');
});
test('WA10-25 duplicate exact key version in registry rejects globally',()=>{
 const r=registry();r.receipt_pins.push({...r.receipt_pins[0]});
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
});
test('WA10-26 same key bytes under another dealership is denied',()=>{
 const r=registry();r.receipt_pins.push({
  ...r.receipt_pins[0],app_ref:'LAB_APP_B',key_id:'OTHER'});
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
});
test('WA10-27 conflicting duplicate M2M subject/issuer key rejected',()=>{
 const r=registry();r.service_principals.push({...r.service_principals[0]});
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
});
test('WA10-28 invalid base64 and non-32-byte pins deny',()=>{
 for(const pub of ['invalid','AA==',Buffer.alloc(31).toString('base64')]){
  const r=registry();r.receipt_pins[0].public_key_base64=pub;
  no(run({registry:r}),'INVALID_TRUST_REGISTRY');
 }
});
test('WA10-29 malformed pin window denies whole trust registry',()=>{
 const r=registry();
 r.receipt_pins[0].not_after_ms=r.receipt_pins[0].not_before_ms;
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
});
test('WA10-30 extra secret field cannot be laundered through pins',()=>{
 const r=registry();Object.assign(r.receipt_pins[0],{secret_private_key:'DO_NOT_READ'});
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
});
test('WA10-31 prototype pollution cannot be passed as registry record',()=>{
 const r=registry();r.receipt_pins[0]=Object.assign(
  Object.create({app_ref:'LAB_APP_A'}),r.receipt_pins[0]);
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
});
test('WA10-32 getters never run during trust registry snapshot',()=>{
 const r=registry();let hits=0;
 Object.defineProperty(r.receipt_pins[0],'status',{enumerable:true,
  get(){hits++;throw Error('should not run');}});
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
 assert.equal(hits,0);
});
test('WA10-33 poisoned Proxy cannot cause privileged success',()=>{
 const r=new Proxy(registry(),{ownKeys(){throw Error('poison');}});
 no(run({registry:r}),'INVALID_TRUST_REGISTRY');
});
test('WA10-34 unexpected host credentials field rejected',()=>{
 const h={...host(),access_token:'LEAK'};
 no(run({host:h}),'INVALID_INPUT');
});
test('WA10-35 wrong instance pin does not match receipt',()=>{
 const r=registry();r.receipt_pins[0].instance_ref='OTHER_INSTANCE';
 no(run({registry:r}),'PIN_NOT_CURRENT');
});
test('WA10-36 valid input never exposes a pin, secret or client details',()=>{
 const x=run(),serialized=JSON.stringify(x);
 for(const sensitive of [KEY,'LAB_META_INFRA','LAB_APP_A',
  'META_INGRESS_SERVICE_A','200001','private','access_token']){
  assert.equal(serialized.includes(sensitive),false,sensitive);
 }
});
test('WA10-37 host time and revision must be safe integers',()=>{
 for(const at_ms of [NaN,-1,Infinity,1.5])
  no(run({host:{...host(),at_ms}}),'INVALID_INPUT');
});
