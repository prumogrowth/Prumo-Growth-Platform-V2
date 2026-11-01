import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { inspectM09ForMetaOffline as inspect } from './wa04a_scope_bridge.ts';

const revs = {route:1,app:1,binding:1,grant:1,principal:1};
const scope = {
  concessionaria_id:'store-A', app_ref:'APP_A',route_ref:'route_A',
  canal_id:'channel_A',waba_id:'100001',phone_number_id:'200001'
};
const flags = {
  production_authorized:false,send_authorized:false,
  external_http_ack:false,commercial_transition_authorized:false
};
function fixture() {
  return {
    contract_version:'prumo.s0.meta.registry.m2m-pg17/0.1-candidate',
    decision:'AUTHENTICATED_READ_LAB_ONLY',
    reason:'SIGNED_READ_COMMITTED',
    snapshot:{...scope,revisions:{...revs},source_revision:'a'.repeat(64),
      snapshot_ref:'a'.repeat(64),
      ownership_evidence_state:'UNVERIFIED',
      delegation_evidence_state:'UNVERIFIED'},
    ...flags
  };
}
function rejected(x) {
  assert.equal(x.decision,'DENIED');
  assert.equal(x.production_authorized,false);
  assert.equal(x.send_authorized,false);
  assert.equal(x.graph_authorized,false);
  assert.equal(x.ack_allowed,false);
  assert.equal(x.s0_proof_verified_by_adapter,false);
  assert.equal(x.legacy_wa04a_directly_compatible,false);
  assert.equal(x.legacy_wa09_directly_compatible,false);
  assert.equal(JSON.stringify(x).includes('200001'),false);
  assert.equal('slot_ref' in x,false);
  assert.ok(Object.isFrozen(x));
}
function safelyMatched(x) {
  assert.equal(x.decision,'LAB_SCOPE_MATCHED_UNVERIFIED');
  assert.equal(x.reason,'SCOPED_SHAPE_MATCHED');
  assert.equal(x.route_revision,1);
  assert.equal(x.app_revision,1);
  assert.equal(x.binding_revision,1);
  assert.equal(x.grant_revision,1);
  assert.equal(x.principal_revision,1);
  assert.equal(x.production_authorized,false);
  assert.equal(x.send_authorized,false);
  assert.equal(x.ack_allowed,false);
  assert.equal(x.s0_proof_verified_by_adapter,false);
  assert.equal(x.provider_ownership_verified,false);
  assert.equal(x.delegation_verified,false);
  assert.equal(x.m2m_operationally_verified,false);
  assert.equal(x.legacy_wa04a_directly_compatible,false);
  assert.equal(x.legacy_wa09_directly_compatible,false);
  assert.ok(Object.isFrozen(x));
  assert.equal(JSON.stringify(x).includes('slot'),false);
}

