/**
 * OFF-22: F02 acceptance screen for current Meta M19 A/B and M20 snapshots.
 * Pure, offline and strictly NON-AUTHORITATIVE. The three snapshot families
 * DO NOT carry a common authenticated S0 attempt/occurrence identity and
 * MUST NOT be joined into a sent, definitive failure, WDC13 or C09 proof.
 */
import {WA39_LAB_RESULT} from './f02-wa39-consumer-lab.mjs';
export const OFF22_INPUT='prumo.openai.f02-m19-m20-compatibility/0.1-lab';
export const OFF22_RESULT='prumo.openai.f02-m19-m20-compatibility-result/0.1-lab';
const bKeys=['sourceAuthenticated','metaProviderVerified','s0ReadbackVerified',
  'sendAuthorized','schedulingAuthorized','c09Authorized',
  'commercialTransitionAuthorized','requiresS0Recheck','productionAuthorized'];
const gKeys=['contract_version','snapshot_sha256','decision','progress','unique_occurrences',
  'exact_replays','conflict_occurrences','sent_observed_lab','delivered_observed_lab',
  'read_observed_lab','failed_observed_lab','api_accepted_lab','source_authenticated',
  'attempt_correlation_verified','sent_verified','delivered_verified','read_verified',
  'definitive_failure_verified','retry_external','send_authorized',
  'production_authorized','ack_allowed','case_transition_authorized',
  'wdc13_increment_authorized','c09_window_authorized'];
const sKeys=['contract_version','snapshot_sha256','observation_count','duplicate_count',
  'saw_explicit_sent','saw_delivered','saw_read','saw_failed','status',
  'quarantine_required','requires_s0_recheck','s0_source_authenticated',
  'callback_hmac_verified','attempt_correlation_verified','durable_persistence_verified',
  'sent_verified','delivered_verified','read_verified','definitive_failure_verified',
  'definitive_failure_count_increment','case_transition_authorized',
  'commercial_transition_authorized','retry_external','ack_allowed',
  'production_authorized'];
const wKeys=['contract_version','snapshot_sha256','decision','attempts_examined',
  'consecutive_failure_claims_at_tail','claimed_sent_reset_count',
  'unknown_or_conflict_seen','two_consecutive_failure_claims_at_tail',
  'requires_s0_recheck','requires_authenticated_evidence','s0_source_authenticated',
  'attempt_correlation_verified','definitive_classification_verified',
  'sent_verified','failure_verified','wdc13_increment_authorized',
  'wdc13_transition_authorized','c09_window_authorized',
  'f02_replan_authorized','automatic_retry_authorized',
  'send_authorized','production_authorized'];
const own=(v,k)=>Object.prototype.hasOwnProperty.call(v,k);
const plain=v=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&
 (Object.getPrototypeOf(v)===Object.prototype||Object.getPrototypeOf(v)===null);
function exact(v,keys){
 if(!plain(v)||Reflect.ownKeys(v).length!==keys.length)return false;
 return Reflect.ownKeys(v).every(k=>typeof k==='string'&&keys.includes(k)&&
   own(Object.getOwnPropertyDescriptor(v,k),'value'))&&keys.every(k=>own(v,k));
}
function safe(v,depth=0,seen=new Set()){
 if(depth>10)return false;
 if(v===null||typeof v==='string'||typeof v==='boolean')return true;
 if(typeof v==='number')return Number.isFinite(v);
 if(typeof v!=='object'||seen.has(v)||(!plain(v)&&!Array.isArray(v)))return false;
 if(Array.isArray(v)&&(v.length>160||Object.keys(v).length!==v.length))return false;
 seen.add(v);
 try{
  for(const k of Reflect.ownKeys(v)){
   if(typeof k!=='string'||['__proto__','prototype','constructor'].includes(k))return false;
   if(Array.isArray(v)&&k!=='length'&&(!/^(0|[1-9]\d*)$/.test(k)||+k>=v.length))return false;
   const d=Object.getOwnPropertyDescriptor(v,k);
   if(!d||!own(d,'value')||!safe(d.value,depth+1,seen))return false;
  }
  return true;
 }finally{seen.delete(v);}
}
const bool=v=>typeof v==='boolean',num=v=>Number.isSafeInteger(v)&&v>=0;
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const allFalse=(v,keys)=>keys.every(k=>v[k]===false);
const gFalse=['source_authenticated','attempt_correlation_verified','sent_verified',
  'delivered_verified','read_verified','definitive_failure_verified','retry_external',
  'send_authorized','production_authorized','ack_allowed','case_transition_authorized',
  'wdc13_increment_authorized','c09_window_authorized'];
