/**
 * OFF-14 — F01 commercial source boundary, synthetic review only.
 *
 * This module NEVER authenticates S0, proves semantic support, approves an
 * offer, publishes a message, loads source text or contacts a provider.
 * All source/consent/approval fields are untrusted TEST FIXTURE assertions.
 * The real S0 per-store knowledge controller and transactional publish
 * recheck are pending in issues #12 and #11.
 */
export const F01_SOURCE_LAB_INPUT='prumo.openai.f01-source-review/0.1-lab';
export const F01_SOURCE_LAB_RESULT='prumo.openai.f01-source-review-result/0.1-lab';
const VKEYS=['catalog','knowledge','policy','consent','grant'];
const REF=/^[A-Za-z0-9_.:-]{1,120}$/;
const CODE=/^[A-Za-z][A-Za-z0-9_.:-]{0,79}$/;
const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&
  (Object.getPrototypeOf(x)===Object.prototype||Object.getPrototypeOf(x)===null);
const exact=(x,keys)=>object(x)&&Reflect.ownKeys(x).length===keys.length&&
  keys.every(k=>has(x,k))&&Reflect.ownKeys(x).every(k=>typeof k==='string'&&keys.includes(k));
const ref=x=>typeof x==='string'&&REF.test(x);
const nat=x=>Number.isSafeInteger(x)&&x>=0;
const list=(x,max)=>Array.isArray(x)&&x.length<=max&&
  Object.keys(x).length===x.length&&
  Reflect.ownKeys(x).every(k=>k==='length'||/^(0|[1-9]\d*)$/.test(String(k)));
function safe(x,level=0,seen=new Set()){
  if(level>9)return false;
  if(x===null||typeof x==='string'||typeof x==='boolean')return true;
  if(typeof x==='number')return Number.isFinite(x);
  if(typeof x!=='object'||seen.has(x)||(!object(x)&&!Array.isArray(x)))return false;
  if(Array.isArray(x)&&!list(x,64))return false;
  seen.add(x);
  try{
    for(const k of Reflect.ownKeys(x)){
      if(typeof k!=='string'||['__proto__','constructor','prototype'].includes(k))return false;
      const d=Object.getOwnPropertyDescriptor(x,k);
      if(!d||!has(d,'value')||!safe(d.value,level+1,seen))return false;
    }
    return true;
  }finally{seen.delete(x);}
}
const version=x=>exact(x,VKEYS)&&VKEYS.every(k=>nat(x[k]));
const versionsMatch=(a,b)=>VKEYS.every(k=>a[k]===b[k]);
const FLAGS=Object.freeze({
  s0SourceAuthenticated:false, s0CatalogVerified:false,
  contentGrantVerified:false, provenanceAuthenticated:false,
  semanticSupportVerified:false, commercialOfferAuthorized:false,
  modelContentAuthorized:false, modelInvocationAuthorized:false,
  publishAuthorized:false, sendAuthorized:false,
  productionAuthorized:false, requiresS0TransactionalRecheck:true
});
const result=(status,stage)=>Object.freeze({
  schemaVersion:F01_SOURCE_LAB_RESULT,status,stage,...FLAGS
});
function validClaim(x){
  return exact(x,['sourceRef','claimCode','usage'])&&ref(x.sourceRef)&&
    typeof x.claimCode==='string'&&CODE.test(x.claimCode)&&
    ['commercial','interpretive'].includes(x.usage);
}
function validRequest(x){
  return exact(x,['requestRef','storeRef','caseRef','personRef','purposeRef',
    'startedAtMs','deadlineMs','versions','claims'])&&
    [x.requestRef,x.storeRef,x.caseRef,x.personRef,x.purposeRef].every(ref)&&
    nat(x.startedAtMs)&&nat(x.deadlineMs)&&x.deadlineMs>x.startedAtMs&&
    version(x.versions)&&list(x.claims,32)&&x.claims.length>0&&
    x.claims.every(validClaim)&&
    new Set(x.claims.map(c=>c.sourceRef+'#'+c.claimCode+'#'+c.usage)).size===x.claims.length;
}
function validSource(x){
  return exact(x,['sourceRef','storeRef','kind','approvalState','sourceVersion',
    'validUntilMs','correctedByRef','claimCodes'])&&
    ref(x.sourceRef)&&ref(x.storeRef)&&
    ['current','historical'].includes(x.kind)&&
    ['APPROVED_ACTIVE','PAUSED','REVOKED','EXPIRED','DRAFT'].includes(x.approvalState)&&
    nat(x.sourceVersion)&&
    (x.validUntilMs===null||nat(x.validUntilMs))&&
    (x.correctedByRef===null||ref(x.correctedByRef))&&
    list(x.claimCodes,30)&&
    x.claimCodes.every(c=>typeof c==='string'&&CODE.test(c))&&
    new Set(x.claimCodes).size===x.claimCodes.length;
}
function validSnapshot(x){
  return exact(x,['storeRef','caseRef','personRef','purposeRef','observedAtMs',
    'versions','contentPolicy','sources','snapshotState'])&&
    [x.storeRef,x.caseRef,x.personRef,x.purposeRef].every(ref)&&
    nat(x.observedAtMs)&&version(x.versions)&&
    ['LAB_ALLOWED','LAB_DENIED','LAB_UNKNOWN'].includes(x.contentPolicy)&&
    x.snapshotState==='LAB_UNVERIFIED'&&list(x.sources,48)&&
    x.sources.every(validSource)&&
    new Set(x.sources.map(s=>s.sourceRef)).size===x.sources.length;
}
function sameScope(req,s){
  return ['storeRef','caseRef','personRef','purposeRef'].every(k=>req[k]===s[k]);
}
function canonicalSources(xs){
  return JSON.stringify(xs.map(s=>({
    ...s,claimCodes:[...s.claimCodes].sort()
  })).sort((a,b)=>a.sourceRef<b.sourceRef?-1:a.sourceRef>b.sourceRef?1:0));
}
/**
 * Synthetic metadata-only two-view compatibility. A LAB_ELIGIBLE_UNVERIFIED
 * output means NOTHING about real S0 provenance, permission, offer semantics,
 * knowledge coverage, confidentiality, or message publication.
 */
