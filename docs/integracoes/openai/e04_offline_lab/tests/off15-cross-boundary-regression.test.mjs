/**
 * OFF-15 cross-domain negative regression: offline/isolated only.
 *
 * Proves each laboratory envelope rejects: another domain's fixture, another
 * domain's output, forged grants, getters, cycles and cross-tenant scope.
 * Does not connect S0, Meta, OpenAI, DB, HTTP or production.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {F01_OWNER_LAB_INPUT,reviewF01S0Ownership} from '../f01-s0-ownership-review-lab.mjs';
import {F01_SOURCE_LAB_INPUT,reviewF01CommercialSources} from '../f01-commercial-source-review-lab.mjs';
import {WA39_LAB_INPUT,previewWa39F02Projection} from '../f02-wa39-consumer-lab.mjs';
import {F03_S0_REVIEW_INPUT,reviewF03S0Metadata} from '../f03-s0-metadata-review-lab.mjs';

const verOwn=()=>({case:1,cycle:2,assignment:3,catalog:4,knowledge:5,policy:6,route:7,consent:8});
const verSources=()=>({catalog:4,knowledge:7,policy:2,consent:6,grant:8});
const baseOwn=()=>{
  const scope={storeRef:'shop1',caseRef:'case1',personRef:'person1'};
  const flags={ownerRoute:'AI',handoffDefinitive:false,humanized:false,optOut:false,
    channelEligible:true,postRemittance:false,postSale:false,snapshotState:'LAB_UNVERIFIED'};
  return {
    schemaVersion:F01_OWNER_LAB_INPUT,
    request:{requestRef:'r1',...scope,purpose:'F01',startedAtMs:100,deadlineMs:250,expectedVersions:verOwn()},
    before:{...scope,...flags,versions:verOwn(),observedAtMs:110},
    after:{...scope,...flags,versions:verOwn(),observedAtMs:180}
  };
};
const baseSources=()=>{
  const scope={storeRef:'shop1',caseRef:'case1',personRef:'person1',purposeRef:'F01'};
  const sample=()=>({sourceRef:'source1',storeRef:'shop1',kind:'current',
    approvalState:'APPROVED_ACTIVE',sourceVersion:3,validUntilMs:500,
    correctedByRef:null,claimCodes:['OFFER_A']});
  const snap=t=>({...scope,observedAtMs:t,versions:verSources(),
    contentPolicy:'LAB_ALLOWED',snapshotState:'LAB_UNVERIFIED',sources:[sample()]});
  return {
    schemaVersion:F01_SOURCE_LAB_INPUT,
    request:{requestRef:'r1',...scope,startedAtMs:100,deadlineMs:250,
      versions:verSources(),claims:[{sourceRef:'source1',claimCode:'OFFER_A',usage:'commercial'}]},
    before:snap(110),after:snap(180)
  };
};
const baseMeta=()=>({
  schemaVersion:WA39_LAB_INPUT,
  expected:{storeRef:'shop1',caseRef:'case1',flowRef:'flow1',
    planRevision:2,minEvidenceRevision:4,
    attempts:[{attemptRef:'attempt1',templateVersionRef:'version1',isFinalTemplate:false}]},
  snapshot:{storeRef:'shop1',caseRef:'case1',flowRef:'flow1',
    planRevision:2,evidenceRevision:4,
    events:[{eventRef:'event1',sequence:1,attemptRef:'attempt1',templateVersionRef:'version1',
      phase:'GRAPH',correlationState:'API_ACCEPTED',providerErrorCode:null}]}
});
const hash=c=>c.repeat(64);
const baseHistory=()=>{
  const binding={storeRef:'shop1',caseRef:'case1',closureRef:'closure1',
    cycleVersion:2,snapshotSha256:hash('a')};
  return {
    schemaVersion:F03_S0_REVIEW_INPUT,
    request:{...binding},
    before:{...binding,state:'VERIFIED_CONTRACT_PENDING'},
    after:{...binding,state:'VERIFIED_CONTRACT_PENDING'},
    inspection:{state:'REVIEW_ONLY_NOT_FROZEN',count:3,caseCount:2,metadataSha256:hash('b')},
    application:null
  };
};

const items=[
  {name:'F01 owner',mk:baseOwn,fn:reviewF01S0Ownership,version:F01_OWNER_LAB_INPUT,
    positive:'LAB_CONSISTENT_UNVERIFIED',deep:'before',
    forge:i=>i.before.publishAuthorized=true,scope:i=>i.after.storeRef='other_shop'},
  {name:'F01 sources',mk:baseSources,fn:reviewF01CommercialSources,version:F01_SOURCE_LAB_INPUT,
    positive:'LAB_ELIGIBLE_UNVERIFIED',deep:'before',
    forge:i=>i.after.commercialOfferAuthorized=true,scope:i=>i.after.storeRef='other_shop'},
  {name:'F02 WA39',mk:baseMeta,fn:previewWa39F02Projection,version:WA39_LAB_INPUT,
    positive:'LAB_UNVERIFIED_PROJECTION',deep:'snapshot',
    forge:i=>i.expected.graphDispatchAuthorized=true,scope:i=>i.snapshot.storeRef='other_shop'},
  {name:'F03 metadata',mk:baseHistory,fn:reviewF03S0Metadata,version:F03_S0_REVIEW_INPUT,
    positive:'LAB_METADATA_REVIEW_ONLY',deep:'before',
    forge:i=>i.before.fieldApplicationAuthorized=true,scope:i=>i.after.storeRef='other_shop'}
];
const denyFlags=[
 'publishAuthorized','sendAuthorized','productionAuthorized','modelInvocationAuthorized',
 'commercialOfferAuthorized','commercialTransitionAuthorized','fieldApplicationAuthorized',
 'graphDispatchAuthorized','c09Authorized','f02RestartAuthorized','schedulingAuthorized',
 's0SourceAuthenticated','s0ReadbackVerified','sourceAuthenticated','historyComplete'
];
const verifyNoGrant=answer=>{
  assert.ok(answer&&typeof answer==='object'&&!Array.isArray(answer));
  assert.ok(typeof answer.status==='string');
  for(const key of denyFlags)assert.notEqual(answer[key],true,key);
  assert.equal(Object.isFrozen(answer),true);
};

// OFF15-01..04: each valid lab fixture still cannot be an operational grant.
for(const it of items)test('OFF15 baseline '+it.name+' remains unverified',()=>{
  const answer=it.fn(it.mk());
  assert.equal(answer.status,it.positive);
  verifyNoGrant(answer);
});

// OFF15-05..16: coercing a different domain's fixture into this version is
// never enough to pass shape validation. There is no implicit schema bridge.
for(const dst of items)for(const src of items){
  if(dst===src)continue;
  test('OFF15 reject cross-domain fixture '+src.name+' -> '+dst.name,()=>{
    const input=src.mk();
    input.schemaVersion=dst.version;
    const answer=dst.fn(input);
    assert.equal(answer.status,'INVALID_INPUT');
    verifyNoGrant(answer);
  });
}

// OFF15-17..28: output from a successful review-only lab is NOT a valid input
// to any other lab even when forged with that lab's expected schema label.
for(const dst of items)for(const src of items){
  if(dst===src)continue;
  test('OFF15 reject cross-domain positive report '+src.name+' -> '+dst.name,()=>{
    const report=src.fn(src.mk());
    assert.equal(report.status,src.positive);
    const forged={...report,schemaVersion:dst.version};
    const answer=dst.fn(forged);
    assert.equal(answer.status,'INVALID_INPUT');
    verifyNoGrant(answer);
  });
}

// OFF15-29..32: adding a self-asserted grant to valid metadata cannot approve.
for(const it of items)test('OFF15 deny forged authority field in '+it.name,()=>{
  const v=it.mk();it.forge(v);
  const answer=it.fn(v);
  assert.equal(answer.status,'INVALID_INPUT');
  verifyNoGrant(answer);
});

// OFF15-33..36: hostile cyclic input must fail closed, not recurse indefinitely.
for(const it of items)test('OFF15 deny cyclic root payload in '+it.name,()=>{
  const v=it.mk();v.badCycle=v;
  const answer=it.fn(v);
  assert.equal(answer.status,'INVALID_INPUT');
  verifyNoGrant(answer);
});

// OFF15-37..40: a malicious getter is never evaluated during validation.
for(const it of items)test('OFF15 never execute getter for '+it.name,()=>{
  const v=it.mk();let calls=0;
  Object.defineProperty(v,it.deep,{
    configurable:true,enumerable:true,get(){calls++;throw new Error('GETTER_EXECUTED');}
  });
  const answer=it.fn(v);
  assert.equal(answer.status,'INVALID_INPUT');
  assert.equal(calls,0);
  verifyNoGrant(answer);
});

// OFF15-41..44: a valid-looking event/snapshot from another tenant is denied,
// without any source IDs/PII being exposed in the result.
for(const it of items)test('OFF15 deny cross-store scope in '+it.name,()=>{
  const v=it.mk();it.scope(v);
  const answer=it.fn(v);
  assert.equal(answer.status,'DENIED');
  assert.ok(!JSON.stringify(answer).includes('other_shop'));
  verifyNoGrant(answer);
});
