import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const root=process.env.S0_F01_OFF14_PIN;
const off=root?await import(pathToFileURL(resolve(root,
 'docs/integracoes/openai/e04_offline_lab/f01-commercial-source-review-lab.mjs')).href):null;
const run={skip:!off};
let pg=null;
if(process.env.S0_F01_SOURCE_EVIDENCE){
 pg=JSON.parse(await readFile(process.env.S0_F01_SOURCE_EVIDENCE,'utf8'));
 assert.equal(pg.lab_only,true);
}
function fixture(){
 const versions={catalog:1,knowledge:1,policy:1,consent:1,grant:1};
 const a={sourceRef:'ref_A',storeRef:'store-A',kind:'current',
   approvalState:'APPROVED_ACTIVE',sourceVersion:1,validUntilMs:900000,
   correctedByRef:null,claimCodes:['PRODUCT_FEATURE']};
 const old={sourceRef:'old_A',storeRef:'store-A',kind:'historical',
   approvalState:'EXPIRED',sourceVersion:1,validUntilMs:100,
   correctedByRef:null,claimCodes:['OLD_EXPLANATION']};
 const scope={storeRef:'store-A',caseRef:'case_A',personRef:'person_A',
   purposeRef:'offer_info'};
 const snap=time=>({...scope,observedAtMs:time,versions:{...versions},
   contentPolicy:'LAB_ALLOWED',sources:[{...a},{...old}],
   snapshotState:'LAB_UNVERIFIED'});
 return {schemaVersion:'prumo.openai.f01-source-review/0.1-lab',
  request:{requestRef:'turn_A',...scope,startedAtMs:100,deadlineMs:500,
   versions:{...versions},claims:[{sourceRef:'ref_A',
     claimCode:'PRODUCT_FEATURE',usage:'commercial'}]},
  before:snap(200),after:snap(250)};
}
function review(x){return off.reviewF01CommercialSources(x);}
function denyAuthority(x){
 for(const k of ['s0SourceAuthenticated','s0CatalogVerified',
 'contentGrantVerified','provenanceAuthenticated','semanticSupportVerified',
 'commercialOfferAuthorized','modelContentAuthorized',
 'modelInvocationAuthorized','publishAuthorized','sendAuthorized',
 'productionAuthorized'])assert.equal(x[k],false,k);
 assert.equal(x.requiresS0TransactionalRecheck,true);
}
test('S0-OFF14-01 stable synthetic metadata cannot grant content',run,()=>{
 const x=review(fixture());
 assert.equal(x.status,'LAB_ELIGIBLE_UNVERIFIED');denyAuthority(x);
});
test('S0-OFF14-02 historical item never proves current offer',run,()=>{
 const q=fixture();q.request.claims=[{sourceRef:'old_A',
  claimCode:'OLD_EXPLANATION',usage:'commercial'}];
 assert.equal(review(q).stage,'HISTORICAL_OFFER');
});
test('S0-OFF14-03 historic interpretive item remains nonauthoritative',run,()=>{
 const q=fixture();q.request.claims=[{sourceRef:'old_A',
  claimCode:'OLD_EXPLANATION',usage:'interpretive'}];
 denyAuthority(review(q));
});
test('S0-OFF14-04 store/source change is rejected',run,()=>{
 const q=fixture();q.after.sources[0].storeRef='store-B';
 assert.equal(review(q).status,'DENIED');
});
test('S0-OFF14-05 full catalog changed despite unselected item',run,()=>{
 const q=fixture();q.after.sources[1].sourceVersion=2;
 assert.equal(review(q).stage,'SOURCES_CHANGED');
});
test('S0-OFF14-06 unknown claim fails, no semantic authority',run,()=>{
 const q=fixture();q.request.claims[0].claimCode='UNPROVEN_PRICE';
 assert.equal(review(q).stage,'CLAIM_UNSUPPORTED');
 denyAuthority(review(q));
});
test('S0-OFF14-07 revoked/commercial expiry blocks unverified offer',run,()=>{
 const q=fixture();q.before.sources[0].validUntilMs=250;
 q.after.sources[0].validUntilMs=250;
 assert.equal(review(q).stage,'EXPIRED_OR_UNBOUNDED');
});
test('S0-OFF14-08 PG17 source snapshots interpreted by original OFF14',
 {skip:!off||!pg},()=>{
 assert.deepEqual(pg.aliases,[{alias:'src_001',
   claimCode:'PRODUCT_FEATURE',usage:'commercial'}]);
 const ok=review(pg.stable);
 assert.equal(ok.status,'LAB_ELIGIBLE_UNVERIFIED');
 denyAuthority(ok);
 const mutated=review(pg.changed);
 assert.equal(mutated.status,'REVIEW_REQUIRED');
 assert.equal(mutated.stage,'SOURCES_CHANGED');
 denyAuthority(mutated);
});
