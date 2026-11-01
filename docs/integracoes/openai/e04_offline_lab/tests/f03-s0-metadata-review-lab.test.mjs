import test from 'node:test';
import assert from 'node:assert/strict';
import {F03_S0_REVIEW_INPUT,F03_S0_REVIEW_OUTPUT,reviewF03S0Metadata as review} from '../f03-s0-metadata-review-lab.mjs';

const sha=(c='a')=>c.repeat(64);
function fixture(){
  const binding={storeRef:'store1',caseRef:'case1',closureRef:'closure1',cycleVersion:7,snapshotSha256:sha()};
  return {schemaVersion:F03_S0_REVIEW_INPUT,request:{...binding},
    before:{state:'VERIFIED_CONTRACT_PENDING',...binding},
    inspection:{state:'REVIEW_ONLY_NOT_FROZEN',count:5,caseCount:2,metadataSha256:sha('b')},
    after:{state:'VERIFIED_CONTRACT_PENDING',...binding},application:null};
}
function check(fn,status,stage){
  const x=fixture();fn(x);const y=review(x);assert.equal(y.status,status);
  if(stage)assert.equal(y.stage,stage);return y;
}
const noAuthority = out => {
  assert.equal(out.schemaVersion,F03_S0_REVIEW_OUTPUT);
  for(const name of ['s0SourceAuthenticated','historyComplete','mediaCoverageAttested',
    'crossCaseIdentityAttested','modelContentAuthorized','modelInvocationAuthorized',
    'fieldApplicationAuthorized','commercialTransitionAuthorized','sendAuthorized','productionAuthorized'])
    assert.equal(out[name],false,name);
  assert.equal(out.requiresCanonicalS0Contract,true);
};

