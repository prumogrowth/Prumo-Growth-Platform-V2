import { test } from 'node:test';
import assert from 'node:assert/strict';
import { selectMetaCredential, resolveSignedMetaChannel,
  type TrustedMetaRegistry, type TrustedMetaScope } from './credential-routing.ts';
const now = 1792320000000;
const appA = {
  app_ref: 'APP_A', route_ref: 'ROUTE_A', concessionaria_id: 'SHOP_A', active: true,
  revision: 4, valid_from_ms: now - 5000, valid_until_ms: now + 5000,
  secret_slots: {get_verify_token: 'WA_META_A_VERIFY', post_app_secret: 'WA_META_A_HMAC',
    graph_access_token: 'WA_META_A_GRAPH'},
  channels: [{canal_id: 'CHAN_A', waba_id: 'WABA_A', phone_number_id: '12345678901', active: true}],
};
const appB = {
  ...appA, app_ref: 'APP_B', route_ref: 'ROUTE_B', concessionaria_id: 'SHOP_B', revision: 2,
  secret_slots: {get_verify_token: 'WA_META_B_VERIFY', post_app_secret: 'WA_META_B_HMAC',
    graph_access_token: 'WA_META_B_GRAPH'},
  channels: [{canal_id: 'CHAN_B', waba_id: 'WABA_B', phone_number_id: '99999999999', active: true}],
};
const reg: TrustedMetaRegistry = {contract_version: 'wa-meta-credential-routing.v0.1-proposed', apps: [appA, appB]};
const scope: TrustedMetaScope = {app_ref: 'APP_A', concessionaria_id: 'SHOP_A',
  canal_id: 'CHAN_A', waba_id: 'WABA_A', phone_number_id: '12345678901'};
const get = (route = 'ROUTE_A', purpose: 'GET_VERIFY_TOKEN' | 'POST_APP_SECRET' = 'GET_VERIFY_TOKEN', registry = reg) =>
  selectMetaCredential(registry,{purpose,trusted_route_ref:route,at_ms:now,expected_revision:4});
const graph = (trusted_scope:TrustedMetaScope = scope, registry=reg) =>
  selectMetaCredential(registry,{purpose:'GRAPH_ACCESS_TOKEN',trusted_scope,at_ms:now,expected_revision:4});
const signed = (registry=reg) => resolveSignedMetaChannel(registry,{
  trusted_route_ref:'ROUTE_A',authenticated_app_ref:'APP_A',waba_id:'WABA_A',
  phone_number_id:'12345678901',at_ms:now,expected_revision:4});

