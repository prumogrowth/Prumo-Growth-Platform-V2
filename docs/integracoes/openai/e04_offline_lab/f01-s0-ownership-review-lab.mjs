/**
 * OFF-13 — F01/S0 ownership and publication recheck compatibility (lab only).
 *
 * This pure function compares SYNTHETIC claims. It cannot authenticate a
 * principal, seal a snapshot, prove an S0 handoff, grant messaging authority,
 * send, allocate a consultant or write a customer record.
 *
 * Real S0 authoritative read, CAS/recheck and publication remain #11/#12.
 */
export const F01_OWNER_LAB_INPUT='prumo.openai.f01-owner-recheck/0.1-lab';
export const F01_OWNER_LAB_OUTPUT='prumo.openai.f01-owner-review/0.1-lab';
const ID=/^[A-Za-z0-9_.:-]{1,120}$/;
const VERSION_KEYS=['case','cycle','assignment','catalog','knowledge','policy','route','consent'];
const SCOPE_KEYS=['storeRef','caseRef','personRef'];
const SNAPSHOT_KEYS=[...SCOPE_KEYS,'ownerRoute','handoffDefinitive','humanized','optOut',
  'channelEligible','postRemittance','postSale','observedAtMs','versions','snapshotState'];
const REQUEST_KEYS=['requestRef',...SCOPE_KEYS,'startedAtMs','deadlineMs','expectedVersions','purpose'];
const id=x=>typeof x==='string'&&ID.test(x);
const nat=x=>Number.isSafeInteger(x)&&x>=0;
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&
  (Object.getPrototypeOf(x)===Object.prototype||Object.getPrototypeOf(x)===null);
const exact=(x,keys)=>object(x)&&Reflect.ownKeys(x).length===keys.length&&
  keys.every(k=>own(x,k))&&Reflect.ownKeys(x).every(k=>typeof k==='string'&&keys.includes(k));
function safe(x,depth=0,seen=new Set()){
  if(depth>8)return false;
  if(x===null||typeof x==='string'||typeof x==='boolean')return true;
  if(typeof x==='number')return Number.isFinite(x);
  if(!object(x)||seen.has(x))return false;
  seen.add(x);
  try{
    for(const key of Reflect.ownKeys(x)){
      if(typeof key!=='string'||['__proto__','prototype','constructor'].includes(key))return false;
      const d=Object.getOwnPropertyDescriptor(x,key);
      if(!d||!own(d,'value')||!safe(d.value,depth+1,seen))return false;
    }
    return true;
  }finally{seen.delete(x);}
}
const version=v=>exact(v,VERSION_KEYS)&&VERSION_KEYS.every(k=>nat(v[k]));
const sameVersion=(a,b)=>VERSION_KEYS.every(k=>a[k]===b[k]);
const sameScope=(a,b)=>SCOPE_KEYS.every(k=>a[k]===b[k]);
function requestValid(q){
  return exact(q,REQUEST_KEYS)&&[q.requestRef,...SCOPE_KEYS.map(k=>q[k]),q.purpose].every(id)&&
    nat(q.startedAtMs)&&nat(q.deadlineMs)&&q.deadlineMs>q.startedAtMs&&
    version(q.expectedVersions);
}
function snapshotValid(s){
  return exact(s,SNAPSHOT_KEYS)&&SCOPE_KEYS.every(k=>id(s[k]))&&
    ['AI','HUMAN','NONE'].includes(s.ownerRoute)&&
    ['handoffDefinitive','humanized','optOut','channelEligible','postRemittance','postSale'].every(
      k=>typeof s[k]==='boolean')&&
    nat(s.observedAtMs)&&version(s.versions)&&s.snapshotState==='LAB_UNVERIFIED';
}
const FLAGS=Object.freeze({
  principalAuthenticated:false, s0OwnerVerified:false, s0SnapshotAuthenticated:false,
  contentAuthorized:false, modelInvocationAuthorized:false,
  publishAuthorized:false, handoffAuthorized:false,
  consultantAssignmentAuthorized:false, f02RestartAuthorized:false,
  sent:false, commercialTransitionAuthorized:false, productionAuthorized:false,
  requiresS0TransactionalRecheck:true
});
const out=(status,stage)=>Object.freeze({schemaVersion:F01_OWNER_LAB_OUTPUT,status,stage,...FLAGS});
/**
 * Both snapshots are treated as untrusted laboratory claims, even if identical.
 * No result can authorize F01 invocation/publication: S0 must independently
 * authenticate, recheck atomically and decide whether any message can be sent.
 */
export function reviewF01S0Ownership(input){
  try{
    if(!safe(input)||!exact(input,['schemaVersion','request','before','after'])||
       input.schemaVersion!==F01_OWNER_LAB_INPUT)return out('INVALID_INPUT','ENVELOPE');
    const {request:q,before,after}=input;
    if(!requestValid(q)||!snapshotValid(before)||!snapshotValid(after))
      return out('INVALID_INPUT','SHAPE');
    // Cross-tenant/case/person denial precedes all timestamp/owner/version work.
    if(!sameScope(q,before)||!sameScope(q,after))return out('DENIED','SCOPE');
    // Ownership and human handoff always outrank recheck freshness.
    // A "new inbound" or an apparent owner transition back to AI cannot resume.
    if(before.handoffDefinitive||before.humanized||before.ownerRoute==='HUMAN'){
      if(!after.handoffDefinitive||!after.humanized||after.ownerRoute!=='HUMAN')
        return out('REVIEW_REQUIRED','HANDOFF_REGRESSION');
      return out('HUMAN_ONLY_REVIEW','DEFINITIVE_HANDOFF');
    }
    if(after.handoffDefinitive||after.humanized||after.ownerRoute==='HUMAN')
      return out('HUMAN_ONLY_REVIEW','DEFINITIVE_HANDOFF');
    if(before.ownerRoute!=='AI'||after.ownerRoute!=='AI')
      return out('DENIED','OWNER');
    // Any suppression or post-sale/remittance flag blocks model invocation.
    if(before.optOut||after.optOut)return out('DENIED','OPT_OUT');
    if(!before.channelEligible||!after.channelEligible)
      return out('DENIED','CHANNEL');
    if(before.postRemittance||after.postRemittance||before.postSale||after.postSale)
      return out('DENIED','POST_COMMERCIAL');
    if(before.observedAtMs<q.startedAtMs||after.observedAtMs<before.observedAtMs)
      return out('REVIEW_REQUIRED','CLOCK');
    if(after.observedAtMs>q.deadlineMs)return out('LATE_RECHECK','DEADLINE');
    if(!sameVersion(before.versions,q.expectedVersions)||
       !sameVersion(after.versions,q.expectedVersions))
      return out('STALE','VERSION');
    // This "happy path" explicitly grants nothing; it only tells a caller
    // that its own two synthetic snapshots have no detectable contradiction.
    return out('LAB_CONSISTENT_UNVERIFIED','S0_CONTRACT_PENDING');
  }catch{return out('INVALID_INPUT','EXCEPTION');}
}
