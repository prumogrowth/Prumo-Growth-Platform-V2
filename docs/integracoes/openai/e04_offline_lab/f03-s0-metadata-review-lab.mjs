/**
 * OFF-12. Synthetic structural review of the existing S0 F03 local history
 * metadata and CFI receipt states. NOT an S0-authenticated API, a content
 * manifest, a complete cross-case snapshot, or an authority to call F03.
 * Pure: no network, model, disk, SQL, clock, secrets, writes, or effects.
 */
export const F03_S0_REVIEW_INPUT='prumo.openai.f03-s0-review/0.1-lab';
export const F03_S0_REVIEW_OUTPUT='prumo.openai.f03-s0-review-result/0.1-lab';
const ID=/^[A-Za-z0-9_.:-]{1,120}$/;
const DIGEST=/^[0-9a-f]{64}$/;
const PRE=['VERIFIED_CONTRACT_PENDING','INPUT_REJECTED','DENIED','STALE','UNAVAILABLE'];
const HISTORY=['REVIEW_ONLY_NOT_FROZEN','DENIED','INPUT_REJECTED','STALE','UNAVAILABLE','HISTORY_INCOMPLETE'];
const APPLICATION=['APPLIED_SYNTHETIC_ONLY','ALREADY_APPLIED_AUDIT_ONLY','DENIED','BLOCKED_S1',
  'STALE_REVIEW_REQUIRED','CONFLICT_REVIEW_REQUIRED','FIELD_REVIEW_REQUIRED','CATALOG_REVIEW_REQUIRED','UNAVAILABLE'];
const has=(x,k)=>Object.prototype.hasOwnProperty.call(x,k);
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&
  (Object.getPrototypeOf(x)===Object.prototype||Object.getPrototypeOf(x)===null);
const exact=(x,keys)=>obj(x)&&Reflect.ownKeys(x).length===keys.length&&
  keys.every(k=>has(x,k))&&Reflect.ownKeys(x).every(k=>typeof k==='string'&&keys.includes(k));
const id=x=>typeof x==='string'&&ID.test(x);
const digest=x=>typeof x==='string'&&DIGEST.test(x);
const nat=x=>Number.isSafeInteger(x)&&x>=0;
function safe(x,depth=0,seen=new Set()){
  if(depth>9)return false;
  if(x===null||typeof x==='string'||typeof x==='boolean')return true;
  if(typeof x==='number')return Number.isFinite(x);
  if(typeof x!=='object'||seen.has(x)||(!obj(x)&&!Array.isArray(x)))return false;
  if(Array.isArray(x)&&(x.length>80||Object.keys(x).length!==x.length||
    Reflect.ownKeys(x).some(k=>k!=='length'&&!/^(0|[1-9]\d*)$/.test(String(k)))))return false;
  seen.add(x);
  try{
    for(const k of Reflect.ownKeys(x)){
      if(typeof k!=='string'||['__proto__','constructor','prototype'].includes(k))return false;
      const desc=Object.getOwnPropertyDescriptor(x,k);
      if(!desc||!has(desc,'value')||!safe(desc.value,depth+1,seen))return false;
    }
    return true;
  }finally{seen.delete(x);}
}
const FAIL_FLAGS=Object.freeze({
  s0SourceAuthenticated:false,historyComplete:false,mediaCoverageAttested:false,
  crossCaseIdentityAttested:false,modelContentAuthorized:false,modelInvocationAuthorized:false,
  fieldApplicationAuthorized:false,commercialTransitionAuthorized:false,sendAuthorized:false,
  productionAuthorized:false,requiresCanonicalS0Contract:true
});
function outcome(status,stage){
  return Object.freeze({status,stage,schemaVersion:F03_S0_REVIEW_OUTPUT,...FAIL_FLAGS});
}
function binding(x){
  return exact(x,['storeRef','caseRef','closureRef','cycleVersion','snapshotSha256'])&&
    [x.storeRef,x.caseRef,x.closureRef].every(id)&&nat(x.cycleVersion)&&
    x.cycleVersion>0&&digest(x.snapshotSha256);
}
const same=(a,b)=>a.storeRef===b.storeRef&&a.caseRef===b.caseRef&&
  a.closureRef===b.closureRef;
