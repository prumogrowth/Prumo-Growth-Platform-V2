/**
 * M19 / WA39: ONLY in-memory LAB forensic reconciliation of S0-claimed
 * attempt binding and Meta-claimed status occurrences. No HMAC verification,
 * no trusted S0 port, no durable ingest, HTTP ACK, Graph, retry or commercial
 * inference. A syntactically well-formed 'sent' is NEVER verified sent.
 *
 * Existing WA32/WA35 are the (still offline) signed ingress and exact-binding
 * experiments; WA38 supplies ambiguity discipline. Do not duplicate them.
 */
import {createHash} from 'node:crypto';
import {isMetaWamid,isMetaPhoneNumberId} from './status-evidence.ts';

const SCOPE=['contract_version','selection_ref','concessionaria_id','app_ref',
 'waba_id','phone_number_id','canal_ref','case_ref','intent_ref','attempt_ref',
 'provider_message_id','recipient_sha256','now_ms','max_age_ms'] as const;
const BIND=['contract_version','selection_ref','concessionaria_id','app_ref',
 'waba_id','phone_number_id','canal_ref','case_ref','intent_ref','attempt_ref',
 'provider_message_id','recipient_sha256','binding_revision','claim_state',
 'observed_at_ms'] as const;
const EVENT=['contract_version','selection_ref','concessionaria_id',
 'app_ref','waba_id','phone_number_id','canal_ref','provider_message_id',
 'recipient_sha256','occurrence_ref','body_sha256','position_index',
 'provider_kind','provider_timestamp','meta_error_code','meta_error_subcode',
 'hmac_verified','s0_source_authenticated','durably_persisted'] as const;
const RESULT=['contract_version','snapshot_sha256','observation_count',
 'duplicate_count','saw_explicit_sent','saw_delivered','saw_read',
 'saw_failed','status','quarantine_required','requires_s0_recheck',
 's0_source_authenticated','callback_hmac_verified',
 'attempt_correlation_verified','durable_persistence_verified',
 'sent_verified','delivered_verified','read_verified',
 'definitive_failure_verified','definitive_failure_count_increment',
 'case_transition_authorized','commercial_transition_authorized',
 'retry_external','ack_allowed','production_authorized'] as const;
type RecordData=Record<string,unknown>;
const REF=/^[A-Za-z0-9_.:-]{1,128}$/,HEX=/^[0-9a-f]{64}$/,
 UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const goodId=(v:unknown):v is string=>typeof v==='string'&&REF.test(v);
const positive=(v:unknown):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>0;
const nonneg=(v:unknown):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0;
const sha=(v:unknown):string=>createHash('sha256').update(JSON.stringify(v),'utf8').digest('hex');
const iso=(x:unknown):x is string=>{
 if(typeof x!=='string'||!/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$/.test(x))return false;
 const t=Date.parse(x);
 return Number.isFinite(t)&&new Date(t).toISOString()===x;
};
function own(raw:unknown,required:readonly string[]):RecordData|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const keys=Reflect.ownKeys(raw),d=Object.getOwnPropertyDescriptors(raw);
  if(keys.length!==required.length||
   keys.some(k=>typeof k!=='string'||!required.includes(k)||
    !Object.hasOwn(d[k],'value'))||
   required.some(k=>!Object.hasOwn(d,k)))return null;
  return Object.fromEntries(required.map(k=>[k,d[k].value]));
 }catch{return null;}
}
function dense(raw:unknown):unknown[]|null{
 try{
  if(!Array.isArray(raw)||Object.getPrototypeOf(raw)!==Array.prototype)return null;
  const d=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
  const n=d.length?.value;
  if(!nonneg(n)||n>100||keys.length!==n+1)return null;
  const a:unknown[]=[];
  for(let i=0;i<n;i++){
   const x=d[String(i)];
   if(!x||!Object.hasOwn(x,'value'))return null;
   a.push(x.value);
  }
  return a;
 }catch{return null;}
}
export type Wa19Status='LAB_NO_OBSERVATIONS'|
 'LAB_SENT_OBSERVED_UNVERIFIED'|'LAB_DELIVERED_OBSERVED_UNVERIFIED'|
 'LAB_READ_OBSERVED_UNVERIFIED'|'LAB_FAILURE_OBSERVED_UNVERIFIED'|
 'LAB_CONFLICT_QUARANTINED'|'LAB_INVALIDATED_OBSERVATION_HOLD';
export type Wa19Snapshot=Readonly<{
 contract_version:'wa19-status-snapshot.lab.v0.1';
 snapshot_sha256:string;
 observation_count:number;duplicate_count:number;
 saw_explicit_sent:boolean;saw_delivered:boolean;saw_read:boolean;
 saw_failed:boolean;status:Wa19Status;quarantine_required:boolean;
 requires_s0_recheck:true;
 s0_source_authenticated:false;callback_hmac_verified:false;
 attempt_correlation_verified:false;durable_persistence_verified:false;
 sent_verified:false;delivered_verified:false;read_verified:false;
 definitive_failure_verified:false;definitive_failure_count_increment:false;
 case_transition_authorized:false;commercial_transition_authorized:false;
 retry_external:false;ack_allowed:false;production_authorized:false;
}>;
export type Wa19Reason='INVALID_INPUT'|'BINDING_SCOPE_DENIED'|
 'SNAPSHOT_STALE_OR_FUTURE'|'EVENT_SCOPE_DENIED'|
 'PREVIOUS_SNAPSHOT_INVALID'|'SNAPSHOT_OR_CONTEXT_CHANGED';
