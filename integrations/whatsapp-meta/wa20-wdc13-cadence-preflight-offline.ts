/**
 * M20 WDC-13 / WA-39. An isolated, PURE LAB analysis of alleged S0 cadence
 * observations. No Meta/S0 authentication, database write, failure counter,
 * commercial transition, C09 window, scheduling, API, retries or dispatch.
 *
 * A claim named LAB_DEFINITIVE_FAILURE_CLAIM is NEVER proof of definitive
 * failure. Only S0 may correlate and enact the WDC-13 rule.
 */
import {createHash} from 'node:crypto';

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const REF=/^[A-Za-z0-9_.:-]{1,128}$/;
const PHONE=/^[0-9]{5,25}$/,HEX=/^[a-f0-9]{64}$/;
const pos=(v:unknown):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>0;
const nonneg=(v:unknown):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0;
const id=(v:unknown):v is string=>typeof v==='string'&&REF.test(v);
const K_CONTEXT=['contract_version','concessionaria_id','app_ref','waba_ref',
 'phone_number_id','case_ref','flow_ref','plan_ref','cadence_ref',
 'plan_revision','case_revision','evidence_revision','observed_at_ms',
 'now_ms','max_age_ms','cadence_state','s0_source_authenticated',
 'attempt_correlation_verified','definitive_classification_verified',
 'durable_evidence_verified'] as const;
const K_ATTEMPT=['contract_version','concessionaria_id','app_ref','waba_ref',
 'phone_number_id','case_ref','flow_ref','plan_ref','cadence_ref',
 'attempt_ref','intent_ref','sequence_no',
 'template_ref','template_version_ref','is_final_template','event_ref',
 'event_sha256','provider_error_code','status_claim','observed_at_ms'] as const;
const K_SNAPSHOT=['contract_version','snapshot_sha256','decision',
 'attempts_examined','consecutive_failure_claims_at_tail',
 'claimed_sent_reset_count','unknown_or_conflict_seen',
 'two_consecutive_failure_claims_at_tail','requires_s0_recheck',
 'requires_authenticated_evidence','s0_source_authenticated',
 'attempt_correlation_verified','definitive_classification_verified',
 'sent_verified','failure_verified','wdc13_increment_authorized',
 'wdc13_transition_authorized','c09_window_authorized',
 'f02_replan_authorized','automatic_retry_authorized',
 'send_authorized','production_authorized'] as const;
type RecordData=Record<string,unknown>;
export type Wa20Decision='LAB_NO_ATTEMPTS_UNVERIFIED'|
 'LAB_BELOW_TWO_UNVERIFIED'|'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED'|
 'LAB_HOLD_UNCERTAIN_OR_CONFLICT'|'LAB_INACTIVE_HOLD';
export type Wa20Reason='INVALID_INPUT'|'SNAPSHOT_STALE_OR_FUTURE'|
 'SEQUENCE_GAP_OR_DUPLICATE'|'ATTEMPT_SCOPE_DENIED'|'INVALID_PREVIOUS'|
 'SNAPSHOT_OR_CONTEXT_CHANGED';
const FLAGS=Object.freeze({
 s0_source_authenticated:false,attempt_correlation_verified:false,
 definitive_classification_verified:false,sent_verified:false,
 failure_verified:false,wdc13_increment_authorized:false,
 wdc13_transition_authorized:false,c09_window_authorized:false,
 f02_replan_authorized:false,automatic_retry_authorized:false,
 send_authorized:false,production_authorized:false,
} as const);
export type Wa20Snapshot=Readonly<typeof FLAGS & {
 contract_version:'wa20-wdc13-snapshot.lab.v0.2';
 snapshot_sha256:string;decision:Wa20Decision;attempts_examined:number;
 consecutive_failure_claims_at_tail:number;
 claimed_sent_reset_count:number;unknown_or_conflict_seen:boolean;
 two_consecutive_failure_claims_at_tail:boolean;
 requires_s0_recheck:true;requires_authenticated_evidence:true;
}>;
export type Wa20Result=Readonly<typeof FLAGS & {
 decision:'DENIED'|Wa20Decision|'LAB_RECHECKED_UNVERIFIED';
 reason:Wa20Reason|null;snapshot:Wa20Snapshot|null;
}>;
const sha=(input:unknown)=>createHash('sha256')
 .update(JSON.stringify(input),'utf8').digest('hex');
