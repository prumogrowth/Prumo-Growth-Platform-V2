/**
 * M21 — Meta-only synthetic guard for case routing after human handoff.
 * NOT a S0 event processor, F01/F03 caller, Meta sender or commercial gate.
 * All claimed S0 identities/states are UNTRUSTED fixtures.
 */
import {createHash} from 'node:crypto';

const REF=/^[A-Za-z0-9_.:-]{1,128}$/,UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const PHONE=/^[0-9]{5,25}$/,SHA=/^[a-f0-9]{64}$/;
const REF_OK=(v:unknown)=>typeof v==='string'&&REF.test(v);
const INT=(v:unknown)=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0;
const POS=(v:unknown)=>INT(v)&&Number(v)>0;
const CASE_FIELDS=['contract_version','concessionaria_id','app_ref','waba_ref',
 'phone_number_id','case_ref','lead_ref','case_revision','assignment_revision',
 'handoff_revision','f03_cutoff_revision','case_state',
 'handoff_ever_definitive','handoff_at_ms','human_assignment_ref',
 'meta_window_claim','opt_out_claim','observed_at_ms','now_ms',
 'max_age_ms','s0_source_authenticated','case_authority_verified'] as const;
const EVENT_FIELDS=['contract_version','concessionaria_id','app_ref','waba_ref',
 'phone_number_id','case_ref','lead_ref','event_ref','event_digest',
 'event_kind','event_at_ms','closure_ref','actor_ref','actor_role',
 'closure_cutoff_ms','s0_event_authenticated','human_closure_verified'] as const;
const SNAP_FIELDS=['contract_version','snapshot_sha256','decision',
 'f01_resume_denied','f03_requires_explicit_human_closure',
 'meta_window_is_not_f03_cutoff','s0_recheck_required',
 'source_authenticated','case_verified','closure_verified',
 'f01_invocation_authorized','f03_invocation_authorized',
 'human_dispatch_authorized','graph_dispatch_authorized',
 'human_closure_apply_authorized','commercial_transition_authorized',
 'c09_window_authorized','ack_allowed','production_authorized'] as const;
type Data=Record<string,unknown>;
type Decision='LAB_F01_ACTIVE_UNVERIFIED'|
 'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED'|
 'LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED'|
 'LAB_POST_CLOSURE_HOLD'|'LAB_NON_CLOSURE_EVENT_HOLD';
type Reason='INVALID_INPUT'|'SCOPE_MISMATCH'|'TIMELINE_INCOHERENT'|
 'DEF_HANDOFF_CANNOT_RESUME_F01'|'CLOSURE_NOT_EXPLICIT'|
 'CLOSURE_IN_WRONG_STATE'|'PREVIOUS_INVALID'|'CONTEXT_CHANGED';
const NEVER=Object.freeze({
 source_authenticated:false,case_verified:false,closure_verified:false,
 f01_invocation_authorized:false,f03_invocation_authorized:false,
 human_dispatch_authorized:false,graph_dispatch_authorized:false,
 human_closure_apply_authorized:false,commercial_transition_authorized:false,
 c09_window_authorized:false,ack_allowed:false,production_authorized:false,
} as const);
export type Wa21Snapshot=Readonly<typeof NEVER & {
 contract_version:'wa21-human-handoff-snapshot.lab.v0.1';
 snapshot_sha256:string;decision:Decision;
 f01_resume_denied:boolean;
 f03_requires_explicit_human_closure:true;
 meta_window_is_not_f03_cutoff:true;s0_recheck_required:true;
}>;
export type Wa21Result=Readonly<typeof NEVER & {
 decision:Decision|'LAB_RECHECKED_UNVERIFIED'|'DENIED';
 reason:Reason|null;snapshot:Wa21Snapshot|null;
}>;
const denied=(reason:Reason):Wa21Result=>Object.freeze({
 ...NEVER,decision:'DENIED' as const,reason,snapshot:null});
const allowed=(snap:Wa21Snapshot,checked=false):Wa21Result=>
 Object.freeze({...NEVER,decision:checked?'LAB_RECHECKED_UNVERIFIED':snap.decision,
  reason:null,snapshot:snap});