export type Wa19Result=Readonly<{
 decision:'DENIED'|'LAB_STATUS_RECONCILED_UNVERIFIED'|
 'LAB_RECHECKED_UNVERIFIED';
 reason:Wa19Reason|null;snapshot:Wa19Snapshot|null;
 callback_hmac_verified:false;s0_source_authenticated:false;
 sent_verified:false;delivered_verified:false;read_verified:false;
 definitive_failure_count_increment:false;case_transition_authorized:false;
 retry_external:false;ack_allowed:false;production_authorized:false;
}>;
const ZERO=Object.freeze({callback_hmac_verified:false,
 s0_source_authenticated:false,sent_verified:false,delivered_verified:false,
 read_verified:false,definitive_failure_count_increment:false,
 case_transition_authorized:false,retry_external:false,ack_allowed:false,
 production_authorized:false} as const);
const denied=(reason:Wa19Reason):Wa19Result=>Object.freeze({
 ...ZERO,decision:'DENIED',reason,snapshot:null,
});
const success=(snap:Wa19Snapshot,recheck=false):Wa19Result=>Object.freeze({
 ...ZERO,decision:recheck?'LAB_RECHECKED_UNVERIFIED':
 'LAB_STATUS_RECONCILED_UNVERIFIED',reason:null,snapshot:snap,
});
const COMMON=['selection_ref','concessionaria_id','app_ref','waba_id',
 'phone_number_id','canal_ref','provider_message_id','recipient_sha256'] as const;
function validScope(s:RecordData):boolean{
 return s.contract_version==='wa19-status-request.lab.v0.1'&&
  ['selection_ref','app_ref','canal_ref','case_ref','intent_ref','attempt_ref']
   .every(k=>goodId(s[k]))&&
  typeof s.concessionaria_id==='string'&&UUID.test(s.concessionaria_id)&&
  goodId(s.waba_id)&&isMetaPhoneNumberId(s.phone_number_id)&&
  isMetaWamid(s.provider_message_id)&&
  typeof s.recipient_sha256==='string'&&HEX.test(s.recipient_sha256)&&
  nonneg(s.now_ms)&&positive(s.max_age_ms)&&s.max_age_ms<=300000;
}
function validBinding(s:RecordData,b:RecordData):boolean{
 return b.contract_version==='wa19-s0-binding-claim.lab.v0.1'&&
  COMMON.every(k=>b[k]===s[k])&&
  ['case_ref','intent_ref','attempt_ref'].every(k=>b[k]===s[k])&&
  positive(b.binding_revision)&&nonneg(b.observed_at_ms)&&
  (b.claim_state==='LAB_CLAIMED'||b.claim_state==='LAB_INVALIDATED');
}
function validEvent(s:RecordData,e:RecordData):boolean{
 return e.contract_version==='wa19-status-occurrence.lab.v0.1'&&
  COMMON.every(k=>e[k]===s[k])&&
  goodId(e.occurrence_ref)&&
  typeof e.body_sha256==='string'&&HEX.test(e.body_sha256)&&
  nonneg(e.position_index)&&e.position_index<=10000&&
  ['sent','delivered','read','failed'].includes(e.provider_kind as string)&&
  iso(e.provider_timestamp)&&
  (e.provider_kind==='failed'||
   (e.meta_error_code===null&&e.meta_error_subcode===null))&&
  (e.meta_error_code===null||
   nonneg(e.meta_error_code)&&e.meta_error_code<=999999999)&&
  (e.meta_error_subcode===null||
   nonneg(e.meta_error_subcode)&&e.meta_error_subcode<=999999999)&&
  e.hmac_verified===false&&e.s0_source_authenticated===false&&
  e.durably_persisted===false;
}
const same=(a:RecordData,b:RecordData,fields:readonly string[]):boolean=>
 fields.every(k=>a[k]===b[k]);
