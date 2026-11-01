/**
 * M19 / WA39: bounded, synthetic status-occurrence reconciliation for one
 * claimed outbound attempt. ALL sources are LAB claims, not authenticated
 * Graph callbacks, S0 receipts, HMAC proofs, persistence or a webhook.
 * Never authorizes sent/delivery/read, retry, commercial WDC-13/C09 or ACK.
 */
import {createHash} from 'node:crypto';
import {isMetaWamid} from './status-evidence.ts';

const REF=/^[A-Za-z0-9_.:-]{1,128}$/,UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const PHONE=/^[0-9]{5,25}$/,HEX=/^[0-9a-f]{64}$/;
const POS=(x:unknown):x is number=>typeof x==='number'&&Number.isSafeInteger(x)&&x>0;
const NONNEG=(x:unknown):x is number=>typeof x==='number'&&Number.isSafeInteger(x)&&x>=0;
const scope=['concessionaria_id','app_ref','waba_id','phone_number_id',
 'attempt_ref','intent_ref','case_ref','template_ref','template_version_ref',
 'provider_message_id'] as const;
const K_REQUEST=['contract_version',...scope,'case_revision','template_revision',
 'assignment_revision','consent_revision','now_ms','max_age_ms',
 'authority_state','revoked_at_ms'] as const;
const K_GRAPH=['contract_version',...scope,'graph_state','observed_at_ms',
 'source_authenticated','attempt_binding_verified'] as const;
const K_EVENT=['contract_version',...scope,'source_boundary','occurrence_ref',
 'batch_ref','entry_index','change_index','item_index','body_sha256',
 'provider_status','provider_timestamp_ms','observed_at_ms','error_code'] as const;
const K_BATCH=['contract_version','events'] as const;
const K_RESULT=['contract_version','snapshot_sha256','decision','progress',
 'unique_occurrences','exact_replays','conflict_occurrences',
 'sent_observed_lab','delivered_observed_lab','read_observed_lab',
 'failed_observed_lab','api_accepted_lab','source_authenticated',
 'attempt_correlation_verified','sent_verified','delivered_verified',
 'read_verified','definitive_failure_verified','retry_external',
 'send_authorized','production_authorized','ack_allowed',
 'case_transition_authorized','wdc13_increment_authorized',
 'c09_window_authorized'] as const;
type Status='sent'|'delivered'|'read'|'failed';
type GraphState='API_ACCEPTED'|'EXTERNAL_UNKNOWN'|'PROVIDER_REJECTED';
type Decision='LAB_NO_CALLBACK_UNVERIFIED'|'LAB_OBSERVATION_UNVERIFIED'|
 'LAB_LATE_HISTORICAL_UNVERIFIED'|'LAB_QUARANTINED_CONFLICT'|'DENIED';
type Progress='NONE'|'SENT_OBSERVED'|'DELIVERED_OBSERVED'|'READ_OBSERVED'|
 'FAILED_OBSERVED'|'CONFLICT';
export type Wa19Snapshot=Readonly<{
 contract_version:'wa19-graph-status-snapshot.lab.v0.2';
 snapshot_sha256:string;decision:Exclude<Decision,'DENIED'>;
 progress:Progress;unique_occurrences:number;exact_replays:number;
 conflict_occurrences:number;
 sent_observed_lab:boolean;delivered_observed_lab:boolean;
 read_observed_lab:boolean;failed_observed_lab:boolean;
 api_accepted_lab:boolean;
 source_authenticated:false;attempt_correlation_verified:false;
 sent_verified:false;delivered_verified:false;read_verified:false;
 definitive_failure_verified:false;retry_external:false;
 send_authorized:false;production_authorized:false;ack_allowed:false;
 case_transition_authorized:false;wdc13_increment_authorized:false;
 c09_window_authorized:false;
}>;
export type Wa19Result=Readonly<{
 decision:Decision;reason:'INVALID_INPUT'|'SCOPE_MISMATCH'|
 'OBSERVATION_UNTRUSTED'|'CAPACITY_REACHED'|
 'INVALID_PREVIOUS'|'SNAPSHOT_CHANGED'|null;
 snapshot:Wa19Snapshot|null;
 source_authenticated:false;attempt_correlation_verified:false;
 sent_verified:false;delivered_verified:false;read_verified:false;
 definitive_failure_verified:false;retry_external:false;
 send_authorized:false;production_authorized:false;ack_allowed:false;
 case_transition_authorized:false;wdc13_increment_authorized:false;
 c09_window_authorized:false;
}>;
const FAIL=Object.freeze({
 source_authenticated:false,attempt_correlation_verified:false,
 sent_verified:false,delivered_verified:false,read_verified:false,
 definitive_failure_verified:false,retry_external:false,
 send_authorized:false,production_authorized:false,ack_allowed:false,
 case_transition_authorized:false,wdc13_increment_authorized:false,
 c09_window_authorized:false,
} as const);
const deny=(reason:Exclude<Wa19Result['reason'],null>):Wa19Result=>
 Object.freeze({...FAIL,decision:'DENIED' as const,reason,snapshot:null});
