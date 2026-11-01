import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectWa14ConsentOffline as inspect,
 recheckWa14ConsentOffline as recheck}
 from './wa14-purpose-consent-preflight.ts';

const NOW=1_800_000_000_000;
const request=(mod:Record<string,unknown>={})=>({
 contract_version:'wa14-request.lab.v0.1',
 selection_ref:'SELECTION_1',concessionaria_id:'SHOP_A',
 waba_ref:'WABA_A',lead_ref:'LEAD_TEST_A',case_ref:'CASE_A',
 case_version:3,authorization_revision:7,
 template_ref:'TPL_A',template_version_ref:'TPL_A_V2',
 template_purpose_ref:'RECONTACT',consent_purpose_ref:'SERVICE',
 actor_kind:'PLANNER',actor_ref:'ACTOR_A',
 flow_ref:'FLOW_A',campaign_ref:null,
 now_ms:NOW,max_age_ms:60000,...mod,
});
const granted=(purpose='SERVICE')=>({
 consent_purpose_ref:purpose,state:'GRANTED',
 valid_from_ms:NOW-40000,valid_until_ms:NOW+40000,revision:4,
});
const activeGrant=(mod:Record<string,unknown>={})=>({
 template_ref:'TPL_A',template_version_ref:'TPL_A_V2',
 template_purpose_ref:'RECONTACT',consent_purpose_ref:'SERVICE',
 actor_kind:'PLANNER',actor_ref:'ACTOR_A',flow_ref:'FLOW_A',
 campaign_ref:null,state:'ACTIVE',revision:7,...mod,
});
const suppressed=(purpose:string|null='SERVICE',active=true)=>({
 consent_purpose_ref:purpose,active,revision:6,
});
const ledger=(mod:Record<string,unknown>={})=>({
 contract_version:'wa14-s0-ledger.lab.v0.1',
 selection_ref:'SELECTION_1',concessionaria_id:'SHOP_A',
 waba_ref:'WABA_A',lead_ref:'LEAD_TEST_A',case_ref:'CASE_A',
 case_version:3,authorization_revision:7,
 policy_revision:12,consent_revision:5,suppression_revision:6,
 grant_revision:7,observed_at_ms:NOW-1000,
 case_authorized:true,audience_eligible:true,
 campaign_eligibility:'NOT_APPLICABLE',
 consents:[granted()],suppressions:[],grants:[activeGrant()],...mod,
});
type Result=ReturnType<typeof inspect>;
function noAuthority(r:Result){
 for(const f of ['consent_verified','consent_source_authenticated',
  's0_source_authenticated','principal_verified','tenant_binding_verified',
  'suppression_source_authenticated','grant_source_authenticated',
  'template_approval_verified','campaign_authorized','send_authorized',
  'production_authorized','s0_write_authorized','ack_allowed',
  'http_response_authorized','graph_dispatch_authorized',
  'automatic_retry_authorized'] as const)assert.equal(r[f],false,f);
 assert.equal(Object.isFrozen(r),true);
 for(const secret of ['LEAD_TEST_A','CASE_A','WABA_A','ACTOR_A',
  'SUPPRESSED_PHONE','GRAPH_SECRET','CONSENT_RECEIPT'])assert.equal(
  JSON.stringify(r).includes(secret),false,secret);
}
function ok(r:Result,name:'LAB_POLICY_COHERENT_UNVERIFIED'|
 'LAB_RECHECKED_UNVERIFIED'='LAB_POLICY_COHERENT_UNVERIFIED'){
 noAuthority(r);assert.equal(r.decision,name);assert.equal(r.reason,null);
}
function denied(r:Result,reason?:Result['reason']){
 noAuthority(r);assert.equal(r.decision,'DENIED');
 if(reason)assert.equal(r.reason,reason);
}
const run=(r:unknown=request(),s:unknown=ledger())=>inspect(r,s);
const revisit=(r:unknown=request(),s:unknown=ledger(),
 nr:unknown=request({now_ms:NOW+1000}),
 ns:unknown=ledger({observed_at_ms:NOW}))=>recheck(r,s,nr,ns);