test('S0M09-META-01 scoped full five-revision match is audit-only',()=>{
  safelyMatched(inspect(fixture(),scope,revs));
});
test('S0M09-META-02 never infer a legacy slot for GET/POST/Graph',()=>{
  for(const p of ['GET_VERIFY_TOKEN','POST_APP_SECRET','GRAPH_ACCESS_TOKEN']){
    const x=inspect(fixture(),scope,revs,p);
    rejected(x);assert.equal(x.reason,'LEGACY_PURPOSE_NOT_SUPPORTED');
  }
});
test('S0M09-META-03 forged source cannot elevate authority even when matching all fields',()=>{
  const x=fixture();
  safelyMatched(inspect(x,scope,revs));
  assert.equal('m2m_verified' in inspect(x,scope,revs),false);
});
test('S0M09-META-04 revoked, stale, denied, unavailable sources fail closed',()=>{
  for(const decision of ['DENIED','STALE_OR_REVOKED','UNAVAILABLE',
                         'PHYSICAL_REGISTRY_LAB_ONLY','SNAPSHOT_CANDIDATE_ONLY']){
    const x=fixture();x.decision=decision;
    rejected(inspect(x,scope,revs));
  }
});
test('S0M09-META-05 exact store, route, app, channel, WABA and sender all required',()=>{
  for(const k of Object.keys(scope)){
    const expected={...scope,[k]:k==='phone_number_id'?'99999999':'FORGED'};
    const x=inspect(fixture(),expected,revs);
    rejected(x); assert.equal(x.reason,'SCOPE_MISMATCH');
  }
});
test('S0M09-META-06 version independence, not singular WA expected_revision',()=>{
  for(const k of Object.keys(revs)){
    const x=inspect(fixture(),scope,{...revs,[k]:2});
    rejected(x); assert.equal(x.reason,'STALE_REVISION');
  }
});
test('S0M09-META-07 purpose is not sender authority and no hidden grant fields',()=>{
  const x=fixture();
  x.snapshot.send_authorized=true;
  rejected(inspect(x,scope,revs));
  const y=inspect(fixture(),scope,revs);
  safelyMatched(y);
  assert.equal('trusted_meta_registry' in y,false);
  assert.equal('secret_slots' in y,false);
});
test('S0M09-META-08 no shadow App store or unknown snapshot fields',()=>{
  const x=fixture();x.snapshot.shadow_app='APP_B';
  rejected(inspect(x,scope,revs));
});
test('S0M09-META-09 denied on true authority flags anywhere',()=>{
  for(const k of Object.keys(flags)){
    const x=fixture();x[k]=true;
    rejected(inspect(x,scope,revs));
  }
});
test('S0M09-META-10 no source acceptance without identity of contract and reason',()=>{
  for(const key of ['contract_version','decision','reason']){
    const x=fixture();x[key]='NOT_VERIFIED';
    rejected(inspect(x,scope,revs));
  }
});
test('S0M09-META-11 source has to keep ownership unverified',()=>{
  const x=fixture();x.snapshot.ownership_evidence_state='VERIFIED';
  rejected(inspect(x,scope,revs));
  const y=fixture();y.snapshot.delegation_evidence_state='VERIFIED';
  rejected(inspect(y,scope,revs));
});
test('S0M09-META-12 source_revision and snapshot_ref must agree and be SHA256 syntax',()=>{
  const x=fixture();x.snapshot.source_revision='b'.repeat(64);
  rejected(inspect(x,scope,revs));
  const y=fixture();y.snapshot.source_revision='not-a-hash';
  rejected(inspect(y,scope,revs));
});
test('S0M09-META-13 reject stale, float, unsafe, null, boolean versions',()=>{
  for(const value of [0,-1,1.5,Number.MAX_SAFE_INTEGER+1,null,true,'1']){
    const x=fixture();x.snapshot.revisions.grant=value;
    rejected(inspect(x,scope,revs));
  }
});
test('S0M09-META-14 rejects extra, missing, symbol, inherited and non-data fields',()=>{
  const x=fixture();x.extra_field='TOKEN';
  rejected(inspect(x,scope,revs));
  const y=fixture();delete y.snapshot.grant;
  rejected(inspect(y,scope,revs)); // no extraneous property required
  const z=Object.assign(Object.create({inherited:true}),fixture());
  rejected(inspect(z,scope,revs));
  const w=fixture();w[Symbol('secret')]='token';
  rejected(inspect(w,scope,revs));
});
test('S0M09-META-15 getters never execute during snapshot',()=>{
  let hits=0;
  const x=fixture();
  Object.defineProperty(x.snapshot,'route_ref',{
    enumerable:true,get(){hits++;throw Error('poison');}
  });
  rejected(inspect(x,scope,revs));
  assert.equal(hits,0);
});
test('S0M09-META-16 proxies and throwing reflection are sanitized',()=>{
  const x = new Proxy(fixture(),{ownKeys(){throw Error('malicious');}});
  rejected(inspect(x,scope,revs));
});
test('S0M09-META-17 no input mutation',()=>{
  const x=fixture(),before=JSON.stringify([x,scope,revs]);
  safelyMatched(inspect(x,scope,revs));
  assert.equal(JSON.stringify([x,scope,revs]),before);
});
test('S0M09-META-18 wrong expected scope shape refuses to guess',()=>{
  rejected(inspect(fixture(),{...scope,secret_slot:'FAKE'},revs));
  rejected(inspect(fixture(),scope,{...revs,expected_revision:1}));
});
test('S0M09-META-19 source must not reveal secret slots',()=>{
  const x=fixture();x.snapshot.slot_ref='GRAPH_TOKEN_SLOT';
  rejected(inspect(x,scope,revs));
});
test('S0M09-META-20 all audit outputs scrub technical identifiers',()=>{
  const x=inspect(fixture(),scope,revs);
  for(const value of [scope.app_ref,scope.route_ref,scope.canal_id,
                      scope.waba_id,scope.phone_number_id]) {
    assert.equal(JSON.stringify(x).includes(value),false);
  }
});