const digest=(x:unknown)=>createHash('sha256').update(JSON.stringify(x),'utf8').digest('hex');
function strict(raw:unknown,fields:readonly string[]):Data|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const ds=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
  if(keys.length!==fields.length||keys.some(k=>typeof k!=='string'||
   !fields.includes(k)||!Object.hasOwn(ds[k],'value'))||
   fields.some(k=>!Object.hasOwn(ds,k)))return null;
  return Object.fromEntries(fields.map(k=>[k,ds[k].value]));
 }catch{return null;}
}
function scope(x:Data):boolean{
 return typeof x.concessionaria_id==='string'&&UUID.test(x.concessionaria_id)&&
  typeof x.phone_number_id==='string'&&PHONE.test(x.phone_number_id)&&
  ['app_ref','waba_ref','case_ref','lead_ref'].every(k=>REF_OK(x[k]));
}
const sameScope=(a:Data,b:Data)=>['concessionaria_id','app_ref','waba_ref',
 'phone_number_id','case_ref','lead_ref'].every(k=>a[k]===b[k]);
function validCase(x:Data):boolean{
 return x.contract_version==='wa21-s0-case-state.lab.v0.1'&&scope(x)&&
  ['case_revision','assignment_revision','handoff_revision','f03_cutoff_revision']
   .every(k=>POS(x[k]))&&
  ['LAB_F01_ACTIVE','LAB_HUMAN_HANDOFF_DEFINITIVE','LAB_HUMAN_CLOSED']
   .includes(x.case_state as string)&&
  typeof x.handoff_ever_definitive==='boolean'&&
  (x.handoff_at_ms===null||INT(x.handoff_at_ms))&&
  (x.human_assignment_ref===null||REF_OK(x.human_assignment_ref))&&
  ['LAB_OPEN','LAB_CLOSED','LAB_UNKNOWN'].includes(x.meta_window_claim as string)&&
  typeof x.opt_out_claim==='boolean'&&INT(x.observed_at_ms)&&
  INT(x.now_ms)&&POS(x.max_age_ms)&&Number(x.max_age_ms)<=300000&&
  x.s0_source_authenticated===false&&x.case_authority_verified===false;
}
function validEvent(e:Data):boolean{
 if(e.contract_version!=='wa21-case-event.lab.v0.1'||!scope(e)||
    !REF_OK(e.event_ref)||typeof e.event_digest!=='string'||
    !SHA.test(e.event_digest)||!INT(e.event_at_ms)||
    e.s0_event_authenticated!==false||e.human_closure_verified!==false||
    !['LAB_INBOUND_MESSAGE','LAB_HUMAN_CLOSURE_EXPLICIT',
      'LAB_META_WINDOW_TIMEOUT','LAB_TEMPLATE_SENT_CLAIM',
      'LAB_HUMAN_MESSAGE_SENT_CLAIM'].includes(e.event_kind as string))
  return false;
 if(e.event_kind==='LAB_HUMAN_CLOSURE_EXPLICIT')
  return REF_OK(e.closure_ref)&&REF_OK(e.actor_ref)&&
   ['CONSULTOR','GESTOR','DIRETOR'].includes(e.actor_role as string)&&
   INT(e.closure_cutoff_ms);
 return e.closure_ref===null&&e.actor_ref===null&&
  e.actor_role===null&&e.closure_cutoff_ms===null;
}
/** A preview is NEVER permission to call F01, F03, Meta, or change S0. */
export function inspectWa21HandoffOffline(rawCase:unknown,rawEvent:unknown):Wa21Result{
 const c=strict(rawCase,CASE_FIELDS),e=strict(rawEvent,EVENT_FIELDS);
 if(!c||!e||!validCase(c)||!validEvent(e))return denied('INVALID_INPUT');
 if(!sameScope(c,e))return denied('SCOPE_MISMATCH');
 if(Number(c.observed_at_ms)>Number(c.now_ms)||
    Number(c.now_ms)-Number(c.observed_at_ms)>Number(c.max_age_ms)||
    Number(e.event_at_ms)>Number(c.observed_at_ms))
  return denied('TIMELINE_INCOHERENT');
 const isActive=c.case_state==='LAB_F01_ACTIVE';
 const hasDef=c.handoff_ever_definitive===true;
 if((isActive&&hasDef)||(!isActive&&!hasDef))
  return denied('DEF_HANDOFF_CANNOT_RESUME_F01');
 if(isActive&&(c.handoff_at_ms!==null||c.human_assignment_ref!==null))
  return denied('DEF_HANDOFF_CANNOT_RESUME_F01');
 if(!isActive&&(!INT(c.handoff_at_ms)||
  !REF_OK(c.human_assignment_ref)||
  Number(c.handoff_at_ms)>Number(c.observed_at_ms)))
  return denied('TIMELINE_INCOHERENT');
 const closure=e.event_kind==='LAB_HUMAN_CLOSURE_EXPLICIT';
 if(closure && c.case_state!=='LAB_HUMAN_CLOSED')
  return denied('CLOSURE_IN_WRONG_STATE');
 if(closure && (Number(e.closure_cutoff_ms)!==Number(e.event_at_ms)||
    Number(e.closure_cutoff_ms)<Number(c.handoff_at_ms)))
  return denied('TIMELINE_INCOHERENT');
 // No Meta event (inbound, timeout, template or human-sent) can trigger F03.
 const decision:Decision=closure?'LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED':
  c.case_state==='LAB_HUMAN_CLOSED'?'LAB_POST_CLOSURE_HOLD':
  c.case_state==='LAB_HUMAN_HANDOFF_DEFINITIVE'?
   'LAB_HUMAN_ROUTE_ONLY_UNVERIFIED':
  e.event_kind==='LAB_INBOUND_MESSAGE'?'LAB_F01_ACTIVE_UNVERIFIED':
   'LAB_NON_CLOSURE_EVENT_HOLD';
 const snap:Wa21Snapshot=Object.freeze({
  contract_version:'wa21-human-handoff-snapshot.lab.v0.1',
  snapshot_sha256:digest(['WA21_HANDOFF_LAB_V0_1',
    CASE_FIELDS.map(k=>c[k]),EVENT_FIELDS.map(k=>e[k]),decision]),
  decision,f01_resume_denied:hasDef,
  f03_requires_explicit_human_closure:true,
  meta_window_is_not_f03_cutoff:true,s0_recheck_required:true,
  ...NEVER,
 });
 return allowed(snap);
}
function validSnapshot(x:Data):boolean{
 return x.contract_version==='wa21-human-handoff-snapshot.lab.v0.1'&&
  typeof x.snapshot_sha256==='string'&&SHA.test(x.snapshot_sha256)&&
  ['LAB_F01_ACTIVE_UNVERIFIED','LAB_HUMAN_ROUTE_ONLY_UNVERIFIED',
   'LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED','LAB_POST_CLOSURE_HOLD',
   'LAB_NON_CLOSURE_EVENT_HOLD'].includes(x.decision as string)&&
  typeof x.f01_resume_denied==='boolean'&&
  x.f03_requires_explicit_human_closure===true&&
  x.meta_window_is_not_f03_cutoff===true&&x.s0_recheck_required===true&&
  Object.keys(NEVER).every(k=>x[k]===false);
}
export function recheckWa21HandoffOffline(
 oldSnapshot:unknown,rawCase:unknown,rawEvent:unknown,
):Wa21Result{
 const old=strict(oldSnapshot,SNAP_FIELDS);
 if(!old||!validSnapshot(old))return denied('PREVIOUS_INVALID');
 const next=inspectWa21HandoffOffline(rawCase,rawEvent);
 if(!next.snapshot)return next;
 if(SNAP_FIELDS.some(k=>old[k]!==next.snapshot![k as keyof Wa21Snapshot]))
  return denied('CONTEXT_CHANGED');
 return allowed(next.snapshot,true);
}