export function reviewF01CommercialSources(input){
  try{
    if(!safe(input)||!exact(input,['schemaVersion','request','before','after'])||
       input.schemaVersion!==F01_SOURCE_LAB_INPUT)
      return result('INVALID_INPUT','ENVELOPE');
    const {request:req,before,after}=input;
    if(!validRequest(req)||!validSnapshot(before)||!validSnapshot(after))
      return result('INVALID_INPUT','SHAPE');
    // Deny cross-store/case/person and any cross-store selected source first.
    if(!sameScope(req,before)||!sameScope(req,after)||
       [...before.sources,...after.sources].some(s=>s.storeRef!==req.storeRef))
      return result('DENIED','SCOPE');
    if(before.contentPolicy==='LAB_DENIED'||after.contentPolicy==='LAB_DENIED')
      return result('DENIED','CONTENT_POLICY');
    if(before.contentPolicy!=='LAB_ALLOWED'||after.contentPolicy!=='LAB_ALLOWED')
      return result('REVIEW_REQUIRED','CONTENT_POLICY');
    if(before.observedAtMs<req.startedAtMs||
       after.observedAtMs<before.observedAtMs)
      return result('REVIEW_REQUIRED','CLOCK');
    if(after.observedAtMs>req.deadlineMs)
      return result('LATE_RECHECK','DEADLINE');
    if(!versionsMatch(req.versions,before.versions)||
       !versionsMatch(req.versions,after.versions))
      return result('STALE','VERSION');
    if(canonicalSources(before.sources)!==canonicalSources(after.sources))
      return result('REVIEW_REQUIRED','SOURCES_CHANGED');
    const sources=new Map(after.sources.map(s=>[s.sourceRef,s]));
    for(const claim of req.claims){
      const s=sources.get(claim.sourceRef);
      if(!s)return result('SOURCE_INVALID','NOT_IN_SNAPSHOT');
      if(s.correctedByRef!==null)return result('SOURCE_INVALID','CORRECTED');
      if(!s.claimCodes.includes(claim.claimCode))
        return result('SOURCE_INVALID','CLAIM_UNSUPPORTED');
      if(claim.usage==='commercial'){
        if(s.kind!=='current')return result('SOURCE_INVALID','HISTORICAL_OFFER');
        if(s.approvalState!=='APPROVED_ACTIVE')
          return result('SOURCE_INVALID','NOT_ACTIVE');
        if(s.validUntilMs===null||
           s.validUntilMs<=after.observedAtMs)
          return result('SOURCE_INVALID','EXPIRED_OR_UNBOUNDED');
      }else{
        // Historical evidence can be used only interpretively; a revoked,
        // paused or draft item must never be silently promoted to evidence.
        if(!['APPROVED_ACTIVE','EXPIRED'].includes(s.approvalState))
          return result('SOURCE_INVALID','INTERPRETIVE_INELIGIBLE');
      }
    }
    // Even an apparently stable pair of fixtures does not authorize model
    // content, the commercial claim, publication, or customer messaging.
    return result('LAB_ELIGIBLE_UNVERIFIED','S0_CONTRACT_PENDING');
  }catch{return result('INVALID_INPUT','EXCEPTION');}
}
