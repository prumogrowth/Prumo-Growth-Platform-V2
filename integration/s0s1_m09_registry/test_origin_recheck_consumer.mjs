import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync, sign} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {inspectOriginRecheckLab as inspect} from './origin_recheck_consumer.ts';

const DOMAIN=Buffer.from('PRUMO.S0.M09.ATTEST.RECHECK/0.1\0','utf8');
const {publicKey,privateKey}=generateKeyPairSync('ed25519');
const key=publicKey.export({format:'der',type:'spki'});
const scope={concessionaria_id:'store-A',app_ref:'APP_A',route_ref:'route_A',
  canal_id:'channel_A',waba_id:'100001',phone_number_id:'200001'};
const revs={route:1,app:1,binding:1,grant:1,principal:1};
const hash='b'.repeat(64);
const nonce='A'.repeat(24), freshNonce='B'.repeat(24);
function canonical(o){
  if(Array.isArray(o))return '['+o.map(canonical).join(',')+']';
  if(o!==null&&typeof o==='object')
    return '{'+Object.keys(o).sort().map(k=>JSON.stringify(k)+':'+canonical(o[k])).join(',')+'}';
  return JSON.stringify(o);
}
function payload(kind){
  return {contract_version:'prumo.s0.meta.origin-recheck/0.1-lab',
    kind,issuer_ref:'M09_S0_LAB',audience:'LAB_META_CONSUMER',
    purpose:'POST_APP_SECRET',scope:structuredClone(scope),
    revisions:structuredClone(revs),source_snapshot_ref:hash,
    slot_ref:'POST_SLOT_A',issued_ms:kind==='ORIGIN'?1000:1100,
    expires_ms:20000,nonce:kind==='ORIGIN'?nonce:freshNonce,
    parent_nonce:kind==='ORIGIN'?null:nonce};
}
function signed(p,k=privateKey){
  return {payload:p,signature:sign(null,Buffer.concat([
    DOMAIN,Buffer.from(canonical(p),'utf8')]),k).toString('base64url')};
}
function fixture(){
  return [signed(payload('ORIGIN')),signed(payload('RECHECK'))];
}
function expected(){return {purpose:'POST_APP_SECRET',scope:structuredClone(scope),
  revisions:structuredClone(revs),source_snapshot_ref:hash};}
function run(a,b,e=expected(),k=key,now=1200){
  return inspect(a,b,e,k,now);
}
function denied(x){
  assert.equal(x.decision,'DENIED');
  assert.equal(x.signature_integrity_lab_verified,false);
  assert.equal(x.purpose,null);
  assert.equal(x.production_authorized,false);
  assert.equal(x.send_authorized,false);
  assert.equal(x.graph_authorized,false);
  assert.equal(x.ack_allowed,false);
  assert.equal(x.credential_resolution_authorized,false);
  assert.equal(x.recheck_atomic_with_dispatch,false);
  assert.ok(Object.isFrozen(x));
}
function matched(x){
  assert.equal(x.decision,'LAB_SIGNED_RECHECK_MATCHED_UNVERIFIED');
  assert.equal(x.reason,'SIGNED_TWO_OBSERVATIONS');
  assert.equal(x.signature_integrity_lab_verified,true);
  assert.equal(x.purpose,'POST_APP_SECRET');
  assert.equal(x.production_authorized,false);
  assert.equal(x.send_authorized,false);
  assert.equal(x.graph_authorized,false);
  assert.equal(x.ack_allowed,false);
  assert.equal(x.credential_resolution_authorized,false);
  assert.equal(x.recheck_atomic_with_dispatch,false);
  assert.equal('slot_ref' in x,false);
  assert.ok(Object.isFrozen(x));
}