const sFalse=['s0_source_authenticated','callback_hmac_verified','attempt_correlation_verified',
  'durable_persistence_verified','sent_verified','delivered_verified','read_verified',
  'definitive_failure_verified','definitive_failure_count_increment',
  'case_transition_authorized','commercial_transition_authorized','retry_external',
  'ack_allowed','production_authorized'];
const wFalse=['s0_source_authenticated','attempt_correlation_verified',
  'definitive_classification_verified','sent_verified','failure_verified',
  'wdc13_increment_authorized','wdc13_transition_authorized','c09_window_authorized',
  'f02_replan_authorized','automatic_retry_authorized',
  'send_authorized','production_authorized'];
const FLAGS=Object.freeze({
 s0SourceAuthenticated:false,metaProviderAuthenticated:false,
 callbackHmacVerified:false,attemptCorrelationVerified:false,
 sentVerified:false,definitiveFailureVerified:false,
 wdc13TransitionAuthorized:false,c09WindowAuthorized:false,
 f02ReplanAuthorized:false,automaticRetryAuthorized:false,
 sendAuthorized:false,schedulingAuthorized:false,
 commercialTransitionAuthorized:false,productionAuthorized:false,
 crossSourceIdentityAttested:false,rawStatusExposed:false,
 requiresCanonicalS0Wa39Contract:true,requiresS0TransactionalRecheck:true
});
const result=(status,reason)=>Object.freeze({
 schemaVersion:OFF22_RESULT,status,reason,...FLAGS
});
function wa39(p){
 return exact(p,['status','schemaVersion','evidenceRevision','observations',
  'uniqueEventCount',...bKeys])&&p.status==='LAB_UNVERIFIED_PROJECTION'&&
  p.schemaVersion===WA39_LAB_RESULT&&num(p.evidenceRevision)&&num(p.uniqueEventCount)&&
  Array.isArray(p.observations)&&p.observations.length===p.uniqueEventCount&&
  p.observations.length<=120&&allFalse(p,bKeys.filter(k=>k!=='requiresS0Recheck'))&&
  p.requiresS0Recheck===true&&
  p.observations.every(o=>exact(o,['eventRef','attemptRef','sequence','observation',
    'finalTemplateCandidate','technical131049','verified'])&&
    typeof o.eventRef==='string'&&typeof o.attemptRef==='string'&&
    num(o.sequence)&&bool(o.finalTemplateCandidate)&&bool(o.technical131049)&&
    o.verified===false&&[
      'API_ACCEPTED_NOT_SENT','QUEUED_NOT_SENT','AWAITING_TRANSPORT_RECONCILIATION',
      'AWAITING_S0_CORRELATION','SENT_CANDIDATE_UNVERIFIED',
      'PROGRESS_WITHOUT_SENT_INFERENCE','FAILURE_CANDIDATE_UNVERIFIED',
      'UNCERTAIN_REQUIRES_REVIEW','CONFLICT_REQUIRES_REVIEW',
      'QUARANTINED_REQUIRES_REVIEW'].includes(o.observation));
}
function graph(g){
 return exact(g,gKeys)&&g.contract_version==='wa19-graph-status-snapshot.lab.v0.2'&&
 hash(g.snapshot_sha256)&&num(g.unique_occurrences)&&num(g.exact_replays)&&
 num(g.conflict_occurrences)&&
 ['LAB_NO_CALLBACK_UNVERIFIED','LAB_OBSERVATION_UNVERIFIED',
  'LAB_LATE_HISTORICAL_UNVERIFIED','LAB_QUARANTINED_CONFLICT'].includes(g.decision)&&
 ['NONE','SENT_OBSERVED','DELIVERED_OBSERVED','READ_OBSERVED',
  'FAILED_OBSERVED','CONFLICT'].includes(g.progress)&&
 ['sent_observed_lab','delivered_observed_lab','read_observed_lab',
  'failed_observed_lab','api_accepted_lab'].every(k=>bool(g[k]))&&allFalse(g,gFalse);
}
function binding(s){
 return exact(s,sKeys)&&s.contract_version==='wa19-status-snapshot.lab.v0.2'&&
 hash(s.snapshot_sha256)&&num(s.observation_count)&&num(s.duplicate_count)&&
 ['LAB_NO_OBSERVATIONS','LAB_SENT_OBSERVED_UNVERIFIED',
  'LAB_DELIVERED_OBSERVED_UNVERIFIED','LAB_READ_OBSERVED_UNVERIFIED',
  'LAB_FAILURE_OBSERVED_UNVERIFIED','LAB_CONFLICT_QUARANTINED',
  'LAB_INVALIDATED_OBSERVATION_HOLD'].includes(s.status)&&
 ['saw_explicit_sent','saw_delivered','saw_read','saw_failed',
  'quarantine_required'].every(k=>bool(s[k]))&&
 s.requires_s0_recheck===true&&allFalse(s,sFalse);
}
function cadence(w){
 return exact(w,wKeys)&&w.contract_version==='wa20-wdc13-snapshot.lab.v0.2'&&
 hash(w.snapshot_sha256)&&
 ['LAB_NO_ATTEMPTS_UNVERIFIED','LAB_BELOW_TWO_UNVERIFIED',
  'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED',
  'LAB_HOLD_UNCERTAIN_OR_CONFLICT','LAB_INACTIVE_HOLD'].includes(w.decision)&&
 ['attempts_examined','consecutive_failure_claims_at_tail',
  'claimed_sent_reset_count'].every(k=>num(w[k]))&&
 w.attempts_examined<=40&&w.consecutive_failure_claims_at_tail<=w.attempts_examined&&
 bool(w.unknown_or_conflict_seen)&&bool(w.two_consecutive_failure_claims_at_tail)&&
 w.requires_s0_recheck===true&&w.requires_authenticated_evidence===true&&
 allFalse(w,wFalse);
}
/**
 * Recognizes the exact current LAB shapes but deliberately DOES NOT correlate
 * M19 and M20 snapshots to the WA39 attempt list: those responses lack an
 * authenticated common ID, timestamp/cursor and S0 receipt. Only S0 can
 * publish a canonical projection after confirming actual Meta/S0 evidence.
 */
