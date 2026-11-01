/**
 * OFF-11: WA-39 -> F02 consumer compatibility laboratory.
 * All inputs are caller-owned synthetic assertions. They are NOT authenticated
 * S0 readbacks, verified Meta callbacks, grants, or permission to dispatch.
 * Pure, deterministic, no SDK, I/O, persistence, clock, retries or effects.
 */
export const WA39_LAB_INPUT = 'prumo.openai.f02-wa39-consumer/0.1-lab';
export const WA39_LAB_RESULT = 'prumo.openai.f02-wa39-preview/0.1-lab';
const ID = /^[A-Za-z0-9_.:-]{1,120}$/;
const STATE = new Set([
  'API_ACCEPTED', 'QUEUED', 'UNKNOWN', 'PENDING_CORRELATION',
  'CORRELATED_SENT', 'CORRELATED_DELIVERED', 'CORRELATED_READ',
  'CORRELATED_DEFINITIVE_FAILURE', 'UNCERTAIN', 'CONFLICT', 'QUARANTINED'
]);
const GRAPH = new Set(['API_ACCEPTED','QUEUED','UNKNOWN']);
const RECONCILED = new Set([...STATE].filter(s=>!GRAPH.has(s)));
const has = (v,k)=>Object.prototype.hasOwnProperty.call(v,k);
const obj = v=>v!==null && typeof v==='object' && !Array.isArray(v) &&
  (Object.getPrototypeOf(v)===Object.prototype || Object.getPrototypeOf(v)===null);
const exact = (v, keys)=>obj(v) && Reflect.ownKeys(v).length===keys.length &&
  keys.every(k=>has(v,k)) && Reflect.ownKeys(v).every(k=>typeof k==='string' && keys.includes(k));
const id = v=>typeof v==='string' && ID.test(v);
const int = v=>Number.isSafeInteger(v) && v>=0;
const arr = (v,max)=>Array.isArray(v) && v.length<=max && Object.keys(v).length===v.length &&
  Reflect.ownKeys(v).every(k=>k==='length'||/^(0|[1-9]\d*)$/.test(String(k)));
function safe(v,depth=0,stack=new Set()) {
  if(depth>9)return false;
  if(v===null||typeof v==='string'||typeof v==='boolean')return true;
  if(typeof v==='number')return Number.isFinite(v);
  if(typeof v!=='object'||stack.has(v)||(!obj(v)&&!Array.isArray(v)))return false;
  if(Array.isArray(v)&&!arr(v,160))return false;
  stack.add(v);
  try{
    for(const k of Reflect.ownKeys(v)){
      if(typeof k!=='string'||['__proto__','constructor','prototype'].includes(k))return false;
      const d=Object.getOwnPropertyDescriptor(v,k);
      if(!d || !has(d,'value') || !safe(d.value,depth+1,stack))return false;
    }
    return true;
  }finally{stack.delete(v);}
}
const FLAGS=Object.freeze({
  sourceAuthenticated:false, metaProviderVerified:false, s0ReadbackVerified:false,
  sendAuthorized:false, schedulingAuthorized:false, c09Authorized:false,
  commercialTransitionAuthorized:false, requiresS0Recheck:true, productionAuthorized:false
});
const result=(status,stage)=>Object.freeze({status,stage,...FLAGS});
const view=v=>Object.freeze({...v});
const attemptValid=a=>exact(a,['attemptRef','templateVersionRef','isFinalTemplate']) &&
  id(a.attemptRef)&&id(a.templateVersionRef)&&typeof a.isFinalTemplate==='boolean';
const eventValid=e=>exact(e,['eventRef','sequence','attemptRef','templateVersionRef','phase','correlationState','providerErrorCode']) &&
  id(e.eventRef)&&int(e.sequence)&&id(e.attemptRef)&&id(e.templateVersionRef)&&
  (e.phase==='GRAPH'?GRAPH.has(e.correlationState):
    e.phase==='S0_RECONCILED'&&RECONCILED.has(e.correlationState)) &&
  (e.providerErrorCode===null||(int(e.providerErrorCode)&&e.providerErrorCode<=999999));
const classify = s=>({
  API_ACCEPTED:'API_ACCEPTED_NOT_SENT',
  QUEUED:'QUEUED_NOT_SENT',
  UNKNOWN:'AWAITING_TRANSPORT_RECONCILIATION',
  PENDING_CORRELATION:'AWAITING_S0_CORRELATION',
  CORRELATED_SENT:'SENT_CANDIDATE_UNVERIFIED',
  CORRELATED_DELIVERED:'PROGRESS_WITHOUT_SENT_INFERENCE',
  CORRELATED_READ:'PROGRESS_WITHOUT_SENT_INFERENCE',
  CORRELATED_DEFINITIVE_FAILURE:'FAILURE_CANDIDATE_UNVERIFIED',
  UNCERTAIN:'UNCERTAIN_REQUIRES_REVIEW',
  CONFLICT:'CONFLICT_REQUIRES_REVIEW',
  QUARANTINED:'QUARANTINED_REQUIRES_REVIEW'
})[s];

