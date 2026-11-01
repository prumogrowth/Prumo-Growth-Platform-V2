import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareWa15F02PreviewOffline as prepare}
 from './wa15-f02-planner-preview.ts';
import {wa13NormalizedComponentsDigest as digest}
 from './wa13-template-catalog-reconciliation.ts';

const NOW=1800000000000;
const details=(n=1)=>({
 id:String(100000+n),name:'welcome_'+n,language:'pt_BR',
 status:'APPROVED',category:'UTILITY',
 components:[{type:'BODY',text:'Sample '+n}],
});
const catalog13=(n=1)=>({
 template_ref:'TEMPLATE_'+n,version_ref:'VERSION_'+n,
 template_revision:2,provider_template_id:String(100000+n),
 template_name:'welcome_'+n,language_code:'pt_BR',
 provider_components_sha256:digest([{type:'BODY',text:'Sample '+n}]),
 meta_category:'UTILITY',local_status:'APPROVED',
 locally_active:true,current_version:true,
 valid_from_ms:NOW-20000,valid_until_ms:NOW+20000,
});
const purpose=(n=1)=>({
 template_ref:'TEMPLATE_'+n,version_ref:'VERSION_'+n,
 catalog_revision:7,concessionaria_id:'SHOP_A',waba_ref:'100001',
 language:'pt_BR',meta_category:'UTILITY',meta_status:'APPROVED',
 locally_active:true,current_version:true,purpose_refs:['RECONTACT'],
 grants:[{purpose_ref:'RECONTACT',actor_kind:'PLANNER',
  actor_ref:'PLANNER_A',flow_ref:'FLOW_A',campaign_ref:null}],
});
const grant=(n=1)=>({
 template_ref:'TEMPLATE_'+n,template_version_ref:'VERSION_'+n,
 template_purpose_ref:'RECONTACT',consent_purpose_ref:'SERVICE',
 actor_kind:'PLANNER',actor_ref:'PLANNER_A',flow_ref:'FLOW_A',
 campaign_ref:null,state:'ACTIVE',revision:8,
});
const factory=()=>{
 const q:any={
  contract_version:'wa15-f02-planning-request.lab.v0.1',
  selection_ref:'SELECT_A',concessionaria_id:'SHOP_A',app_ref:'APP_A',
  waba_id:'100001',catalog_revision:7,language:'pt_BR',
  purpose_ref:'RECONTACT',consent_purpose_ref:'SERVICE',
  actor_kind:'PLANNER',actor_ref:'PLANNER_A',flow_ref:'FLOW_A',
  campaign_ref:null,case_ref:'CASE_A',lead_ref:'LEAD_A',
  case_version:4,authorization_revision:6,plan_revision:2,
  now_ms:NOW,max_age_ms:60000,
 };
 const scope:any={
  selection_ref:'SELECT_A',concessionaria_id:'SHOP_A',
  waba_ref:'100001',catalog_revision:7,language:'pt_BR',
  purpose_ref:'RECONTACT',actor_kind:'PLANNER',
  actor_ref:'PLANNER_A',flow_ref:'FLOW_A',campaign_ref:null,
  case_ref:'CASE_A',lead_ref:'LEAD_A',case_version:4,
  authorization_revision:6,
 };
 const policy:any={
  selection_ref:'SELECT_A',concessionaria_id:'SHOP_A',
  waba_ref:'100001',case_ref:'CASE_A',lead_ref:'LEAD_A',
  case_version:4,authorization_revision:6,policy_revision:9,
  consent_state:'VALID',opted_out:false,case_authorized:true,
  audience_eligible:true,campaign_eligibility:'NOT_APPLICABLE',
 };
 const m13Host:any={
  contract_version:'wa13-host-scope.lab.v0.1',
  concessionaria_id:'SHOP_A',app_ref:'APP_A',waba_id:'100001',
  catalog_revision:7,now_ms:NOW,max_age_ms:60000,
 };
 const m13S0:any={
  contract_version:'wa13-s0-catalog.lab.v0.1',
  concessionaria_id:'SHOP_A',app_ref:'APP_A',waba_id:'100001',
  catalog_revision:7,observed_at_ms:NOW-1000,
  templates:[catalog13()],
 };
 const m13Provider:any={
  contract_version:'wa13-meta-detail-batch.lab.v0.1',
  waba_id:'100001',observed_at_ms:NOW-1000,
  details:[details()],
 };
 const m14Ledger:any={
  contract_version:'wa14-s0-ledger.lab.v0.1',
  selection_ref:'SELECT_A',concessionaria_id:'SHOP_A',
  waba_ref:'100001',lead_ref:'LEAD_A',case_ref:'CASE_A',
  case_version:4,authorization_revision:6,
  policy_revision:9,consent_revision:7,suppression_revision:8,
  grant_revision:8,observed_at_ms:NOW-1000,
  case_authorized:true,audience_eligible:true,
  campaign_eligibility:'NOT_APPLICABLE',
  consents:[{consent_purpose_ref:'SERVICE',state:'GRANTED',
   valid_from_ms:NOW-30000,valid_until_ms:NOW+30000,revision:6}],
  suppressions:[],grants:[grant()],
 };
 const state={q,scope,policy,templates:[purpose()] as any[],
  m13Host,m13S0,m13Provider,m14Ledger,reads:[] as string[]};
 const ports={
  async resolveSelection(_ref:string,phase:string){
   state.reads.push('scope:'+phase);return state.scope;
  },
  async readScopedPolicy(_scope:unknown,phase:string){
   state.reads.push('policy:'+phase);return state.policy;
  },
  async readScopedCatalog(_scope:unknown,phase:string){
   state.reads.push('catalog:'+phase);return state.templates;
  },
 };
 return Object.assign(state,{ports});
};
type Factory=ReturnType<typeof factory>;
const run=(f:Factory)=>prepare(f.q,f.ports,
 f.m13Host,f.m13S0,f.m13Provider,f.m14Ledger);
