import test from 'node:test';
import assert from 'node:assert/strict';
import {reconcileWa13CatalogOffline as reconcile}
 from './wa13-template-catalog-reconciliation.ts';

const NOW=1_800_000_000_000;
const host=()=>({
 contract_version:'wa13-host-scope.lab.v0.1',
 concessionaria_id:'SHOP_A',app_ref:'APP_A',waba_id:'100001',
 catalog_revision:7,now_ms:NOW,max_age_ms:60000,
});
const template=(n=1)=>({
 template_ref:'TPL_'+n,version_ref:'VERSION_'+n,template_revision:3,
 provider_template_id:String(100000+n),
 template_name:'approved_'+n,language_code:'pt_BR',
 meta_category:'UTILITY',local_status:'APPROVED',
 locally_active:true,current_version:true,
 valid_from_ms:NOW-100000,valid_until_ms:NOW+100000,
});
const detail=(n=1)=>({
 id:String(100000+n),name:'approved_'+n,language:'pt_BR',
 status:'APPROVED',category:'UTILITY',
 components:[{type:'BODY',text:'Synthetic {{1}}'}],
});
const s0=(templates:any[]=[template()])=>({
 contract_version:'wa13-s0-catalog.lab.v0.1',
 concessionaria_id:'SHOP_A',app_ref:'APP_A',waba_id:'100001',
 catalog_revision:7,observed_at_ms:NOW-5000,templates,
});
const meta=(details:any[]=[detail()])=>({
 contract_version:'wa13-meta-detail-batch.lab.v0.1',
 waba_id:'100001',observed_at_ms:NOW-5000,details,
});
type Result=ReturnType<typeof reconcile>;
function flags(x:Result){
 for(const key of ['meta_approval_verified','provider_source_authenticated',
  's0_source_authenticated','tenant_binding_verified',
  'provider_page_chain_authenticated','catalog_publication_authorized',
  'send_authorized','production_authorized','s0_write_authorized',
  'ack_allowed','http_response_authorized','m2m_verified',
  'consent_verified','grants_verified','actual_sync_performed'] as const)
  assert.equal(x[key],false,key);
 assert.equal(Object.isFrozen(x),true);
 const dump=JSON.stringify(x);
 for(const secret of ['Synthetic {{1}}','CUSTOMER_PHONE','GRAPH_TOKEN','wamid.'])
  assert.equal(dump.includes(secret),false,secret);
}
function ok(x:Result,accepted=1,withheld=0){
 flags(x);assert.equal(x.decision,'LAB_CATALOG_RECONCILED_UNVERIFIED');
 assert.equal(x.reason,null);
 assert.equal(x.candidates.length,accepted);
 assert.equal(x.withheld_entries,withheld);
 assert.equal(x.observed_entries,accepted+withheld);
 assert.equal(Object.isFrozen(x.candidates),true);
 for(const c of x.candidates){
  assert.equal(c.approval_verified,false);
  assert.equal(c.requires_s0_recheck,true);
  assert.equal(Object.isFrozen(c),true);
 }
}
function deny(x:Result,why?:Result['reason']){
 flags(x);assert.equal(x.decision,'DENIED');
 if(why)assert.equal(x.reason,why);
 assert.deepEqual(x.candidates,[]);
 assert.equal(x.observed_entries,0);
}
const check=(a:unknown=host(),b:unknown=s0(),c:unknown=meta())=>
 reconcile(a,b,c);