function snapshot(s:RecordData,b:RecordData,events:RecordData[]):Wa19Snapshot{
 const unique=new Map<string,RecordData>();
 let duplicates=0,collision=false;
 for(const e of events){
  const prior=unique.get(e.occurrence_ref as string);
  if(!prior)unique.set(e.occurrence_ref as string,e);
  else if(same(prior,e,EVENT))duplicates++;
  else collision=true;
 }
 const canon=[...unique.values()].sort((a,z)=>
  (a.occurrence_ref as string).localeCompare(z.occurrence_ref as string));
 const kinds=new Set(canon.map(x=>x.provider_kind));
 const sent=kinds.has('sent'),delivered=kinds.has('delivered'),
  read=kinds.has('read'),failed=kinds.has('failed');
 const ambiguous=collision||(failed&&(sent||delivered||read));
 const invalidated=b.claim_state==='LAB_INVALIDATED'&&canon.length>0;
 const status:Wa19Status=ambiguous?'LAB_CONFLICT_QUARANTINED':
  invalidated?'LAB_INVALIDATED_OBSERVATION_HOLD':
  read?'LAB_READ_OBSERVED_UNVERIFIED':
  delivered?'LAB_DELIVERED_OBSERVED_UNVERIFIED':
  sent?'LAB_SENT_OBSERVED_UNVERIFIED':
  failed?'LAB_FAILURE_OBSERVED_UNVERIFIED':'LAB_NO_OBSERVATIONS';
 const digest=sha(['WA19_OBSERVATIONS_LAB_V0_1',
  SCOPE.map(k=>s[k]),BIND.map(k=>b[k]),
  canon.map(x=>EVENT.map(k=>x[k])),collision]);
 return Object.freeze({
  contract_version:'wa19-status-snapshot.lab.v0.1',
  snapshot_sha256:digest,observation_count:unique.size,
  duplicate_count:duplicates,saw_explicit_sent:sent,
  saw_delivered:delivered,saw_read:read,saw_failed:failed,status,
  quarantine_required:ambiguous||invalidated,requires_s0_recheck:true,
  s0_source_authenticated:false,callback_hmac_verified:false,
  attempt_correlation_verified:false,durable_persistence_verified:false,
  sent_verified:false,delivered_verified:false,read_verified:false,
  definitive_failure_verified:false,definitive_failure_count_increment:false,
  case_transition_authorized:false,commercial_transition_authorized:false,
  retry_external:false,ack_allowed:false,production_authorized:false,
 });
}
function previous(raw:unknown):Wa19Snapshot|null{
 const v=own(raw,RESULT);
 if(!v||v.contract_version!=='wa19-status-snapshot.lab.v0.1'||
    typeof v.snapshot_sha256!=='string'||!HEX.test(v.snapshot_sha256)||
    !nonneg(v.observation_count)||v.observation_count>100||
    !nonneg(v.duplicate_count)||v.duplicate_count>100||
    !['LAB_NO_OBSERVATIONS','LAB_SENT_OBSERVED_UNVERIFIED',
    'LAB_DELIVERED_OBSERVED_UNVERIFIED','LAB_READ_OBSERVED_UNVERIFIED',
    'LAB_FAILURE_OBSERVED_UNVERIFIED','LAB_CONFLICT_QUARANTINED',
    'LAB_INVALIDATED_OBSERVATION_HOLD'].includes(v.status as string)||
    !['saw_explicit_sent','saw_delivered','saw_read','saw_failed',
      'quarantine_required'].every(k=>typeof v[k]==='boolean')||
    v.requires_s0_recheck!==true||
    ['s0_source_authenticated','callback_hmac_verified',
     'attempt_correlation_verified','durable_persistence_verified',
     'sent_verified','delivered_verified','read_verified',
     'definitive_failure_verified','definitive_failure_count_increment',
     'case_transition_authorized','commercial_transition_authorized',
     'retry_external','ack_allowed','production_authorized']
     .some(k=>v[k]!==false))return null;
 return v as Wa19Snapshot;
}
export function reconcileWa19StatusOffline(
 rawScope:unknown,rawBinding:unknown,rawEvents:unknown,
):Wa19Result{
 const s=own(rawScope,SCOPE),b=own(rawBinding,BIND),arr=dense(rawEvents);
 if(!s||!b||!arr||!validScope(s))return denied('INVALID_INPUT');
 if(!validBinding(s,b))return denied('BINDING_SCOPE_DENIED');
 const now=s.now_ms as number,maxAge=s.max_age_ms as number;
 if(b.observed_at_ms!>now||now-(b.observed_at_ms as number)>maxAge)
  return denied('SNAPSHOT_STALE_OR_FUTURE');
 const events:RecordData[]=[];
 for(const x of arr){
  const e=own(x,EVENT);
  if(!e||!validEvent(s,e)||
     Date.parse(e.provider_timestamp as string)>now)
   return denied('EVENT_SCOPE_DENIED');
  events.push(e);
 }
 return success(snapshot(s,b,events));
}
/** Full snapshot check, never commit, append, ACK or trusted S0 readback. */
export function recheckWa19StatusOffline(
 rawPrevious:unknown,rawScope:unknown,rawBinding:unknown,
 rawEvents:unknown,
):Wa19Result{
 const p=previous(rawPrevious);
 if(!p)return denied('PREVIOUS_SNAPSHOT_INVALID');
 const current=reconcileWa19StatusOffline(rawScope,rawBinding,rawEvents);
 if(!current.snapshot)return current;
 if(RESULT.some(k=>p[k as keyof Wa19Snapshot]!==
   current.snapshot![k as keyof Wa19Snapshot]))
  return denied('SNAPSHOT_OR_CONTEXT_CHANGED');
 return success(current.snapshot,true);
}
