import test from 'node:test';
import assert from 'node:assert/strict';
import {
  selectPlannerTemplateCandidates,recheckPlannerTemplateCandidate,
  type PurposeTemplateSnapshot,type TrustedSelectionContext,
} from './template-purpose-eligibility.ts';

const context:TrustedSelectionContext={
  concessionaria_id:'shop_A',waba_ref:'waba_A',
  catalog_revision:7,language:'pt_BR',purpose_ref:'recontato',
  actor_kind:'PLANNER',actor_ref:'planner_A',flow_ref:'flow_A',
  campaign_ref:null,
};
const row:PurposeTemplateSnapshot={
  template_ref:'template_A',version_ref:'approved_v2',
  catalog_revision:7,concessionaria_id:'shop_A',waba_ref:'waba_A',
  language:'pt_BR',meta_category:'MARKETING',
  meta_status:'APPROVED',locally_active:true,current_version:true,
  purpose_refs:['recontato','campanha_junho'],
  grants:[{
    purpose_ref:'recontato',actor_kind:'PLANNER',
    actor_ref:'planner_A',flow_ref:'flow_A',campaign_ref:null,
  },{
    purpose_ref:'campanha_junho',actor_kind:'PLANNER',
    actor_ref:'planner_A',flow_ref:'flow_A',campaign_ref:'campaign_123',
  }],
};
const select=(rows:unknown=[row],c:unknown=context)=>
  selectPlannerTemplateCandidates(rows,c);
const includes=(rows:unknown=[row],c:unknown=context)=>
  select(rows,c).candidates.length>0;