test('M13-01 valid synthetic triple aligns, but never attests Meta approval',()=>{
 ok(check());
});
test('M13-02 two templates no ordering dependence between S0 and provider',()=>{
 const result=check(host(),s0([template(2),template(1)]),
  meta([detail(1),detail(2)]));
 ok(result,2);assert.deepEqual(result.candidates.map(x=>x.template_ref),
  ['TPL_1','TPL_2']);
});
test('M13-03 zero templates in consistent empty catalog is no grant',()=>{
 ok(check(host(),s0([]),meta([])),0,0);
});
test('M13-04 pending template is withheld despite structural match',()=>{
 ok(check(host(),s0([{...template(),local_status:'PENDING'}]),
  meta([{...detail(),status:'PENDING'}])),0,1);
});
test('M13-05 rejected withheld',()=>{
 ok(check(host(),s0([{...template(),local_status:'REJECTED'}]),
  meta([{...detail(),status:'REJECTED'}])),0,1);
});
test('M13-06 paused withheld',()=>{
 ok(check(host(),s0([{...template(),local_status:'PAUSED'}]),
  meta([{...detail(),status:'PAUSED'}])),0,1);
});
test('M13-07 disabled withheld',()=>{
 ok(check(host(),s0([{...template(),local_status:'DISABLED'}]),
  meta([{...detail(),status:'DISABLED'}])),0,1);
});
test('M13-08 approved but locally inactive withheld',()=>{
 ok(check(host(),s0([{...template(),locally_active:false}])),0,1);
});
test('M13-09 old/noncurrent version withheld',()=>{
 ok(check(host(),s0([{...template(),current_version:false}])),0,1);
});
test('M13-10 not-yet-valid version withheld',()=>{
 ok(check(host(),s0([{...template(),
  valid_from_ms:NOW+1,valid_until_ms:NOW+100000}])),0,1);
});
test('M13-11 exact expiry time withheld',()=>{
 ok(check(host(),s0([{...template(),valid_until_ms:NOW}])),0,1);
});
test('M13-12 S0 snapshot too old denied, no partial',()=>{
 deny(check(host(),{...s0(),observed_at_ms:NOW-60001}),
  'STALE_OR_FUTURE_SNAPSHOT');
});
test('M13-13 provider snapshot too old denied',()=>{
 deny(check(host(),s0(),{...meta(),observed_at_ms:NOW-60001}),
  'STALE_OR_FUTURE_SNAPSHOT');
});
test('M13-14 future-dated synthetic provider observation denied',()=>{
 deny(check(host(),s0(),{...meta(),observed_at_ms:NOW+1}),
  'STALE_OR_FUTURE_SNAPSHOT');
});
test('M13-15 S0 future-dated denied',()=>{
 deny(check(host(),{...s0(),observed_at_ms:NOW+1}),
  'STALE_OR_FUTURE_SNAPSHOT');
});
test('M13-16 S0 concessionaria mismatch denied',()=>{
 deny(check(host(),{...s0(),concessionaria_id:'SHOP_B'}),
  'SCOPE_MISMATCH');
});
test('M13-17 S0 App mismatch denied',()=>{
 deny(check(host(),{...s0(),app_ref:'APP_B'}),'SCOPE_MISMATCH');
});
test('M13-18 provider WABA mismatch denied',()=>{
 deny(check(host(),s0(),{...meta(),waba_id:'100002'}),'SCOPE_MISMATCH');
});
test('M13-19 S0 WABA mismatch denied',()=>{
 deny(check(host(),{...s0(),waba_id:'100002'}),'SCOPE_MISMATCH');
});
test('M13-20 stale catalog revision denied',()=>{
 deny(check(host(),{...s0(),catalog_revision:6}),'SCOPE_MISMATCH');
});
test('M13-21 provider detail missing even if other approved denied whole',()=>{
 deny(check(host(),s0([template(),template(2)]),meta([detail()])),
  'INCOMPLETE_PROVIDER_DETAILS');
});
test('M13-22 provider extra detail denied whole',()=>{
 deny(check(host(),s0([template()]),meta([detail(),detail(2)])),
  'INCOMPLETE_PROVIDER_DETAILS');
});
test('M13-23 provider identity different from S0 denied',()=>{
 deny(check(host(),s0(),meta([{...detail(),id:'200002'}])),
  'PROVIDER_IDENTITY_MISMATCH');
});
test('M13-24 provider name altered denied',()=>{
 deny(check(host(),s0(),meta([{...detail(),name:'other_name'}])),
  'PROVIDER_SHAPE_DENIED');
});
test('M13-25 provider category mismatch denied',()=>{
 deny(check(host(),s0(),meta([{...detail(),category:'MARKETING'}])),
  'PROVIDER_IDENTITY_MISMATCH');
});
test('M13-26 provider PAUSED despite local APPROVED denied, not chosen',()=>{
 deny(check(host(),s0(),meta([{...detail(),status:'PAUSED'}])),
  'PROVIDER_IDENTITY_MISMATCH');
});
test('M13-27 duplicate S0 template_ref versions denied',()=>{
 deny(check(host(),s0([template(),{...template(2),template_ref:'TPL_1'}]),
  meta([detail(),detail(2)])),'DUPLICATE_OR_CONFLICTING_TEMPLATE');
});
test('M13-28 duplicate S0 provider_id denied',()=>{
 deny(check(host(),s0([template(),{...template(2),provider_template_id:'100001'}]),
  meta([detail(),detail(2)])),'DUPLICATE_OR_CONFLICTING_TEMPLATE');
});
test('M13-29 duplicate version_ref denied',()=>{
 deny(check(host(),s0([template(),{...template(2),version_ref:'VERSION_1'}]),
  meta([detail(),detail(2)])),'DUPLICATE_OR_CONFLICTING_TEMPLATE');
});
test('M13-30 duplicate provider detail denied',()=>{
 deny(check(host(),s0([template(),template(2)]),meta([detail(),detail()])),
  'DUPLICATE_OR_CONFLICTING_TEMPLATE');
});
test('M13-31 malformed provider components denied',()=>{
 deny(check(host(),s0(),meta([{...detail(),components:[{
  type:'BODY',text:''}]}])),'PROVIDER_SHAPE_DENIED');
});
test('M13-32 injected provider claimed approval field denied',()=>{
 deny(check(host(),s0(),meta([{...detail(),approved:true}])),
  'PROVIDER_SHAPE_DENIED');
});
test('M13-33 AUTHENTICATION category cannot be silently relabeled',()=>{
 deny(check(host(),s0(),meta([{...detail(),category:'AUTHENTICATION'}])),
  'PROVIDER_IDENTITY_MISMATCH');
});
test('M13-34 invalid host max_age_ms denied',()=>{
 deny(check({...host(),max_age_ms:99999999}),'INVALID_INPUT');
});
test('M13-35 accessor on S0 template entry denied without invocation',()=>{
 let hit=0;const x=template();
 Object.defineProperty(x,'local_status',{get(){hit++;return 'APPROVED';}});
 deny(check(host(),s0([x])),'INVALID_INPUT');
 assert.equal(hit,0);
});
test('M13-36 array getter on details denied without invocation',()=>{
 let hit=0;const values=meta();
 Object.defineProperty(values.details,'0',{get(){hit++;return detail();}});
 deny(check(host(),s0(),values),'INVALID_INPUT');
 assert.equal(hit,0);
});
test('M13-37 sparse S0 templates denied',()=>{
 const list=[template()];list.length=2;
 deny(check(host(),s0(list),meta([detail(),detail(2)])),'INVALID_INPUT');
});
test('M13-38 symbol property on host cannot claim extra authority',()=>{
 const a=host();Object.defineProperty(a,Symbol('secret'),{value:'x'});
 deny(check(a),'INVALID_INPUT');
});
test('M13-39 unknown S0 field cannot claim live grant',()=>{
 deny(check(host(),{...s0(),send_authorized:true}),'INVALID_INPUT');
});
test('M13-40 provider detail accessor denied without invocation',()=>{
 let hit=0;const x=detail();Object.defineProperty(x,'status',{
  get(){hit++;return 'APPROVED';}});
 deny(check(host(),s0(),meta([x])),'PROVIDER_SHAPE_DENIED');
 assert.equal(hit,0);
});
test('M13-41 template with impossible timeframe denied',()=>{
 deny(check(host(),s0([{...template(),valid_until_ms:NOW-100001}])),
  'INVALID_INPUT');
});
test('M13-42 resource bound >100 entries denied with no candidates',()=>{
 const list=Array.from({length:101},(_,i)=>template(i+1));
 deny(check(host(),s0(list),meta([])),'INVALID_INPUT');
});
test('M13-43 even matching snapshots are not authenticated or synchronized',()=>{
 const result=check();ok(result);
 assert.equal('status' in result,false);
 assert.equal('provider_components' in result,false);
 assert.equal('m2m_token' in result,false);
});
