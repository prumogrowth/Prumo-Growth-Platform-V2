import test from 'node:test';
import assert from 'node:assert/strict';
import {F01_SOURCE_LAB_INPUT,F01_SOURCE_LAB_RESULT,reviewF01CommercialSources as review}
  from '../f01-commercial-source-review-lab.mjs';

const vers=()=>({catalog:4,knowledge:7,policy:2,consent:6,grant:8});
const current=()=>({sourceRef:'source_active',storeRef:'shop1',kind:'current',
  approvalState:'APPROVED_ACTIVE',sourceVersion:10,validUntilMs:500,
  correctedByRef:null,claimCodes:['OFFER_A','DETAIL_A']});
const history=()=>({sourceRef:'source_old',storeRef:'shop1',kind:'historical',
  approvalState:'EXPIRED',sourceVersion:2,validUntilMs:90,
  correctedByRef:null,claimCodes:['RETRO']});
function fixture(){
  const s={storeRef:'shop1',caseRef:'case1',personRef:'person1',purposeRef:'sales'};
  const snapshot=(time)=>({...s,observedAtMs:time,versions:vers(),contentPolicy:'LAB_ALLOWED',
    snapshotState:'LAB_UNVERIFIED',sources:[current(),history()]});
  return {schemaVersion:F01_SOURCE_LAB_INPUT,
    request:{requestRef:'req1',...s,startedAtMs:100,deadlineMs:250,
      versions:vers(),claims:[{sourceRef:'source_active',claimCode:'OFFER_A',usage:'commercial'}]},
    before:snapshot(110),after:snapshot(180)};
}
const both=(i,fn)=>{fn(i.before.sources[0]);fn(i.after.sources[0]);};
const useHistory=i=>{i.request.claims=[{sourceRef:'source_old',claimCode:'RETRO',usage:'interpretive'}];};
function check(fn,status,stage){
  const i=fixture();fn(i);const o=review(i);
  assert.equal(o.status,status);
  if(stage)assert.equal(o.stage,stage);
  return o;
}
function noAuthority(x){
  assert.equal(x.schemaVersion,F01_SOURCE_LAB_RESULT);
  for(const k of ['s0SourceAuthenticated','s0CatalogVerified','contentGrantVerified','provenanceAuthenticated',
    'semanticSupportVerified','commercialOfferAuthorized','modelContentAuthorized',
    'modelInvocationAuthorized','publishAuthorized','sendAuthorized','productionAuthorized'])
    assert.equal(x[k],false,k);
  assert.equal(x.requiresS0TransactionalRecheck,true);
}
test('OFF14-01 coherent synthetic sources are NOT authoritative',()=>{
  const x=review(fixture());assert.equal(x.status,'LAB_ELIGIBLE_UNVERIFIED');noAuthority(x);
});
test('OFF14-02 expiry after observation still grants no commercial offer',()=>noAuthority(check(
  i=>{i.before.observedAtMs=200;i.after.observedAtMs=250;},'LAB_ELIGIBLE_UNVERIFIED')));
