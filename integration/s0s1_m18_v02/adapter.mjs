/**
 * S0 -> Meta M18 v0.2 laboratory evidence adapter.
 *
 * The actual Meta M18 accepts ONLY a v0.1 S0 shape and fictitious claims.
 * This adapter NEVER repackages S0 v0.2 as v0.1 and NEVER issues a lease.
 * The S0 response contains NO authenticated attempt/intent/selection
 * correlation for the consumer; even a physically committed receipt is
 * unbound for Meta use. No Graph, HTTP, secrets or production.
 */
export const VERSION='prumo.s0.meta.m18-v02-evidence.lab.v0.1';
const STAGED=new Set(['LAB_RESERVATION_STAGED_BEFORE_COMMIT',
 'LAB_REPLAY_REQUIRES_READBACK','LAB_CANCEL_STAGED_BEFORE_COMMIT']);
const READBACK=new Set(['LAB_COMMITTED_RECEIPT_NO_DISPATCH',
 'LAB_COMMIT_UNKNOWN','LAB_STALE_NO_DISPATCH',
 'LAB_CANCELLED_NO_DISPATCH','LAB_EXPIRED_NO_DISPATCH',
 'LAB_INVALIDATED_NO_DISPATCH','DENIED','UNAVAILABLE']);
const BOOLEAN_FLAGS=[
 'lab_only','host_authenticated','consent_source_authenticated',
 'm09_host_authenticated','provider_approval_verified',
 'external_lease_issued','graph_dispatch_authorized','send_authorized',
 'automatic_retry_authorized','ack_allowed','production_authorized',
 'commercial_transition_authorized'];
const REQUIRED={
 lab_only:true,host_authenticated:false,consent_source_authenticated:false,
 m09_host_authenticated:false,provider_approval_verified:false,
 external_lease_issued:false,graph_dispatch_authorized:false,
 send_authorized:false,automatic_retry_authorized:false,ack_allowed:false,
 production_authorized:false,commercial_transition_authorized:false
};
const OPTIONAL=['commit_verified','quota_slot_recorded_lab_only',
 'external_retry_suppressed','original_attempt_ref'];