const sha=(x:unknown):string=>createHash('sha256').update(
 JSON.stringify(x),'utf8').digest('hex');
function record(raw:unknown,expected:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const ds=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
  if(keys.length!==expected.length||keys.some(k=>typeof k!=='string'||
    !expected.includes(k)||!Object.hasOwn(ds[k],'value'))||
    expected.some(k=>!Object.hasOwn(ds,k)))return null;
  return Object.fromEntries(expected.map(k=>[k,ds[k].value]));
 }catch{return null;}
}
const sref=(x:unknown):x is string=>typeof x==='string'&&REF.test(x);
function validScope(x:Record<string,unknown>):boolean{
 return typeof x.concessionaria_id==='string'&&UUID.test(x.concessionaria_id)&&
  typeof x.phone_number_id==='string'&&PHONE.test(x.phone_number_id)&&
  (['app_ref','waba_id','attempt_ref','intent_ref','case_ref',
    'template_ref','template_version_ref'] as const).every(k=>sref(x[k]))&&
  typeof x.provider_message_id==='string'&&isMetaWamid(x.provider_message_id)&&
  x.provider_message_id.length<=128;
}
function sameScope(a:Record<string,unknown>,b:Record<string,unknown>):boolean{
 return scope.every(k=>a[k]===b[k]);
}
function request(x:Record<string,unknown>):boolean{
 return x.contract_version==='wa19-graph-status-request.lab.v0.1'&&validScope(x)&&
  ['case_revision','template_revision','assignment_revision','consent_revision']
   .every(k=>POS(x[k]))&&NONNEG(x.now_ms)&&POS(x.max_age_ms)&&
  (x.max_age_ms as number)<=300000&&
  ['LAB_ACTIVE','LAB_REVOKED'].includes(x.authority_state as string)&&
  (x.authority_state==='LAB_ACTIVE'?x.revoked_at_ms===null:
   NONNEG(x.revoked_at_ms)&&(x.revoked_at_ms as number)<=(x.now_ms as number));
}
function graph(x:Record<string,unknown>,q:Record<string,unknown>):boolean{
 return x.contract_version==='wa19-graph-claim.lab.v0.1'&&sameScope(x,q)&&
  ['API_ACCEPTED','EXTERNAL_UNKNOWN','PROVIDER_REJECTED']
    .includes(x.graph_state as string)&&
  NONNEG(x.observed_at_ms)&&x.observed_at_ms!<=q.now_ms!&&
  q.now_ms!-x.observed_at_ms!<=q.max_age_ms!&&
  x.source_authenticated===false&&x.attempt_binding_verified===false;
}
function event(x:Record<string,unknown>,q:Record<string,unknown>):boolean{
 return x.contract_version==='wa19-callback-event.lab.v0.1'&&
  sameScope(x,q)&&x.source_boundary==='LAB_UNAUTHENTICATED_POST'&&
  sref(x.occurrence_ref)&&sref(x.batch_ref)&&
  ['entry_index','change_index','item_index'].every(k=>NONNEG(x[k]))&&
  typeof x.body_sha256==='string'&&HEX.test(x.body_sha256)&&
  ['sent','delivered','read','failed'].includes(x.provider_status as string)&&
  NONNEG(x.provider_timestamp_ms)&&NONNEG(x.observed_at_ms)&&
  x.provider_timestamp_ms!<=q.now_ms!&&x.observed_at_ms!<=q.now_ms!&&
  q.now_ms!-x.observed_at_ms!<=q.max_age_ms!&&
  (x.provider_status==='failed'?x.error_code===null||
   (NONNEG(x.error_code)&&(x.error_code as number)<=99999999):
   x.error_code===null);
}
/** Event occurrence key uses both batch + physical Meta position.
 * Identical repeats are counted once; reused key with different body/event
 * quarantines. A digest alone or wamid alone is NOT a unique occurrence.
 */