const deny=async(f:Factory,reason?:string)=>{
 const out=await run(f);
 assert.equal(out.decision,'DENIED');
 if(reason)assert.equal(out.reason,reason);
 assert.equal(out.preview,null);
 for(const field of ['send_authorized','production_authorized',
  'graph_dispatch_authorized','s0_source_authenticated'] as const)
  assert.equal(out[field],false);
 assert.equal(Object.isFrozen(out),true);
 return out;
};
const success=async(f:Factory,count=1)=>{
 const out=await run(f);
 assert.equal(out.decision,'LAB_F02_PREVIEW_UNVERIFIED');
 assert.equal(out.reason,null);
 if(out.decision!=='LAB_F02_PREVIEW_UNVERIFIED'||!out.preview)
  throw Error('not preview');
 assert.equal(out.preview.candidates.length,count);
 assert.equal(Object.isFrozen(out.preview),true);
 assert.equal(Object.isFrozen(out.preview.candidates),true);
 for(const field of ['send_authorized','production_authorized',
  'meta_approval_verified','consent_verified','s0_source_authenticated',
  'graph_dispatch_authorized','provider_sync_performed'] as const)
  assert.equal(out.preview[field],false);
 assert.equal(out.preview.requires_s0_recheck,true);
 const serialized=JSON.stringify(out);
 for(const token of ['CASE_A','LEAD_A','PLANNER_A','SHOP_A','100001',
  'policy_revision','consent_revision','provider_components_sha256',
  'internal_ticket','Sample 1','opted_out','consent_purpose_ref'])
  assert.equal(serialized.includes(token),false,token);
 for(const c of out.preview.candidates){
  assert.equal(Object.isFrozen(c),true);
  assert.deepEqual(Object.keys(c).sort(),[
   'template_ref','version_ref','catalog_revision','meta_category',
   'purpose_ref','send_authorized','production_authorized',
   'requires_s0_recheck'].sort());
 }
 return out.preview;
};

