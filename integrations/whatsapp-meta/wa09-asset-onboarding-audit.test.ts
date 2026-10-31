/** WA09 offline reconciliation regressions. No Meta, S0, HTTP, or secrets. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectWa09OfflineAssetInventory as inspect} from './wa09-asset-onboarding-audit.ts';
import type {TrustedMetaRegistry} from './credential-routing.ts';

const NOW=1792320000000;
const appA={
 app_ref:'APP_A',concessionaria_id:'STORE_A',route_ref:'ROUTE_A',
 business_owner_ref:'BUSINESS_A',delegated_partner_ref:'PRUMO_PARTNER',
 revision:4,wabas:[{waba_id:'WABA_A',catalog_ref:'CAT_A',
   phone_number_ids:['12345678901','12345678902']}],
 s0_bindings:[
  {canal_id:'CHAN_A1',waba_id:'WABA_A',phone_number_id:'12345678901'},
  {canal_id:'CHAN_A2',waba_id:'WABA_A',phone_number_id:'12345678902'},
 ],
};
const appB={
 app_ref:'APP_B',concessionaria_id:'STORE_B',route_ref:'ROUTE_B',
 business_owner_ref:'BUSINESS_B',delegated_partner_ref:'PRUMO_PARTNER',
 revision:2,wabas:[{waba_id:'WABA_B',catalog_ref:'CAT_B',
   phone_number_ids:['99999999999']}],
 s0_bindings:[{canal_id:'CHAN_B1',waba_id:'WABA_B',
   phone_number_id:'99999999999'}],
};
const secret=(name:string)=>({
 get_verify_token:name+'_VERIFY',post_app_secret:name+'_HMAC',
 graph_access_token:name+'_GRAPH',
});
const registry:TrustedMetaRegistry={
 contract_version:'wa-meta-credential-routing.v0.1-proposed',
 apps:[
  {app_ref:'APP_A',concessionaria_id:'STORE_A',route_ref:'ROUTE_A',
   active:true,revision:4,valid_from_ms:NOW-1000,valid_until_ms:NOW+1000,
   secret_slots:secret('WA_APP_A'),channels:[
    {canal_id:'CHAN_A1',waba_id:'WABA_A',phone_number_id:'12345678901',active:true},
    {canal_id:'CHAN_A2',waba_id:'WABA_A',phone_number_id:'12345678902',active:true},
   ]},
  {app_ref:'APP_B',concessionaria_id:'STORE_B',route_ref:'ROUTE_B',
   active:true,revision:2,valid_from_ms:NOW-1000,valid_until_ms:NOW+1000,
   secret_slots:secret('WA_APP_B'),channels:[
    {canal_id:'CHAN_B1',waba_id:'WABA_B',phone_number_id:'99999999999',active:true},
   ]},
 ],
};
const expected=()=>({
 contract_version:'wa09-s0-asset-expectation.fixture.v0.1',
 apps:structuredClone([appA,appB]),
});
const observed=()=>({
 contract_version:'wa09-meta-assets.fixture.v0.1',
 apps:structuredClone([appA,appB].map(({s0_bindings,...provider})=>provider)),
});
const run=(s:unknown=expected(),p:unknown=observed(),reg=registry,now=NOW)=>
 inspect(reg,s,p,now);
const denied=(result:ReturnType<typeof run>)=>{
 assert.equal(result.decision,'DENIED');
 assert.equal(result.provider_ownership_verified,false);
 assert.equal(result.delegation_verified,false);
 assert.equal(result.s0_principal_verified,false);
 assert.equal(result.onboarding_approved,false);
 assert.equal(result.production_authorized,false);
 assert.equal(result.send_authorized,false);
 assert.equal(result.ack_allowed,false);
 assert.equal(result.s0_write_authorized,false);
 assert.equal(result.app_count,0);
 assert.equal(result.channel_count,0);
 assert.equal(Object.isFrozen(result),true);
 assert.equal('secret_slots' in result,false);
};
test('WA09-01 two shops have private Apps, WABAs, catalogs and delegated partner fixtures',()=>{
 const x=run();
 assert.deepEqual(x,{
  decision:'LAB_INVENTORY_MATCHED_UNVERIFIED',reason:'MATCHED_FIXTURES',
  app_count:2,waba_count:2,channel_count:3,catalog_count:2,
  provider_ownership_verified:false,delegation_verified:false,
  s0_principal_verified:false,onboarding_approved:false,
  production_authorized:false,send_authorized:false,
  ack_allowed:false,s0_write_authorized:false,
 });
 assert.ok(Object.isFrozen(x));
});
test('WA09-02 fixture success cannot claim provider ownership or S0 authorization',()=>{
 const x=run();
 assert.equal(JSON.stringify(x).includes('verified":true'),false);
 assert.equal('status' in x,false);
 assert.equal('action' in x,false);
});
test('WA09-03 mismatched dealership denied',()=>{
 const o=observed();o.apps[0].concessionaria_id='STORE_B';denied(run(expected(),o));
});
test('WA09-04 Meta App owner mismatch denied',()=>{
 const o=observed();o.apps[0].business_owner_ref='OTHER_OWNER';denied(run(expected(),o));
});
test('WA09-05 delegation identifier mismatch denied',()=>{
 const o=observed();o.apps[0].delegated_partner_ref='PARTNER_OTHER';denied(run(expected(),o));
});
test('WA09-06 missing partner reference denied',()=>{
 const o=observed();o.apps[0].delegated_partner_ref='';denied(run(expected(),o));
});
test('WA09-07 duplicate App record rejected globally',()=>{
 const o=observed();o.apps.push({...o.apps[0]});
 const x=run(expected(),o);denied(x);
});
test('WA09-08 duplicate WABA across shops rejected globally',()=>{
 const o=observed();o.apps[1].wabas[0].waba_id='WABA_A';
 denied(run(expected(),o));
});
test('WA09-09 duplicate phone within one WABA rejected globally',()=>{
 const o=observed();o.apps[0].wabas[0].phone_number_ids[1]='12345678901';
 denied(run(expected(),o));
});
test('WA09-10 same catalog may not span two independent shops',()=>{
 const o=observed();o.apps[1].wabas[0].catalog_ref='CAT_A';
 denied(run(expected(),o));
});
test('WA09-11 fake external asset not in S0 expectation rejected',()=>{
 const o=observed();o.apps.push({...appB,app_ref:'APP_C',route_ref:'ROUTE_C',
 business_owner_ref:'BUSINESS_C',wabas:[{waba_id:'WABA_C',catalog_ref:'CAT_C',
 phone_number_ids:['77777777777']}]});
 denied(run(expected(),o));
});
test('WA09-12 omitted asset is not silently accepted',()=>{
 const o=observed();o.apps.pop();denied(run(expected(),o));
});
test('WA09-13 changed catalog reference rejects',()=>{
 const o=observed();o.apps[0].wabas[0].catalog_ref='CAT_INVALID';
 denied(run(expected(),o));
});
test('WA09-14 changed phone identity rejects',()=>{
 const o=observed();o.apps[0].wabas[0].phone_number_ids[0]='44444444444';
 denied(run(expected(),o));
});
test('WA09-15 changed App route rejects',()=>{
 const o=observed();o.apps[0].route_ref='ROUTE_B';denied(run(expected(),o));
});
test('WA09-16 stale S0 expected revision rejects',()=>{
 const e=expected();e.apps[0].revision=3;denied(run(e));
});
test('WA09-17 stale provider fixture revision rejects',()=>{
 const o=observed();o.apps[0].revision=3;denied(run(expected(),o));
});
test('WA09-18 App revoked in trusted registry rejects',()=>{
 const r=structuredClone(registry);r.apps[0].active=false;denied(run(expected(),observed(),r));
});
test('WA09-19 channel revoked in trusted registry rejects',()=>{
 const r=structuredClone(registry);r.apps[0].channels[1].active=false;
 denied(run(expected(),observed(),r));
});
test('WA09-20 changed channel owner in registry rejects',()=>{
 const r=structuredClone(registry);r.apps[0].channels[0].waba_id='WABA_B';
 denied(run(expected(),observed(),r));
});
test('WA09-21 hidden extra channel in registry rejects',()=>{
 const r=structuredClone(registry);r.apps[0].channels.push({
 canal_id:'CHAN_A3',waba_id:'WABA_A',phone_number_id:'55555555555',active:false});
 denied(run(expected(),observed(),r));
});
test('WA09-22 inactive or expired App denies',()=>{
 for(const now of [NOW-1000-1,NOW+1000])denied(run(expected(),observed(),registry,now));
});
test('WA09-23 all apps and catalogs required',()=>{
 const e=expected();e.apps[0].wabas=[];denied(run(e));
});
test('WA09-24 duplicate target in S0 fixture rejected',()=>{
 const e=expected();e.apps[1].wabas[0].phone_number_ids[0]='12345678901';
 denied(run(e));
});
test('WA09-25 wrong fixture schema fails closed',()=>{
 const e=expected();e.contract_version='other';denied(run(e));
});
test('WA09-26 unknown extra property cannot smuggle token or attestation flag',()=>{
 const o=observed();Object.assign(o.apps[0],{access_token:'secret'});
 denied(run(expected(),o));
});
test('WA09-27 unexpected nested field fails closed',()=>{
 const o=observed();Object.assign(o.apps[0].wabas[0],{provider_ownership_verified:true});
 denied(run(expected(),o));
});
test('WA09-28 accessor cannot execute during snapshot',()=>{
 const o=observed();let hits=0;
 Object.defineProperty(o.apps[0],'delegated_partner_ref',{
 enumerable:true,get(){hits++;throw Error('untrusted');}});
 denied(run(expected(),o));
 assert.equal(hits,0);
});
test('WA09-29 malicious top-level proxy fails closed',()=>{
 const x=run(new Proxy(expected(),{ownKeys(){throw Error('trap');}}));
 denied(x);
});
test('WA09-30 unknown registry type fails closed',()=>{
 denied(run(expected(),observed(),{
  ...registry,contract_version:'unsupported' as TrustedMetaRegistry['contract_version']}));
});
test('WA09-31 invalid host clock fails closed',()=>{
 denied(run(expected(),observed(),registry,Number.NaN));
});
test('WA09-32 a legitimate re-ordered fixture is order-independent',()=>{
 const e=expected(),o=observed();
 o.apps.reverse();o.apps[1].wabas[0].phone_number_ids.reverse();
 const x=run(e,o);assert.equal(x.decision,'LAB_INVENTORY_MATCHED_UNVERIFIED');
 assert.equal(x.production_authorized,false);
});
test('WA09-33 no input mutation or leaked business identifiers',()=>{
 const e=expected(),o=observed(),before=JSON.stringify([e,o,registry]);
 const x=run(e,o);
 assert.equal(JSON.stringify([e,o,registry]),before);
 const text=JSON.stringify(x);
 for(const value of ['BUSINESS_A','PRUMO_PARTNER','WA_APP_A_GRAPH',
  '12345678901','CAT_A'])assert.equal(text.includes(value),false);
});


test('WA09-34 wrong S0 canal_id on known Meta phone pair denied',()=>{
 const e=expected();e.apps[0].s0_bindings[0].canal_id='CHAN_OTHER';
 denied(run(e));
});
test('WA09-35 duplicate S0 canal_id under different phone denied',()=>{
 const e=expected();e.apps[0].s0_bindings[1].canal_id='CHAN_A1';
 denied(run(e));
});
test('WA09-36 same Meta Business owner cannot represent two shops',()=>{
 const o=observed();o.apps[1].business_owner_ref='BUSINESS_A';
 denied(run(expected(),o));
});
test('WA09-37 missing S0 mapping fails even when provider phone matches',()=>{
 const e=expected();e.apps[0].s0_bindings.pop();
 denied(run(e));
});
test('WA09-38 provider cannot invent canal_id as proof of S0 grant',()=>{
 const o=observed();
 Object.assign(o.apps[0],{s0_bindings:[{
   canal_id:'CHAN_A1',waba_id:'WABA_A',phone_number_id:'12345678901'}]});
 denied(run(expected(),o));
});
