import test from 'node:test';
import assert from 'node:assert/strict';
import { WA39_LAB_INPUT,WA39_LAB_RESULT,previewWa39F02Projection as project } from '../f02-wa39-consumer-lab.mjs';

const ev=(state='CORRELATED_SENT',opts={})=>({
  eventRef:'evt_01',sequence:1,attemptRef:'a_01',templateVersionRef:'tpl_v1',
  phase:['API_ACCEPTED','QUEUED','UNKNOWN'].includes(state)?'GRAPH':'S0_RECONCILED',
  correlationState:state,providerErrorCode:null,...opts
});
const base=()=>({
  schemaVersion:WA39_LAB_INPUT,
  expected:{storeRef:'s1',caseRef:'c1',flowRef:'f1',planRevision:3,minEvidenceRevision:4,
    attempts:[{attemptRef:'a_01',templateVersionRef:'tpl_v1',isFinalTemplate:true},
      {attemptRef:'a_02',templateVersionRef:'tpl_v2',isFinalTemplate:false}]},
  snapshot:{storeRef:'s1',caseRef:'c1',flowRef:'f1',planRevision:3,evidenceRevision:4,
    events:[ev()]}
});
const check=(change,status,stage)=>{const x=base();change(x);const out=project(x);assert.equal(out.status,status);if(stage)assert.equal(out.stage,stage);return out;};
test('OFF11 01 correlated sent is an unverified observation only',()=>{
  const x=project(base());assert.equal(x.status,'LAB_UNVERIFIED_PROJECTION');assert.equal(x.schemaVersion,WA39_LAB_RESULT);
  assert.equal(x.observations[0].observation,'SENT_CANDIDATE_UNVERIFIED');
  assert.equal(x.observations[0].verified,false);
  for(const k of ['sourceAuthenticated','metaProviderVerified','s0ReadbackVerified','sendAuthorized',
    'schedulingAuthorized','c09Authorized','commercialTransitionAuthorized','productionAuthorized'])assert.equal(x[k],false);
  assert.equal(x.requiresS0Recheck,true);
});
test('OFF11 02 fields of result contain no tenant, case, provider, template or raw event content',()=>{
  const x=project(base()),str=JSON.stringify(x);
  for(const s of ['"s1"','"c1"','"f1"','"tpl_v1"','providerMessageId','phone_number_id','payload','wamid'])assert.ok(!str.includes(s),s);
});
test('OFF11 03 final template marker does not grant C09',()=>{
  const x=project(base());assert.equal(x.observations[0].finalTemplateCandidate,true);assert.equal(x.c09Authorized,false);
});
test('OFF11 04 graph API accepted is not sent',()=>check(x=>x.snapshot.events=[ev('API_ACCEPTED')],'LAB_UNVERIFIED_PROJECTION').observations[0].observation==='API_ACCEPTED_NOT_SENT');
test('OFF11 05 graph queued is not sent',()=>assert.equal(check(x=>x.snapshot.events=[ev('QUEUED')],'LAB_UNVERIFIED_PROJECTION').observations[0].observation,'QUEUED_NOT_SENT'));
test('OFF11 06 unknown is not definitive failure',()=>assert.equal(check(x=>x.snapshot.events=[ev('UNKNOWN')],'LAB_UNVERIFIED_PROJECTION').observations[0].observation,'AWAITING_TRANSPORT_RECONCILIATION'));
test('OFF11 07 pending correlation blocked from proof',()=>assert.equal(check(x=>x.snapshot.events=[ev('PENDING_CORRELATION')],'LAB_UNVERIFIED_PROJECTION').observations[0].observation,'AWAITING_S0_CORRELATION'));
test('OFF11 08 delivered is not retroactive sent proof',()=>assert.equal(check(x=>x.snapshot.events=[ev('CORRELATED_DELIVERED')],'LAB_UNVERIFIED_PROJECTION').observations[0].observation,'PROGRESS_WITHOUT_SENT_INFERENCE'));
test('OFF11 09 read is not retroactive sent proof',()=>assert.equal(check(x=>x.snapshot.events=[ev('CORRELATED_READ')],'LAB_UNVERIFIED_PROJECTION').observations[0].observation,'PROGRESS_WITHOUT_SENT_INFERENCE'));
test('OFF11 10 definitive failure is candidate, not C09 or commercial loss',()=>{
  const x=check(i=>i.snapshot.events=[ev('CORRELATED_DEFINITIVE_FAILURE')],'LAB_UNVERIFIED_PROJECTION');
  assert.equal(x.observations[0].observation,'FAILURE_CANDIDATE_UNVERIFIED');assert.equal(x.commercialTransitionAuthorized,false);
});
test('OFF11 11 131049 remains technical diagnosis',()=>{
  const x=check(i=>i.snapshot.events=[ev('CORRELATED_DEFINITIVE_FAILURE',{providerErrorCode:131049})],'LAB_UNVERIFIED_PROJECTION');
  assert.equal(x.observations[0].technical131049,true);assert.equal(x.commercialTransitionAuthorized,false);
});
test('OFF11 12 unrelated error code not marked 131049',()=>assert.equal(check(i=>i.snapshot.events=[ev('CORRELATED_DEFINITIVE_FAILURE',{providerErrorCode:131000})],'LAB_UNVERIFIED_PROJECTION').observations[0].technical131049,false));
test('OFF11 13 rejected Meta conflict',()=>check(i=>i.snapshot.events=[ev('CONFLICT')],'REVIEW_REQUIRED','META_CONFLICT'));
test('OFF11 14 quarantined events require review',()=>check(i=>i.snapshot.events=[ev('QUARANTINED')],'REVIEW_REQUIRED','META_CONFLICT'));
test('OFF11 15 uncertain observation is not failure',()=>assert.equal(check(i=>i.snapshot.events=[ev('UNCERTAIN')],'LAB_UNVERIFIED_PROJECTION').observations[0].observation,'UNCERTAIN_REQUIRES_REVIEW'));
test('OFF11 16 cross-store denied before event contents',()=>check(i=>{i.snapshot.storeRef='s2';i.snapshot.events[0].providerErrorCode=131049},'DENIED','SCOPE'));
test('OFF11 17 cross-case denied',()=>check(i=>i.snapshot.caseRef='c_other','DENIED','SCOPE'));
test('OFF11 18 cross-flow denied',()=>check(i=>i.snapshot.flowRef='f_other','DENIED','SCOPE'));
test('OFF11 19 stale plan revision',()=>check(i=>i.snapshot.planRevision=2,'STALE','VERSION'));
test('OFF11 20 stale evidence revision',()=>check(i=>i.snapshot.evidenceRevision=3,'STALE','VERSION'));
test('OFF11 21 another attempt binding denied',()=>check(i=>i.snapshot.events[0].attemptRef='a_other','DENIED','ATTEMPT_BINDING'));
test('OFF11 22 swapped template version denied',()=>check(i=>i.snapshot.events[0].templateVersionRef='tpl_v2','DENIED','ATTEMPT_BINDING'));
test('OFF11 23 repeat identical event is deduplicated',()=>{
  const x=check(i=>i.snapshot.events.push(structuredClone(i.snapshot.events[0])),'LAB_UNVERIFIED_PROJECTION');
  assert.equal(x.uniqueEventCount,1);
});
test('OFF11 24 divergent replay of same event ID blocked',()=>check(i=>i.snapshot.events.push({...i.snapshot.events[0],correlationState:'CORRELATED_READ'}),'REVIEW_REQUIRED','DIVERGENT_REPLAY'));
test('OFF11 25 same sequence on distinct events blocked',()=>check(i=>i.snapshot.events.push(ev('CORRELATED_READ',{eventRef:'evt_02'})),'REVIEW_REQUIRED','ORDER_COLLISION'));
test('OFF11 26 sent and failed for same attempt need S0 review',()=>check(i=>i.snapshot.events.push(ev('CORRELATED_DEFINITIVE_FAILURE',{eventRef:'evt_02',sequence:2})),'REVIEW_REQUIRED','CONTRADICTORY_TERMINALS'));
test('OFF11 27 read before sent not invented as delivery proof',()=>{
  const x=check(i=>i.snapshot.events=[ev('CORRELATED_READ',{sequence:1}),ev('CORRELATED_SENT',{eventRef:'evt_02',sequence:2})],'LAB_UNVERIFIED_PROJECTION');
  assert.equal(x.observations[0].observation,'PROGRESS_WITHOUT_SENT_INFERENCE');
  assert.equal(x.observations[1].observation,'SENT_CANDIDATE_UNVERIFIED');
});
test('OFF11 28 late event sorts by sequence, not array arrival',()=>{
  const x=check(i=>i.snapshot.events=[ev('CORRELATED_READ',{sequence:9}),ev('CORRELATED_SENT',{eventRef:'evt_02',sequence:4})],'LAB_UNVERIFIED_PROJECTION');
  assert.deepEqual(x.observations.map(e=>e.sequence),[4,9]);
});
test('OFF11 29 cross-attempt evidence remains separate',()=>{
  const x=check(i=>i.snapshot.events.push(ev('CORRELATED_DEFINITIVE_FAILURE',{eventRef:'evt_02',sequence:2,attemptRef:'a_02',templateVersionRef:'tpl_v2'})),'LAB_UNVERIFIED_PROJECTION');
  assert.equal(x.uniqueEventCount,2);assert.equal(x.observations[1].finalTemplateCandidate,false);
});
test('OFF11 30 missing attempt list rejected',()=>check(i=>i.expected.attempts=[],'INVALID_INPUT','EXPECTED'));
test('OFF11 31 duplicate attempt ref rejected',()=>check(i=>i.expected.attempts.push({...i.expected.attempts[0]}),'INVALID_INPUT','EXPECTED'));
test('OFF11 32 event with extra send_authorized rejected',()=>check(i=>i.snapshot.events[0].send_authorized=true,'INVALID_INPUT','EVENT'));
test('OFF11 33 event with meta raw token rejected',()=>check(i=>i.snapshot.events[0].token='canary','INVALID_INPUT','EVENT'));
test('OFF11 34 unapproved phase/state pairing GRAPH->SENT rejected',()=>check(i=>i.snapshot.events[0].phase='GRAPH','INVALID_INPUT','EVENT'));
test('OFF11 35 unapproved phase/state pairing S0->API_ACCEPTED rejected',()=>check(i=>i.snapshot.events=[ev('API_ACCEPTED',{phase:'S0_RECONCILED'})],'INVALID_INPUT','EVENT'));
test('OFF11 36 empty snapshot remains unverified',()=>{const x=check(i=>i.snapshot.events=[],'LAB_UNVERIFIED_PROJECTION');assert.equal(x.uniqueEventCount,0);});
test('OFF11 37 wrong envelope schema fails closed',()=>check(i=>i.schemaVersion='other','INVALID_INPUT','ENVELOPE'));
test('OFF11 38 extra global field cannot confer authority',()=>check(i=>i.sendAuthorized=true,'INVALID_INPUT','ENVELOPE'));
test('OFF11 39 invalid provider error code denied',()=>check(i=>i.snapshot.events[0].providerErrorCode=-1,'INVALID_INPUT','EVENT'));
test('OFF11 40 oversize event list rejected',()=>check(i=>i.snapshot.events=Array.from({length:121},(_,j)=>ev('API_ACCEPTED',{eventRef:'evt_'+j,sequence:j})),'INVALID_INPUT','SNAPSHOT'));
test('OFF11 41 sparse array rejected',()=>check(i=>{i.snapshot.events=new Array(2);i.snapshot.events[0]=ev();},'INVALID_INPUT','ENVELOPE'));
test('OFF11 42 accessor never executed',()=>{
  let count=0;const i=base();Object.defineProperty(i.snapshot.events[0],'correlationState',{get(){count++;throw Error('leak');}});
  assert.equal(project(i).status,'INVALID_INPUT');assert.equal(count,0);
});
test('OFF11 43 cycles rejected',()=>check(i=>{i.loop=i;},'INVALID_INPUT','ENVELOPE'));
test('OFF11 44 no input mutation',()=>{
  const x=base(),s=structuredClone(x),result=project(x);
  assert.equal(result.status,'LAB_UNVERIFIED_PROJECTION');assert.deepEqual(x,s);
  assert.equal(Object.isFrozen(result.observations),true);
});
test('OFF11 45 no output representation accepted as verified F02 event',()=>{
  const x=project(base()),e=x.observations[0];assert.equal(e.verified,false);
  assert.equal(Object.hasOwn(e,'kind'),false);assert.equal(Object.hasOwn(e,'storeId'),false);
  assert.equal(Object.hasOwn(e,'sourceAuthenticated'),false);
});
test('OFF11 46 ordered multi-event preview immutable and unverified',()=>{
  const x=check(i=>i.snapshot.events.push(ev('CORRELATED_READ',{eventRef:'evt_02',sequence:2})),'LAB_UNVERIFIED_PROJECTION');
  assert.equal(Object.isFrozen(x),true);assert.equal(Object.isFrozen(x.observations[0]),true);
  assert.equal(x.uniqueEventCount,2);assert.equal(x.s0ReadbackVerified,false);
});