test('M15-01 minimal F02 LAB preview without S0/Meta authority',async()=>{
 const f=factory(),view=await success(f);
 assert.equal(view.planning_flow_ref,'FLOW_A');
 assert.equal(view.campaign_ref,null);assert.equal(view.plan_revision,2);
 assert.deepEqual(f.reads,['scope:PLAN','policy:PLAN','catalog:PLAN']);
});
test('M15-02 two approved consent/granted templates visible in sorted order',async()=>{
 const f=factory();
 f.templates=[purpose(2),purpose(1)];
 f.m13S0.templates=[catalog13(2),catalog13(1)];
 f.m13Provider.details=[details(1),details(2)];
 f.m14Ledger.grants=[grant(1),grant(2)];
 const v=await success(f,2);
 assert.deepEqual(v.candidates.map(x=>x.template_ref),
  ['TEMPLATE_1','TEMPLATE_2']);
});
test('M15-03 WA26 no active template cannot invent a candidate',async()=>{
 const f=factory();f.templates=[];await deny(f,'WA26_POLICY_OR_CATALOG_DENIED');
});
test('M15-04 WA26 paused candidate denied',async()=>{
 const f=factory();f.templates[0].meta_status='PAUSED';
 await deny(f,'WA26_POLICY_OR_CATALOG_DENIED');
});
test('M15-05 M13 provider PAUSED cannot be hidden by WA26 APPROVED',async()=>{
 const f=factory();f.m13Provider.details[0].status='PAUSED';
 f.m13S0.templates[0].local_status='PAUSED';
 await deny(f,'CATALOG_VERSION_OR_SCOPE_MISMATCH');
});
test('M15-06 mismatched BODY digest denied entire preview',async()=>{
 const f=factory();f.m13Provider.details[0].components[0].text='Tampered';
 await deny(f,'M13_CATALOG_DENIED');
});
test('M15-07 different provider template version denied',async()=>{
 const f=factory();f.m13S0.templates[0].version_ref='VERSION_2';
 await deny(f,'CATALOG_VERSION_OR_SCOPE_MISMATCH');
});
test('M15-08 other shop M13 host denied',async()=>{
 const f=factory();f.m13Host.concessionaria_id='SHOP_B';
 await deny(f,'M13_CATALOG_DENIED');
});
test('M15-09 other app M13 host denied',async()=>{
 const f=factory();f.m13Host.app_ref='APP_B';
 await deny(f,'M13_CATALOG_DENIED');
});
test('M15-10 other WABA provider denied',async()=>{
 const f=factory();f.m13Provider.waba_id='100002';
 await deny(f,'M13_CATALOG_DENIED');
});
test('M15-11 WA26 scope foreign shop denied',async()=>{
 const f=factory();f.scope.concessionaria_id='SHOP_B';
 await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-12 WA26 scope foreign case denied',async()=>{
 const f=factory();f.scope.case_ref='CASE_B';
 await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-13 WA26 scope actor changed denied',async()=>{
 const f=factory();f.scope.actor_ref='PLANNER_B';
 await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-14 WA26 scope campaign changed denied',async()=>{
 const f=factory();f.scope.campaign_ref='CAMPAIGN_X';
 await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-15 M14 ledger wrong lead denied even if WA26 grants match',async()=>{
 const f=factory();f.m14Ledger.lead_ref='LEAD_B';
 await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-16 WA26 policy revision differs from M14 denied',async()=>{
 const f=factory();f.policy.policy_revision=10;
 await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-17 WA26 policy claims audience while M14 denies',async()=>{
 const f=factory();f.m14Ledger.audience_eligible=false;
 await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-18 WA26 opt-out blocks planning even if M14 grants',async()=>{
 const f=factory();f.policy.opted_out=true;await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-19 M14 shop-wide suppression denies preview',async()=>{
 const f=factory();f.m14Ledger.suppressions=[
  {consent_purpose_ref:null,active:true,revision:8}];
 await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
});
test('M15-20 M14 revoked consent denies preview',async()=>{
 const f=factory();f.m14Ledger.consents[0].state='REVOKED';
 await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
});
test('M15-21 M14 expired consent denies preview',async()=>{
 const f=factory();f.m14Ledger.consents[0].valid_until_ms=NOW;
 await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
});
test('M15-22 no M14 matching grant denies preview',async()=>{
 const f=factory();f.m14Ledger.grants=[];
 await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
});
test('M15-23 M14 outdated template grant cannot authorize other version',async()=>{
 const f=factory();f.m14Ledger.grants[0].template_version_ref='VERSION_99';
 await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
});
test('M15-24 M14 campaign requires grant and eligibility',async()=>{
 const f=factory();f.q.campaign_ref='CAMPAIGN_1';
 f.scope.campaign_ref='CAMPAIGN_1';
 f.policy.campaign_eligibility='ELIGIBLE';
 f.m14Ledger.campaign_eligibility='ELIGIBLE';
 f.templates[0].grants[0].campaign_ref='CAMPAIGN_1';
 f.m14Ledger.grants[0].campaign_ref='CAMPAIGN_1';
 const v=await success(f);assert.equal(v.campaign_ref,'CAMPAIGN_1');
});
test('M15-25 missing WA26 campaign grant denied',async()=>{
 const f=factory();f.q.campaign_ref='CAMPAIGN_1';
 f.scope.campaign_ref='CAMPAIGN_1';f.policy.campaign_eligibility='ELIGIBLE';
 f.m14Ledger.campaign_eligibility='ELIGIBLE';
 f.m14Ledger.grants[0].campaign_ref='CAMPAIGN_1';
 await deny(f,'WA26_POLICY_OR_CATALOG_DENIED');
});
test('M15-26 missing M14 campaign grant denied',async()=>{
 const f=factory();f.q.campaign_ref='CAMPAIGN_1';
 f.scope.campaign_ref='CAMPAIGN_1';f.policy.campaign_eligibility='ELIGIBLE';
 f.m14Ledger.campaign_eligibility='ELIGIBLE';
 f.templates[0].grants[0].campaign_ref='CAMPAIGN_1';
 await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
});
test('M15-27 consent purpose must be explicitly granted independently',async()=>{
 const f=factory();f.q.consent_purpose_ref='MARKETING';
 f.m14Ledger.consents.push({
  consent_purpose_ref:'MARKETING',state:'GRANTED',
  valid_from_ms:NOW-100,valid_until_ms:NOW+1000,revision:7,
 });
 await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
});
test('M15-28 supplied request cannot claim authority via extra field',async()=>{
 const f=factory();f.q.send_authorized=true;
 await deny(f,'INVALID_REQUEST');
});
test('M15-29 request getter is never invoked',async()=>{
 const f=factory();let hits=0;
 Object.defineProperty(f.q,'concessionaria_id',{get(){
  hits++;return 'SHOP_A';
 }});
 await deny(f,'INVALID_REQUEST');assert.equal(hits,0);
});
test('M15-30 WA26 scope getter denied without invocation',async()=>{
 const f=factory();let hits=0;
 Object.defineProperty(f.scope,'actor_ref',{get(){
  hits++;return 'PLANNER_A';
 }});
 await deny(f,'UNTRUSTED_SCOPE');assert.equal(hits,0);
});
test('M15-31 policy getter denied without invocation',async()=>{
 const f=factory();let hits=0;
 Object.defineProperty(f.policy,'consent_state',{get(){
  hits++;return 'VALID';
 }});
 await deny(f,'UNTRUSTED_SCOPE');assert.equal(hits,0);
});
test('M15-32 M14 ledger getter denied without invocation',async()=>{
 const f=factory();let hits=0;
 Object.defineProperty(f.m14Ledger,'case_authorized',{get(){
  hits++;return true;
 }});
 await deny(f,'INVALID_REQUEST');assert.equal(hits,0);
});
test('M15-33 duplicate WA26 candidates denied',async()=>{
 const f=factory();f.templates.push({...purpose()});
 await deny(f,'WA26_POLICY_OR_CATALOG_DENIED');
});
test('M15-34 no M13 details denies despite WA26 candidate',async()=>{
 const f=factory();f.m13Provider.details=[];
 await deny(f,'M13_CATALOG_DENIED');
});
test('M15-35 stale M13 provider denies',async()=>{
 const f=factory();f.m13Provider.observed_at_ms=NOW-60001;
 await deny(f,'M13_CATALOG_DENIED');
});
test('M15-36 M14 stale ledger denies',async()=>{
 const f=factory();f.m14Ledger.observed_at_ms=NOW-60001;
 await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
});
test('M15-37 claimed catalog revision incompatible with WA26 denied',async()=>{
 const f=factory();f.scope.catalog_revision=8;
 await deny(f,'UNTRUSTED_SCOPE');
});
test('M15-38 changed planning revision is not authority',async()=>{
 const f=factory();f.q.plan_revision=17;
 const v=await success(f);assert.equal(v.plan_revision,17);
 assert.equal(v.send_authorized,false);
});
test('M15-39 M13 other language cannot enable F02 template',async()=>{
 const f=factory();
 f.m13Provider.details[0].language='en_US';
 f.m13S0.templates[0].language_code='en_US';
 await deny(f,'CATALOG_VERSION_OR_SCOPE_MISMATCH');
});
test('M15-40 blocked preview never exposes candidate PII or tickets',async()=>{
 const f=factory();f.m14Ledger.consents[0].state='DENIED';
 const out=await deny(f,'M14_CONSENT_OR_GRANT_DENIED');
 assert.deepEqual(Object.keys(out).sort(),[
  'decision','reason','preview','send_authorized',
  'production_authorized','graph_dispatch_authorized',
  's0_source_authenticated'].sort());
});


