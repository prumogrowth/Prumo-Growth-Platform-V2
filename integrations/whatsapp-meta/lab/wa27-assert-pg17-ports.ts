/**
 * WA-27 PG17 -> actual WA-26 TypeScript gate, on read-only snapshots.
 * Four independent SQL COMMITs + new psql sessions; no database drivers,
 * tokens, runtime authorization, Graph request or production endpoints.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  prepareS0TemplateCandidatesFixture,recheckS0TemplateCandidateFixture,
  type Wa26FixturePorts,
} from '../s0-template-purpose-bridge.ts';

type SqlRow={
  stage:string; observed_role:string; scope:unknown; policy:unknown;
  catalog:unknown; visible_scopes:number; cross_tenant_scopes:number;
  can_write:boolean;
};
const [initialAFile,initialBFile,noneFile,optoutFile,pausedFile,grantFile,
  actorFile,afterBFile]=process.argv.slice(2);
assert.equal(process.argv.length,10,'WA27 expects exactly eight PG17 snapshots');
function snapshot(file:string,stage:string,role:string,visible:number):SqlRow{
  const raw=readFileSync(file,'utf8').trim();
  const row=JSON.parse(raw) as SqlRow;
  assert.equal(row.stage,stage);
  assert.equal(row.observed_role,role);
  assert.equal(row.visible_scopes,visible);
  assert.equal(row.cross_tenant_scopes,0);
  assert.equal(row.can_write,false);
  return row;
}
const A='wa27_reader_shop_a',B='wa27_reader_shop_b',N='wa27_reader_shop_none';
const a=snapshot(initialAFile,'initial_a',A,1);
const b=snapshot(initialBFile,'initial_b',B,1);
const none=snapshot(noneFile,'no_scope',N,0);
const optout=snapshot(optoutFile,'optout',A,1);
const paused=snapshot(pausedFile,'paused',A,1);
const grant=snapshot(grantFile,'grant_revoked',A,1);
const actor=snapshot(actorFile,'actor_revoked',A,1);
const afterB=snapshot(afterBFile,'after_b',B,1);
const pass=(n:string)=>process.stdout.write('WA27-'+n+' PASS\n');
function ports(row:SqlRow):Wa26FixturePorts{
  return Object.freeze({
    resolveSelection:async()=>row.scope,
    readScopedPolicy:async()=>row.policy,
    readScopedCatalog:async()=>row.catalog,
  });
}
const REF='fixture_selection_100';
const plan=(row:SqlRow)=>prepareS0TemplateCandidatesFixture(REF,ports(row));
const resultA=await plan(a);
assert.equal(resultA.decision,'LAB_CANDIDATES');
if(resultA.decision!=='LAB_CANDIDATES')throw Error('expected laboratory ticket');
assert.equal(resultA.candidates.length,1);
assert.equal(resultA.candidates[0].template_ref,'template_A');
assert.equal(resultA.candidates[0].send_authorized,false);
assert.equal(resultA.production_authorized,false);
pass('01');
const resultB=await plan(b);
assert.equal(resultB.decision,'LAB_CANDIDATES');
if(resultB.decision!=='LAB_CANDIDATES')throw Error('missing tenant B');
assert.equal(resultB.candidates[0].template_ref,'template_B');
assert.equal(resultB.candidates[0].send_authorized,false);
pass('02');
assert.equal((await plan(none)).decision,'DENIED');
pass('03');
assert.equal(a.cross_tenant_scopes,0);
assert.equal(b.cross_tenant_scopes,0);
assert.equal(none.visible_scopes,0);
pass('04');
assert.equal([a,b,none,optout,paused,grant,actor,afterB].every(x=>x.can_write===false),true);
pass('05');

const originalTicket=resultA.internal_tickets[0];
const reserve=await recheckS0TemplateCandidateFixture(originalTicket,'RESERVE',ports(a));
assert.equal(reserve.decision,'LAB_RECHECKED');
pass('06');
if(reserve.decision!=='LAB_RECHECKED')throw Error('missing reserve');
const beforeDispatch=await recheckS0TemplateCandidateFixture(
  reserve.internal_ticket,'PRE_DISPATCH',ports(a));
assert.equal(beforeDispatch.decision,'LAB_RECHECKED');
assert.equal(beforeDispatch.send_authorized,false);
assert.equal(beforeDispatch.production_authorized,false);
pass('07');

const postOptout=await plan(optout);
assert.equal(postOptout.decision,'DENIED');
if(postOptout.decision==='DENIED')assert.equal(postOptout.reason,'POLICY_DENIED');
const lateOptout=await recheckS0TemplateCandidateFixture(
  reserve.internal_ticket,'PRE_DISPATCH',ports(optout));
assert.equal(lateOptout.decision,'DENIED');
if(lateOptout.decision==='DENIED')assert.equal(lateOptout.reason,'POLICY_DENIED');
pass('08');

const postPaused=await plan(paused);
assert.equal(postPaused.decision,'DENIED');
if(postPaused.decision==='DENIED')assert.equal(postPaused.reason,'CATALOG_DENIED');
pass('09');

const postGrant=await plan(grant);
assert.equal(postGrant.decision,'DENIED');
if(postGrant.decision==='DENIED')assert.equal(postGrant.reason,'CATALOG_DENIED');
pass('10');

const postActor=await plan(actor);
assert.equal(postActor.decision,'DENIED');
if(postActor.decision==='DENIED')assert.equal(postActor.reason,'CATALOG_DENIED');
pass('11');

for(const fresh of [paused,grant,actor]){
  const res=await recheckS0TemplateCandidateFixture(originalTicket,'RESERVE',ports(fresh));
  assert.equal(res.decision,'DENIED');
  if(res.decision==='DENIED')assert.equal(res.reason,'STALE_OR_CHANGED');
}
pass('12');

const resultAfterB=await plan(afterB);
assert.equal(resultAfterB.decision,'LAB_CANDIDATES');
if(resultAfterB.decision!=='LAB_CANDIDATES')throw Error('B changed across A writes');
assert.equal(resultAfterB.candidates[0].template_ref,'template_B');
assert.equal(JSON.stringify(resultAfterB).includes('template_A'),false);
pass('13');

assert.equal('send_authorized' in beforeDispatch && beforeDispatch.send_authorized,false);
assert.equal('graph_request' in beforeDispatch,false);
assert.equal('recipient' in beforeDispatch,false);
assert.equal('access_token' in beforeDispatch,false);
pass('14');