test('OFF14-03 no identifiers or commercial knowledge in output',()=>{
  const s=JSON.stringify(review(fixture()));
  for(const value of ['shop1','person1','case1','req1','source_active','OFFER_A','claimCodes','expires'])assert.ok(!s.includes(value),value);
});
test('OFF14-04 output is immutable',()=>assert.equal(Object.isFrozen(review(fixture())),true));
test('OFF14-05 caller snapshot is unchanged',()=>{
  const i=fixture(),old=structuredClone(i);review(i);assert.deepEqual(i,old);
});
const cases=[
 ['cross-store before',i=>i.before.storeRef='shop2','DENIED','SCOPE'],
 ['cross-store after',i=>i.after.storeRef='shop2','DENIED','SCOPE'],
 ['cross-store source before',i=>i.before.sources[0].storeRef='shop2','DENIED','SCOPE'],
 ['cross-store source after',i=>i.after.sources[1].storeRef='shop2','DENIED','SCOPE'],
 ['cross-case before',i=>i.before.caseRef='case2','DENIED','SCOPE'],
 ['cross-case after',i=>i.after.caseRef='case2','DENIED','SCOPE'],
 ['cross-person before',i=>i.before.personRef='person2','DENIED','SCOPE'],
 ['cross-purpose after',i=>i.after.purposeRef='other','DENIED','SCOPE'],
 ['content denied before',i=>i.before.contentPolicy='LAB_DENIED','DENIED','CONTENT_POLICY'],
 ['content denied after',i=>i.after.contentPolicy='LAB_DENIED','DENIED','CONTENT_POLICY'],
 ['content unknown before',i=>i.before.contentPolicy='LAB_UNKNOWN','REVIEW_REQUIRED','CONTENT_POLICY'],
 ['content unknown after',i=>i.after.contentPolicy='LAB_UNKNOWN','REVIEW_REQUIRED','CONTENT_POLICY'],
 ['initial clock backdated',i=>i.before.observedAtMs=99,'REVIEW_REQUIRED','CLOCK'],
 ['second clock regressed',i=>i.after.observedAtMs=109,'REVIEW_REQUIRED','CLOCK'],
 ['late recheck',i=>i.after.observedAtMs=251,'LATE_RECHECK','DEADLINE'],
 ['catalog version stale',i=>i.before.versions.catalog++,'STALE','VERSION'],
 ['knowledge version stale',i=>i.after.versions.knowledge++,'STALE','VERSION'],
 ['policy version stale',i=>i.after.versions.policy++,'STALE','VERSION'],
 ['grant version stale',i=>i.after.versions.grant++,'STALE','VERSION'],
 ['consent version stale',i=>i.after.versions.consent++,'STALE','VERSION'],
 ['unversioned claim code mutation',i=>i.after.sources[0].claimCodes.push('OFFER_B'),'REVIEW_REQUIRED','SOURCES_CHANGED'],
 ['approval altered during generation',i=>i.after.sources[0].approvalState='REVOKED','REVIEW_REQUIRED','SOURCES_CHANGED'],
 ['expiration altered without revision',i=>i.after.sources[0].validUntilMs=700,'REVIEW_REQUIRED','SOURCES_CHANGED'],
 ['new unseen source',i=>i.after.sources.push({...history(),sourceRef:'extra'}),'REVIEW_REQUIRED','SOURCES_CHANGED'],
 ['allowed codes mutated',i=>i.after.sources[0].claimCodes=['DETAIL_A'],'REVIEW_REQUIRED','SOURCES_CHANGED'],
 ['source version mutated',i=>i.after.sources[0].sourceVersion++,'REVIEW_REQUIRED','SOURCES_CHANGED'],
 ['missing source',i=>i.request.claims[0].sourceRef='source_missing','SOURCE_INVALID','NOT_IN_SNAPSHOT'],
 ['unsupported claim',i=>i.request.claims[0].claimCode='UNSUPPORTED','SOURCE_INVALID','CLAIM_UNSUPPORTED'],
 ['historical source as current commercial offer',i=>{i.request.claims=[{sourceRef:'source_old',claimCode:'RETRO',usage:'commercial'}];},'SOURCE_INVALID','HISTORICAL_OFFER'],
 ['paused commercial source',i=>both(i,s=>s.approvalState='PAUSED'),'SOURCE_INVALID','NOT_ACTIVE'],
 ['revoked commercial source',i=>both(i,s=>s.approvalState='REVOKED'),'SOURCE_INVALID','NOT_ACTIVE'],
 ['draft commercial source',i=>both(i,s=>s.approvalState='DRAFT'),'SOURCE_INVALID','NOT_ACTIVE'],
 ['expired commercial source',i=>both(i,s=>s.approvalState='EXPIRED'),'SOURCE_INVALID','NOT_ACTIVE'],
 ['unbounded offer expiry',i=>both(i,s=>s.validUntilMs=null),'SOURCE_INVALID','EXPIRED_OR_UNBOUNDED'],
 ['offer expires at recheck',i=>both(i,s=>s.validUntilMs=180),'SOURCE_INVALID','EXPIRED_OR_UNBOUNDED'],
 ['corrected offer source',i=>both(i,s=>s.correctedByRef='source_new'),'SOURCE_INVALID','CORRECTED'],
 ['revoked interpretive history',i=>{useHistory(i);i.before.sources[1].approvalState='REVOKED';i.after.sources[1].approvalState='REVOKED';},'SOURCE_INVALID','INTERPRETIVE_INELIGIBLE'],
 ['paused interpretive history',i=>{useHistory(i);i.before.sources[1].approvalState='PAUSED';i.after.sources[1].approvalState='PAUSED';},'SOURCE_INVALID','INTERPRETIVE_INELIGIBLE'],
 ['draft interpretive history',i=>{useHistory(i);i.before.sources[1].approvalState='DRAFT';i.after.sources[1].approvalState='DRAFT';},'SOURCE_INVALID','INTERPRETIVE_INELIGIBLE'],
 ['duplicate source refs',i=>i.after.sources.push({...history()}),'INVALID_INPUT','SHAPE']
];
if(cases.length!==40)throw new Error('test matrix must contain exactly 40 cases');
cases.forEach(([name,mutate,status,stage],j)=>{
  test('OFF14-'+String(j+6).padStart(2,'0')+' '+name,()=>{
    noAuthority(check(mutate,status,stage));
  });
});
