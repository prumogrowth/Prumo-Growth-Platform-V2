import test from 'node:test';
import assert from 'node:assert/strict';
import {F01_OWNER_LAB_INPUT,F01_OWNER_LAB_OUTPUT,reviewF01S0Ownership as review}
  from '../f01-s0-ownership-review-lab.mjs';

const vers=()=>({case:1,cycle:2,assignment:3,catalog:4,knowledge:5,policy:6,route:7,consent:8});
function fixture(){
  const src={storeRef:'store1',caseRef:'case1',personRef:'person1'};
  const flags={ownerRoute:'AI',handoffDefinitive:false,humanized:false,optOut:false,
    channelEligible:true,postRemittance:false,postSale:false,snapshotState:'LAB_UNVERIFIED'};
  return {schemaVersion:F01_OWNER_LAB_INPUT,
    request:{requestRef:'req1',...src,purpose:'sales_attention',startedAtMs:100,deadlineMs:250,expectedVersions:vers()},
    before:{...src,...flags,versions:vers(),observedAtMs:110},
    after:{...src,...flags,versions:vers(),observedAtMs:180}};
}
const get=(f,status,stage)=>{
  const x=fixture();f(x);const y=review(x);
  assert.equal(y.status,status);if(stage)assert.equal(y.stage,stage);
  return y;
};
const zero=a=>{
  assert.equal(a.schemaVersion,F01_OWNER_LAB_OUTPUT);
  for(const k of ['principalAuthenticated','s0OwnerVerified','s0SnapshotAuthenticated','contentAuthorized',
    'modelInvocationAuthorized','publishAuthorized','handoffAuthorized',
    'consultantAssignmentAuthorized','f02RestartAuthorized','sent',
    'commercialTransitionAuthorized','productionAuthorized'])assert.equal(a[k],false,k);
  assert.equal(a.requiresS0TransactionalRecheck,true);
};
test('OFF13-01 coherent synthetic snapshots remain strictly unverified',()=>{
  const x=review(fixture());assert.equal(x.status,'LAB_CONSISTENT_UNVERIFIED');zero(x);
});
test('OFF13-02 no user, store, session or assignment identifier in result',()=>{
  const s=JSON.stringify(review(fixture()));
  for(const t of ['store1','person1','case1','req1','sales_attention','ownerRoute','cycle','policy'])assert.ok(!s.includes(t),t);
});
test('OFF13-03 result immutable',()=>assert.equal(Object.isFrozen(review(fixture())),true));
test('OFF13-04 caller data unchanged',()=>{const a=fixture(),b=structuredClone(a);review(a);assert.deepEqual(a,b);});
test('OFF13-05 output never grants message, consultant or F02 restart',()=>zero(review(fixture())));
test('OFF13-06 definitive human handoff before/after stays human only',()=>{
  const x=get(i=>{for(const k of ['before','after']){i[k].ownerRoute='HUMAN';i[k].handoffDefinitive=true;i[k].humanized=true;}},'HUMAN_ONLY_REVIEW','DEFINITIVE_HANDOFF');
  zero(x);
});
test('OFF13-07 inbound cannot undo durable human handoff',()=>get(i=>{
  i.before.ownerRoute='HUMAN';i.before.handoffDefinitive=true;i.before.humanized=true;
},'REVIEW_REQUIRED','HANDOFF_REGRESSION'));
test('OFF13-08 human handoff during inference blocks continuation',()=>get(i=>{
  i.after.ownerRoute='HUMAN';i.after.handoffDefinitive=true;i.after.humanized=true;
},'HUMAN_ONLY_REVIEW'));
test('OFF13-09 human owner alone before infer cannot be AI',()=>get(i=>{
  i.before.ownerRoute='HUMAN';
},'REVIEW_REQUIRED','HANDOFF_REGRESSION'));
test('OFF13-10 human owner alone at recheck denies',()=>get(i=>i.after.ownerRoute='HUMAN','HUMAN_ONLY_REVIEW'));
test('OFF13-11 humanized before rejects later AI even if version changes',()=>get(i=>{
  i.before.humanized=true;i.after.versions.route=15;
},'REVIEW_REQUIRED','HANDOFF_REGRESSION'));
test('OFF13-12 definitive handoff after even with owner AI blocks',()=>get(i=>i.after.handoffDefinitive=true,'HUMAN_ONLY_REVIEW'));
test('OFF13-13 before owner NONE blocks',()=>get(i=>i.before.ownerRoute='NONE','DENIED','OWNER'));
test('OFF13-14 after owner NONE blocks',()=>get(i=>i.after.ownerRoute='NONE','DENIED','OWNER'));
test('OFF13-15 opt-out before denies',()=>get(i=>i.before.optOut=true,'DENIED','OPT_OUT'));
test('OFF13-16 opt-out after denies',()=>get(i=>i.after.optOut=true,'DENIED','OPT_OUT'));
test('OFF13-17 opt-out outranks version stale',()=>get(i=>{i.after.optOut=true;i.after.versions.policy++;},'DENIED','OPT_OUT'));
test('OFF13-18 channel ineligible before denies',()=>get(i=>i.before.channelEligible=false,'DENIED','CHANNEL'));
test('OFF13-19 channel ineligible after denies',()=>get(i=>i.after.channelEligible=false,'DENIED','CHANNEL'));
test('OFF13-20 remittance before denies',()=>get(i=>i.before.postRemittance=true,'DENIED','POST_COMMERCIAL'));
test('OFF13-21 remittance after denies',()=>get(i=>i.after.postRemittance=true,'DENIED','POST_COMMERCIAL'));
test('OFF13-22 sale before denies',()=>get(i=>i.before.postSale=true,'DENIED','POST_COMMERCIAL'));
test('OFF13-23 sale after denies',()=>get(i=>i.after.postSale=true,'DENIED','POST_COMMERCIAL'));
test('OFF13-24 other store before denied',()=>get(i=>i.before.storeRef='other','DENIED','SCOPE'));
test('OFF13-25 other store after denied',()=>get(i=>i.after.storeRef='other','DENIED','SCOPE'));
test('OFF13-26 other case before denied',()=>get(i=>i.before.caseRef='other','DENIED','SCOPE'));
test('OFF13-27 other case after denied',()=>get(i=>i.after.caseRef='other','DENIED','SCOPE'));
test('OFF13-28 other person before denied',()=>get(i=>i.before.personRef='other','DENIED','SCOPE'));
test('OFF13-29 other person after denied',()=>get(i=>i.after.personRef='other','DENIED','SCOPE'));
test('OFF13-30 scope rejection precedes stale versions',()=>get(i=>{i.after.storeRef='other';i.after.versions.route++;},'DENIED','SCOPE'));
test('OFF13-31 stale before policy',()=>get(i=>i.before.versions.policy=9,'STALE','VERSION'));
test('OFF13-32 stale after route',()=>get(i=>i.after.versions.route=9,'STALE','VERSION'));
test('OFF13-33 stale after catalog',()=>get(i=>i.after.versions.catalog=10,'STALE','VERSION'));
test('OFF13-34 stale after consent',()=>get(i=>i.after.versions.consent=10,'STALE','VERSION'));
test('OFF13-35 stale after knowledge',()=>get(i=>i.after.versions.knowledge=10,'STALE','VERSION'));
test('OFF13-36 before snapshot predates request',()=>get(i=>i.before.observedAtMs=99,'REVIEW_REQUIRED','CLOCK'));
test('OFF13-37 after snapshot clock rollback',()=>get(i=>i.after.observedAtMs=109,'REVIEW_REQUIRED','CLOCK'));
test('OFF13-38 recheck after deadline',()=>get(i=>i.after.observedAtMs=251,'LATE_RECHECK','DEADLINE'));
test('OFF13-39 exact deadline still grants nothing',()=>{const r=get(i=>i.after.observedAtMs=250,'LAB_CONSISTENT_UNVERIFIED');zero(r);});
test('OFF13-40 snapshot must not claim verified state',()=>get(i=>i.after.snapshotState='S0_VERIFIED','INVALID_INPUT','SHAPE'));
test('OFF13-41 model cannot insert send authorization field',()=>get(i=>i.after.sendAuthorized=true,'INVALID_INPUT','SHAPE'));
test('OFF13-42 malicious getter never invoked',()=>{
  const i=fixture();let reads=0;Object.defineProperty(i.after,'ownerRoute',{get(){reads++;throw Error('canary');}});
  assert.equal(review(i).status,'INVALID_INPUT');assert.equal(reads,0);
});
test('OFF13-43 cyclic object rejected',()=>get(i=>i.request.loop=i,'INVALID_INPUT','ENVELOPE'));
test('OFF13-44 no prototype pollution accepted',()=>get(i=>Object.setPrototypeOf(i.after,{evil:true}),'INVALID_INPUT','ENVELOPE'));
test('OFF13-45 malformed caller request cannot imply S0 authentication',()=>{
  const r=get(i=>i.request.startedAtMs='100','INVALID_INPUT','SHAPE');zero(r);
});