test('WA25-01 approved active and exact purpose grant yields identifier-only candidate',()=>{
  const result=select();
  assert.equal(result.candidates.length,1);
  assert.deepEqual(result.candidates[0],{
    template_ref:'template_A',version_ref:'approved_v2',
    catalog_revision:7,meta_category:'MARKETING',
    purpose_ref:'recontato',send_authorized:false,production_authorized:false,
  });
  assert.equal(result.send_authorized,false);
  assert.equal(result.requires_external_recheck,true);
  assert.equal(Object.isFrozen(result.candidates[0]),true);
  assert.equal(Object.isFrozen(result.candidates),true);
});
test('WA25-02 Meta category and internal purposes are independent',()=>{
  assert.equal(includes([{...row,meta_category:'UTILITY'}]),true);
  assert.equal(includes([row],{...context,purpose_ref:'MARKETING'}),false);
});
test('WA25-03 association without explicit matching grant cannot be planned',()=>{
  assert.equal(includes([{...row,grants:[]}]),false);
  assert.equal(includes([{...row,purpose_refs:['campanha_junho']}]),false);
});
test('WA25-04 grants for another purpose never extend the requested purpose',()=>{
  const onlyCampaign={...row,grants:[row.grants[1]]};
  assert.equal(includes([onlyCampaign]),false);
  assert.equal(includes([onlyCampaign],{...context,purpose_ref:'campanha_junho',
    campaign_ref:'campaign_123'}),true);
});
test('WA25-05 neither concessionaria nor WABA are interchangeable',()=>{
  assert.equal(includes([{...row,concessionaria_id:'shop_B'}]),false);
  assert.equal(includes([{...row,waba_ref:'waba_B'}]),false);
  assert.equal(includes([row],{...context,concessionaria_id:'shop_B'}),false);
  assert.equal(includes([row],{...context,waba_ref:'waba_B'}),false);
});
test('WA25-06 actor kind and authenticated actor reference are independent gates',()=>{
  assert.equal(includes([row],{...context,actor_kind:'CONSULTOR'}),false);
  assert.equal(includes([row],{...context,actor_ref:'planner_B'}),false);
  const toConsultor={...row,grants:[...row.grants,{
    purpose_ref:'recontato',actor_kind:'CONSULTOR' as const,
    actor_ref:'consultor_7',flow_ref:'flow_A',campaign_ref:null,
  }]};
  assert.equal(includes([toConsultor],{...context,actor_kind:'CONSULTOR',
    actor_ref:'consultor_7'}),true);
});
test('WA25-07 flow must match exact grant; no wildcard permission',()=>{
  assert.equal(includes([row],{...context,flow_ref:'flow_B'}),false);
  assert.equal(includes([{...row,grants:[{...row.grants[0],flow_ref:'*'}]}]),false);
});
test('WA25-08 campaign grant never leaks into non-campaign context',()=>{
  assert.equal(includes([row],{...context,purpose_ref:'campanha_junho'}),false);
  assert.equal(includes([row],{...context,purpose_ref:'campanha_junho',
    campaign_ref:'campaign_other'}),false);
  assert.equal(includes([row],{...context,purpose_ref:'campanha_junho',
    campaign_ref:'campaign_123'}),true);
});
test('WA25-09 all unapproved provider statuses are denied',()=>{
  for(const status of ['PENDING','PAUSED','REJECTED','DISABLED'] as const){
    assert.equal(includes([{...row,meta_status:status}]),false);
  }
});
test('WA25-10 local suspension, obsolete version and catalog revisions fail closed',()=>{
  assert.equal(includes([{...row,locally_active:false}]),false);
  assert.equal(includes([{...row,current_version:false}]),false);
  assert.equal(includes([{...row,catalog_revision:6}]),false);
  assert.equal(includes([row],{...context,catalog_revision:8}),false);
});
test('WA25-11 language and missing trusted context deny without fallback',()=>{
  assert.equal(includes([{...row,language:'en_US'}]),false);
  assert.equal(includes([row],{...context,language:'en_US'}),false);
  assert.equal(includes([row],null),false);
  assert.equal(includes([row],{...context,actor_ref:''}),false);
});
test('WA25-12 extra fields and inherited properties never grant permission',()=>{
  assert.equal(includes([{...row,send_authorized:true}]),false);
  assert.equal(includes([Object.assign(Object.create({meta_status:'APPROVED'}),row)]),false);
  assert.equal(includes([row],{...context,override_consent:true}),false);
});
test('WA25-13 hostile accessors in scope/template/grant are not executed',()=>{
  const evil={...row};
  Object.defineProperty(evil,'meta_status',{get(){throw Error('UNTRUSTED_GETTER');}});
  assert.equal(includes([evil]),false);
  const evilContext={...context};
  Object.defineProperty(evilContext,'actor_ref',{get(){throw Error('UNTRUSTED_GETTER');}});
  assert.equal(includes([row],evilContext),false);
  const evilGrant={...row.grants[0]};
  Object.defineProperty(evilGrant,'actor_ref',{get(){throw Error('UNTRUSTED_GETTER');}});
  assert.equal(includes([{...row,grants:[evilGrant]}]),false);
});
test('WA25-14 malformed grants and undeclared purpose association fail closed',()=>{
  assert.equal(includes([{...row,grants:[{...row.grants[0],
    purpose_ref:'hidden_other_purpose'}]}]),false);
  assert.equal(includes([{...row,grants:['not-a-grant']}]),false);
  assert.equal(includes([{...row,purpose_refs:['recontato','recontato']}]),false);
  assert.equal(includes([{...row,purpose_refs:['recontato','wrong/{{x}}']}]),false);
});
test('WA25-15 duplicated template IDs (including versions) are withheld',()=>{
  assert.equal(select([row,{...row,version_ref:'approved_v3'}]).candidates.length,0);
  assert.equal(select([row,row]).candidates.length,0);
});
test('WA25-16 current candidate still requires fresh catalog/actor recheck',()=>{
  const selected=select().candidates[0];
  assert.equal(recheckPlannerTemplateCandidate(selected,[row],context),true);
  assert.equal(recheckPlannerTemplateCandidate(selected,[{...row,meta_status:'PAUSED'}],context),false);
  assert.equal(recheckPlannerTemplateCandidate(selected,[row],{...context,actor_ref:'other'}),false);
  assert.equal(recheckPlannerTemplateCandidate(selected,[{...row,version_ref:'v3'}],context),false);
  assert.equal(recheckPlannerTemplateCandidate({...selected,send_authorized:true},[row],context),false);
});
test('WA25-17 a positive recheck STILL does not authorize a send',()=>{
  const selected=select().candidates[0];
  assert.equal(recheckPlannerTemplateCandidate(selected,[row],context),true);
  assert.equal(selected.send_authorized,false);
  assert.equal(selected.production_authorized,false);
  assert.equal('recipient' in selected,false);
  assert.equal('text' in selected,false);
  assert.equal('consent_status' in selected,false);
});
test('WA25-18 untrusted object keys and missing catalog always deny',()=>{
  assert.equal(includes({},context),false);
  assert.equal(includes(undefined,context),false);
  assert.equal(includes([null,{template_ref:'t'}],context),false);
  assert.equal(includes([{...row,grants:undefined}],context),false);
  assert.equal(includes([row],{...context,campaign_ref:undefined}),false);
});