const pinned=process.env.M09_META_PIN;
test('S0M09-META-21 exact original WA04A refuses direct M09 projection',
  {skip:!pinned},async()=>{
  const file=pathToFileURL(resolve(pinned,'integrations/whatsapp-meta/credential-routing.ts')).href;
  const {selectMetaCredential,resolveSignedMetaChannel}=await import(file);
  const response=fixture();
  // The original WA04A expects 3 slot refs in TrustedMetaRegistry, which
  // M09 MUST NOT supply. Passing its full response must fail closed.
  const first=selectMetaCredential(response,{
    purpose:'POST_APP_SECRET',trusted_route_ref:scope.route_ref,
    at_ms:100,expected_revision:1
  });
  assert.equal(first.ok,false);
  assert.equal(first.production_authorized,false);
  const second=resolveSignedMetaChannel(response,{
    trusted_route_ref:scope.route_ref,authenticated_app_ref:scope.app_ref,
    waba_id:scope.waba_id,phone_number_id:scope.phone_number_id,
    at_ms:100,expected_revision:1
  });
  assert.equal(second.ok,false);
});
test('S0M09-META-22 original WA09 refuses M09 as a legacy registry',
  {skip:!pinned},async()=>{
  const file=pathToFileURL(resolve(pinned,'integrations/whatsapp-meta/wa09-asset-onboarding-audit.ts')).href;
  const {inspectWa09OfflineAssetInventory}=await import(file);
  const e={contract_version:'wa09-s0-asset-expectation.fixture.v0.1',apps:[{
    ...{app_ref:scope.app_ref,route_ref:scope.route_ref,
        concessionaria_id:scope.concessionaria_id,
        business_owner_ref:'BUSINESS_A',delegated_partner_ref:'PARTNER_A',
        revision:1,wabas:[{waba_id:scope.waba_id,catalog_ref:'CAT_A',
                            phone_number_ids:[scope.phone_number_id]}]},
    s0_bindings:[{canal_id:scope.canal_id,waba_id:scope.waba_id,
                   phone_number_id:scope.phone_number_id}]
  }]};
  const o={contract_version:'wa09-meta-assets.fixture.v0.1',
    apps:e.apps.map(({s0_bindings,...rest})=>rest)};
  const decision=inspectWa09OfflineAssetInventory(fixture(),e,o,100);
  assert.equal(decision.decision,'DENIED');
  assert.equal(decision.provider_ownership_verified,false);
  assert.equal(decision.onboarding_approved,false);
  assert.equal(decision.production_authorized,false);
});
test('S0M09-META-23 exact Meta WA04A still works with its OLD synthetic fixture',
  {skip:!pinned},async()=>{
    const file=pathToFileURL(resolve(pinned,'integrations/whatsapp-meta/credential-routing.ts')).href;
    const {selectMetaCredential}=await import(file);
    const at_ms=1000;
    const registry={
      contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[{
        app_ref:'APP_A',route_ref:'route_A',concessionaria_id:'store-A',
        active:true,revision:1,valid_from_ms:900,valid_until_ms:1200,
        secret_slots:{get_verify_token:'GET_SLOT_A',post_app_secret:'POST_SLOT_A',
                      graph_access_token:'GRAPH_SLOT_A'},
        channels:[{canal_id:'channel_A',waba_id:'100001',
                   phone_number_id:'200001',active:true}],
      }]};
    const out=selectMetaCredential(registry,{
      purpose:'POST_APP_SECRET',trusted_route_ref:'route_A',
      at_ms,expected_revision:1
    });
    assert.equal(out.ok,true);
    assert.equal(out.production_authorized,false);
    // This verifies only the old Meta fixture continues to operate offline.
    assert.equal(out.secret_slot,'POST_SLOT_A');
});

test('S0M09-META-24 real PG17 synthetic signed-read evidence matches safely',
  {skip:!process.env.M09_BRIDGE_EVIDENCE},async()=>{
  const raw=JSON.parse(await readFile(process.env.M09_BRIDGE_EVIDENCE,'utf8'));
  safelyMatched(inspect(raw,scope,revs));
  assert.equal(raw.decision,'AUTHENTICATED_READ_LAB_ONLY');
  const legacy=inspect(raw,scope,revs,'POST_APP_SECRET');
  rejected(legacy);
});
