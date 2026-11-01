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


test('AUD-CRED-01 GET/POST/Graph slots within ONE App may never alias',()=>{
 for(const field of ['post_app_secret','graph_access_token'] as const){
  const registry={...reg,apps:[{...appA,secret_slots:{
   ...appA.secret_slots,[field]:appA.secret_slots.get_verify_token}},appB]};
  for(const purpose of ['GET_VERIFY_TOKEN','POST_APP_SECRET'] as const){
   const result=get('ROUTE_A',purpose,registry);
   assert.deepEqual(result,{ok:false,reason:'INVALID_REGISTRY',production_authorized:false});
  }
  assert.equal(graph(scope,registry).ok,false);
 }
 const registry={...reg,apps:[{...appA,secret_slots:{
  ...appA.secret_slots,graph_access_token:appA.secret_slots.post_app_secret}},appB]};
 assert.equal(get('ROUTE_A','POST_APP_SECRET',registry).ok,false);
 assert.equal(graph(scope,registry).ok,false);
});


test('AUD-GLOBAL-CRED-01 registry App getter is never invoked',()=>{
 let calls=0;
 const poisoned={...appA};
 Object.defineProperty(poisoned,'active',{enumerable:true,get(){calls++;return true;}});
 const result=get('ROUTE_A','GET_VERIFY_TOKEN',{...reg,apps:[poisoned,appB]});
 assert.equal(result.ok,false);if(!result.ok)assert.equal(result.reason,'INVALID_REGISTRY');
 assert.equal(calls,0);
});
test('AUD-GLOBAL-CRED-02 secret slot getter never resolves',()=>{
 let calls=0;
 const slots={...appA.secret_slots};
 Object.defineProperty(slots,'post_app_secret',{enumerable:true,get(){
  calls++;throw Error('GETTER_SIDE_EFFECT');}});
 const result=get('ROUTE_A','POST_APP_SECRET',
  {...reg,apps:[{...appA,secret_slots:slots},appB]});
 assert.equal(result.ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-CRED-03 channel getter never maps tenant',()=>{
 let calls=0;const ch={...appA.channels[0]};
 Object.defineProperty(ch,'active',{enumerable:true,get(){calls++;return true;}});
 const result=signed({...reg,apps:[{...appA,channels:[ch]},appB]});
 assert.equal(result.ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-CRED-04 accessor at trusted route never executes',()=>{
 let calls=0;const cmd:any={purpose:'GET_VERIFY_TOKEN',
  trusted_route_ref:'ROUTE_A',at_ms:now,expected_revision:4};
 Object.defineProperty(cmd,'trusted_route_ref',{enumerable:true,get(){
  calls++;return 'ROUTE_A';}});
 assert.equal(selectMetaCredential(reg,cmd).ok,false);
 assert.equal(calls,0);
});
test('AUD-GLOBAL-CRED-05 accessor inside Graph trusted scope never executes',()=>{
 let calls=0;const sc:any={...scope};
 Object.defineProperty(sc,'app_ref',{enumerable:true,get(){
  calls++;return 'APP_A';}});
 assert.equal(graph(sc).ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-CRED-06 accessor inside signed route query never executes',()=>{
 let calls=0;const q:any={trusted_route_ref:'ROUTE_A',
  authenticated_app_ref:'APP_A',waba_id:'WABA_A',
  phone_number_id:'12345678901',at_ms:now,expected_revision:4};
 Object.defineProperty(q,'phone_number_id',{enumerable:true,get(){
  calls++;return '12345678901';}});
 assert.equal(resolveSignedMetaChannel(reg,q).ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-CRED-07 malformed registry array element getter not read',()=>{
 let calls=0;const entries:any[]=[appA,appB];
 Object.defineProperty(entries,'0',{enumerable:true,configurable:true,get(){
  calls++;return appA;}});
 assert.equal(get('ROUTE_A','GET_VERIFY_TOKEN',{...reg,apps:entries}).ok,false);
 assert.equal(calls,0);
});
test('AUD-GLOBAL-CRED-08 extra untrusted authority field denies registry',()=>{
 const registry:any={...reg,grant_verified:true};
 const x=graph(scope,registry);assert.equal(x.ok,false);
 if(!x.ok)assert.equal(x.reason,'INVALID_REGISTRY');
});
test('AUD-GLOBAL-CRED-09 extra Graph grant field denies request',()=>{
 const cmd:any={purpose:'GRAPH_ACCESS_TOKEN',trusted_scope:scope,
  at_ms:now,expected_revision:4,send_authorized:true};
 const x=selectMetaCredential(reg,cmd);
 assert.equal(x.ok,false);if(!x.ok)assert.equal(x.reason,'INVALID_INPUT');
});
test('AUD-GLOBAL-CRED-10 safe registry still routes distinct GET/POST/Graph slots',()=>{
 const getSlot=get(),postSlot=get('ROUTE_A','POST_APP_SECRET'),graphSlot=graph();
 assert.equal(getSlot.ok,true);assert.equal(postSlot.ok,true);assert.equal(graphSlot.ok,true);
 if(getSlot.ok&&postSlot.ok&&graphSlot.ok){
  assert.equal(new Set([getSlot.secret_slot,postSlot.secret_slot,
   graphSlot.secret_slot]).size,3);
  assert.equal(getSlot.production_authorized,false);
 }
});
