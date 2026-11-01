/**
 * OAI-OFF-04 — offline candidate for F02 planning and recovery.
 * Synthetic S0 assertions are NOT actual authentication, consent, signatures,
 * durable state, Meta acknowledgements or dispatch permission.
 * Pure functions. No SDK, network, disk, SQL, clock reads or business effects.
 */

export const F02_PRIVATE = 'prumo.openai.f02-plan-private/0.1-candidate';
export const F02_PROVIDER = 'prumo.openai.f02-plan-provider/0.1-candidate';
export const F02_RESPONSE = 'prumo.openai.f02-plan-response/0.1-candidate';
const VER = ['case','cycle','catalog','assignment','policy','consent','chain'];
const CATEGORY = ['MARKETING','UTILITY','AUTHENTICATION'];
const EVENT_KIND = ['API_ACCEPTED','QUEUED','UNKNOWN','SENT','DEFINITIVE_FAILED','META_131049','CUSTOMER_INBOUND','HANDOFF','OPT_OUT','CANCEL','TEMPLATE_REVOKED'];
const CONTROL = new Set(['CUSTOMER_INBOUND','HANDOFF','OPT_OUT','CANCEL','TEMPLATE_REVOKED']);
const ID = /^[A-Za-z0-9_.:-]{1,120}$/;
const has = (x,k) => Object.prototype.hasOwnProperty.call(x,k);
const obj = x => x!==null && typeof x==='object' && !Array.isArray(x) && (Object.getPrototypeOf(x)===Object.prototype || Object.getPrototypeOf(x)===null);
const exact = (x,r,o=[]) => obj(x) && r.every(k=>has(x,k)) && Reflect.ownKeys(x).every(k=>typeof k==='string'&&(r.includes(k)||o.includes(k)));
const id = x => typeof x==='string' && ID.test(x);
const natural = x => Number.isSafeInteger(x) && x>=0;
const list = (x,max=60) => Array.isArray(x) && x.length<=max && Object.keys(x).length===x.length;
const unique = a=>new Set(a).size===a.length;
const error = (status,stage)=>Object.freeze({status,stage});
const text = (x,max=1800) => typeof x==='string' && x.length>0 && x.length<=max && x.trim().length>0 && !/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(x);
function validTime(x) {
  if(typeof x!=='string')return false;
  const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|([+-])(\d{2}):(\d{2}))$/.exec(x);
  if(!m)return false;
  const [,y,mo,d,h,mi,s,,zone,sg,oh,om]=m;
  const yy=+y,mm=+mo,dd=+d;
  if(yy<2000||yy>2100||mm<1||mm>12||dd<1||dd>new Date(Date.UTC(yy,mm,0)).getUTCDate() || +h>23 || +mi>59 || +s>59)return false;
  if(zone!=='Z'&&(+oh>14 || +om>59 || (+oh===14&&+om!==0)))return false;
  return Number.isFinite(Date.parse(x));
}
function safe(x,level=0,seen=new Set()) {
  if(level>12)return false;
  if(x===null||typeof x==='boolean'||typeof x==='string')return true;
  if(typeof x==='number')return Number.isFinite(x);
  if(typeof x!=='object'||seen.has(x)||(!obj(x)&&!Array.isArray(x)))return false;
  if(Array.isArray(x)&&(!list(x,120)||Reflect.ownKeys(x).some(k=>k!=='length'&&!/^(0|[1-9]\d*)$/.test(k))))return false;
  if(Reflect.ownKeys(x).some(k=>typeof k!=='string'||['__proto__','prototype','constructor'].includes(k)))return false;
  seen.add(x);
  for(const desc of Object.values(Object.getOwnPropertyDescriptors(x)))if(!has(desc,'value')||!safe(desc.value,level+1,seen))return false;
  seen.delete(x);return true;
}
const clone = x => JSON.parse(JSON.stringify(x));
function freeze(x) {if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
const versions = x=>exact(x,VER)&&VER.every(k=>natural(x[k]));
function authorized(s) {
  if(!obj(s))return false;
  return ['authenticated','authorized','tenantAllowed'].every(k=>{const d=Object.getOwnPropertyDescriptor(s,k);return d&&has(d,'value')&&d.value===true;});
}
function scope(s) {
  return exact(s,['authenticated','authorized','tenantAllowed','storeId','caseId','personId','expectedVersions','currentVersions'])&&
    [s.storeId,s.caseId,s.personId].every(id)&&versions(s.expectedVersions)&&versions(s.currentVersions);
}
function requestValid(r,s) {
  return exact(r,['explicitS0Request','optOut','ownerRoute','purpose','handoffDefinitive','priorAiPlanCancelled',
    'windowStart','windowEnd','maxAttempts','templates','instructions','privateRefs','continuity']) &&
    r.explicitS0Request===true && r.optOut===false &&
    ['human','seller_ai'].includes(r.ownerRoute)&&id(r.purpose)&&
    typeof r.handoffDefinitive==='boolean'&&typeof r.priorAiPlanCancelled==='boolean'&&
    (!r.handoffDefinitive || (r.ownerRoute==='human' && r.priorAiPlanCancelled===true)) &&
    !(r.purpose==='post_human'&&r.ownerRoute!=='human') &&
    validTime(r.windowStart)&&validTime(r.windowEnd)&&Date.parse(r.windowStart)<Date.parse(r.windowEnd)&&
    natural(r.maxAttempts)&&r.maxAttempts<=16&&list(r.templates,32)&&r.templates.length>0&&
    unique(r.templates.map(t=>t?.id+'@'+t?.version))&&
    r.templates.every(t=>exact(t,['id','version','storeId','purpose','category','active','approved','eligible'])&&
      id(t.id)&&id(t.version)&&t.storeId===s.storeId&&t.purpose===r.purpose&&
      CATEGORY.includes(t.category)&&t.active===true&&t.approved===true&&t.eligible===true)&&
    exact(r.instructions,['text','version'])&&text(r.instructions.text)&&id(r.instructions.version)&&
    exact(r.privateRefs,['consentRef','authorizationRef','sessionRef','s0EvidenceRef'])&&
    Object.values(r.privateRefs).every(id)&&
    exact(r.continuity,['chainRef','chainVersion','previousPlanRef','revision'])&&
    id(r.continuity.chainRef)&&natural(r.continuity.chainVersion)&&natural(r.continuity.revision)&&
    (r.continuity.previousPlanRef===null||id(r.continuity.previousPlanRef))&&
    r.continuity.chainVersion===s.expectedVersions.chain;
}
const issued=new WeakSet();
/** Inspect authorization through descriptors before invoking any caller-owned properties. */
export function prepareF02Plan(input) {
  try{
    if(!obj(input)||!authorized(Object.getOwnPropertyDescriptor(input,'scope')?.value))return error('DENIED','S0_SCOPE');
    if(!safe(input)||!exact(input,['schemaVersion','requestId','providerTag','nowMs','deadlineMs','scope','request'])||
       input.schemaVersion!==F02_PRIVATE||!id(input.requestId)||!id(input.providerTag)||
       !natural(input.nowMs)||!natural(input.deadlineMs)||input.deadlineMs<=input.nowMs||
       !scope(input.scope)||!requestValid(input.request,input.scope))return error('INVALID_INPUT','PRIVATE');
    if(VER.some(k=>input.scope.expectedVersions[k]!==input.scope.currentVersions[k]))return error('STALE','S0_VERSION');
    const saved=freeze(clone(input));
    const aliases=saved.request.templates.map((t,i)=>({alias:'tpl_'+String(i+1).padStart(3,'0'),id:t.id,version:t.version}));
    const handle=Object.freeze({status:'READY_CANDIDATE',private: saved,aliases:freeze(aliases)});
    issued.add(handle);return handle;
  }catch{return error('INVALID_INPUT','PRIVATE');}
}
/** Provider view: no tenant, person, case, chain, consent, session, evidence receipt or template IDs. */
export function f02ProviderView(handle) {
  try{
    if(!issued.has(handle))return error('INVALID_INPUT','HANDLE');
    const r=handle.private.request;
    return freeze({schemaVersion:F02_PROVIDER,providerTag:handle.private.providerTag,
      instructions:{text:r.instructions.text},
      planning:{purpose:r.purpose,windowStart:r.windowStart,windowEnd:r.windowEnd,maxAttempts:r.maxAttempts,
        templates:r.templates.map((t,i)=>({alias:handle.aliases[i].alias,version:t.version}))}});
  }catch{return error('INVALID_INPUT','HANDLE');}
}
function parseResponse(raw) {
  if(typeof raw!=='string'||Buffer.byteLength(raw,'utf8')>16384)return null;
  // Strict duplicate-key check by tokenized context, including escaped aliases.
  try{
    const v=JSON.parse(raw), stack=[];
    for(const m of raw.matchAll(/"(?:\\.|[^"\\])*"|[{}\[\]]/g)){
      const t=m[0];
      if(t==='{'||t==='['){stack.push(t==='{'?new Set():null);if(stack.length>12)return null;}
      else if(t==='}'||t===']')stack.pop();
      else if(/^\s*:/.test(raw.slice(m.index+t.length))){const k=JSON.parse(t),top=stack.at(-1);if(!(top instanceof Set)||top.has(k))return null;top.add(k);}
    }
    return safe(v)?v:null;
  }catch{return null;}
}
/** A proposed plan can only be returned to S0 for a NEW recheck; never schedule/send. */
export function evaluateF02Model(handle,raw,{nowMs,scope}={}) {
  try{
    if(!issued.has(handle))return error('INVALID_INPUT','HANDLE');
    const p=handle.private;
    if(!authorized(scope))return error('DENIED','S0_RECHECK');
    if(!safe(scope)||!scopeEqual(scope,p.scope))return error('DENIED','S0_RECHECK');
    if(VER.some(k=>scope.currentVersions[k]!==p.scope.expectedVersions[k]))return error('STALE','S0_RECHECK');
    if(!natural(nowMs))return error('INVALID_INPUT','CLOCK');
    // Clock rollback is not proof that a pending plan is still within its window.
    if(nowMs<p.nowMs)return error('REVIEW_REQUIRED','CLOCK');
    if(nowMs>p.deadlineMs)return error('LATE_RESPONSE','DEADLINE');
    const out=parseResponse(raw);
    if(!exact(out,['schemaVersion','providerTag','attempts','finalTemplate'])||out.schemaVersion!==F02_RESPONSE||
        out.providerTag!==p.providerTag||!list(out.attempts,16)||out.attempts.length>p.request.maxAttempts)return error('SCHEMA_INVALID','RESULT');
    const table=new Map(handle.aliases.map(a=>[a.alias,a]));
    let prev=Date.parse(p.request.windowStart)-1;
    function translate(a) {
      if(!exact(a,['templateAlias','version','purpose','at'])||!id(a.templateAlias)||!id(a.version)||
        a.purpose!==p.request.purpose||!validTime(a.at))return null;
      const t=table.get(a.templateAlias),time=Date.parse(a.at);
      if(!t||t.version!==a.version||time<=prev||time<Date.parse(p.request.windowStart)||
         time>Date.parse(p.request.windowEnd))return null;
      prev=time;
      return {templateId:t.id,templateVersion:t.version,purpose:a.purpose,at:a.at};
    }
    const rows=[];
    for(const a of out.attempts){const row=translate(a);if(!row)return error('SCHEMA_INVALID','RESULT');rows.push(row);}
    const final=out.finalTemplate===null?null:translate(out.finalTemplate);
    if(out.finalTemplate!==null&&!final)return error('SCHEMA_INVALID','RESULT');
    return freeze({status:'S0_RECHECK_ONLY',schemaVersion:'prumo.openai.f02-plan-candidate/0.1',
      requestId:p.requestId,chainRef:p.request.continuity.chainRef,
      expectedVersions:clone(p.scope.expectedVersions),attempts:rows,finalTemplate:final,
      sendAuthorized:false,schedulingAuthorized:false,commercialTransitionAuthorized:false});
  }catch{return error('MODEL_FAILURE','RESULT');}
}
function scopeEqual(a,b){
  return exact(a,['authenticated','authorized','tenantAllowed','storeId','caseId','personId','expectedVersions','currentVersions']) &&
    scope(a)&&a.storeId===b.storeId&&a.caseId===b.caseId&&a.personId===b.personId&&
    VER.every(k=>a.expectedVersions[k]===b.expectedVersions[k]);
}
/** Pure ledger preflight on *synthetic* S0 timeline; exact replays are harmless. */
export function reviewF02Continuity({scope:sc,plan,events,prior}={}) {
  try{
    if(!authorized(sc))return error('DENIED','S0_SCOPE');
    if(!safe({scope:sc,plan,events,prior})||!scope(sc)||!exact(plan,['storeId','personId','caseId','chainRef','requestId','revision','fingerprint','ownerRoute','isFinal','attemptIds','expectedVersions'])||
      ![plan.storeId,plan.personId,plan.caseId,plan.chainRef,plan.requestId].every(id)||
      !natural(plan.revision)||!id(plan.fingerprint)||!['human','seller_ai'].includes(plan.ownerRoute)||typeof plan.isFinal!=='boolean'||
      !list(plan.attemptIds,32)||plan.attemptIds.length===0||!unique(plan.attemptIds)||!plan.attemptIds.every(id)||!versions(plan.expectedVersions)||
      !list(events,100)||(prior!==null&&!exact(prior,['requestId','revision','fingerprint','verified'])))return error('INVALID_INPUT','TIMELINE');
    if(plan.storeId!==sc.storeId||plan.personId!==sc.personId||plan.caseId!==sc.caseId)return error('DENIED','S0_SCOPE');
    if(VER.some(k=>sc.expectedVersions[k]!==sc.currentVersions[k]||plan.expectedVersions[k]!==sc.expectedVersions[k]))return error('STALE','VERSION');
    if(prior!==null){
      if(!id(prior.requestId)||!natural(prior.revision)||!id(prior.fingerprint)||prior.verified!==true)return error('REVIEW_REQUIRED','PRIOR');
      if(prior.requestId===plan.requestId&&prior.revision===plan.revision&&prior.fingerprint===plan.fingerprint)return error('ALREADY_HANDLED_REVIEW_ONLY','REPLAY');
      return error('REVIEW_REQUIRED','REPLAY');
    }
    const eventsById=new Map(),sequences=new Set();
    for(const e of events){
      if(!exact(e,['eventId','sequence','kind','storeId','personId','caseId','chainRef','attemptId','verified'])||!id(e.eventId)||!natural(e.sequence)||
         !EVENT_KIND.includes(e.kind)||e.chainRef!==plan.chainRef||e.storeId!==sc.storeId||e.personId!==sc.personId||e.caseId!==sc.caseId||typeof e.verified!=='boolean'||
         (CONTROL.has(e.kind)? e.attemptId!==null: !id(e.attemptId)||!plan.attemptIds.includes(e.attemptId)))return error('INVALID_INPUT','EVENT');
      const encoded=JSON.stringify(e);
      if(eventsById.has(e.eventId)){
        if(eventsById.get(e.eventId).encoded!==encoded)return error('REVIEW_REQUIRED','REPLAY');
        continue;
      }
      if(sequences.has(e.sequence))return error('REVIEW_REQUIRED','ORDER');
      eventsById.set(e.eventId,{...e,encoded});sequences.add(e.sequence);
    }
    let hold=false,terminal=false,unknown=false,metaHold=false,sent=false;
    const terminalByAttempt=new Map();
    for(const e of [...eventsById.values()].sort((a,b)=>a.sequence-b.sequence)){
      if(!e.verified)return error('REVIEW_REQUIRED','UNVERIFIED');
      if(e.kind==='OPT_OUT'||e.kind==='CANCEL'||e.kind==='TEMPLATE_REVOKED'||e.kind==='HANDOFF'&&plan.ownerRoute==='seller_ai')terminal=true;
      if(e.kind==='CUSTOMER_INBOUND'||e.kind==='HANDOFF')hold=true;
      if(e.kind==='API_ACCEPTED'||e.kind==='QUEUED'||e.kind==='UNKNOWN')unknown=true;
      if(e.kind==='META_131049')metaHold=true;
      if(e.kind==='SENT')sent=true;
      if(e.kind==='DEFINITIVE_FAILED')hold=true;
      if(['SENT','DEFINITIVE_FAILED'].includes(e.kind)){
        const old=terminalByAttempt.get(e.attemptId);
        if(old&&old!==e.kind)return error('REVIEW_REQUIRED','CONTRADICTORY_TRANSPORT');
        terminalByAttempt.set(e.attemptId,e.kind);
      }
      // SENT remains a synthetic observation, never send approval, C09 trigger or commercial fact.
    }
    if(terminal)return error('CANCELLED_REVIEW_ONLY','TIMELINE');
    if(metaHold)return error('META_ECOSYSTEM_REVIEW','TIMELINE');
    if(hold)return error('REVIEW_REQUIRED','TIMELINE');
    if(unknown)return error('AWAITING_META_PROOF','TIMELINE');
    if(sent)return error('ALREADY_SENT_EVIDENCE_ONLY','TIMELINE');
    return freeze({status:'S0_RECHECK_ONLY',stage:'TIMELINE',requestId:plan.requestId,
      uniqueEventCount:eventsById.size,sendAuthorized:false,schedulingAuthorized:false,
      commercialTransitionAuthorized:false});
  }catch{return error('INVALID_INPUT','TIMELINE');}
}