test('M14-01 explicit SERVICE consent and RECONTACT grant is LAB-only',()=>{
 ok(run());
});
test('M14-02 no consent, even with active grant, denied',()=>{
 denied(run(request(),ledger({consents:[]})),'CONSENT_DENIED');
});
test('M14-03 other consent purpose cannot authorize SERVICE',()=>{
 denied(run(request(),ledger({consents:[granted('MARKETING')]})),'CONSENT_DENIED');
});
test('M14-04 utility or Meta category cannot imply consent purpose',()=>{
 denied(run(request({consent_purpose_ref:'MARKETING'}),
  ledger({consents:[granted('MARKETING')]})),'GRANT_DENIED');
});
test('M14-05 consent UNKNOWN denied',()=>{
 denied(run(request(),ledger({consents:[{...granted(),state:'UNKNOWN'}]})),
  'CONSENT_DENIED');
});
test('M14-06 consent DENIED denied',()=>{
 denied(run(request(),ledger({consents:[{...granted(),state:'DENIED'}]})),
  'CONSENT_DENIED');
});
test('M14-07 revoked consent denied',()=>{
 denied(run(request(),ledger({consents:[{...granted(),state:'REVOKED'}]})),
  'CONSENT_DENIED');
});
test('M14-08 expired consent at exact boundary denied',()=>{
 denied(run(request(),ledger({consents:[{
  ...granted(),valid_until_ms:NOW,
 }]})),'CONSENT_DENIED');
});
test('M14-09 consent not yet valid denied',()=>{
 denied(run(request(),ledger({consents:[{
  ...granted(),valid_from_ms:NOW+1,
 }]})),'CONSENT_DENIED');
});
test('M14-10 active purpose suppression denied',()=>{
 denied(run(request(),ledger({suppressions:[suppressed()]})),'SUPPRESSED');
});
test('M14-11 active shop-wide suppression denied',()=>{
 denied(run(request(),ledger({suppressions:[suppressed(null)]})),
  'SUPPRESSED');
});
test('M14-12 suppressing another purpose does not expand to SERVICE',()=>{
 ok(run(request(),ledger({suppressions:[suppressed('MARKETING')]})));
});
test('M14-13 INACTIVE suppression is not treated as opt-out',()=>{
 ok(run(request(),ledger({suppressions:[suppressed('SERVICE',false)]})));
});
test('M14-14 grant missing is denied despite valid consent',()=>{
 denied(run(request(),ledger({grants:[]})),'GRANT_DENIED');
});
test('M14-15 revoked grant denied despite consent',()=>{
 denied(run(request(),ledger({grants:[activeGrant({state:'REVOKED'})]})),
  'GRANT_DENIED');
});
test('M14-16 changed actor cannot reuse another actor grant',()=>{
 denied(run(request({actor_ref:'ACTOR_B'})), 'GRANT_DENIED');
});
test('M14-17 changed template version cannot reuse original grant',()=>{
 denied(run(request({template_version_ref:'TPL_A_V3'})),
  'GRANT_DENIED');
});
test('M14-18 changed flow cannot reuse grant',()=>{
 denied(run(request({flow_ref:'FLOW_B'})),'GRANT_DENIED');
});
test('M14-19 campaign requires separate campaign and matching grant',()=>{
 const r=request({campaign_ref:'CAMPAIGN_1'});
 const p=ledger({campaign_eligibility:'ELIGIBLE',
  grants:[activeGrant({campaign_ref:'CAMPAIGN_1'})]});
 ok(run(r,p));
});
test('M14-20 campaign with no matching grant denied',()=>{
 denied(run(request({campaign_ref:'CAMPAIGN_1'}),
  ledger({campaign_eligibility:'ELIGIBLE'})),'GRANT_DENIED');
});
test('M14-21 UNKNOWN campaign denied',()=>{
 denied(run(request({campaign_ref:'CAMPAIGN_1'}),
  ledger({campaign_eligibility:'UNKNOWN'})),'CAMPAIGN_DENIED');
});
test('M14-22 campaign assertion for noncampaign request denied',()=>{
 denied(run(request(),ledger({campaign_eligibility:'ELIGIBLE'})),
  'CAMPAIGN_DENIED');
});
test('M14-23 case revocation denied',()=>{
 denied(run(request(),ledger({case_authorized:false})),
  'CASE_OR_AUDIENCE_DENIED');
});
test('M14-24 audience revocation denied',()=>{
 denied(run(request(),ledger({audience_eligible:false})),
  'CASE_OR_AUDIENCE_DENIED');
});
test('M14-25 cross-tenant policy snapshot denied',()=>{
 denied(run(request(),ledger({concessionaria_id:'SHOP_B'})),
  'SCOPE_MISMATCH');
});
test('M14-26 wrong WABA denied',()=>{
 denied(run(request(),ledger({waba_ref:'WABA_B'})),
  'SCOPE_MISMATCH');
});
test('M14-27 wrong lead denied without leaking lead',()=>{
 denied(run(request(),ledger({lead_ref:'LEAD_TEST_B'})),
  'SCOPE_MISMATCH');
});
test('M14-28 wrong case revision denied',()=>{
 denied(run(request(),ledger({case_version:4})),
  'SCOPE_MISMATCH');
});
test('M14-29 stale policy ledger denied',()=>{
 denied(run(request(),ledger({observed_at_ms:NOW-60001})),
  'STALE_OR_FUTURE_SNAPSHOT');
});
test('M14-30 future-dated ledger denied',()=>{
 denied(run(request(),ledger({observed_at_ms:NOW+1})),
  'STALE_OR_FUTURE_SNAPSHOT');
});
test('M14-31 malformed duplicate consent purposes fail closed',()=>{
 denied(run(request(),ledger({consents:[granted(),granted()]})),
  'INVALID_INPUT');
});
test('M14-32 duplicate suppressions fail closed',()=>{
 denied(run(request(),ledger({suppressions:[suppressed(null),suppressed(null)]})),
  'INVALID_INPUT');
});
test('M14-33 duplicate grant tuple fails closed',()=>{
 denied(run(request(),ledger({grants:[activeGrant(),activeGrant()]})),
  'INVALID_INPUT');
});
test('M14-34 consent revision greater than snapshot denied',()=>{
 denied(run(request(),ledger({consents:[{...granted(),revision:6}]})),
  'INVALID_INPUT');
});
test('M14-35 getter in grant denied without invocation',()=>{
 let hits=0;const g=activeGrant();
 Object.defineProperty(g,'state',{enumerable:true,get(){
  hits++;return 'ACTIVE';
 }});
 denied(run(request(),ledger({grants:[g]})),'INVALID_INPUT');
 assert.equal(hits,0);
});
test('M14-36 sparse consent list denied',()=>{
 const c=[granted()];c.length=2;
 denied(run(request(),ledger({consents:c})),'INVALID_INPUT');
});
test('M14-37 unexpected authority field in request denied',()=>{
 denied(run({...request(),send_authorized:true}),'INVALID_INPUT');
});
test('M14-38 fresh unchanged lab recheck has no authority',()=>{
 ok(revisit(),'LAB_RECHECKED_UNVERIFIED');
});
test('M14-39 opt-out emerging after initial check denied on recheck',()=>{
 denied(revisit(request(),ledger(),request({now_ms:NOW+1000}),
  ledger({observed_at_ms:NOW,suppressions:[suppressed()]})),
  'SUPPRESSED');
});
test('M14-40 grant revoked after initial check denied on recheck',()=>{
 denied(revisit(request(),ledger(),request({now_ms:NOW+1000}),
  ledger({observed_at_ms:NOW,grants:[activeGrant({state:'REVOKED'})]})),
  'GRANT_DENIED');
});
test('M14-41 consent changed after first read denied',()=>{
 denied(revisit(request(),ledger(),request({now_ms:NOW+1000}),
  ledger({observed_at_ms:NOW,consents:[{...granted(),state:'REVOKED'}]})),
  'CONSENT_DENIED');
});
test('M14-42 policy revision changed though still eligible denies continuation',()=>{
 denied(revisit(request(),ledger(),request({now_ms:NOW+1000}),
  ledger({observed_at_ms:NOW,policy_revision:13})),
  'REVISION_OR_CONTEXT_CHANGED');
});
test('M14-43 suppression revision increased, even still clear denies',()=>{
 denied(revisit(request(),ledger(),request({now_ms:NOW+1000}),
  ledger({observed_at_ms:NOW,suppression_revision:7})),
  'REVISION_OR_CONTEXT_CHANGED');
});
test('M14-44 matching values but different lead on recheck denied',()=>{
 denied(revisit(request(),ledger(),request({
  now_ms:NOW+1000,lead_ref:'LEAD_TEST_B',
 }),ledger({observed_at_ms:NOW,lead_ref:'LEAD_TEST_B'})),
  'REVISION_OR_CONTEXT_CHANGED');
});
test('M14-45 recheck cannot move clock backwards',()=>{
 denied(revisit(request(),ledger(),request({now_ms:NOW-1}),
  ledger({observed_at_ms:NOW-500})),
  'REVISION_OR_CONTEXT_CHANGED');
});
test('M14-46 replaying a positive check does not claim idempotency',()=>{
 ok(run());ok(run());ok(revisit(),'LAB_RECHECKED_UNVERIFIED');
});
test('M14-47 untrusted getter in scope denied',()=>{
 let hits=0;const x=request();
 Object.defineProperty(x,'concessionaria_id',{enumerable:true,get(){
  hits++;return 'SHOP_A';
 }});
 denied(run(x),'INVALID_INPUT');assert.equal(hits,0);
});
test('M14-48 malformed suppression revision denied',()=>{
 denied(run(request(),ledger({suppressions:[
  {...suppressed(),revision:7},
 ]})),'INVALID_INPUT');
});
test('M14-49 grant at another purpose alone cannot authorize selection',()=>{
 denied(run(request(),ledger({grants:[
  activeGrant({template_purpose_ref:'PROMOTION',
   consent_purpose_ref:'MARKETING'}),
 ]})),'GRANT_DENIED');
});
test('M14-50 consent granted to multiple purposes remains separate',()=>{
 ok(run(request(),ledger({consents:[granted(),granted('MARKETING')]})));
 denied(run(request({consent_purpose_ref:'MARKETING'}),
  ledger({consents:[granted(),granted('MARKETING')]})),
  'GRANT_DENIED');
});