const deny=(reason:Wa20Reason):Wa20Result=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,snapshot:null,
});
const ok=(snapshot:Wa20Snapshot,recheck=false):Wa20Result=>Object.freeze({
 ...FLAGS,decision:recheck?'LAB_RECHECKED_UNVERIFIED' as const:
  snapshot.decision,reason:null,snapshot,
});
function strict(raw:unknown,required:readonly string[]):RecordData|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const p=Object.getPrototypeOf(raw);
  if(p!==Object.prototype&&p!==null)return null;
  const ds=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
  if(keys.length!==required.length||
     keys.some(k=>typeof k!=='string'||!required.includes(k)||
      !Object.hasOwn(ds[k],'value'))||
     required.some(k=>!Object.hasOwn(ds,k)))return null;
  return Object.fromEntries(required.map(k=>[k,ds[k].value]));
 }catch{return null;}
}
function dense(raw:unknown):unknown[]|null{
 try{
  if(!Array.isArray(raw)||Object.getPrototypeOf(raw)!==Array.prototype)
   return null;
  const d=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
  const n=d.length?.value;
  if(!nonneg(n)||n>40||keys.length!==n+1)return null;
  const out:unknown[]=[];
  for(let i=0;i<n;i++){
   if(!d[String(i)]||!Object.hasOwn(d[String(i)],'value'))return null;
   out.push(d[String(i)].value);
  }
  return out;
 }catch{return null;}
}
function validContext(c:RecordData):boolean{
 return c.contract_version==='wa20-cadence-claim.lab.v0.1'&&
  typeof c.concessionaria_id==='string'&&UUID.test(c.concessionaria_id)&&
  ['app_ref','waba_ref','case_ref','flow_ref','plan_ref','cadence_ref']
   .every(k=>id(c[k]))&&
  typeof c.phone_number_id==='string'&&PHONE.test(c.phone_number_id)&&
  ['plan_revision','case_revision','evidence_revision'].every(k=>pos(c[k]))&&
  nonneg(c.now_ms)&&nonneg(c.observed_at_ms)&&pos(c.max_age_ms)&&
  (c.max_age_ms as number)<=300000&&
  ['LAB_ACTIVE','LAB_PAUSED','LAB_REVOKED'].includes(c.cadence_state as string)&&
  ['s0_source_authenticated','attempt_correlation_verified',
   'definitive_classification_verified','durable_evidence_verified']
   .every(k=>c[k]===false);
}
function validAttempt(a:RecordData,c:RecordData):boolean{
 return a.contract_version==='wa20-attempt-claim.lab.v0.1'&&
  typeof a.concessionaria_id==='string'&&UUID.test(a.concessionaria_id)&&
  typeof a.phone_number_id==='string'&&PHONE.test(a.phone_number_id)&&
  ['concessionaria_id','app_ref','waba_ref','phone_number_id',
   'case_ref','flow_ref','plan_ref','cadence_ref'].every(k=>a[k]===c[k])&&
  ['attempt_ref','intent_ref','template_ref','template_version_ref',
   'event_ref'].every(k=>id(a[k]))&&
  pos(a.sequence_no)&&a.sequence_no<=40&&
  typeof a.event_sha256==='string'&&HEX.test(a.event_sha256)&&
  typeof a.is_final_template==='boolean'&&nonneg(a.observed_at_ms)&&
  ['LAB_SENT_CLAIM','LAB_DEFINITIVE_FAILURE_CLAIM',
   'LAB_UNKNOWN_CLAIM','LAB_PENDING_CLAIM','LAB_CONFLICT_CLAIM']
    .includes(a.status_claim as string)&&
  (a.status_claim==='LAB_DEFINITIVE_FAILURE_CLAIM'?
    a.provider_error_code===null||
     (nonneg(a.provider_error_code)&&
      (a.provider_error_code as number)<=999999999):
    a.provider_error_code===null)&&
  a.observed_at_ms!<=c.now_ms!&&
  // The synthetic S0 context cannot claim evidence observed after itself.
  a.observed_at_ms!<=c.observed_at_ms!&&
  c.now_ms!-a.observed_at_ms!<=c.max_age_ms!;
}
/**
 * Any UNKNOWN/CONFLICT/PENDING leaves a hold until a later claimed SENT.
 * Do not count failures separated by gaps, reused intents, or uncertain
 * attempts. A later LAB SENT resets the provisional consecutive counter.
 * No C09 effect is computed, even when is_final_template is true.
 */