function occurrenceKey(x:Record<string,unknown>):string{
 return JSON.stringify([x.batch_ref,x.entry_index,x.change_index,x.item_index]);
}
function eventTuple(x:Record<string,unknown>):string{
 return JSON.stringify(K_EVENT.map(k=>x[k]));
}
function makeResult(x:Wa19Snapshot):Wa19Result{
 return Object.freeze({...FAIL,decision:x.decision,reason:null,snapshot:x});
}
/** Every positive branch returns LAB-only observations without S0 authority.
 * Synthetic out-of-order READ does NOT invent a SENT callback. */
export function reconcileWa19StatusOffline(
 rawRequest:unknown,rawGraph:unknown,rawBatch:unknown,
):Wa19Result{
 try{
  const q=record(rawRequest,K_REQUEST),g=record(rawGraph,K_GRAPH),
   batch=record(rawBatch,K_BATCH);
  if(!q||!g||!batch||!request(q))return deny('INVALID_INPUT');
  if(!sameScope(g,q))return deny('SCOPE_MISMATCH');
  if(!graph(g,q))return deny('OBSERVATION_UNTRUSTED');
  if(batch.contract_version!=='wa19-status-batch.lab.v0.1'||
     !Array.isArray(batch.events))return deny('INVALID_INPUT');
  const arr=batch.events as unknown[];
  // Bounded, dense lab batches only; never access elements through getters.
  const ad=Object.getOwnPropertyDescriptors(arr),keys=Reflect.ownKeys(arr);
  if(arr.length>80)return deny('CAPACITY_REACHED');
  if(keys.length!==arr.length+1||
     Array.from({length:arr.length},(_,i)=>String(i)).some(k=>
      !Object.hasOwn(ad,k)||!Object.hasOwn(ad[k],'value')))
   return deny('INVALID_INPUT');
  // First collect all distinct variants; a conflict MUST NOT discard
  // the body/status of the later contender before fingerprinting.
  // A deterministic order prevents first-wins differences on replay.
  const variants=new Map<string,Record<string,unknown>>();
  let replay=0,conflict=0;
  for(let k=0;k<arr.length;k++){
   const x=record(ad[String(k)].value,K_EVENT);
   if(!x)return deny('INVALID_INPUT');
   if(!sameScope(x,q))return deny('SCOPE_MISMATCH');
   if(!event(x,q))return deny('OBSERVATION_UNTRUSTED');
   const canonical=eventTuple(x);
   if(variants.has(canonical)){replay++;continue;}
   variants.set(canonical,x);
  }
  const canonical=[...variants.keys()].sort();
  const positions=new Map<string,string>(),refs=new Map<string,string>();
  for(const tuple of canonical){
   const x=variants.get(tuple)!;
   const pos=occurrenceKey(x),refId=x.occurrence_ref as string;
   const oldPosition=positions.get(pos),oldRef=refs.get(refId);
   if((oldPosition!==undefined&&oldPosition!==tuple)||
      (oldRef!==undefined&&oldRef!==tuple))conflict++;
   if(oldPosition===undefined)positions.set(pos,tuple);
   if(oldRef===undefined)refs.set(refId,tuple);
  }
  const unique=canonical.map(tuple=>variants.get(tuple)!);
  let sent=false,delivered=false,read=false,failed=false;
  const flags=unique.map(x=>x.provider_status as Status);
  sent=flags.includes('sent');delivered=flags.includes('delivered');
  read=flags.includes('read');failed=flags.includes('failed');
  const afterRevocation=q.authority_state==='LAB_REVOKED'&&
    unique.some(x=>(x.provider_timestamp_ms as number)>=(q.revoked_at_ms as number));
  const incompatible=conflict>0||
    (failed&&(sent||delivered||read))||
    (g.graph_state==='PROVIDER_REJECTED'&&(sent||delivered||read))||
    afterRevocation;
  let decision:Wa19Snapshot['decision']='LAB_OBSERVATION_UNVERIFIED';
  let progress:Progress='NONE';
  if(incompatible){decision='LAB_QUARANTINED_CONFLICT';progress='CONFLICT';}
  else if(q.authority_state==='LAB_REVOKED'&&unique.length>0)
   decision='LAB_LATE_HISTORICAL_UNVERIFIED';
  else if(!unique.length)decision='LAB_NO_CALLBACK_UNVERIFIED';
  if(!incompatible){
   progress=read?'READ_OBSERVED':delivered?'DELIVERED_OBSERVED':
    sent?'SENT_OBSERVED':failed?'FAILED_OBSERVED':'NONE';
  }
  // Canonical projection for deterministic event-array permutation; all
  // claimed fields, timestamps, positions and error codes affect the hash.
  const snapshot:Wa19Snapshot=Object.freeze({
   contract_version:'wa19-graph-status-snapshot.lab.v0.2',
   snapshot_sha256:sha(['WA19_STATUS_LAB_V0_2',K_REQUEST.map(k=>q[k]),
    K_GRAPH.map(k=>g[k]),canonical,replay,conflict,decision,progress]),
   decision,progress,unique_occurrences:unique.length,exact_replays:replay,
   conflict_occurrences:conflict,sent_observed_lab:sent,
   delivered_observed_lab:delivered,read_observed_lab:read,
   failed_observed_lab:failed,
   api_accepted_lab:g.graph_state==='API_ACCEPTED',
   ...FAIL,
  });
  return makeResult(snapshot);
 }catch{return deny('INVALID_INPUT');}
}
function previous(raw:unknown):Record<string,unknown>|null{
 const x=record(raw,K_RESULT);
 if(!x||x.contract_version!=='wa19-graph-status-snapshot.lab.v0.2'||
    typeof x.snapshot_sha256!=='string'||!HEX.test(x.snapshot_sha256)||
    !['LAB_NO_CALLBACK_UNVERIFIED','LAB_OBSERVATION_UNVERIFIED',
      'LAB_LATE_HISTORICAL_UNVERIFIED','LAB_QUARANTINED_CONFLICT']
      .includes(x.decision as string)||
    !['NONE','SENT_OBSERVED','DELIVERED_OBSERVED','READ_OBSERVED',
      'FAILED_OBSERVED','CONFLICT'].includes(x.progress as string)||
    !NONNEG(x.unique_occurrences)||!NONNEG(x.exact_replays)||
    !NONNEG(x.conflict_occurrences)||
    ['sent_observed_lab','delivered_observed_lab','read_observed_lab',
     'failed_observed_lab','api_accepted_lab'].some(k=>typeof x[k]!=='boolean')||
    Object.keys(FAIL).some(k=>x[k]!==false))return null;
 return x;
}
/** Fresh LAB readback only; no version/authority upgrade from old snapshots. */
export function recheckWa19StatusOffline(
 oldSnapshot:unknown,rawRequest:unknown,rawGraph:unknown,rawBatch:unknown,
):Wa19Result{
 const p=previous(oldSnapshot);
 if(!p)return deny('INVALID_PREVIOUS');
 const current=reconcileWa19StatusOffline(rawRequest,rawGraph,rawBatch);
 if(!current.snapshot)return current;
 if(K_RESULT.some(k=>p[k]!==current.snapshot![k as keyof Wa19Snapshot]))
  return deny('SNAPSHOT_CHANGED');
 return current;
}
