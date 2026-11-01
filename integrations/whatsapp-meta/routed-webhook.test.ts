import { test } from 'node:test';
import assert from 'node:assert/strict';
import { inspectRoutedMetaGet, inspectRoutedMetaPost,
  type TrustedRoutingPorts } from './routed-webhook.ts';
import type { TrustedMetaRegistry } from './credential-routing.ts';

const now = 1792320000000;
const keyA = 'ONLY_FAKE_HMAC_APP_A_77', keyB = 'ONLY_FAKE_HMAC_APP_B_99';
const getA = 'ONLY_FAKE_VERIFY_TOKEN_APP_A_1';
const fakeVault: Record<string, string> = {
  SLOT_A_POST: keyA, SLOT_A_GET: getA, SLOT_A_GRAPH: 'GRAPH_FAKE_A',
  SLOT_B_POST: keyB, SLOT_B_GET: 'ONLY_FAKE_VERIFY_TOKEN_APP_B_2', SLOT_B_GRAPH: 'GRAPH_FAKE_B',
};
const appA = {
  app_ref: 'APP_A', route_ref: 'TRUSTED_ROUTE_A', concessionaria_id: 'SHOP_A',
  revision: 3, active: true, valid_from_ms: now - 100, valid_until_ms: now + 100,
  secret_slots: { get_verify_token: 'SLOT_A_GET', post_app_secret: 'SLOT_A_POST', graph_access_token: 'SLOT_A_GRAPH' },
  channels: [
    { canal_id: 'CHANNEL_A1', waba_id: '100001', phone_number_id: '1234567890', active: true },
    { canal_id: 'CHANNEL_A2', waba_id: '100002', phone_number_id: '1234567891', active: true },
  ],
};
const appB = {
  app_ref: 'APP_B', route_ref: 'TRUSTED_ROUTE_B', concessionaria_id: 'SHOP_B',
  revision: 5, active: true, valid_from_ms: now - 100, valid_until_ms: now + 100,
  secret_slots: { get_verify_token: 'SLOT_B_GET', post_app_secret: 'SLOT_B_POST', graph_access_token: 'SLOT_B_GRAPH' },
  channels: [{ canal_id: 'CHANNEL_B1', waba_id: '200001', phone_number_id: '9876543210', active: true }],
};
const reg: TrustedMetaRegistry = { contract_version: 'wa-meta-credential-routing.v0.1-proposed', apps: [appA, appB] };
const routeA = { route_ref: 'TRUSTED_ROUTE_A', expected_revision: 3 };
const routeB = { route_ref: 'TRUSTED_ROUTE_B', expected_revision: 5 };
const mkPorts = (opts: {
  registry?: () => TrustedMetaRegistry;
  resolver?: (slot: string) => string | undefined | Promise<string | undefined>;
  clock?: () => number;
} = {}) => {
  const called: string[] = [];
  const ports: TrustedRoutingPorts = {
    currentRegistry: opts.registry ?? (() => reg),
    resolveSecret: async (s) => {
      called.push(s);
      return opts.resolver ? opts.resolver(s) : fakeVault[s];
    },
    nowMs: opts.clock ?? (() => now),
  };
  return { ports, called };
};
const query = (token = getA) => new URLSearchParams({
  'hub.mode': 'subscribe', 'hub.verify_token': token, 'hub.challenge': '000042',
}).toString();
const makeEntry = (waba = '100001', phone = '1234567890',
  statuses: unknown[] = []) => ({ id: waba, changes: [{ field: 'messages', value: {
    metadata: { phone_number_id: phone }, statuses: statuses.length ? statuses : undefined,
    messages: statuses.length ? undefined : [ { id: 'wamid.SYNTHETIC_IN', from: '5581900000000', type: 'text', timestamp: '1792320000' } ],
  } }] });
const makeStatus = (state = 'delivered') => ({ id: 'wamid.SYNTHETIC_OUT',
  recipient_id: '5581900000000', status: state, timestamp: '1792320001' });
const body = (entries: unknown[] = [makeEntry()]) => new TextEncoder().encode(JSON.stringify({
  object: 'whatsapp_business_account', entry: entries,
}));
const sign = async (payload: Uint8Array, value = keyA) => {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(value),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = new Uint8Array(await crypto.subtle.sign('HMAC', key, payload));
  return 'sha256='+Array.from(mac, b => b.toString(16).padStart(2,'0')).join('');
};
const send = async (entries: unknown[] = [makeEntry()],
  options?: { route?: typeof routeA; key?: string; ports?: TrustedRoutingPorts }) => {
  const raw_body = body(entries);
  return inspectRoutedMetaPost({ route: options?.route ?? routeA, raw_body,
    signature_header: await sign(raw_body, options?.key ?? keyA) }, options?.ports ?? mkPorts().ports);
};

