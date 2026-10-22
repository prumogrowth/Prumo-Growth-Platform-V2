import test from 'node:test';
import assert from 'node:assert/strict';
import {
  prepareS0TemplateCandidatesFixture,recheckS0TemplateCandidateFixture,
  type Wa26Scope,type Wa26Policy,type Wa26FixturePorts,
} from './s0-template-purpose-bridge.ts';
import type {PurposeTemplateSnapshot} from './template-purpose-eligibility.ts';

const scope:Wa26Scope={
  selection_ref:'fixture_selection_100',
  concessionaria_id:'shop_A',waba_ref:'waba_A',catalog_revision:8,
  language:'pt_BR',purpose_ref:'recontato',
  actor_kind:'PLANNER',actor_ref:'planner_A',flow_ref:'flow_A',
  campaign_ref:null,case_ref:'case_A',lead_ref:'lead_A',
  case_version:4,authorization_revision:2,
};
const policy:Wa26Policy={
  selection_ref:'fixture_selection_100',
  concessionaria_id:'shop_A',waba_ref:'waba_A',
  case_ref:'case_A',lead_ref:'lead_A',
  case_version:4,authorization_revision:2,policy_revision:3,
  consent_state:'VALID',opted_out:false,case_authorized:true,
  audience_eligible:true,campaign_eligibility:'NOT_APPLICABLE',
};
const template:PurposeTemplateSnapshot={
  template_ref:'template_A',version_ref:'v5',catalog_revision:8,
  concessionaria_id:'shop_A',waba_ref:'waba_A',language:'pt_BR',
  meta_category:'UTILITY',meta_status:'APPROVED',locally_active:true,
  current_version:true,purpose_refs:['recontato'],
  grants:[{
    purpose_ref:'recontato',actor_kind:'PLANNER',actor_ref:'planner_A',
    flow_ref:'flow_A',campaign_ref:null,
  }],
};

function fixture(){
  const state:{
    scope:unknown; policy:unknown; catalog:unknown;
    phases:string[];
  }={
    scope:structuredClone(scope),policy:structuredClone(policy),
    catalog:[structuredClone(template)],phases:[],
  };
  const ports:Wa26FixturePorts={
    async resolveSelection(ref,phase){
      state.phases.push('scope:'+phase+':'+ref);
      return state.scope;
    },
    async readScopedPolicy(_scope,phase){
      state.phases.push('policy:'+phase);
      return state.policy;
    },
    async readScopedCatalog(_scope,phase){
      state.phases.push('catalog:'+phase);
      return state.catalog;
    },
  };
  return {state,ports};
}
const plan=async(f:ReturnType<typeof fixture>)=>
  prepareS0TemplateCandidatesFixture(scope.selection_ref,f.ports);
const first=async(f:ReturnType<typeof fixture>)=>{
  const result=await plan(f);
  assert.equal(result.decision,'LAB_CANDIDATES');
  if(result.decision!=='LAB_CANDIDATES')throw Error('wrong gate');
  return result.internal_tickets[0];
};
const deny=async(f:ReturnType<typeof fixture>,reason:string)=>{
  const result=await plan(f);
  assert.equal(result.decision,'DENIED');
  if(result.decision==='DENIED')assert.equal(result.reason,reason);
  assert.deepEqual(result.candidates,[]);
  assert.equal(result.production_authorized,false);
};

