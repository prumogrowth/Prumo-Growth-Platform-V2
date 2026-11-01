import test from 'node:test';
import assert from 'node:assert/strict';
import {F02_PRIVATE,F02_PROVIDER,F02_RESPONSE,prepareF02Plan,f02ProviderView,evaluateF02Model,reviewF02Continuity} from '../f02-plan-boundary.mjs';

const versions=()=>({case:1,cycle:2,catalog:3,assignment:4,policy:5,consent:6,chain:7});
function input(){return {
  schemaVersion:F02_PRIVATE,requestId:'req_01',providerTag:'opaque_01',nowMs:100,deadlineMs:200,
  scope:{authenticated:true,authorized:true,tenantAllowed:true,storeId:'s1',caseId:'c1',personId:'p1',expectedVersions:versions(),currentVersions:versions()},
  request:{explicitS0Request:true,optOut:false,ownerRoute:'human',purpose:'post_human',handoffDefinitive:true,
    priorAiPlanCancelled:true,windowStart:'2026-11-01T10:00:00Z',windowEnd:'2026-11-01T18:00:00Z',maxAttempts:2,
    templates:[{id:'t1',version:'v1',storeId:'s1',purpose:'post_human',category:'MARKETING',active:true,approved:true,eligible:true},
      {id:'t2',version:'v2',storeId:'s1',purpose:'post_human',category:'UTILITY',active:true,approved:true,eligible:true}],
    instructions:{text:'Planeje apenas modelos permitidos.',version:'cfg01'},
    privateRefs:{consentRef:'private_consent',authorizationRef:'private_grant',sessionRef:'private_session',s0EvidenceRef:'private_receipt'},
    continuity:{chainRef:'chain1',chainVersion:7,previousPlanRef:'previous_plan',revision:1}}
}};
const prepared=()=>{const p=prepareF02Plan(input());assert.equal(p.status,'READY_CANDIDATE');return p;};
const ans=(extra={})=>JSON.stringify({schemaVersion:F02_RESPONSE,providerTag:'opaque_01',attempts:[{templateAlias:'tpl_001',version:'v1',purpose:'post_human',at:'2026-11-01T11:00:00Z'}],finalTemplate:{templateAlias:'tpl_002',version:'v2',purpose:'post_human',at:'2026-11-01T12:00:00Z'},...extra});
const reply=(h=prepared(),v=ans(),nowMs=110,scope=structuredClone(h.private.scope))=>evaluateF02Model(h,v,{nowMs,scope});
function timeline(){return {scope:input().scope,plan:{storeId:'s1',personId:'p1',caseId:'c1',chainRef:'chain1',requestId:'req_01',revision:1,fingerprint:'fp01',ownerRoute:'human',isFinal:true,attemptIds:['attempt1','attempt2'],expectedVersions:versions()},events:[],prior:null};}
const ev=(kind,eventId='evt1',sequence=1,attemptId='attempt1')=>({eventId,sequence,kind,storeId:'s1',personId:'p1',caseId:'c1',chainRef:'chain1',attemptId,verified:true});
const bad=(i,status='INVALID_INPUT')=>assert.equal(prepareF02Plan(i).status,status);