test('ROUTE-01 GET uses only route A verification secret and preserves challenge', async () => {
  const {ports, called} = mkPorts();
  const r = await inspectRoutedMetaGet({route: routeA,raw_query: query()}, ports);
  assert.deepEqual(r,{ok:true,challenge:'000042',production_authorized:false});
  assert.deepEqual(called,['SLOT_A_GET']);
});
test('ROUTE-02 GET never uses POST HMAC or Graph token as verification credential', async () => {
  const r = await inspectRoutedMetaGet({route: routeA,raw_query: query(keyA)}, mkPorts().ports);
  assert.deepEqual(r,{ok:false,reason:'VERIFICATION_DENIED',production_authorized:false});
});
test('ROUTE-03 GET cannot cross App by providing other App token on App A route', async () => {
  const r = await inspectRoutedMetaGet({route: routeA,raw_query: query(fakeVault.SLOT_B_GET)}, mkPorts().ports);
  assert.equal(r.ok,false);
});
test('ROUTE-04 POST verifies raw signed body with correct App and scopes message', async () => {
  const {ports,called} = mkPorts(); const r = await send(undefined,{ports});
  assert.equal(r.ok,true); assert.deepEqual(called,['SLOT_A_POST']);
  if(r.ok){assert.equal(r.events.length,1);assert.equal(r.events[0].scope.canal_id,'CHANNEL_A1');
    assert.equal(r.events[0].scope.concessionaria_id,'SHOP_A');
    assert.equal(r.events[0].event.position.array_kind,'messages');
    assert.equal(r.authenticated_app_ref,'APP_A');}
  assert.equal(r.ack_allowed,false); assert.equal(r.production_authorized,false);
});
test('ROUTE-05 POST may contain two separate WABAs within the SAME authenticated App', async () => {
  const r = await send([makeEntry('100001','1234567890'),makeEntry('100002','1234567891')]);
  assert.equal(r.ok,true);if(r.ok)assert.deepEqual(r.events.map(x=>x.scope.canal_id),['CHANNEL_A1','CHANNEL_A2']);
});
test('ROUTE-06 one signed POST cannot smuggle another App channel', async () => {
  const r = await send([makeEntry(),makeEntry('200001','9876543210')]);
  assert.deepEqual(r,{ok:false,reason:'CHANNEL_DENIED',ack_allowed:false,production_authorized:false});
});
test('ROUTE-07 signature from App B cannot pass trusted App A route', async () => {
  const r = await send([makeEntry()],{key:keyB});
  assert.equal(r.ok,false);if(!r.ok)assert.equal(r.reason,'SIGNATURE_OR_ENVELOPE_DENIED');
});
test('ROUTE-08 unknown or disabled phone number rejects whole POST, not partial result', async () => {
  const r = await send([makeEntry(),makeEntry('100001','0000000000')]);
  assert.equal(r.ok,false);assert.equal(r.ack_allowed,false);
});
test('ROUTE-09 trusted app disabled before first registry read denies before resolving secret',async()=>{
  const {ports,called}=mkPorts({registry:()=>({...reg, apps:[{...appA, active:false},appB]})});
  const r=await send(undefined,{ports});assert.equal(r.ok,false);assert.deepEqual(called,[]);
});
test('ROUTE-10 revoked while resolving secret denies POST even with good signed body', async()=>{
  let revoked=false;
  const {ports}=mkPorts({registry:()=>({...reg,apps:[{...appA,active:!revoked},appB]}),
    resolver:async name=>{revoked=true;return fakeVault[name]}});
  const r=await send(undefined,{ports});assert.equal(r.ok,false);
  if(!r.ok)assert.equal(r.reason,'ROUTING_CHANGED');
});
test('ROUTE-11 rotation of slot+revision while secret lookup is in flight denies',async()=>{
  let changed=false;
  const {ports}=mkPorts({registry:()=>({...reg,apps:[{
    ...appA,revision:changed?4:3,secret_slots: changed ? {...appA.secret_slots,post_app_secret:'SLOT_NEW_POST'}:appA.secret_slots,
  },appB]}),resolver:async name=>{changed=true;return fakeVault[name]}});
  const r=await send(undefined,{ports});assert.equal(r.ok,false);
});
test('ROUTE-12 registry revoked after HMAC but before channel binding denies',async()=>{
  let calls=0;
  const {ports}=mkPorts({registry:()=>{calls++;return {...reg,apps:[{...appA,active:calls<3},appB]}}});
  const r=await send(undefined,{ports});assert.equal(r.ok,false);
  if(!r.ok)assert.equal(r.reason,'ROUTING_CHANGED');
});
test('ROUTE-13 missing secret and thrown secret resolver never expose values',async()=>{
  for(const resolver of [()=>undefined,()=>{throw Error('SHOULD_NOT_LEAK_VAULT_SECRET')}]){
    const {ports}=mkPorts({resolver});
    const r=await send(undefined,{ports});assert.equal(r.ok,false);
    assert.equal(JSON.stringify(r).includes('SHOULD_NOT_LEAK'),false);
  }
});
test('ROUTE-14 tampered bytes invalidate HMAC',async()=>{
  const original=body(), altered=Uint8Array.from(original);
  altered[altered.length-2] ^= 1;
  const r=await inspectRoutedMetaPost({route:routeA,raw_body:altered,signature_header:await sign(original)},mkPorts().ports);
  assert.equal(r.ok,false);
});
test('ROUTE-15 invalid JSON and invalid signature are not returned as business events',async()=>{
  const bad=new TextEncoder().encode('{bad}');
  const r=await inspectRoutedMetaPost({route:routeA,raw_body:bad,signature_header:await sign(bad)},mkPorts().ports);
  assert.deepEqual(r,{ok:false,reason:'SIGNATURE_OR_ENVELOPE_DENIED',ack_allowed:false,production_authorized:false});
});
test('ROUTE-16 fabricated unknown route cannot select a secret',async()=>{
  const {ports,called}=mkPorts();
  const r=await inspectRoutedMetaPost({route:{route_ref:'ATTACKER_ROUTE',expected_revision:3},raw_body:body(),signature_header:null},ports);
  assert.equal(r.ok,false);assert.deepEqual(called,[]);
});
test('ROUTE-17 duplicate registry configuration fails closed',async()=>{
  const {ports}=mkPorts({registry:()=>({...reg,apps:[appA,appB,appA]})});
  assert.equal((await send(undefined,{ports})).ok,false);
});
test('ROUTE-18 input buffer mutation after invocation does not change verified event content',async()=>{
  const original=body(), signature_header=await sign(original);
  const promise=inspectRoutedMetaPost({route:routeA,raw_body:original,signature_header},mkPorts().ports);
  const flipped=body([makeEntry('200001','9876543210')]);
  assert.equal(original.length,flipped.length);
  original.set(flipped);
  const r=await promise; assert.equal(r.ok,true);
  if(r.ok)assert.equal(r.events[0].scope.concessionaria_id,'SHOP_A');
});
test('ROUTE-19 signed payload cannot declare a trusted concessionaria_id',async()=>{
  const rogue=makeEntry() as ReturnType<typeof makeEntry> & {concessionaria_id:string};
  rogue.concessionaria_id='SHOP_B';
  const r=await send([rogue]);assert.equal(r.ok,true);
  if(r.ok)assert.equal(r.events[0].scope.concessionaria_id,'SHOP_A');
});
test('ROUTE-20 status callback maintains array_kind and never authorizes ACK',async()=>{
  const r=await send([makeEntry('100001','1234567890',[makeStatus()])]);
  assert.equal(r.ok,true);assert.equal(r.ack_allowed,false);
  if(r.ok)assert.equal(r.events[0].event.position.array_kind,'statuses');
});
test('ROUTE-21 stale revisions deny before touching vault',async()=>{
  const {ports,called}=mkPorts();
  const r=await inspectRoutedMetaPost({route:{...routeA,expected_revision:2},raw_body:body(),signature_header:null},ports);
  assert.equal(r.ok,false);assert.deepEqual(called,[]);
});
test('ROUTE-22 expired clock after resolution denies even before HMAC parse',async()=>{
  let current=now;
  const {ports}=mkPorts({clock:()=>current,resolver:async name=>{current=now+100;return fakeVault[name]}});
  const r=await send(undefined,{ports});assert.equal(r.ok,false);
  if(!r.ok)assert.equal(r.reason,'ROUTING_CHANGED');
});
test('ROUTE-23 GET secret rotation or revocation before comparison denies',async()=>{
  let revoked=false;
  const {ports}=mkPorts({registry:()=>({...reg,apps:[{...appA,active:!revoked},appB]}),
    resolver:async name=>{revoked=true;return fakeVault[name]}});
  const r=await inspectRoutedMetaGet({route:routeA,raw_query:query()},ports);
  assert.equal(r.ok,false);
});
test('ROUTE-24 oversize body rejected without requesting secret or cloning body',async()=>{
  const {ports,called}=mkPorts();
  const r=await inspectRoutedMetaPost({route:routeA,raw_body:new Uint8Array(256*1024+1),signature_header:'sha256='+('0'.repeat(64))},ports);
  assert.equal(r.ok,false);assert.deepEqual(called,[]);
});
test('ROUTE-25 GET unknown route/extra query remain denied without exposing token',async()=>{
  const {ports}=mkPorts();
  const r=await inspectRoutedMetaGet({route:routeB,raw_query:query(getA)+'&canal_id=SHOP_A'},ports);
  assert.equal(r.ok,false);
  assert.equal(JSON.stringify(r).includes(getA),false);
});
test('ROUTE-26 same globally unique Phone Number ID under different WABA must fail',async()=>{
 const registry:TrustedMetaRegistry={...reg, apps:[appA,{...appB,channels:[{
   ...appB.channels[0],phone_number_id:'1234567890',
 }]}]};
 const {ports}=mkPorts({registry:()=>registry});
 assert.equal((await send(undefined,{ports})).ok,false);
});
test('ROUTE-27 different Apps cannot claim one WABA even with different phone IDs',async()=>{
 const registry:TrustedMetaRegistry={...reg, apps:[appA,{...appB,channels:[{
   ...appB.channels[0],waba_id:'100001',
 }]}]};
 const {ports}=mkPorts({registry:()=>registry});
 assert.equal((await send(undefined,{ports})).ok,false);
});
test('ROUTE-28 S0 channel id is globally unique across apps',async()=>{
 const registry:TrustedMetaRegistry={...reg, apps:[appA,{...appB,channels:[{
   ...appB.channels[0],canal_id:'CHANNEL_A1',
 }]}]};
 const {ports}=mkPorts({registry:()=>registry});
 assert.equal((await send(undefined,{ports})).ok,false);
});