/** Interleave a synthetic mutable caller/source change while WA26 awaits.
 * The preview must never splice a previously reconciled M13/M14 claim
 * together with a later, silently changed claim. */
function mutateAtPolicy(f:Factory,change:()=>void){
 const original=f.ports.readScopedPolicy;
 f.ports.readScopedPolicy=async(scope,phase)=>{
  change();return original(scope,phase);
 };
}
function mutateAtCatalog(f:Factory,change:()=>void){
 const original=f.ports.readScopedCatalog;
 f.ports.readScopedCatalog=async(scope,phase)=>{
  change();return original(scope,phase);
 };
}
test('AUD-M15-41 consent revoked during policy port denies mixed-time preview',async()=>{
 const f=factory();
 mutateAtPolicy(f,()=>{f.m14Ledger.consents[0].state='REVOKED';});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-42 unrelated MARKETING consent changed during catalog read denies',async()=>{
 const f=factory();
 f.m14Ledger.consents.push({
  consent_purpose_ref:'MARKETING',state:'DENIED',
  valid_from_ms:NOW-100,valid_until_ms:NOW+20000,revision:7,
 });
 mutateAtCatalog(f,()=>{f.m14Ledger.consents[1].state='GRANTED';});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-43 shop-wide suppression added during WA26 read denies',async()=>{
 const f=factory();
 mutateAtPolicy(f,()=>f.m14Ledger.suppressions.push({
  consent_purpose_ref:null,active:true,revision:8,
 }));
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-44 grant revoked during catalog read denies',async()=>{
 const f=factory();
 mutateAtCatalog(f,()=>{f.m14Ledger.grants[0].state='REVOKED';});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-45 provider components changed after M13 reading denies',async()=>{
 const f=factory();
 mutateAtPolicy(f,()=>{f.m13Provider.details[0].components[0].text='MUTATED';});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-46 S0 catalog version changed between sources denies',async()=>{
 const f=factory();
 mutateAtCatalog(f,()=>{f.m13S0.templates[0].version_ref='VERSION_99';});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-47 original request campaign changed during read denied',async()=>{
 const f=factory();
 mutateAtPolicy(f,()=>{f.q.campaign_ref='CAMPAIGN_2';});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-48 host scope WABA changed after reconciliation denied',async()=>{
 const f=factory();
 mutateAtCatalog(f,()=>{f.m13Host.waba_id='100009';});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-49 WA26 scope changed after captured at PLAN denied',async()=>{
 const f=factory();
 mutateAtPolicy(f,()=>{f.scope.actor_ref='PLANNER_B';});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-50 WA26 policy changed after captured at PLAN denied',async()=>{
 const f=factory();
 mutateAtCatalog(f,()=>{f.policy.opted_out=true;});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-51 WA26 catalog changed after its port captured denied',async()=>{
 const f=factory();
 const original=f.ports.readScopedCatalog;
 f.ports.readScopedCatalog=async(scope,phase)=>{
  const raw=await original(scope,phase);
  // Promise microtask mutation may happen before snapshot (then selector
  // sees new content); verify that it cannot create a positive F02 preview.
  f.templates[0].meta_status='PAUSED';
  return raw;
 };
 await deny(f,'WA26_POLICY_OR_CATALOG_DENIED');
});
test('AUD-M15-52 consent object injected getter mid-read denied without call',async()=>{
 const f=factory();let called=0;
 mutateAtPolicy(f,()=>{
  Object.defineProperty(f.m14Ledger.consents[0],'state',{
   enumerable:true,get(){called++;return 'GRANTED';},
  });
 });
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
 assert.equal(called,0);
});
test('AUD-M15-53 ledger array made sparse during async WA26 phase denies',async()=>{
 const f=factory();
 mutateAtCatalog(f,()=>{f.m14Ledger.consents.length=2;});
 await deny(f,'INPUT_CHANGED_DURING_PREVIEW');
});
test('AUD-M15-54 unchanged two-template preview remains deterministic',async()=>{
 const f=factory();f.templates=[purpose(2),purpose(1)];
 f.m13S0.templates=[catalog13(2),catalog13(1)];
 f.m13Provider.details=[details(1),details(2)];
 f.m14Ledger.grants=[grant(1),grant(2)];
 await success(f,2);
});
test('AUD-M15-55 unchanged snapshots deny no legitimate candidate',async()=>{
 const f=factory();
 mutateAtPolicy(f,()=>{});
 await success(f);
});
test('AUD-M15-56 policy mismatch must remain explicit and never expose PII',async()=>{
 const f=factory();f.policy.policy_revision=10;
 const out=await deny(f,'UNTRUSTED_SCOPE');
 assert.equal(JSON.stringify(out).includes('LEAD_A'),false);
});