test('WA26-01 PLAN emits minimal candidates and internal-only tickets, never send authority',async()=>{
  const f=fixture();
  const p=await plan(f);
  assert.equal(p.decision,'LAB_CANDIDATES');
  assert.deepEqual(p.candidates.map(x=>x.template_ref),['template_A']);
  assert.equal(p.send_authorized,false);
  assert.equal(p.production_authorized,false);
  assert.equal('lead_ref' in p.candidates[0],false);
  assert.equal('case_ref' in p.candidates[0],false);
  assert.equal('recipient' in p.candidates[0],false);
  if(p.decision==='LAB_CANDIDATES'){
    assert.equal(p.internal_tickets[0].phase,'PLAN');
    assert.equal(p.internal_tickets[0].case_ref,'case_A');
    assert.equal(Object.isFrozen(p.internal_tickets),true);
  }
  assert.deepEqual(f.state.phases,[
    'scope:PLAN:fixture_selection_100','policy:PLAN','catalog:PLAN',
  ]);
});
test('WA26-02 phase chain rereads policy/catalog/identity three times',async()=>{
  const f=fixture(),t=await first(f);
  const reserve=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
  assert.equal(reserve.decision,'LAB_RECHECKED');
  if(reserve.decision!=='LAB_RECHECKED')return;
  assert.equal(reserve.internal_ticket.phase,'RESERVE');
  const dispatch=await recheckS0TemplateCandidateFixture(
    reserve.internal_ticket,'PRE_DISPATCH',f.ports);
  assert.equal(dispatch.decision,'LAB_RECHECKED');
  assert.equal(dispatch.production_authorized,false);
  assert.equal(f.state.phases.length,9);
  assert.equal(f.state.phases[6],'scope:PRE_DISPATCH:fixture_selection_100');
});
test('WA26-03 unknown or denied consent fails closed before exposing catalog',async()=>{
  for(const state of ['UNKNOWN','DENIED'] as const){
    const f=fixture();
    f.state.policy={...policy,consent_state:state};
    await deny(f,'POLICY_DENIED');
    assert.equal(f.state.phases.some(x=>x.startsWith('catalog')),false);
  }
});
test('WA26-04 opt-out of A blocks A even with valid template/grant',async()=>{
  const f=fixture();f.state.policy={...policy,opted_out:true};
  await deny(f,'POLICY_DENIED');
});
test('WA26-05 case authorization revoked between planning and reserve',async()=>{
  const f=fixture(),t=await first(f);
  f.state.policy={...policy,case_authorized:false};
  const res=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
  assert.equal(res.decision,'DENIED');
  if(res.decision==='DENIED')assert.equal(res.reason,'POLICY_DENIED');
});
test('WA26-06 audience eligibility is not inferred from template approval',async()=>{
  const f=fixture();f.state.policy={...policy,audience_eligible:false};
  await deny(f,'POLICY_DENIED');
});
test('WA26-07 campaign requires separate matching grant AND trusted eligibility',async()=>{
  const f=fixture();
  f.state.scope={...scope,purpose_ref:'campaign_open',campaign_ref:'campaign_7'};
  f.state.policy={...policy,campaign_eligibility:'ELIGIBLE'};
  f.state.catalog=[{...template,
    purpose_refs:['recontato','campaign_open'],
    grants:[...template.grants,{purpose_ref:'campaign_open',actor_kind:'PLANNER',
      actor_ref:'planner_A',flow_ref:'flow_A',campaign_ref:'campaign_7'}],
  }];
  const p=await plan(f);
  assert.equal(p.decision,'LAB_CANDIDATES');
  if(p.decision==='LAB_CANDIDATES')assert.equal(p.candidates[0].purpose_ref,'campaign_open');
});
test('WA26-08 campaign eligibility alone never creates missing purpose grant',async()=>{
  const f=fixture();
  f.state.scope={...scope,purpose_ref:'campaign_open',campaign_ref:'campaign_7'};
  f.state.policy={...policy,campaign_eligibility:'ELIGIBLE'};
  await deny(f,'CATALOG_DENIED');
});
test('WA26-09 a campaign ID with UNKNOWN eligibility always denies',async()=>{
  const f=fixture();
  f.state.scope={...scope,campaign_ref:'campaign_7'};
  f.state.policy={...policy,campaign_eligibility:'UNKNOWN'};
  await deny(f,'POLICY_DENIED');
});
test('WA26-10 no-campaign path denies fabricated campaign eligibility',async()=>{
  const f=fixture();
  f.state.policy={...policy,campaign_eligibility:'ELIGIBLE'};
  await deny(f,'POLICY_DENIED');
});
test('WA26-11 tenant mismatch in policy is not a grant to another shop',async()=>{
  const f=fixture();
  f.state.policy={...policy,concessionaria_id:'shop_B'};
  await deny(f,'UNTRUSTED_SCOPE');
});
test('WA26-12 WABA mismatch in policy is not an eligible channel',async()=>{
  const f=fixture();f.state.policy={...policy,waba_ref:'waba_B'};
  await deny(f,'UNTRUSTED_SCOPE');
});
test('WA26-13 actor revoked/changed at reserve invalidates cached choice',async()=>{
  const f=fixture(),t=await first(f);
  f.state.scope={...scope,actor_ref:'planner_B'};
  const out=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
  assert.equal(out.decision,'DENIED');
  if(out.decision==='DENIED')assert.equal(out.reason,'CATALOG_DENIED');
});
test('WA26-14 case version changed between stages invalidates internal ticket',async()=>{
  const f=fixture(),t=await first(f);
  f.state.scope={...scope,case_version:5};
  f.state.policy={...policy,case_version:5};
  const out=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
  assert.equal(out.decision,'DENIED');
  if(out.decision==='DENIED')assert.equal(out.reason,'STALE_OR_CHANGED');
});
test('WA26-15 auth or policy revision changes require fresh PLAN',async()=>{
  for(const key of ['authorization_revision','policy_revision'] as const){
    const f=fixture(),t=await first(f);
    if(key==='authorization_revision'){
      f.state.scope={...scope,authorization_revision:3};
      f.state.policy={...policy,authorization_revision:3};
    }else f.state.policy={...policy,policy_revision:4};
    const out=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
    assert.equal(out.decision,'DENIED');
    if(out.decision==='DENIED')assert.equal(out.reason,'STALE_OR_CHANGED');
  }
});
test('WA26-16 paused Meta template is withheld after reserve',async()=>{
  const f=fixture(),t=await first(f);
  f.state.catalog=[{...template,meta_status:'PAUSED'}];
  const out=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
  assert.equal(out.decision,'DENIED');
  if(out.decision==='DENIED')assert.equal(out.reason,'CATALOG_DENIED');
});
test('WA26-17 changed catalog revision or version fails candidate recheck',async()=>{
  for(const mode of ['revision','version']){
    const f=fixture(),t=await first(f);
    if(mode==='revision'){
      f.state.scope={...scope,catalog_revision:9};
      f.state.catalog=[{...template,catalog_revision:9}];
    }else f.state.catalog=[{...template,version_ref:'v6'}];
    const out=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
    assert.equal(out.decision,'DENIED');
  }
});
test('WA26-18 revoked purpose grant blocks PRE_DISPATCH even after RESERVE',async()=>{
  const f=fixture(),t=await first(f);
  const reserved=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
  assert.equal(reserved.decision,'LAB_RECHECKED');
  if(reserved.decision!=='LAB_RECHECKED')return;
  f.state.catalog=[{...template,grants:[]}];
  const out=await recheckS0TemplateCandidateFixture(reserved.internal_ticket,'PRE_DISPATCH',f.ports);
  assert.equal(out.decision,'DENIED');
});
test('WA26-19 skip RESERVE, fake phase and replay PRE_DISPATCH are rejected',async()=>{
  const f=fixture(),t=await first(f);
  assert.equal((await recheckS0TemplateCandidateFixture(t,'PRE_DISPATCH',f.ports)).decision,'DENIED');
  assert.equal((await recheckS0TemplateCandidateFixture({...t,phase:'PRE_DISPATCH'},
    'RESERVE',f.ports)).decision,'DENIED');
  assert.equal((await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports)).decision,'LAB_RECHECKED');
});
test('WA26-20 extra claims of send authority or accessor tickets are denied',async()=>{
  const f=fixture(),t=await first(f);
  for(const hostile of [
    {...t,production_authorized:true}, {...t,send_authorized:true},
    {...t,bypass_policy:true}, {...t,candidate:{...t.candidate,send_authorized:true}},
  ]){
    assert.equal((await recheckS0TemplateCandidateFixture(hostile,'RESERVE',f.ports)).decision,'DENIED');
  }
  const accessor={...t};
  Object.defineProperty(accessor,'case_ref',{get(){throw Error('EVIL_GETTER');}});
  assert.equal((await recheckS0TemplateCandidateFixture(accessor,'RESERVE',f.ports)).decision,'DENIED');
});
test('WA26-21 malformed S0 ports and failures deny without leaking details',async()=>{
  const f=fixture();
  assert.equal((await prepareS0TemplateCandidatesFixture('bad/ref',f.ports)).decision,'DENIED');
  assert.equal((await prepareS0TemplateCandidatesFixture(scope.selection_ref,{} as Wa26FixturePorts)).decision,'DENIED');
  const broken:Wa26FixturePorts={...f.ports,
    async readScopedPolicy(){throw Error('SECRET_OR_DB_DETAIL');}};
  const out=await prepareS0TemplateCandidatesFixture(scope.selection_ref,broken);
  assert.equal(out.decision,'DENIED');
  if(out.decision==='DENIED')assert.equal(out.reason,'DEPENDENCY_UNAVAILABLE');
  assert.equal(JSON.stringify(out).includes('SECRET'),false);
});
test('WA26-22 missing or forged scope/extra fields denied',async()=>{
  const f=fixture();
  f.state.scope={...scope,concessionaria_id:'shop_B'};
  await deny(f,'UNTRUSTED_SCOPE');
  f.state.scope={...scope,admin_mode:true};
  await deny(f,'UNTRUSTED_SCOPE');
  f.state.scope=null;
  await deny(f,'UNTRUSTED_SCOPE');
});
test('WA26-23 scope and policy accessors denied without invocation',async()=>{
  const f=fixture();
  const bad={...scope};
  Object.defineProperty(bad,'actor_ref',{get(){throw Error('SHOULD_NOT_RUN');}});
  f.state.scope=bad;
  await deny(f,'UNTRUSTED_SCOPE');
  f.state.scope=scope;
  const badPolicy={...policy};
  Object.defineProperty(badPolicy,'consent_state',{get(){throw Error('SHOULD_NOT_RUN');}});
  f.state.policy=badPolicy;
  await deny(f,'UNTRUSTED_SCOPE');
});
test('WA26-24 case/lead mismatched in policy denied, never defaults',async()=>{
  for(const key of ['case_ref','lead_ref'] as const){
    const f=fixture();f.state.policy={...policy,[key]:'other'};
    await deny(f,'UNTRUSTED_SCOPE');
  }
});
test('WA26-25 catalog with unrelated tenants yields zero candidates',async()=>{
  const f=fixture();f.state.catalog=[{...template,concessionaria_id:'shop_B'}];
  await deny(f,'CATALOG_DENIED');
});
test('WA26-26 a passed pre-dispatch check is NOT Graph authorization',async()=>{
  const f=fixture(),t=await first(f);
  const reserve=await recheckS0TemplateCandidateFixture(t,'RESERVE',f.ports);
  assert.equal(reserve.decision,'LAB_RECHECKED');
  if(reserve.decision!=='LAB_RECHECKED')return;
  const out=await recheckS0TemplateCandidateFixture(reserve.internal_ticket,'PRE_DISPATCH',f.ports);
  assert.equal(out.decision,'LAB_RECHECKED');
  assert.equal(out.send_authorized,false);
  assert.equal(out.production_authorized,false);
  assert.equal('graph_request' in out,false);
  assert.equal('window_24h_valid' in out,false);
  assert.equal('api_accepted' in out,false);
});