/**
 * Structural compatibility with candidate WA-39 only.
 * A plausible event is NOT promoted into a verified event for
 * reviewF02Continuity; this returns descriptions, never an event with verified:true.
 */
export function previewWa39F02Projection(input) {
  try{
    if(!safe(input)||!exact(input,['schemaVersion','expected','snapshot'])||
       input.schemaVersion!==WA39_LAB_INPUT)return result('INVALID_INPUT','ENVELOPE');
    const exp=input.expected, snap=input.snapshot;
    if(!exact(exp,['storeRef','caseRef','flowRef','planRevision','minEvidenceRevision','attempts']) ||
       ![exp.storeRef,exp.caseRef,exp.flowRef].every(id)||
       !int(exp.planRevision)||!int(exp.minEvidenceRevision)||
       !arr(exp.attempts,32)||exp.attempts.length===0||!exp.attempts.every(attemptValid)||
       new Set(exp.attempts.map(a=>a.attemptRef)).size!==exp.attempts.length)
       return result('INVALID_INPUT','EXPECTED');
    if(!exact(snap,['storeRef','caseRef','flowRef','planRevision','evidenceRevision','events'])||
       ![snap.storeRef,snap.caseRef,snap.flowRef].every(id)||
       !int(snap.planRevision)||!int(snap.evidenceRevision)||!arr(snap.events,120))
       return result('INVALID_INPUT','SNAPSHOT');
    // Deny scope before exposing any event, timestamp or attempt metadata.
    if(snap.storeRef!==exp.storeRef||snap.caseRef!==exp.caseRef||snap.flowRef!==exp.flowRef)
       return result('DENIED','SCOPE');
    if(snap.planRevision!==exp.planRevision||snap.evidenceRevision<exp.minEvidenceRevision)
       return result('STALE','VERSION');
    const refs=new Map(exp.attempts.map(a=>[a.attemptRef,a]));
    const byId=new Map(), byOrder=new Map(), terminals=new Map();
    for(const e of snap.events){
      if(!eventValid(e))return result('INVALID_INPUT','EVENT');
      const t=refs.get(e.attemptRef);
      if(!t||t.templateVersionRef!==e.templateVersionRef)return result('DENIED','ATTEMPT_BINDING');
      const packed=JSON.stringify(e);
      if(byId.has(e.eventRef)){
        if(byId.get(e.eventRef)!==packed)return result('REVIEW_REQUIRED','DIVERGENT_REPLAY');
        continue; // Identical replay: one event, no new evidence.
      }
      if(byOrder.has(e.sequence))return result('REVIEW_REQUIRED','ORDER_COLLISION');
      byId.set(e.eventRef,packed);byOrder.set(e.sequence,e);
      if(e.correlationState==='CONFLICT'||e.correlationState==='QUARANTINED')
        return result('REVIEW_REQUIRED','META_CONFLICT');
      if(['CORRELATED_SENT','CORRELATED_DEFINITIVE_FAILURE'].includes(e.correlationState)){
        const prior=terminals.get(e.attemptRef);
        if(prior&&prior!==e.correlationState)return result('REVIEW_REQUIRED','CONTRADICTORY_TERMINALS');
        terminals.set(e.attemptRef,e.correlationState);
      }
    }
    const observations=[...byOrder.values()].sort((a,b)=>a.sequence-b.sequence).map(e=>view({
      eventRef:e.eventRef,attemptRef:e.attemptRef,sequence:e.sequence,
      observation:classify(e.correlationState),
      // Even final-template evidence is not permission to open C09.
      finalTemplateCandidate:refs.get(e.attemptRef).isFinalTemplate,
      technical131049:e.providerErrorCode===131049,
      verified:false
    }));
    Object.freeze(observations);
    return view({status:'LAB_UNVERIFIED_PROJECTION',schemaVersion:WA39_LAB_RESULT,
      evidenceRevision:snap.evidenceRevision,observations,
      uniqueEventCount:observations.length,...FLAGS});
  }catch{
    // Proxy traps, cyclic graphs, malformed prototypes and all other hostile data fail closed.
    return result('INVALID_INPUT','EXCEPTION');
  }
}