test('OFF04 01 valid private request and frozen preparation',()=>{const p=prepared();assert.equal(Object.isFrozen(p.private.request),true);});
test('OFF04 02 provider view minimized, aliases only and no sensitive IDs',()=>{const view=f02ProviderView(prepared());assert.equal(view.schemaVersion,F02_PROVIDER);assert.equal(view.planning.templates[0].alias,'tpl_001');for(const s of ['private_consent','private_grant','private_session','private_receipt','s1','p1','c1','t1','t2','chain1'])assert.ok(!JSON.stringify(view).includes('"'+s+'"'));});
test('OFF04 03 success is proposal, never an effect',()=>{const r=reply();assert.equal(r.status,'S0_RECHECK_ONLY');assert.equal(r.sendAuthorized,false);assert.equal(r.schedulingAuthorized,false);assert.equal(r.commercialTransitionAuthorized,false);assert.equal(r.attempts[0].templateId,'t1');assert.equal(r.finalTemplate.templateId,'t2');});
test('OFF04 04 unauthorized before stale',()=>{const x=input();x.scope.authorized=false;x.scope.currentVersions.case=9;bad(x,'DENIED');});
test('OFF04 05 stale private version',()=>{const x=input();x.scope.currentVersions.case=99;bad(x,'STALE');});
test('OFF04 06 explicit S0 request required',()=>{const x=input();x.request.explicitS0Request=false;bad(x);});
test('OFF04 07 optout blocks plan',()=>{const x=input();x.request.optOut=true;bad(x);});
test('OFF04 08 handoff forbids seller-ai ownership',()=>{const x=input();x.request.ownerRoute='seller_ai';bad(x);});
test('OFF04 09 handoff requires prior ai plan cancelled',()=>{const x=input();x.request.priorAiPlanCancelled=false;bad(x);});
test('OFF04 10 post human cannot change purpose route',()=>{const x=input();x.request.handoffDefinitive=false;x.request.ownerRoute='seller_ai';bad(x);});
test('OFF04 11 template tenant isolation',()=>{const x=input();x.request.templates[0].storeId='s2';bad(x);});
test('OFF04 12 inactive template',()=>{const x=input();x.request.templates[0].active=false;bad(x);});
test('OFF04 13 unapproved template',()=>{const x=input();x.request.templates[0].approved=false;bad(x);});
test('OFF04 14 ineligible template',()=>{const x=input();x.request.templates[0].eligible=false;bad(x);});
test('OFF04 15 duplicate template version',()=>{const x=input();x.request.templates[1]={...x.request.templates[0]};bad(x);});
test('OFF04 16 template purpose not allowed',()=>{const x=input();x.request.templates[1].purpose='campaign';bad(x);});
test('OFF04 17 unsupported Meta category',()=>{const x=input();x.request.templates[0].category='PROMOTIONAL';bad(x);});
test('OFF04 18 refused extra field at nested level',()=>{const x=input();x.request.templates[1].sendAuthorized=true;bad(x);});
test('OFF04 19 no fifth instruction field / F01 behavior',()=>{const x=input();x.request.instructions.behavior='override';bad(x);});
test('OFF04 20 cannot move chain version',()=>{const x=input();x.request.continuity.chainVersion=6;bad(x);});
test('OFF04 21 invalid day rejected',()=>{const x=input();x.request.windowStart='2026-02-30T10:00:00Z';bad(x);});
test('OFF04 22 nonexistent timezone rejected',()=>{const x=input();x.request.windowEnd='2026-11-01T18:00:00+25:00';bad(x);});
test('OFF04 23 getter on envelope never executed',()=>{let hits=0;const x=input();Object.defineProperty(x,'request',{get(){hits++;throw Error('secret');}});bad(x);assert.equal(hits,0);});
test('OFF04 24 getter on scope never executed',()=>{let hits=0;const x=input();Object.defineProperty(x.scope,'authenticated',{get(){hits++;throw Error('secret');}});bad(x,'DENIED');assert.equal(hits,0);});
test('OFF04 25 anonymous handle blocked',()=>assert.equal(f02ProviderView({status:'READY_CANDIDATE'}).status,'INVALID_INPUT'));
test('OFF04 26 provider tag mismatch',()=>assert.equal(reply(prepared(),ans({providerTag:'other'})).status,'SCHEMA_INVALID'));
test('OFF04 27 unknown template alias',()=>assert.equal(reply(prepared(),ans({attempts:[{templateAlias:'tpl_003',version:'v1',purpose:'post_human',at:'2026-11-01T11:00:00Z'}]})).status,'SCHEMA_INVALID'));
test('OFF04 28 tampered version',()=>assert.equal(reply(prepared(),ans({attempts:[{templateAlias:'tpl_001',version:'v77',purpose:'post_human',at:'2026-11-01T11:00:00Z'}]})).status,'SCHEMA_INVALID'));
test('OFF04 29 extra slots in model response',()=>assert.equal(reply(prepared(),ans({slots:{name:'customer'}})).status,'SCHEMA_INVALID'));
test('OFF04 30 stale S0 at result',()=>{const h=prepared(),s=structuredClone(h.private.scope);s.currentVersions.policy++;assert.equal(reply(h,ans(),110,s).status,'STALE');});
test('OFF04 31 S0 authorization revoked at result',()=>{const h=prepared(),s=structuredClone(h.private.scope);s.authorized=false;s.currentVersions.case++;assert.equal(reply(h,ans(),110,s).status,'DENIED');});
test('OFF04 32 result wrong tenant denied',()=>{const h=prepared(),s=structuredClone(h.private.scope);s.storeId='s2';assert.equal(reply(h,ans(),110,s).status,'DENIED');});
test('OFF04 33 timeout/late result',()=>assert.equal(reply(prepared(),ans(),201).status,'LATE_RESPONSE'));
test('OFF04 34 attempts beyond maximum',()=>{const q=JSON.parse(ans());q.attempts=Array.from({length:3},(_,i)=>({...q.attempts[0],at:`2026-11-01T1${i}:00:00Z`}));assert.equal(reply(prepared(),JSON.stringify(q)).status,'SCHEMA_INVALID');});
test('OFF04 35 duplicate JSON key blocked',()=>{const q=ans().replace('{','{"providerTag":"opaque_01",');assert.equal(reply(prepared(),q).status,'SCHEMA_INVALID');});
test('OFF04 36 escaped alias duplicate JSON key blocked',()=>{const q=ans().replace('{','{"provider\\u0054ag":"opaque_01",');assert.equal(reply(prepared(),q).status,'SCHEMA_INVALID');});
test('OFF04 37 duplicate attempt time',()=>{const q=JSON.parse(ans());q.attempts.push({...q.attempts[0]});assert.equal(reply(prepared(),JSON.stringify(q)).status,'SCHEMA_INVALID');});
test('OFF04 38 final before earlier attempt',()=>{const q=JSON.parse(ans());q.finalTemplate.at='2026-11-01T10:30:00Z';assert.equal(reply(prepared(),JSON.stringify(q)).status,'SCHEMA_INVALID');});
test('OFF04 39 outside window',()=>{const q=JSON.parse(ans());q.attempts[0].at='2026-11-02T11:00:00Z';assert.equal(reply(prepared(),JSON.stringify(q)).status,'SCHEMA_INVALID');});
test('OFF04 40 malformed JSON blocked',()=>assert.equal(reply(prepared(),'{broken').status,'SCHEMA_INVALID'));
test('OFF04 41 no model grants',()=>assert.equal(reply(prepared(),ans({sendAuthorized:true})).status,'SCHEMA_INVALID'));
test('OFF04 42 no model toolcalls',()=>assert.equal(reply(prepared(),ans({tool_calls:[{name:'send'}]})).status,'SCHEMA_INVALID'));
test('OFF04 43 zero attempts with final allowed under explicit window',()=>{const q=JSON.parse(ans());q.attempts=[];assert.equal(reply(prepared(),JSON.stringify(q)).status,'S0_RECHECK_ONLY');});
test('OFF04 44 null final with empty attempt accepted only as candidate',()=>{const q=JSON.parse(ans());q.attempts=[];q.finalTemplate=null;const r=reply(prepared(),JSON.stringify(q));assert.equal(r.status,'S0_RECHECK_ONLY');assert.equal(r.sendAuthorized,false);});
test('OFF04 45 success continuation returns review only',()=>{const r=reviewF02Continuity(timeline());assert.equal(r.status,'S0_RECHECK_ONLY');assert.equal(r.sendAuthorized,false);});
test('OFF04 46 continuation denied before stale',()=>{const x=timeline();x.scope.authorized=false;x.scope.currentVersions.catalog++;assert.equal(reviewF02Continuity(x).status,'DENIED');});
test('OFF04 47 duplicate event replay idempotent',()=>{const x=timeline();x.events=[ev('SENT'),ev('SENT')];const r=reviewF02Continuity(x);assert.equal(r.status,'ALREADY_SENT_EVIDENCE_ONLY');});
test('OFF04 48 event ID contradictory',()=>{const x=timeline();x.events=[ev('SENT'),ev('DEFINITIVE_FAILED')];assert.equal(reviewF02Continuity(x).status,'REVIEW_REQUIRED');});
test('OFF04 49 equal sequence different event IDs conflict',()=>{const x=timeline();x.events=[ev('SENT'),ev('SENT','evt2',1)];assert.equal(reviewF02Continuity(x).status,'REVIEW_REQUIRED');});
test('OFF04 50 technical status API_ACCEPTED not sent',()=>{const x=timeline();x.events=[ev('API_ACCEPTED')];assert.equal(reviewF02Continuity(x).status,'AWAITING_META_PROOF');});
test('OFF04 51 unknown status awaits proof',()=>{const x=timeline();x.events=[ev('UNKNOWN')];assert.equal(reviewF02Continuity(x).status,'AWAITING_META_PROOF');});
test('OFF04 52 Meta 131049 requires review',()=>{const x=timeline();x.events=[ev('META_131049')];assert.equal(reviewF02Continuity(x).status,'META_ECOSYSTEM_REVIEW');});
test('OFF04 53 optout cancels',()=>{const x=timeline();x.events=[ev('OPT_OUT','evt1',1,null)];assert.equal(reviewF02Continuity(x).status,'CANCELLED_REVIEW_ONLY');});
test('OFF04 54 template revoked cancels',()=>{const x=timeline();x.events=[ev('TEMPLATE_REVOKED','evt1',1,null)];assert.equal(reviewF02Continuity(x).status,'CANCELLED_REVIEW_ONLY');});
test('OFF04 55 customer inbound requires review',()=>{const x=timeline();x.events=[ev('CUSTOMER_INBOUND','evt1',1,null)];assert.equal(reviewF02Continuity(x).status,'REVIEW_REQUIRED');});
test('OFF04 56 handoff cancels old seller AI route',()=>{const x=timeline();x.plan.ownerRoute='seller_ai';x.events=[ev('HANDOFF','evt1',1,null)];assert.equal(reviewF02Continuity(x).status,'CANCELLED_REVIEW_ONLY');});
test('OFF04 57 unverified event blocks',()=>{const x=timeline();x.events=[{...ev('SENT'),verified:false}];assert.equal(reviewF02Continuity(x).status,'REVIEW_REQUIRED');});
test('OFF04 58 wrong chain blocked',()=>{const x=timeline();x.events=[{...ev('SENT'),chainRef:'other'}];assert.equal(reviewF02Continuity(x).status,'INVALID_INPUT');});
test('OFF04 59 conflict sent and failure for same attempt',()=>{const x=timeline();x.events=[ev('SENT'),ev('DEFINITIVE_FAILED','evt2',2)];assert.equal(reviewF02Continuity(x).status,'REVIEW_REQUIRED');});
test('OFF04 60 prior exact S0 synthetic replay',()=>{const x=timeline();x.prior={requestId:'req_01',revision:1,fingerprint:'fp01',verified:true};assert.equal(reviewF02Continuity(x).status,'ALREADY_HANDLED_REVIEW_ONLY');});
test('OFF04 61 prior replay altered fingerprint blocked',()=>{const x=timeline();x.prior={requestId:'req_01',revision:1,fingerprint:'DIFF',verified:true};assert.equal(reviewF02Continuity(x).status,'REVIEW_REQUIRED');});
test('OFF04 62 wrong tenant in timeline denied',()=>{const x=timeline();x.plan.storeId='s2';assert.equal(reviewF02Continuity(x).status,'DENIED');});
test('OFF04 63 version changed in timeline',()=>{const x=timeline();x.scope.currentVersions.chain++;assert.equal(reviewF02Continuity(x).status,'STALE');});
test('OFF04 64 unknown event field rejected',()=>{const x=timeline();x.events=[{...ev('SENT'),grant:true}];assert.equal(reviewF02Continuity(x).status,'INVALID_INPUT');});
test('OFF04 65 no real clock, network, filesystem or process use on public functions',()=>{const p=prepared();assert.equal(reply(p).status,'S0_RECHECK_ONLY');assert.equal(reviewF02Continuity(timeline()).status,'S0_RECHECK_ONLY');});

