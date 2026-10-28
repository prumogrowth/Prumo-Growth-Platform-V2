import test from 'node:test';
import assert from 'node:assert/strict';
import {
 WA36_REQUIREMENTS,createWa36PendingDraft,
 evaluateWa36RatificationProposal as evaluate,
} from './wa36-ratification-gate.ts';

const draft=()=>({
 ...createWa36PendingDraft(),
 evidence:createWa36PendingDraft().evidence.map(x=>({...x})),
});
const safe=(result:ReturnType<typeof evaluate>)=>{
 assert.ok(Object.isFrozen(result));
 assert.equal(Object.keys(result).length,10);
 for(const k of ['ack_allowed','send_authorized','retry_external',
  'production_authorized','service_authenticated','s0_write_authorized',
  'meta_delivery_confirmed','case_transition_authorized'] as const)
  assert.equal(result[k],false);
 assert.equal(result.required_owner_decisions,12);
};
const rejected=(value:unknown)=>{
 const d=evaluate(value);assert.equal(d.decision,'LAB_REJECTED_MANIFEST');safe(d);
};
test('WA36-01 12 canonical interfront obligations are unique and immutable',()=>{
 assert.equal(WA36_REQUIREMENTS.length,12);
 assert.equal(new Set(WA36_REQUIREMENTS.map(x=>x.id)).size,12);
 assert.equal(Object.isFrozen(WA36_REQUIREMENTS),true);
 for(const requirement of WA36_REQUIREMENTS){
  assert.match(requirement.id,/^WA36-[A-Z0-9-]+$/);
  assert.match(requirement.owner,/^[A-Z0-9_]+$/);
  assert.match(requirement.basis,/^[A-Z0-9_]+$/);
 }
});
test('WA36-02 base manifest remains blocked even when structurally complete',()=>{
 const d=evaluate(draft());assert.equal(d.decision,'LAB_REVIEW_PACKET_ONLY');safe(d);
});
test('WA36-03 attaching lab evidence to every requirement does not grant authority',()=>{
 const x=draft();
 for(const record of x.evidence){
  (record as {reference:string}).reference='LAB_EVIDENCE_ONLY';
  (record as {disposition:string}).disposition='PENDING_EXTERNAL_RATIFICATION';
 }
 const d=evaluate(x);assert.equal(d.decision,'LAB_REVIEW_PACKET_ONLY');safe(d);
});
test('WA36-04 referring to S0/S1 Draft is not authentication',()=>{
 const x=draft();
 for(const record of x.evidence)
  (record as {reference:string}).reference='DRAFT_OTHER_FRONT';
 const d=evaluate(x);assert.equal(d.decision,'LAB_REVIEW_PACKET_ONLY');safe(d);
});
test('WA36-05 a forged APPROVED disposition is never accepted',()=>{
 const x=draft();(x.evidence[0] as {disposition:string}).disposition='APPROVED';
 rejected(x);
});
test('WA36-06 a production-approved claim cannot be smuggled in top-level',()=>{
 rejected({...draft(),production_authorized:true});
 rejected({...draft(),ack_allowed:true});
 rejected({...draft(),service_authenticated:true});
});
test('WA36-07 proof of a human GoTrue CFI01 session is not a machine service',()=>{
 rejected({...draft(),user_role:'DIRETOR'});
 rejected({...draft(),gotrue_token:'FAKE'});
});
test('WA36-08 JWT or fake S1 role cannot appear on entries',()=>{
 const x=draft();rejected({...x,evidence:[
  {...x.evidence[0],principal_kind:'CONSULTOR'},...x.evidence.slice(1)]});
});
test('WA36-09 no requirement can be omitted',()=>{
 const x=draft();rejected({...x,evidence:x.evidence.slice(1)});
});
test('WA36-10 repeated requirement ID fails closed',()=>{
 const x=draft();rejected({...x,evidence:[
  x.evidence[0],x.evidence[0],...x.evidence.slice(2)]});
});
test('WA36-11 unknown requirement ID is not an implicit ratification',()=>{
 const x=draft();rejected({...x,evidence:[
  {...x.evidence[0],id:'WA36-SEND-PRODUCTION'},...x.evidence.slice(1)]});
});
test('WA36-12 manifests may not include raw evidence, tokens, PII or messages',()=>{
 const x=draft();
 for(const name of ['customer_phone','raw_webhook','access_token','wamid','sql',
  'commit_sha','signed_at_ms'])rejected({...x,evidence:[
   {...x.evidence[0],[name]:'fake'},...x.evidence.slice(1)]});
});
test('WA36-13 unrecognized evidence state remains denied',()=>{
 const x=draft();rejected({...x,evidence:[
 {...x.evidence[0],reference:'SIGNED_APPROVAL'},...x.evidence.slice(1)]});
});
test('WA36-14 missing status field on a row is rejected',()=>{
 const x=draft();const a={...x.evidence[0]} as Record<string,unknown>;
 delete a.disposition;
 rejected({...x,evidence:[a,...x.evidence.slice(1)]});
});
test('WA36-15 unknown contract revision cannot be accepted',()=>{
 rejected({...draft(),contract:'wa36.ratification-manifest.prod.v2'});
});
test('WA36-16 null/number/arrays and nonobjects always fail closed',()=>{
 for(const x of [null,undefined,NaN,7,'',[],true,{},{evidence:[]},
  {contract:'wa36.ratification-manifest.lab.v1'}])rejected(x);
});
test('WA36-17 hostile proxy and throwing getters are caught',()=>{
 const x=draft();const p=new Proxy(x,{ownKeys(){throw Error('trap')}});
 rejected(p);
 const y=draft();
 Object.defineProperty(y,'evidence',{get(){throw Error('secret')}});
 rejected(y);
});
test('WA36-18 inherited property and symbol extra props are rejected',()=>{
 const x=draft();
 rejected(Object.assign(Object.create({issuer:'OWNER'}),x));
 rejected(Object.assign({...x},{[Symbol('hidden')]:true}));
});
test('WA36-19 claimed signed S0 approval must be outside proposal schema',()=>{
 const x=draft();
 rejected({...x,approvals:[{owner:'S0',signature:'fake'}]});
 rejected({...x,approved_by:'S0'});
});
test('WA36-20 evidence order is not authority, but checklist integrity remains',()=>{
 const x=draft();
 const d=evaluate({...x,evidence:[...x.evidence].reverse()});
 assert.equal(d.decision,'LAB_REVIEW_PACKET_ONLY');safe(d);
});
test('WA36-21 empty issuer claims cannot silently shrink the required set',()=>{
 const x=draft();
 rejected({...x,evidence:x.evidence.map((y,i)=>i?y:null)});
 rejected({...x,evidence:x.evidence.map((y,i)=>i?y:{...y,id:null})});
});
test('WA36-22 no result exposes a real privilege or credential',()=>{
 const d=evaluate(draft()),j=JSON.stringify(d);
 for(const forbidden of ['wamid.','access_token','APP_SECRET','service_token',
  'commit_sha','recipient','CONCEDIDO','PRODUCTION_READY'])assert.ok(!j.includes(forbidden));
 safe(d);
});