test('WA-CRED-01 routes GET by trusted route, never by query token',()=>{
  assert.deepEqual(get(),{ok:true,app_ref:'APP_A',purpose:'GET_VERIFY_TOKEN',
    secret_slot:'WA_META_A_VERIFY',revision:4,production_authorized:false});
});
test('WA-CRED-02 GET and POST use different secret slots',()=>{
  const a=get(),b=get('ROUTE_A','POST_APP_SECRET');
  assert.equal(b.ok,true); if(a.ok && b.ok)assert.notEqual(a.secret_slot,b.secret_slot);
});
test('WA-CRED-03 valid outbound selection returns slot name, not secret value',()=>{
  const r=graph(); assert.equal(r.ok,true);if(r.ok)assert.equal(r.secret_slot,'WA_META_A_GRAPH');
  assert.equal('token' in r,false);assert.equal(r.production_authorized,false);
});
test('WA-CRED-04 two Apps remain isolated with unrelated secret names',()=>{
  const r=selectMetaCredential(reg,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_B',
    at_ms:now,expected_revision:2});
  assert.equal(r.ok,true);if(r.ok)assert.equal(r.secret_slot,'WA_META_B_HMAC');
});
test('WA-CRED-05 wrong trusted route refuses instead of inferring App from body',()=>{
  assert.deepEqual(get('ROUTE_WRONG'),{ok:false,reason:'NO_MATCH',production_authorized:false});
});
test('WA-CRED-06 disabled App never supplies credentials',()=>{
  assert.equal(get('ROUTE_A','GET_VERIFY_TOKEN',{...reg,apps:[{...appA,active:false},appB]}).ok,false);
});
test('WA-CRED-07 future and expired slots deny both inbound and outbound',()=>{
  for(const at_ms of [now-5000-1,now+5000]){
    assert.equal(selectMetaCredential(reg,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',
      at_ms,expected_revision:4}).ok,false);
    assert.equal(selectMetaCredential(reg,{purpose:'GRAPH_ACCESS_TOKEN',trusted_scope:scope,
      at_ms,expected_revision:4}).ok,false);
  }
});
test('WA-CRED-08 stale revision denies requests after credential rotation',()=>{
  const r=selectMetaCredential(reg,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',
    at_ms:now,expected_revision:3});
  assert.equal(r.ok,false);if(!r.ok)assert.equal(r.reason,'STALE_REVISION');
});
test('WA-CRED-09 forged shop, channel, WABA, sender or app denied for Graph',()=>{
  for(const k of ['concessionaria_id','canal_id','waba_id','phone_number_id','app_ref'] as const){
    const s={...scope,[k]:k==='phone_number_id'?'11111111111':'FORGED'};
    assert.equal(graph(s).ok,false);
  }
});
test('WA-CRED-10 disabled channel denies Graph and post-HMAC mapping',()=>{
  const registry={...reg,apps:[{...appA,channels:appA.channels.map(c=>({...c,active:false}))},appB]};
  assert.equal(graph(scope,registry).ok,false);assert.equal(signed(registry).ok,false);
});
test('WA-CRED-11 POST scope resolves only after claimed authenticated App/route match',()=>{
  const s=signed();assert.equal(s.ok,true);
  if(s.ok)assert.deepEqual(s.scope,scope);
  const bad=resolveSignedMetaChannel(reg,{trusted_route_ref:'ROUTE_A',
    authenticated_app_ref:'APP_B',waba_id:'WABA_A',phone_number_id:'12345678901',
    at_ms:now,expected_revision:4});assert.equal(bad.ok,false);
});
test('WA-CRED-12 duplicate App or trusted route makes entire registry invalid',()=>{
  for(const extra of [{...appA}, {...appA,app_ref:'APP_C'}, {...appA,route_ref:'ROUTE_C'}]){
    const r=get('ROUTE_A','GET_VERIFY_TOKEN',{...reg,apps:[...reg.apps,extra]});
    assert.equal(r.ok,false); if(!r.ok)assert.equal(r.reason,'INVALID_REGISTRY');
  }
});
test('WA-CRED-13 same WABA+sender claimed twice fails closed',()=>{
  const collision={...appB,channels:[{...appB.channels[0],waba_id:'WABA_A',phone_number_id:'12345678901'}]};
  assert.equal(get('ROUTE_A','GET_VERIFY_TOKEN',{...reg,apps:[appA,collision]}).ok,false);
});
test('WA-CRED-14 duplicated secret alias across Apps or purposes fails closed',()=>{
  const registry={...reg,apps:[appA,{...appB,secret_slots:{...appB.secret_slots,
    graph_access_token:appA.secret_slots.post_app_secret}}]};
  assert.equal(get('ROUTE_A','POST_APP_SECRET',registry).ok,false);
});
test('WA-CRED-15 malformed secret name and reserved SUPABASE prefix reject',()=>{
  for(const name of ['SUPABASE_FORBIDDEN','bad-key','']){
    const registry={...reg,apps:[{...appA,secret_slots:{...appA.secret_slots,graph_access_token:name}},appB]};
    assert.equal(graph(scope,registry).ok,false);
  }
});
test('WA-CRED-16 empty, malformed, or inconsistent registry rejects',()=>{
  assert.equal(get('ROUTE_A','GET_VERIFY_TOKEN',{...reg,contract_version:'other' as TrustedMetaRegistry['contract_version']}).ok,false);
  assert.equal(get('ROUTE_A','GET_VERIFY_TOKEN',{...reg,apps:null as unknown as TrustedMetaRegistry['apps']}).ok,false);
  assert.equal(get('ROUTE_A','GET_VERIFY_TOKEN',{...reg,apps:[{...appA,revision:0},appB]}).ok,false);
});
test('WA-CRED-17 missing channel or WABA never produces post-HMAC tenant',()=>{
  const bad=resolveSignedMetaChannel(reg,{trusted_route_ref:'ROUTE_A',authenticated_app_ref:'APP_A',
    waba_id:'WABA_B',phone_number_id:'12345678901',at_ms:now,expected_revision:4});
  assert.equal(bad.ok,false);
});
test('WA-CRED-18 rejects invalid clock, revision, and misleading request',()=>{
  assert.equal(selectMetaCredential(reg,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',
    at_ms:NaN,expected_revision:4}).ok,false);
  assert.equal(selectMetaCredential(reg,{purpose:'POST_APP_SECRET',trusted_route_ref:'ROUTE_A',
    at_ms:now,expected_revision:0}).ok,false);
});
test('WA-CRED-19 returns no PII, access tokens, App Secret or commercial grant',()=>{
  const decisions=[get(),get('ROUTE_A','POST_APP_SECRET'),graph(),signed()];
  const json=JSON.stringify(decisions);
  for(const secret of ['Bearer','EAA','5581900000000','access_token_value','app_secret_value'])
    assert.equal(json.includes(secret),false);
  assert.equal(json.includes('production_authorized":true'),false);
});