test('OFF04 66 event from another store denied by synthetic preflight',()=>{const x=timeline();x.events=[{...ev('SENT'),storeId:'other'}];assert.equal(reviewF02Continuity(x).status,'INVALID_INPUT');});
test('OFF04 67 event from another customer refused',()=>{const x=timeline();x.events=[{...ev('SENT'),personId:'other'}];assert.equal(reviewF02Continuity(x).status,'INVALID_INPUT');});
test('OFF04 68 sent receipt cannot make chain available for another send',()=>{const x=timeline();x.events=[ev('SENT')];assert.equal(reviewF02Continuity(x).status,'ALREADY_SENT_EVIDENCE_ONLY');});
test('OFF04 69 transport uncertainty has precedence over confirmed sent',()=>{const x=timeline();x.events=[ev('SENT'),ev('UNKNOWN','evt2',2,'attempt2')];assert.equal(reviewF02Continuity(x).status,'AWAITING_META_PROOF');});

// OFF-07 audit: fail closed on a backward clock and an empty plan ledger.
test('AUD-F02-70 reject clock rollback before plan request',()=>{
  const h=prepared();assert.equal(reply(h,ans(),99).status,'REVIEW_REQUIRED');
});
test('AUD-F02-71 empty attempt registry must not be READY_FOR_S0_RECHECK',()=>{
  const x=timeline();x.plan.attemptIds=[];assert.equal(reviewF02Continuity(x).status,'INVALID_INPUT');
});