test('M09-07-01 two signed observations validate integrity, never authority',()=>{
  const [a,b]=fixture();matched(run(a,b));
});
test('M09-07-02 first observation alone cannot authorize anything',()=>{
  const [a]=fixture();const x=run(a,null);denied(x);assert.equal(x.reason,'RECHECK_REQUIRED');
});
test('M09-07-03 original payload mutation without resigning fails',()=>{
  const [a,b]=fixture();a.payload.slot_ref='GRAPH_SLOT_A';
  denied(run(a,b));
});
test('M09-07-04 fresh payload mutation without resigning fails',()=>{
  const [a,b]=fixture();b.payload.scope.route_ref='route_B';
  denied(run(a,b));
});
test('M09-07-05 cannot replace signature with unrelated domain',()=>{
  const [a,b]=fixture();
  b.signature=sign(null,Buffer.from(canonical(b.payload)),privateKey).toString('base64url');
  denied(run(a,b));
});
test('M09-07-06 unrelated trusted public key denies otherwise correct signatures',()=>{
  const [a,b]=fixture();
  const unrelated=generateKeyPairSync('ed25519').publicKey.export({format:'der',type:'spki'});
  denied(run(a,b,expected(),unrelated));
});
test('M09-07-07 public key is externally pinned and must have exact Ed25519 SPKI',()=>{
  const [a,b]=fixture();
  for(const bad of [null,Buffer.alloc(32),Buffer.alloc(44),{},'SPKI'])
    denied(run(a,b,expected(),bad));
});
test('M09-07-08 recheck must be distinct nonce linked to origin',()=>{
  const [a,b]=fixture();b.payload.nonce=nonce;const s=signed(b.payload);
  const x=run(a,s);denied(x);assert.equal(x.reason,'STALE_RECHECK');
});
test('M09-07-09 missing parent nonce is stale even when signed',()=>{
  const [a,b]=fixture();b.payload.parent_nonce='C'.repeat(24);
  denied(run(a,signed(b.payload)));
});
test('M09-07-10 two signed origin messages cannot masquerade as recheck',()=>{
  const [a]=fixture();denied(run(a,a));
});
test('M09-07-11 future-issued recheck rejected',()=>{
  const [a,b]=fixture();b.payload.issued_ms=10000;
  b.payload.expires_ms=20000;
  denied(run(a,signed(b.payload)));
});
test('M09-07-12 old recheck window rejected',()=>{
  const [a,b]=fixture();denied(run(a,b,expected(),key,20000));
});
test('M09-07-13 recheck older than origin rejected',()=>{
  const [a,b]=fixture();b.payload.issued_ms=500;
  denied(run(a,signed(b.payload)));
});
test('M09-07-14 more than 15s separation rejected even when validly signed',()=>{
  const [a,b]=fixture();b.payload.issued_ms=17001;b.payload.expires_ms=19000;
  const x=run(a,signed(b.payload),expected(),key,18000);
  denied(x);assert.equal(x.reason,'STALE_RECHECK');
});
test('M09-07-15 every separate revision must match host expected',()=>{
  const [a,b]=fixture();
  for(const k of Object.keys(revs)){
    const e=expected();e.revisions[k]=2;
    const x=run(a,b,e);denied(x);assert.equal(x.reason,'SCOPE_CHANGED');
  }
});
test('M09-07-16 every channel/store/app/route/phone must match expected',()=>{
  const [a,b]=fixture();
  for(const k of Object.keys(scope)){
    const e=expected();e.scope[k]=k==='phone_number_id'?'33333333':'OTHER';
    denied(run(a,b,e));
  }
});
test('M09-07-17 origin and recheck cannot disagree on slot or purpose',()=>{
  const [a,b]=fixture();b.payload.slot_ref='GRAPH_SLOT_A';
  denied(run(a,signed(b.payload)));
  const c=fixture()[1];c.payload.purpose='GET_VERIFY_TOKEN';
  denied(run(a,signed(c.payload)));
});
test('M09-07-18 origin/recheck snapshot digest must match host-pinned digest',()=>{
  const [a,b]=fixture();const e=expected();e.source_snapshot_ref='c'.repeat(64);
  denied(run(a,b,e));
  b.payload.source_snapshot_ref='d'.repeat(64);
  denied(run(a,signed(b.payload)));
});
test('M09-07-19 unknown payload fields and missing required ones fail closed',()=>{
  const [a,b]=fixture();a.payload.private_key='fake';
  denied(run(signed(a.payload),b));
  const [c,d]=fixture();delete d.payload.slot_ref;
  denied(run(c,signed(d.payload)));
});
test('M09-07-20 wrong issuer, audience, version or environment fails',()=>{
  for(const [k,v] of [
    ['issuer_ref','APP_PROVIDER'],['audience','PROD'],
    ['contract_version','1.0'],['kind','PRODUCTION']]){
    const [a,b]=fixture();a.payload[k]=v;denied(run(signed(a.payload),b));
  }
});
test('M09-07-21 no getters executed, even on externally trusted expected',()=>{
  const [a,b]=fixture(),e=expected();let count=0;
  Object.defineProperty(e.scope,'app_ref',{enumerable:true,
    get(){count++;throw Error('getter');}});
  denied(run(a,b,e));assert.equal(count,0);
});
test('M09-07-22 Proxy traps fail closed without leaking a key or slot',()=>{
  const [a,b]=fixture();a.payload=new Proxy(a.payload,{ownKeys(){throw Error('malicious');}});
  denied(run(a,b));
});
test('M09-07-23 unusual/invalid signature encoding denied',()=>{
  const [a,b]=fixture();
  for(const sig of ['hello','='.repeat(86),b.signature+'=',b.signature.slice(1)]){
    const x=run(a,{...b,signature:sig});denied(x);
  }
});
test('M09-07-24 invalid expiry exceeding 30s maximum denied',()=>{
  const [a,b]=fixture();a.payload.expires_ms=40000;
  denied(run(signed(a.payload),b));
});
test('M09-07-25 booleans, unsafe versions, malformed IDs fail closed',()=>{
  const [a,b]=fixture();
  const e=expected();e.revisions.grant=Number.MAX_SAFE_INTEGER+1;
  denied(run(a,b,e));
  const c=payload('ORIGIN');c.scope.phone_number_id='NOT_PHONE';
  denied(run(signed(c),b));
});
test('M09-07-26 no mutation of input or identifiers in decision',()=>{
  const [a,b]=fixture(),e=expected();
  const before=JSON.stringify([a,b,e]);const x=run(a,b,e);
  matched(x);assert.equal(JSON.stringify([a,b,e]),before);
  const serialized=JSON.stringify(x);
  for(const v of ['APP_A','route_A','200001','POST_SLOT_A',hash])
    assert.equal(serialized.includes(v),false);
});
test('M09-07-27 cryptographic signatures do NOT imply Meta ownership or operational M2M',()=>{
  const [a,b]=fixture();const x=run(a,b);matched(x);
  assert.equal(x.provider_ownership_verified,false);
  assert.equal(x.m2m_operationally_verified,false);
});
test('M09-07-28 old pair can remain cryptographically valid AFTER revocation: MUST NOT authorize',()=>{
  const [a,b]=fixture();
  const x=run(a,b);matched(x);
  assert.equal(x.recheck_atomic_with_dispatch,false);
  // A real revocation immediately afterward cannot be inferred from old signatures.
  // This is a deliberate negative guarantee, not a proof of live authorization.
});
test('M09-07-29 physical PG17 signed origin and recheck after two separate M2M reads',
 {skip:!process.env.M09_ORIGIN_EVIDENCE},async()=>{
  const d=JSON.parse(await readFile(process.env.M09_ORIGIN_EVIDENCE,'utf8'));
  assert.equal(d.lab_only,true);
  assert.equal(d.actual_m2m_reads,2);
  assert.equal(d.revoked_after_observations,true);
  const der=Buffer.from(d.fixture_public_key_spki,'base64url');
  const result=inspect(d.origin,d.fresh,d.expected,der,d.observed_now_ms);
  assert.equal(result.decision,'LAB_SIGNED_RECHECK_MATCHED_UNVERIFIED');
  assert.equal(result.recheck_atomic_with_dispatch,false);
  assert.equal(result.production_authorized,false);
  // The prior observations cannot prove state AFTER the later revocation.
  denied(inspect(d.origin,null,d.expected,der,d.observed_now_ms));
});
