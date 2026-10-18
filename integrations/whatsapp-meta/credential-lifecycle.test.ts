import { test } from 'node:test';
import assert from 'node:assert/strict';
import { planMetaLifecycleTransition } from './credential-lifecycle.ts';
import { selectMetaCredential, type TrustedMetaRegistry } from './credential-routing.ts';
const NOW = 1792320000000;
const appA={app_ref:'APP_A',route_ref:'ROUTE_A',concessionaria_id:'STORE_A',active:true,
 revision:4,valid_from_ms:NOW-10000,valid_until_ms:NOW+10000,
 secret_slots:{get_verify_token:'META_A_GET',post_app_secret:'META_A_HMAC',graph_access_token:'META_A_GRAPH'},
 channels:[{canal_id:'CANAL_A',waba_id:'WABA_A',phone_number_id:'12345678901',active:true}]};
const appB={...appA,app_ref:'APP_B',route_ref:'ROUTE_B',concessionaria_id:'STORE_B',revision:2,
 secret_slots:{get_verify_token:'META_B_GET',post_app_secret:'META_B_HMAC',graph_access_token:'META_B_GRAPH'},
 channels:[{canal_id:'CANAL_B',waba_id:'WABA_B',phone_number_id:'98765432101',active:true}]};
const registry:TrustedMetaRegistry={contract_version:'wa-meta-credential-routing.v0.1-proposed',apps:[appA,appB]};
const common={app_ref:'APP_A',concessionaria_id:'STORE_A',expected_revision:4,at_ms:NOW,operation_ref:'FIXTURE_OP_1'};
const run=(r:unknown)=>planMetaLifecycleTransition(registry,r as Parameters<typeof planMetaLifecycleTransition>[1]);
const rotated={get_verify_token:'NEW_A_GET',post_app_secret:'NEW_A_HMAC',graph_access_token:'NEW_A_GRAPH'};
test('LIFE-01 revoke App creates inactive *proposal*, not a real action',()=>{
 const r=run({...common,action:'REVOKE_APP'});assert.equal(r.ok,true);
 if(!r.ok)return;
 assert.equal(r.proposal_only,true);assert.equal(r.production_authorized,false);
 assert.equal(r.candidate_registry.apps[0].active,false);assert.equal(r.next_revision,5);
 assert.equal(selectMetaCredential(r.candidate_registry,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',at_ms:NOW,expected_revision:5}).ok,false);
});
test('LIFE-02 independent concessionaria B stays unchanged',()=>{
 const r=run({...common,action:'REVOKE_APP'});assert.equal(r.ok,true);
 if(r.ok)assert.deepEqual(r.candidate_registry.apps[1],appB);
});
test('LIFE-03 revoke channel blocks Graph while App itself stays enabled',()=>{
 const r=run({...common,action:'REVOKE_CHANNEL',canal_id:'CANAL_A'});assert.equal(r.ok,true);
 if(!r.ok)return;
 assert.equal(r.candidate_registry.apps[0].channels[0].active,false);
 assert.equal(r.candidate_registry.apps[0].active,true);
 assert.equal(selectMetaCredential(r.candidate_registry,{purpose:'GRAPH_ACCESS_TOKEN',
 trusted_scope:{app_ref:'APP_A',concessionaria_id:'STORE_A',canal_id:'CANAL_A',waba_id:'WABA_A',phone_number_id:'12345678901'},
 at_ms:NOW,expected_revision:5}).ok,false);
});
test('LIFE-04 staged rotation makes App inactive until external verification',()=>{
 const r=run({...common,action:'STAGE_ROTATION',next_secret_slots:rotated});assert.equal(r.ok,true);
 if(!r.ok)return;
 assert.equal(r.external_token_verification_pending,true);
 assert.equal(r.candidate_registry.apps[0].active,false);
 assert.deepEqual(r.candidate_registry.apps[0].secret_slots,rotated);
});
test('LIFE-05 no mutation of original input',()=>{
 const before=JSON.stringify(registry);
 run({...common,action:'STAGE_ROTATION',next_secret_slots:rotated});
 assert.equal(JSON.stringify(registry),before);
});
test('LIFE-06 a forged store claim fails closed',()=>{
 const r=run({...common,concessionaria_id:'STORE_B',action:'REVOKE_APP'});
 assert.deepEqual(r,{ok:false,production_authorized:false,reason:'SCOPE_MISMATCH'});
});
test('LIFE-07 old or future revisions cannot propose changes',()=>{
 for(const expected_revision of [3,5])assert.equal(run({...common,expected_revision,action:'REVOKE_APP'}).ok,false);
});
test('LIFE-08 unknown or disabled App cannot be acted upon by this candidate',()=>{
 assert.equal(run({...common,app_ref:'APP_UNKNOWN',action:'REVOKE_APP'}).ok,false);
 const inactive={...registry,apps:[{...appA,active:false},appB]};
 assert.equal(planMetaLifecycleTransition(inactive,{...common,action:'REVOKE_APP'}).ok,false);
});
test('LIFE-09 missing, reserved and duplicated secret references reject rotation',()=>{
 for(const slots of [{...rotated,post_app_secret:'META_B_HMAC'},
   {...rotated,get_verify_token:'SUPABASE_FORBIDDEN'},
   {...rotated,post_app_secret:rotated.get_verify_token},
   {...rotated,graph_access_token:''},null]){
  const r=run({...common,action:'STAGE_ROTATION',next_secret_slots:slots});
  assert.equal(r.ok,false);if(!r.ok)assert.equal(r.reason,'INVALID_NEW_SLOTS');
 }
});
test('LIFE-10 unknown/disabled channel refuses instead of changing any unrelated channel',()=>{
 for(const canal_id of ['OTHER','../CANAL_A']){
  const r=run({...common,action:'REVOKE_CHANNEL',canal_id});assert.equal(r.ok,false);
 }
});
test('LIFE-11 time expired and malformed metadata refuse',()=>{
 for(const request of [{...common,at_ms:NOW+10000,action:'REVOKE_APP'},
  {...common,operation_ref:'../bad',action:'REVOKE_APP'},
  {...common,at_ms:Number.NaN,action:'REVOKE_APP'},
  {...common,expected_revision:Number.MAX_SAFE_INTEGER,action:'REVOKE_APP'},
  {...common,action:'ENABLE_APP'}])assert.equal(run(request).ok,false);
});
test('LIFE-12 original credential reference remains usable only in unchanged fixture',()=>{
 const active=selectMetaCredential(registry,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',at_ms:NOW,expected_revision:4});
 assert.equal(active.ok,true);
 const revoked=run({...common,action:'REVOKE_APP'});assert.equal(revoked.ok,true);
 if(revoked.ok)assert.equal(selectMetaCredential(revoked.candidate_registry,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',at_ms:NOW,expected_revision:4}).ok,false);
});
test('LIFE-13 no reactivation path or token value leaves this laboratory',()=>{
 for(const r of [run({...common,action:'REVOKE_APP'}),run({...common,action:'STAGE_ROTATION',next_secret_slots:rotated})]){
  assert.equal(r.ok,true);
  assert.equal(JSON.stringify(r).includes('Bearer'),false);
  assert.equal(JSON.stringify(r).includes('production_authorized":true'),false);
 }
});