function gateValid(g){
  return exact(g,['state','storeRef','caseRef','closureRef','cycleVersion','snapshotSha256'])&&
    PRE.includes(g.state)&&binding({
      storeRef:g.storeRef,caseRef:g.caseRef,closureRef:g.closureRef,
      cycleVersion:g.cycleVersion,snapshotSha256:g.snapshotSha256
    });
}
function inspectValid(i){
  return exact(i,['state','count','caseCount','metadataSha256'])&&HISTORY.includes(i.state)&&
    nat(i.count)&&nat(i.caseCount)&&i.count<=10000&&i.caseCount<=i.count&&
    (i.metadataSha256===null||digest(i.metadataSha256))&&
    (i.state==='REVIEW_ONLY_NOT_FROZEN'?
      i.count>0&&i.caseCount>0&&digest(i.metadataSha256):
      i.count===0&&i.caseCount===0&&i.metadataSha256===null);
}
/**
 * A "verified contract pending" S0 CFI-01 recheck and "review only not frozen"
 * metadata are still insufficient to provide F03 content. This function never
 * outputs a grant, complete-history flag, a receipt, a digest, or client metadata.
 */
export function reviewF03S0Metadata(input){
  try{
    if(!safe(input)||!exact(input,['schemaVersion','request','before','inspection','after','application'])||
       input.schemaVersion!==F03_S0_REVIEW_INPUT)return outcome('INVALID_INPUT','ENVELOPE');
    const {request,before,inspection,after,application}=input;
    if(!binding(request)||!gateValid(before)||!gateValid(after)||!inspectValid(inspection)||
       (application!==null&&!APPLICATION.includes(application)))return outcome('INVALID_INPUT','SHAPE');
    // Cross-store/case/closure denial outranks stale and all result metadata.
    if(!same(request,before)||!same(request,after))return outcome('DENIED','SCOPE');
    if(before.cycleVersion!==request.cycleVersion||after.cycleVersion!==request.cycleVersion||
       before.snapshotSha256!==request.snapshotSha256||
       after.snapshotSha256!==request.snapshotSha256)return outcome('STALE','BINDING');
    if(before.state!=='VERIFIED_CONTRACT_PENDING'||after.state!=='VERIFIED_CONTRACT_PENDING'){
      if(before.state==='STALE'||after.state==='STALE')return outcome('STALE','RECHECK');
      if(before.state==='UNAVAILABLE'||after.state==='UNAVAILABLE')return outcome('UNAVAILABLE','RECHECK');
      return outcome('DENIED','RECHECK');
    }
    if(inspection.state==='STALE')return outcome('STALE','HISTORY');
    if(inspection.state==='UNAVAILABLE')return outcome('UNAVAILABLE','HISTORY');
    if(inspection.state==='DENIED'||inspection.state==='INPUT_REJECTED')
      return outcome('DENIED','HISTORY');
    if(inspection.state==='HISTORY_INCOMPLETE')
      return outcome('REVIEW_REQUIRED','INCOMPLETE_HISTORY');
    // All currently successful S0 outcomes are explicitly non-operational:
    // including an APPLIED_SYNTHETIC_ONLY state from a separate S0 laboratory.
    if(application!==null&&['APPLIED_SYNTHETIC_ONLY','ALREADY_APPLIED_AUDIT_ONLY'].includes(application))
      return outcome('LAB_REVIEW_ONLY_SYNTHETIC_APPLICATION','NO_F03_AUTHORITY');
    if(application!==null)return outcome('REVIEW_REQUIRED','APPLICATION');
    return outcome('LAB_METADATA_REVIEW_ONLY','NOT_FROZEN');
  }catch{return outcome('INVALID_INPUT','EXCEPTION');}
}