export function inspectWa20Wdc13Offline(
 rawContext:unknown,rawAttempts:unknown,
):Wa20Result{
 try{
  const c=strict(rawContext,K_CONTEXT),array=dense(rawAttempts);
  if(!c||!array||!validContext(c))return deny('INVALID_INPUT');
  if(c.observed_at_ms!>c.now_ms!||
     c.now_ms!-c.observed_at_ms!>c.max_age_ms!)
   return deny('SNAPSHOT_STALE_OR_FUTURE');
  const a:RecordData[]=[],seenAttempts=new Set<string>(),
   seenIntents=new Set<string>(),seenEvents=new Set<string>();
  for(const raw of array){
   const x=strict(raw,K_ATTEMPT);
   if(!x||!validAttempt(x,c))return deny('ATTEMPT_SCOPE_DENIED');
   if(seenAttempts.has(x.attempt_ref as string)||
      seenIntents.has(x.intent_ref as string)||
      // A single purported S0 evidence/occurrence cannot support two
      // separate definitive failures or an artificial sent reset.
      seenEvents.has(x.event_ref as string))
    return deny('SEQUENCE_GAP_OR_DUPLICATE');
   seenAttempts.add(x.attempt_ref as string);
   seenIntents.add(x.intent_ref as string);
   seenEvents.add(x.event_ref as string);
   a.push(x);
  }
  a.sort((x,y)=>(x.sequence_no as number)-(y.sequence_no as number));
  if(a.some((x,i)=>x.sequence_no!==i+1))
   return deny('SEQUENCE_GAP_OR_DUPLICATE');
  let consecutive=0,resets=0,hold=false,seenUnknown=false;
  for(const x of a){
   switch(x.status_claim){
    case 'LAB_SENT_CLAIM':
     if(consecutive>0||hold)resets++;
     consecutive=0;hold=false;break;
    case 'LAB_DEFINITIVE_FAILURE_CLAIM':
     if(!hold)consecutive++;
     break;
    default:
     consecutive=0;hold=true;seenUnknown=true;break;
   }
  }
  const decision:Wa20Decision=c.cadence_state!=='LAB_ACTIVE'?
   'LAB_INACTIVE_HOLD':!a.length?'LAB_NO_ATTEMPTS_UNVERIFIED':
   hold?'LAB_HOLD_UNCERTAIN_OR_CONFLICT':
   consecutive>=2?'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED':
   'LAB_BELOW_TWO_UNVERIFIED';
  const snap:Wa20Snapshot=Object.freeze({
   contract_version:'wa20-wdc13-snapshot.lab.v0.2',
   snapshot_sha256:sha(['WA20_WDC13_LAB_V0_2',
    K_CONTEXT.map(k=>c[k]),a.map(x=>K_ATTEMPT.map(k=>x[k])),
    consecutive,resets,hold,seenUnknown,decision]),
   decision,attempts_examined:a.length,
   consecutive_failure_claims_at_tail:consecutive,
   claimed_sent_reset_count:resets,unknown_or_conflict_seen:seenUnknown,
   two_consecutive_failure_claims_at_tail:
     c.cadence_state==='LAB_ACTIVE'&&!hold&&consecutive>=2,
   requires_s0_recheck:true,requires_authenticated_evidence:true,
   ...FLAGS,
  });
  return ok(snap);
 }catch{return deny('INVALID_INPUT');}
}
function validPrevious(raw:unknown):RecordData|null{
 const p=strict(raw,K_SNAPSHOT);
 if(!p||p.contract_version!=='wa20-wdc13-snapshot.lab.v0.2'||
    typeof p.snapshot_sha256!=='string'||!HEX.test(p.snapshot_sha256)||
    !['LAB_NO_ATTEMPTS_UNVERIFIED','LAB_BELOW_TWO_UNVERIFIED',
     'LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED',
     'LAB_HOLD_UNCERTAIN_OR_CONFLICT','LAB_INACTIVE_HOLD']
     .includes(p.decision as string)||
    !nonneg(p.attempts_examined)||p.attempts_examined>40||
    !nonneg(p.consecutive_failure_claims_at_tail)||
    !nonneg(p.claimed_sent_reset_count)||
    typeof p.unknown_or_conflict_seen!=='boolean'||
    typeof p.two_consecutive_failure_claims_at_tail!=='boolean'||
    p.requires_s0_recheck!==true||p.requires_authenticated_evidence!==true||
    Object.keys(FLAGS).some(k=>p[k]!==false))return null;
 return p;
}
export function recheckWa20Wdc13Offline(
 rawPrevious:unknown,rawContext:unknown,rawAttempts:unknown,
):Wa20Result{
 const old=validPrevious(rawPrevious);
 if(!old)return deny('INVALID_PREVIOUS');
 const fresh=inspectWa20Wdc13Offline(rawContext,rawAttempts);
 if(!fresh.snapshot)return fresh;
 if(K_SNAPSHOT.some(k=>old[k]!==fresh.snapshot![k as keyof Wa20Snapshot]))
  return deny('SNAPSHOT_OR_CONTEXT_CHANGED');
 return ok(fresh.snapshot,true);
}
