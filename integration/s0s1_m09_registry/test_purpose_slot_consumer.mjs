import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {inspectPurposeSlotLab as inspect} from './purpose_slot_consumer.ts';

const SCOPE=Object.freeze({concessionaria_id:'store-A',app_ref:'APP_A',
  route_ref:'route_A',canal_id:'channel_A',waba_id:'100001',
  phone_number_id:'200001'});
const REVS=Object.freeze({route:1,app:1,binding:1,grant:1,principal:1});
const DIGEST='d'.repeat(64);
const FLAGS={production_authorized:false,send_authorized:false,
  external_http_ack:false,commercial_transition_authorized:false};
function source(){
  return {contract_version:'prumo.s0.meta.registry.m2m-pg17/0.1-candidate',
    decision:'AUTHENTICATED_READ_LAB_ONLY',reason:'SIGNED_READ_COMMITTED',
    snapshot:{...SCOPE,revisions:{...REVS},source_revision:DIGEST,
      snapshot_ref:DIGEST,ownership_evidence_state:'UNVERIFIED',
      delegation_evidence_state:'UNVERIFIED'},...FLAGS};
}
function witness(purpose='POST_APP_SECRET',slot_ref='POST_SLOT_A'){
  return {contract_version:'prumo.s0.meta.purpose-slot-witness/0.1-lab',
    app_ref:'APP_A',purpose,slot_ref,source_snapshot_ref:DIGEST,
    source_role:'DISPOSABLE_PG17_INSTALLER_UNVERIFIED',
    production_authorized:false,send_authorized:false};
}
function request(purpose='POST_APP_SECRET'){
  return {purpose,scope:{...SCOPE},expected_revisions:{...REVS}};
}
function flags(x){
  for(const k of ['legacy_wa04a_directly_compatible',
    'provider_ownership_verified','delegation_verified',
    'm2m_operationally_verified','production_authorized','send_authorized',
    'graph_authorized','ack_allowed','s0_write_authorized']){
    assert.equal(x[k],false,k);
  }
  assert.ok(Object.isFrozen(x));
}
function deny(x){
  assert.equal(x.decision,'DENIED');
  assert.equal(x.slot_ref,null);
  assert.equal(x.purpose,null);
  assert.equal(x.source_snapshot_ref,null);
  assert.equal(JSON.stringify(x).includes('POST_SLOT_A'),false);
  flags(x);
}
function matched(x,purpose='POST_APP_SECRET',slot_ref='POST_SLOT_A'){
  assert.equal(x.decision,'LAB_SLOT_NAME_MATCHED_UNVERIFIED');
  assert.equal(x.purpose,purpose);
  assert.equal(x.slot_ref,slot_ref);
  assert.equal(x.source_snapshot_ref,DIGEST);
  assert.equal('secret' in x,false);
  assert.equal('secret_slots' in x,false);
  flags(x);
}