export function reviewF02MetaM19M20Compatibility(input){
 try{
  if(!safe(input)||!exact(input,['schemaVersion','wa39Preview',
    'm19GraphSnapshot','m19S0BindingSnapshot','m20CadenceSnapshot'])||
    input.schemaVersion!==OFF22_INPUT)return result('INVALID_INPUT','ENVELOPE');
  if(!wa39(input.wa39Preview))return result('DENIED','WA39_PROJECTION');
  if(!graph(input.m19GraphSnapshot))return result('DENIED','M19_GRAPH_CONTRACT');
  if(!binding(input.m19S0BindingSnapshot))return result('DENIED','M19_BINDING_CONTRACT');
  if(!cadence(input.m20CadenceSnapshot))return result('DENIED','M20_CADENCE_CONTRACT');
  const p=input.wa39Preview,g=input.m19GraphSnapshot,s=input.m19S0BindingSnapshot,
        w=input.m20CadenceSnapshot;
  const conflict=g.decision==='LAB_QUARANTINED_CONFLICT'||g.conflict_occurrences>0||
    s.quarantine_required||s.status==='LAB_CONFLICT_QUARANTINED'||
    s.status==='LAB_INVALIDATED_OBSERVATION_HOLD'||
    w.decision==='LAB_HOLD_UNCERTAIN_OR_CONFLICT'||
    p.observations.some(o=>['UNCERTAIN_REQUIRES_REVIEW','CONFLICT_REQUIRES_REVIEW',
      'QUARANTINED_REQUIRES_REVIEW'].includes(o.observation));
  if(conflict)return result('LAB_HOLD_UNVERIFIED','CONFLICT_OR_UNCERTAIN');
  if(w.decision==='LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED')
    return result('LAB_WDC13_CANDIDATE_HOLD','S0_EXCLUSIVE_COUNTER');
  if(p.observations.some(o=>o.finalTemplateCandidate)&&
     (s.saw_explicit_sent||g.sent_observed_lab))
    return result('LAB_FINAL_TEMPLATE_HOLD','NO_AUTHENTICATED_C09_SENT');
  return result('LAB_UNCORRELATED_HOLD','NO_SHARED_AUTHENTICATED_ATTEMPT_ID');
 }catch{return result('INVALID_INPUT','EXCEPTION');}
}
