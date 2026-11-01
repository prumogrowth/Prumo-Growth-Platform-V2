import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const pinned=process.env.S0_F01_OFF13_PIN;
const original=pinned?await import(pathToFileURL(resolve(pinned,
 'docs/integracoes/openai/e04_offline_lab/f01-s0-ownership-review-lab.mjs')).href):null;
const enabled={skip:!original};
const versions={case:1,cycle:1,assignment:1,catalog:1,
  knowledge:1,policy:1,route:1,consent:1};
const claim=(change={})=>({
 storeRef:'store-A',caseRef:'case_A',personRef:'person_A',ownerRoute:'AI',
 handoffDefinitive:false,humanized:false,optOut:false,channelEligible:true,
 postRemittance:false,postSale:false,observedAtMs:2000,
 versions:{...versions},snapshotState:'LAB_UNVERIFIED',...change
});
const envelope=()=>({
 schemaVersion:'prumo.openai.f01-owner-recheck/0.1-lab',
 request:{requestRef:'turn_A',storeRef:'store-A',caseRef:'case_A',
   personRef:'person_A',startedAtMs:1000,deadlineMs:15000,
   expectedVersions:{...versions},purpose:'F01_DRAFT_LAB'},
 before:claim(),after:claim({observedAtMs:3000})
});
let physical=null;
if(process.env.S0_F01_LAB_EVIDENCE){
 physical=JSON.parse(await readFile(process.env.S0_F01_LAB_EVIDENCE,'utf8'));
 assert.equal(physical.lab_only,true);
}
function check(x){return original.reviewF01S0Ownership(x);}
test('S0-F01-OFF13-01 aligned owner snapshots never authorize a model or send',
 enabled,()=>{
 const out=check(envelope());
 assert.equal(out.status,'LAB_CONSISTENT_UNVERIFIED');
 assert.equal(out.modelInvocationAuthorized,false);
 assert.equal(out.publishAuthorized,false);
 assert.equal(out.productionAuthorized,false);
 assert.equal(out.requiresS0TransactionalRecheck,true);
});
test('S0-F01-OFF13-02 definitive handoff always human only',enabled,()=>{
 const q=envelope();q.after=claim({ownerRoute:'HUMAN',
  handoffDefinitive:true,humanized:true,observedAtMs:3000,
  versions:{...versions,case:2,assignment:2}});
 assert.equal(check(q).status,'HUMAN_ONLY_REVIEW');
});
test('S0-F01-OFF13-03 attempted human to AI regression never reopens',enabled,()=>{
 const q=envelope();q.before=claim({ownerRoute:'HUMAN',
   humanized:true,handoffDefinitive:true});
 assert.equal(check(q).status,'REVIEW_REQUIRED');
});
test('S0-F01-OFF13-04 cross tenant/person scope denied',enabled,()=>{
 const q=envelope();q.after.personRef='unrelated';
 assert.equal(check(q).status,'DENIED');
 assert.equal(check(q).stage,'SCOPE');
});
test('S0-F01-OFF13-05 optout and post sale deny',enabled,()=>{
 for(const changed of [{optOut:true},{postSale:true},{postRemittance:true},
                        {channelEligible:false}]){
  const q=envelope();q.after={...q.after,...changed};
  assert.equal(check(q).status,'DENIED');
 }
});
test('S0-F01-OFF13-06 stale version does not become grant',enabled,()=>{
 const q=envelope();q.after.versions.policy=3;
 assert.equal(check(q).status,'STALE');
 assert.equal(check(q).publishAuthorized,false);
});
test('S0-F01-OFF13-07 malformed source claims cannot grant',enabled,()=>{
 const q=envelope();q.after.extra='forged';
 assert.equal(check(q).status,'INVALID_INPUT');
});
test('S0-F01-OFF13-08 physical PG17 F01 owner/handoff compare with pinned OFF13',
 {skip:!original||!physical},()=>{
 assert.equal(check(physical.consistent).status,'LAB_CONSISTENT_UNVERIFIED');
 const blocked=check(physical.handoff);
 assert.equal(blocked.status,'HUMAN_ONLY_REVIEW');
 assert.equal(blocked.publishAuthorized,false);
 assert.equal(physical.late_recheck,'HUMAN_ONLY');
 assert.equal(physical.handoff_status,
  'LAB_HANDOFF_DURABLY_RECORDED_NO_PUBLISH');
});