function dataRecord(obj){
 try{
  if(!obj||typeof obj!=='object'||Array.isArray(obj))return null;
  const proto=Object.getPrototypeOf(obj);
  if(proto!==Object.prototype&&proto!==null)return null;
  const props=Object.getOwnPropertyDescriptors(obj);
  if(Reflect.ownKeys(obj).some(k=>typeof k!=='string'||
    !Object.hasOwn(props[k],'value')))return null;
  return Object.fromEntries(Object.entries(props).map(([k,d])=>[k,d.value]));
 }catch{return null;}
}
const nonneg=(v)=>Number.isSafeInteger(v)&&v>=0;
const REF=/^[A-Za-z0-9_.:-]{1,128}$/;
const invalid=(reason)=>Object.freeze({
 contract_version:VERSION,decision:'DENIED',reason,
 durable_lab_observed:false,unbound_to_meta_attempt:true,
 s0_source_authenticated:false,wa18_v01_compatible:false,
 m18_dispatch_candidate:null,lease_usable:false,
 graph_dispatch_authorized:false,send_authorized:false,
 automatic_retry_authorized:false,ack_allowed:false,production_authorized:false
});
function valid(raw,category){
 const v=dataRecord(raw);if(!v)return null;
 const must=['contract_version','status','reason',...BOOLEAN_FLAGS];
 const allowed=new Set([...must,...OPTIONAL]);
 if(Object.keys(v).some(k=>!allowed.has(k))||
    must.some(k=>!Object.hasOwn(v,k))||
    v.contract_version!=='prumo.s0.pre-dispatch.readback/0.2-lab'||
    typeof v.reason!=='string'||!REF.test(v.reason)||
    BOOLEAN_FLAGS.some(k=>v[k]!==REQUIRED[k])||
    (category==='STAGED'?!STAGED.has(v.status):!READBACK.has(v.status))
 )return null;
 if(Object.hasOwn(v,'commit_verified')&&typeof v.commit_verified!=='boolean')return null;
 if(Object.hasOwn(v,'quota_slot_recorded_lab_only')&&
    (!nonneg(v.quota_slot_recorded_lab_only)||v.quota_slot_recorded_lab_only===0))return null;
 if(Object.hasOwn(v,'external_retry_suppressed')&&v.external_retry_suppressed!==true)return null;
 if(Object.hasOwn(v,'original_attempt_ref')&&
    (typeof v.original_attempt_ref!=='string'||!REF.test(v.original_attempt_ref)))return null;
 if(category==='STAGED'){
  if(v.commit_verified!==false)return null;
  if(v.status==='LAB_RESERVATION_STAGED_BEFORE_COMMIT'){
   if(v.reason!=='READBACK_REQUIRED'||!nonneg(v.quota_slot_recorded_lab_only)||
      v.quota_slot_recorded_lab_only===0)return null;
  }
  if(v.status==='LAB_REPLAY_REQUIRES_READBACK'&&
    (v.reason!=='NO_COMMIT_ASSERTION'||!v.original_attempt_ref))return null;
  if(v.status==='LAB_CANCEL_STAGED_BEFORE_COMMIT'&&v.reason!=='READBACK_REQUIRED')return null;
 }else{
  const committed=new Set(['LAB_COMMITTED_RECEIPT_NO_DISPATCH',
    'LAB_STALE_NO_DISPATCH','LAB_CANCELLED_NO_DISPATCH',
    'LAB_EXPIRED_NO_DISPATCH','LAB_INVALIDATED_NO_DISPATCH']);
  if(committed.has(v.status) && v.commit_verified!==true)return null;
  if(v.status==='LAB_COMMITTED_RECEIPT_NO_DISPATCH' &&
    (v.reason!=='DURABLE_PG17_LAB_ONLY_NOT_REDEEMABLE'||
     !nonneg(v.quota_slot_recorded_lab_only)||
     v.quota_slot_recorded_lab_only===0))return null;
  if(v.status==='LAB_COMMIT_UNKNOWN'&&
    (v.commit_verified!==false||v.reason!=='NO_DURABLE_RECEIPT'||
     v.external_retry_suppressed!==true))return null;
  if(['DENIED','UNAVAILABLE'].includes(v.status)&&v.commit_verified===true)return null;
 }
 return v;
}
const hold=(reason,durable)=>Object.freeze({
 contract_version:VERSION,decision:'LAB_HOLD_NO_DISPATCH',reason,
 durable_lab_observed:durable,unbound_to_meta_attempt:true,
 s0_source_authenticated:false,wa18_v01_compatible:false,
 m18_dispatch_candidate:null,lease_usable:false,
 graph_dispatch_authorized:false,send_authorized:false,
 automatic_retry_authorized:false,ack_allowed:false,production_authorized:false
});
/** Accepts actual v0.2 outputs, never converts to M18's old S0 v0.1. */
export function inspectS0V02ForM18Offline(rawStage,rawReadback){
 const stage=valid(rawStage,'STAGED'),readback=valid(rawReadback,'READBACK');
 if(!stage||!readback)return invalid('INVALID_V02_LAB_EVIDENCE');
 if(readback.status==='LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  return hold('COMMITTED_PG17_BUT_NO_AUTHENTICATED_ATTEMPT_BINDING',true);
 if(readback.status==='LAB_COMMIT_UNKNOWN')
  return hold('COMMIT_UNKNOWN_NO_EXTERNAL_RETRY',false);
 if(readback.status==='LAB_CANCELLED_NO_DISPATCH')
  return hold('CANCELLED_NO_DISPATCH',true);
 if(readback.status==='LAB_EXPIRED_NO_DISPATCH')
  return hold('EXPIRED_NO_DISPATCH',true);
 if(readback.status==='LAB_INVALIDATED_NO_DISPATCH')
  return hold('ORIGINAL_RESERVATION_INVALIDATED',true);
 if(readback.status==='LAB_STALE_NO_DISPATCH')
  return hold('S0_POLICY_OR_REGISTRY_STALE',true);
 return hold('SOURCE_DENIED_OR_UNAVAILABLE',false);
}