test('OFF12 01 positive metadata remains review only',()=>{
  const r=review(fixture());assert.equal(r.status,'LAB_METADATA_REVIEW_ONLY');noAuthority(r);
});
test('OFF12 02 output discloses no lead, digest, scope, case or raw record metadata',()=>{
  const r=review(fixture()),s=JSON.stringify(r);
  for(const token of ['store1','case1','closure1',sha(),sha('b'),'count','caseCount','receipt','customer','records'])assert.ok(!s.includes(token),token);
});
test('OFF12 03 input immutable by caller review',()=>{
  const x=fixture(),before=structuredClone(x);review(x);assert.deepEqual(x,before);
});
test('OFF12 04 result frozen',()=>assert.equal(Object.isFrozen(review(fixture())),true));
test('OFF12 05 synthetic application cannot grant form commit',()=>{
  const x=check(i=>i.application='APPLIED_SYNTHETIC_ONLY','LAB_REVIEW_ONLY_SYNTHETIC_APPLICATION','NO_F03_AUTHORITY');noAuthority(x);
});
test('OFF12 06 synthetic duplicate application cannot grant commit',()=>check(i=>i.application='ALREADY_APPLIED_AUDIT_ONLY','LAB_REVIEW_ONLY_SYNTHETIC_APPLICATION'));
test('OFF12 07 denied application requires review',()=>check(i=>i.application='DENIED','REVIEW_REQUIRED','APPLICATION'));
test('OFF12 08 stale application requires review',()=>check(i=>i.application='STALE_REVIEW_REQUIRED','REVIEW_REQUIRED','APPLICATION'));
test('OFF12 09 conflict application requires review',()=>check(i=>i.application='CONFLICT_REVIEW_REQUIRED','REVIEW_REQUIRED','APPLICATION'));
test('OFF12 10 S1 blocked application requires review',()=>check(i=>i.application='BLOCKED_S1','REVIEW_REQUIRED','APPLICATION'));
test('OFF12 11 absent S0 application state is not a grant',()=>assert.equal(review(fixture()).modelInvocationAuthorized,false));
test('OFF12 12 before gate denied',()=>check(i=>i.before.state='DENIED','DENIED','RECHECK'));
test('OFF12 13 after gate denied',()=>check(i=>i.after.state='DENIED','DENIED','RECHECK'));
test('OFF12 14 before gate stale',()=>check(i=>i.before.state='STALE','STALE','RECHECK'));
test('OFF12 15 after gate stale',()=>check(i=>i.after.state='STALE','STALE','RECHECK'));
test('OFF12 16 before unavailable',()=>check(i=>i.before.state='UNAVAILABLE','UNAVAILABLE','RECHECK'));
test('OFF12 17 after unavailable',()=>check(i=>i.after.state='UNAVAILABLE','UNAVAILABLE','RECHECK'));
test('OFF12 18 before input rejected',()=>check(i=>i.before.state='INPUT_REJECTED','DENIED','RECHECK'));
test('OFF12 19 incomplete history requires review',()=>check(i=>i.inspection={state:'HISTORY_INCOMPLETE',count:0,caseCount:0,metadataSha256:null},'REVIEW_REQUIRED','INCOMPLETE_HISTORY'));
test('OFF12 20 history denied no metadata disclosed',()=>noAuthority(check(i=>i.inspection={state:'DENIED',count:0,caseCount:0,metadataSha256:null},'DENIED','HISTORY')));
test('OFF12 21 history input rejected',()=>check(i=>i.inspection={state:'INPUT_REJECTED',count:0,caseCount:0,metadataSha256:null},'DENIED','HISTORY'));
test('OFF12 22 history stale',()=>check(i=>i.inspection={state:'STALE',count:0,caseCount:0,metadataSha256:null},'STALE','HISTORY'));
test('OFF12 23 history unavailable',()=>check(i=>i.inspection={state:'UNAVAILABLE',count:0,caseCount:0,metadataSha256:null},'UNAVAILABLE','HISTORY'));
test('OFF12 24 before other store denied even stale versions',()=>check(i=>{i.before.storeRef='store2';i.before.cycleVersion=8;},'DENIED','SCOPE'));
test('OFF12 25 after other store denied',()=>check(i=>i.after.storeRef='store2','DENIED','SCOPE'));
test('OFF12 26 other case denied',()=>check(i=>i.before.caseRef='case2','DENIED','SCOPE'));
test('OFF12 27 other closure denied',()=>check(i=>i.after.closureRef='closure2','DENIED','SCOPE'));
test('OFF12 28 before version mismatched',()=>check(i=>i.before.cycleVersion=8,'STALE','BINDING'));
test('OFF12 29 after version mismatched',()=>check(i=>i.after.cycleVersion=8,'STALE','BINDING'));
test('OFF12 30 before receipt digest mismatched',()=>check(i=>i.before.snapshotSha256=sha('c'),'STALE','BINDING'));
test('OFF12 31 after receipt digest mismatched',()=>check(i=>i.after.snapshotSha256=sha('c'),'STALE','BINDING'));
test('OFF12 32 missing input field denied',()=>check(i=>delete i.request.caseRef,'INVALID_INPUT','SHAPE'));
test('OFF12 33 extra input metadata denied',()=>check(i=>i.inputToken='secret','INVALID_INPUT','ENVELOPE'));
test('OFF12 34 fake ready status denied',()=>check(i=>i.inspection.state='HISTORY_COMPLETE','INVALID_INPUT','SHAPE'));
test('OFF12 35 source too many records denied',()=>check(i=>i.inspection.count=10001,'INVALID_INPUT','SHAPE'));
test('OFF12 36 more cases than rows denied',()=>check(i=>i.inspection.caseCount=6,'INVALID_INPUT','SHAPE'));
test('OFF12 37 empty purported review metadata denied',()=>check(i=>{i.inspection.count=0;i.inspection.caseCount=0;},'INVALID_INPUT','SHAPE'));
test('OFF12 38 incomplete with attested metadata denied',()=>check(i=>{i.inspection.state='HISTORY_INCOMPLETE';},'INVALID_INPUT','SHAPE'));
test('OFF12 39 invalid metadata digest denied',()=>check(i=>i.inspection.metadataSha256='not_sha','INVALID_INPUT','SHAPE'));
test('OFF12 40 getter never executed',()=>{
  const x=fixture();let hits=0;Object.defineProperty(x.inspection,'count',{get(){hits++;throw Error('accessor');}});
  assert.equal(review(x).status,'INVALID_INPUT');assert.equal(hits,0);
});
test('OFF12 41 symbol key is denied',()=>check(i=>i.inspection[Symbol('x')]='leak','INVALID_INPUT','ENVELOPE'));
test('OFF12 42 cyclic payload denied',()=>check(i=>{i.extra=i;},'INVALID_INPUT','ENVELOPE'));
test('OFF12 43 unsafe prototype denied',()=>check(i=>Object.setPrototypeOf(i.before,{bad:true}),'INVALID_INPUT','ENVELOPE'));
test('OFF12 44 toJSON cannot execute',()=>{
  const x=fixture();let hits=0;Object.defineProperty(x,'toJSON',{get(){hits++;throw Error('leak');}});
  assert.equal(review(x).status,'INVALID_INPUT');assert.equal(hits,0);
});
test('OFF12 45 cycle version must be integer',()=>check(i=>i.request.cycleVersion=7.2,'INVALID_INPUT','SHAPE'));
test('OFF12 46 raw S0 message field cannot enter inspection',()=>check(i=>i.inspection.messages=['hello'],'INVALID_INPUT','SHAPE'));
test('OFF12 47 uppercase digest invalid',()=>check(i=>i.request.snapshotSha256=sha('F'),'INVALID_INPUT','SHAPE'));
test('OFF12 48 unknown application status denied',()=>check(i=>i.application='APPLIED_OPERATIONAL','INVALID_INPUT','SHAPE'));
test('OFF12 49 no trusted principal can be smuggled in readback',()=>check(i=>i.before.authorized=true,'INVALID_INPUT','SHAPE'));
test('OFF12 50 no content grant can be smuggled in request',()=>check(i=>i.request.modelContentAuthorized=true,'INVALID_INPUT','SHAPE'));