test('AUD-GLOBAL-ROUTE-01 GET route getter never invoked',async()=>{
 let calls=0;const req:any={raw_query:query()};
 Object.defineProperty(req,'route',{enumerable:true,get(){
  calls++;throw Error('SIDE_EFFECT');}});
 const res=await inspectRoutedMetaGet(req,mkPorts().ports);
 assert.equal(res.ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-ROUTE-02 POST route nested getter never invoked',async()=>{
 let calls=0;const route:any={...routeA};
 Object.defineProperty(route,'expected_revision',{enumerable:true,get(){
  calls++;return 3;}});
 const raw_body=body();
 const res=await inspectRoutedMetaPost({route,raw_body,
  signature_header:await sign(raw_body)},mkPorts().ports);
 assert.equal(res.ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-ROUTE-03 POST body getter never invoked',async()=>{
 let calls=0;const req:any={route:routeA,
  signature_header:'sha256='+('0'.repeat(64))};
 Object.defineProperty(req,'raw_body',{enumerable:true,get(){
  calls++;return body();}});
 const res=await inspectRoutedMetaPost(req,mkPorts().ports);
 assert.equal(res.ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-ROUTE-04 signature getter never invoked',async()=>{
 let calls=0;const req:any={route:routeA,raw_body:body()};
 Object.defineProperty(req,'signature_header',{enumerable:true,get(){
  calls++;return 'sha256='+('0'.repeat(64));}});
 const res=await inspectRoutedMetaPost(req,mkPorts().ports);
 assert.equal(res.ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-ROUTE-05 GET raw query getter never invoked',async()=>{
 let calls=0;const req:any={route:routeA};
 Object.defineProperty(req,'raw_query',{enumerable:true,get(){
  calls++;return query();}});
 const res=await inspectRoutedMetaGet(req,mkPorts().ports);
 assert.equal(res.ok,false);assert.equal(calls,0);
});
test('AUD-GLOBAL-ROUTE-06 extra client authority field denied',async()=>{
 const req:any={route:routeA,raw_query:query(),production_authorized:true};
 const res=await inspectRoutedMetaGet(req,mkPorts().ports);
 assert.equal(res.ok,false);assert.equal(res.production_authorized,false);
});
test('AUD-GLOBAL-ROUTE-07 mutation of request route in resolver cannot redirect POST',async()=>{
 const raw_body=body();const req={route:{...routeA},
  signature_header:await sign(raw_body),raw_body};
 const {ports}=mkPorts({resolver:async slot=>{
  req.route.route_ref='TRUSTED_ROUTE_B';
  req.route.expected_revision=5;
  return fakeVault[slot];
 }});
 const res=await inspectRoutedMetaPost(req,ports);
 assert.equal(res.ok,true);
 if(res.ok)assert.equal(res.authenticated_app_ref,'APP_A');
 assert.equal(res.ack_allowed,false);
});
test('AUD-GLOBAL-ROUTE-08 prototype/polluted route cannot choose App',async()=>{
 const raw_body=body();
 const route=Object.create({route_ref:'TRUSTED_ROUTE_A',
  expected_revision:3});
 const res=await inspectRoutedMetaPost({route,raw_body,
  signature_header:await sign(raw_body)} as any,mkPorts().ports);
 assert.equal(res.ok,false);assert.equal(res.ack_allowed,false);
});