test('M09-06-01 single POST slot name is a non-authority laboratory match',()=>{
  matched(inspect(source(),witness(),request()));
});
test('M09-06-02 GET can observe only the GET name in a separate call',()=>{
  matched(inspect(source(),witness('GET_VERIFY_TOKEN','GET_SLOT_A'),
    request('GET_VERIFY_TOKEN')),'GET_VERIFY_TOKEN','GET_SLOT_A');
});
test('M09-06-03 GRAPH channel scoped match remains no send right',()=>{
  matched(inspect(source(),witness('GRAPH_ACCESS_TOKEN','GRAPH_SLOT_A'),
    request('GRAPH_ACCESS_TOKEN')),'GRAPH_ACCESS_TOKEN','GRAPH_SLOT_A');
});
test('M09-06-04 GET witness never authorizes POST',()=>{
  const x=inspect(source(),witness('GET_VERIFY_TOKEN','GET_SLOT_A'),request());
  deny(x);assert.equal(x.reason,'PURPOSE_MISMATCH');
});
test('M09-06-05 wrong App witness is denied',()=>{
  const w=witness();w.app_ref='APP_B';
  const x=inspect(source(),w,request());deny(x);
});
test('M09-06-06 wrong store, App, route, channel, WABA and number all deny',()=>{
  for(const k of Object.keys(SCOPE)){
    const q=request();
    q.scope[k]=k==='phone_number_id'?'99999999':'OTHER';
    const x=inspect(source(),witness(),q);deny(x);
    assert.equal(x.reason,'REGISTRY_SCOPE_DENIED');
  }
});
test('M09-06-07 each independent revision mismatch denies',()=>{
  for(const k of Object.keys(REVS)){
    const q=request();q.expected_revisions[k]=2;
    deny(inspect(source(),witness(),q));
  }
});
test('M09-06-08 unrelated source digest blocks stale witness',()=>{
  const w=witness();w.source_snapshot_ref='a'.repeat(64);
  const x=inspect(source(),w,request());deny(x);
  assert.equal(x.reason,'SOURCE_CHANGED');
});
test('M09-06-09 malformed source digest cannot yield named slot',()=>{
  const s=source();s.snapshot.snapshot_ref='bad';
  deny(inspect(s,witness(),request()));
});
test('M09-06-10 no match from revoked / preflight / unauthenticated source',()=>{
  for(const state of ['DENIED','STALE_OR_REVOKED','UNAVAILABLE',
    'PHYSICAL_REGISTRY_LAB_ONLY','LAB_SCOPE_MATCHED_UNVERIFIED']){
    const s=source();s.decision=state;
    deny(inspect(s,witness(),request()));
  }
});
test('M09-06-11 source and witness cannot smuggle authority flags',()=>{
  const s=source();s.send_authorized=true;
  deny(inspect(s,witness(),request()));
  const w=witness();w.production_authorized=true;
  deny(inspect(source(),w,request()));
});
test('M09-06-12 slot name invalid or SUPABASE reserved prefix is denied',()=>{
  for(const slot of ['', 'BAD-DASH', 'SUPABASE_SERVICE', 'a'.repeat(300)]){
    const w=witness('POST_APP_SECRET',slot);
    deny(inspect(source(),w,request()));
  }
});
test('M09-06-13 slots are not values, and extra slot fields are not accepted',()=>{
  const w=witness();w.secret_value='synthetic-token';
  deny(inspect(source(),w,request()));
});
test('M09-06-14 unauthorized role markers are not trusted',()=>{
  const w=witness();w.source_role='HOST_TRUSTED';
  deny(inspect(source(),w,request()));
});
test('M09-06-15 prototype, symbols and extra keys fail closed',()=>{
  const w=Object.assign(Object.create({isAdmin:true}),witness());
  deny(inspect(source(),w,request()));
  const z=witness();z[Symbol('privileged')]=true;
  deny(inspect(source(),z,request()));
  const q=request();q.admin=true;
  deny(inspect(source(),witness(),q));
});
test('M09-06-16 getters never execute on untrusted witness',()=>{
  let hits=0;const w=witness();
  Object.defineProperty(w,'slot_ref',{enumerable:true,get(){hits++;throw Error('leak');}});
  deny(inspect(source(),w,request()));
  assert.equal(hits,0);
});
test('M09-06-17 throwing Proxy reflection fails closed',()=>{
  let hits=0;const w=new Proxy(witness(),{
    ownKeys(){hits++;throw Error('untrusted');}});
  deny(inspect(source(),w,request()));
  assert.equal(hits,1);
});
test('M09-06-18 unsafe revisions and wrong purpose fail closed',()=>{
  const q=request();q.expected_revisions.app=Number.MAX_SAFE_INTEGER+1;
  deny(inspect(source(),witness(),q));
  const p=request();p.purpose='REGISTRY_READ';
  deny(inspect(source(),witness(),p));
});
test('M09-06-19 no input mutation and no source identifiers in negative reply',()=>{
  const s=source(),w=witness(),q=request();
  const before=JSON.stringify([s,w,q]);
  matched(inspect(s,w,q));
  assert.equal(JSON.stringify([s,w,q]),before);
  const bad=inspect(s,{...w,app_ref:'APP_B'},q);
  deny(bad);assert.equal(JSON.stringify(bad).includes('APP_B'),false);
});
test('M09-06-20 missing witness/fields denied, never fabricated',()=>{
  deny(inspect(source(),null,request()));
  const w=witness();delete w.source_snapshot_ref;
  deny(inspect(source(),w,request()));
});
test('M09-06-21 positive result contains ONE name and no other names',()=>{
  const r=inspect(source(),witness(),request());
  matched(r);
  const txt=JSON.stringify(r);
  for(const key of ['GET_SLOT_A','GRAPH_SLOT_A','token_value','bearer',
    'WA_META_A_HMAC','PRIVATE_KEY'])assert.equal(txt.includes(key),false);
});
test('M09-06-22 source verifier cannot be inferred from result flags',()=>{
  const x=inspect(source(),witness(),request());
  assert.equal(x.m2m_operationally_verified,false);
  assert.equal(x.provider_ownership_verified,false);
  assert.equal('m2m_verified' in x,false);
});
test('M09-06-23 genuine PG17 signed read plus single installer slot audits',
  {skip:!process.env.M09_PURPOSE_EVIDENCE},async()=>{
  const evidence=JSON.parse(await readFile(process.env.M09_PURPOSE_EVIDENCE,'utf8'));
  const s=evidence.source,w=evidence.witness,q=evidence.request;
  assert.equal(s.decision,'AUTHENTICATED_READ_LAB_ONLY');
  assert.equal(w.purpose,'POST_APP_SECRET');
  assert.equal(w.slot_ref,'POST_SLOT_A');
  const x=inspect(s,w,q);
  assert.equal(x.decision,'LAB_SLOT_NAME_MATCHED_UNVERIFIED');
  assert.equal(x.production_authorized,false);
  assert.equal(x.m2m_operationally_verified,false);
  const bad={...q,purpose:'GRAPH_ACCESS_TOKEN'};
  deny(inspect(s,w,bad));
});
