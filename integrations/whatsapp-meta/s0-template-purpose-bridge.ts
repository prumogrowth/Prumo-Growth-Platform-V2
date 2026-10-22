/**
 * WA-26 — OFFLINE, PROPOSED S0 -> Meta template selection/read contract.
 *
 * Ports in this module are INJECTED LAB FAKES, not an authenticated S0 service.
 * The host must eventually implement identity, tenant RLS, protected state,
 * consent/opt-out, campaign proof and transactional recheck in S0/S1.
 *
 * A positive result never grants Graph dispatch, SQL mutation, HTTP ACK,
 * commercial transitions or production authorization. No external I/O here.
 */
import {
  selectPlannerTemplateCandidates,recheckPlannerTemplateCandidate,
  type PlannerCandidate,type TrustedSelectionContext,type ActorKind,
} from './template-purpose-eligibility.ts';

export type Wa26Phase='PLAN'|'RESERVE'|'PRE_DISPATCH';
export type Wa26Denial='INVALID_INPUT'|'UNTRUSTED_SCOPE'|'POLICY_DENIED'|
  'CATALOG_DENIED'|'STALE_OR_CHANGED'|'DEPENDENCY_UNAVAILABLE';
export type Wa26Scope=Readonly<TrustedSelectionContext & {
  selection_ref:string;
  case_ref:string;
  lead_ref:string;
  case_version:number;
  authorization_revision:number;
}>;
export type Wa26Policy=Readonly<{
  selection_ref:string;
  concessionaria_id:string;
  waba_ref:string;
  case_ref:string;
  lead_ref:string;
  case_version:number;
  authorization_revision:number;
  policy_revision:number;
  /** Claim from an injected privileged FAKE, never from AI or client. */
  consent_state:'VALID'|'UNKNOWN'|'DENIED';
  opted_out:boolean;
  case_authorized:boolean;
  audience_eligible:boolean;
  campaign_eligibility:'NOT_APPLICABLE'|'ELIGIBLE'|'DENIED'|'UNKNOWN';
}>;
export type Wa26FixturePorts=Readonly<{
  /** Future S0: prove principal + case + scoped catalog revision via RLS. */
  resolveSelection(selection_ref:string,phase:Wa26Phase):Promise<unknown>;
  /** Future S0: read the scoped catalog under the verified authority. */
  readScopedCatalog(scope:Wa26Scope,phase:Wa26Phase):Promise<unknown>;
  /** Future S0: re-read case access, consent, opt-out, lead and campaign. */
  readScopedPolicy(scope:Wa26Scope,phase:Wa26Phase):Promise<unknown>;
}>;
export type Wa26InternalTicket=Readonly<{
  contract_version:'wa26-s0-meta.fixture.v0.1';
  phase:Wa26Phase;
  selection_ref:string;
  case_ref:string;
  lead_ref:string;
  case_version:number;
  authorization_revision:number;
  policy_revision:number;
  candidate:PlannerCandidate;
  send_authorized:false;
  production_authorized:false;
}>;
export type Wa26PlanResult=
  | Readonly<{decision:'LAB_CANDIDATES'; candidates:readonly PlannerCandidate[];
      /** Private host-only tickets, NEVER pass to F02/client. */
      internal_tickets:readonly Wa26InternalTicket[];
      send_authorized:false; production_authorized:false}>
  | Readonly<{decision:'DENIED';reason:Wa26Denial; candidates:readonly [];
      internal_tickets:readonly []; send_authorized:false; production_authorized:false}>;
export type Wa26RecheckResult=
  | Readonly<{decision:'LAB_RECHECKED';internal_ticket:Wa26InternalTicket;
      send_authorized:false; production_authorized:false}>
  | Readonly<{decision:'DENIED';reason:Wa26Denial;internal_ticket:null;
      send_authorized:false; production_authorized:false}>;

const REF=/^[A-Za-z0-9_.:-]{1,128}$/;
const LOCALE=/^[a-z]{2,3}(?:_[A-Z]{2})?$/;
const AK:readonly ActorKind[]=['PLANNER','AI_ATTENDANT','CONSULTOR','GESTOR','DIRETOR'];
const SCOPE_KEYS=['selection_ref','concessionaria_id','waba_ref','catalog_revision',
  'language','purpose_ref','actor_kind','actor_ref','flow_ref','campaign_ref',
  'case_ref','lead_ref','case_version','authorization_revision'] as const;
const POLICY_KEYS=['selection_ref','concessionaria_id','waba_ref',
  'case_ref','lead_ref','case_version','authorization_revision','policy_revision',
  'consent_state','opted_out','case_authorized','audience_eligible',
  'campaign_eligibility'] as const;
const TICKET_KEYS=['contract_version','phase','selection_ref','case_ref',
  'lead_ref','case_version','authorization_revision','policy_revision',
  'candidate','send_authorized','production_authorized'] as const;
const CANDIDATE_KEYS=['template_ref','version_ref','catalog_revision',
  'meta_category','purpose_ref','send_authorized','production_authorized'] as const;
const EMPTY_LIST=Object.freeze([]) as readonly [];
const deny=(reason:Wa26Denial):Wa26PlanResult=>Object.freeze({
  decision:'DENIED',reason,candidates:EMPTY_LIST,internal_tickets:EMPTY_LIST,
  send_authorized:false,production_authorized:false,
});
const denyRecheck=(reason:Wa26Denial):Wa26RecheckResult=>Object.freeze({
  decision:'DENIED',reason,internal_ticket:null,
  send_authorized:false,production_authorized:false,
});
const validRef=(x:unknown):x is string=>typeof x==='string'&&REF.test(x);
const positive=(x:unknown):x is number=>typeof x==='number'&&Number.isSafeInteger(x)&&x>0;

/** Copy exact own data keys, no inherited properties or getters. */
function record(v:unknown,keys:readonly string[]):Record<string,unknown>|null{
  try{
    if(v===null||typeof v!=='object'||Array.isArray(v))return null;
    const proto=Object.getPrototypeOf(v);
    if(proto!==Object.prototype&&proto!==null)return null;
    const own=Reflect.ownKeys(v);
    if(own.length!==keys.length||own.some(k=>typeof k!=='string'||!keys.includes(k)))return null;
    const desc=Object.getOwnPropertyDescriptors(v);
    if(keys.some(k=>!Object.hasOwn(desc,k)||!Object.hasOwn(desc[k],'value')))return null;
    return Object.fromEntries(keys.map(k=>[k,desc[k].value]));
  }catch{return null;}
}
function scopeFrom(raw:unknown,request_ref:string):Wa26Scope|null{
  const s=record(raw,SCOPE_KEYS);
  if(!s||s.selection_ref!==request_ref||
    !validRef(s.concessionaria_id)||!validRef(s.waba_ref)||
    !positive(s.catalog_revision)||!positive(s.case_version)||
    !positive(s.authorization_revision)||!validRef(s.case_ref)||
    !validRef(s.lead_ref)||!validRef(s.actor_ref)||!validRef(s.flow_ref)||
    !validRef(s.purpose_ref)||!AK.includes(s.actor_kind as ActorKind)||
    typeof s.language!=='string'||!LOCALE.test(s.language)||
    !(s.campaign_ref===null||validRef(s.campaign_ref)))return null;
  return Object.freeze(s) as Wa26Scope;
}
function policyFrom(raw:unknown,scope:Wa26Scope):Wa26Policy|null{
  const p=record(raw,POLICY_KEYS);
  if(!p||p.selection_ref!==scope.selection_ref||
    p.concessionaria_id!==scope.concessionaria_id||p.waba_ref!==scope.waba_ref||
    p.case_ref!==scope.case_ref||p.lead_ref!==scope.lead_ref||
    p.case_version!==scope.case_version||
    p.authorization_revision!==scope.authorization_revision||
    !positive(p.policy_revision)||
    !['VALID','UNKNOWN','DENIED'].includes(p.consent_state as string)||
    typeof p.opted_out!=='boolean'||typeof p.case_authorized!=='boolean'||
    typeof p.audience_eligible!=='boolean'||
    !['NOT_APPLICABLE','ELIGIBLE','DENIED','UNKNOWN'].includes(p.campaign_eligibility as string))return null;
  return Object.freeze(p) as Wa26Policy;
}
const policyAllows=(p:Wa26Policy,s:Wa26Scope):boolean=>
  p.consent_state==='VALID'&&!p.opted_out&&
  p.case_authorized&&p.audience_eligible&&
  (s.campaign_ref===null
    ?p.campaign_eligibility==='NOT_APPLICABLE'
    :p.campaign_eligibility==='ELIGIBLE');

type Snapshot={scope:Wa26Scope; policy:Wa26Policy; catalog:unknown};
async function read(request_ref:string,phase:Wa26Phase,ports:Wa26FixturePorts):
  Promise<{snapshot:Snapshot}|{reason:Wa26Denial}>{
  if(!validRef(request_ref)||!ports||
    typeof ports.resolveSelection!=='function'||
    typeof ports.readScopedCatalog!=='function'||
    typeof ports.readScopedPolicy!=='function')
    return {reason:'INVALID_INPUT'};
  try{
    const scope=scopeFrom(await ports.resolveSelection(request_ref,phase),request_ref);
    if(!scope)return {reason:'UNTRUSTED_SCOPE'};
    // Host-provided FAKE reads must be independently revalidated on every phase.
    const policy=policyFrom(await ports.readScopedPolicy(scope,phase),scope);
    if(!policy)return {reason:'UNTRUSTED_SCOPE'};
    if(!policyAllows(policy,scope))return {reason:'POLICY_DENIED'};
    const catalog=await ports.readScopedCatalog(scope,phase);
    if(!Array.isArray(catalog))return {reason:'CATALOG_DENIED'};
    return {snapshot:{scope,policy,catalog}};
  }catch{return {reason:'DEPENDENCY_UNAVAILABLE'};}
}
function context(s:Wa26Scope):TrustedSelectionContext{
  return {
    concessionaria_id:s.concessionaria_id,waba_ref:s.waba_ref,
    catalog_revision:s.catalog_revision,language:s.language,
    purpose_ref:s.purpose_ref,actor_kind:s.actor_kind,actor_ref:s.actor_ref,
    flow_ref:s.flow_ref,campaign_ref:s.campaign_ref,
  };
}
function ticket(s:Snapshot,c:PlannerCandidate,phase:Wa26Phase):Wa26InternalTicket{
  return Object.freeze({
    contract_version:'wa26-s0-meta.fixture.v0.1' as const,phase,
    selection_ref:s.scope.selection_ref,case_ref:s.scope.case_ref,
    lead_ref:s.scope.lead_ref,case_version:s.scope.case_version,
    authorization_revision:s.scope.authorization_revision,
    policy_revision:s.policy.policy_revision,
    candidate:c,send_authorized:false as const,production_authorized:false as const,
  });
}
/** PLAN: F02 sees candidates ONLY, never tickets/identity/consent proof. */
export async function prepareS0TemplateCandidatesFixture(
  selection_ref:string,ports:Wa26FixturePorts,
):Promise<Wa26PlanResult>{
  const r=await read(selection_ref,'PLAN',ports);
  if('reason' in r)return deny(r.reason);
  const result=selectPlannerTemplateCandidates(
    r.snapshot.catalog,context(r.snapshot.scope));
  if(result.candidates.length===0)return deny('CATALOG_DENIED');
  return Object.freeze({
    decision:'LAB_CANDIDATES' as const,candidates:result.candidates,
    internal_tickets:Object.freeze(result.candidates.map(c=>ticket(r.snapshot,c,'PLAN'))),
    send_authorized:false as const,production_authorized:false as const,
  });
}
/**
 * RESERVE and PRE_DISPATCH: independently re-read scope, catalog & policy.
 * An unchanged ticket is STILL NOT a send authorization or a lock. Actual
 * execution needs real atomic S0 checks and a separately ratified dispatch.
 */
export async function recheckS0TemplateCandidateFixture(
  rawTicket:unknown,phase:'RESERVE'|'PRE_DISPATCH',
  ports:Wa26FixturePorts,
):Promise<Wa26RecheckResult>{
  try{
    const t=record(rawTicket,TICKET_KEYS);
    const c=record(t?.candidate,CANDIDATE_KEYS);
    if(!t||!c||t.contract_version!=='wa26-s0-meta.fixture.v0.1'||
       !validRef(t.selection_ref)||!validRef(t.case_ref)||!validRef(t.lead_ref)||
       !positive(t.case_version)||!positive(t.authorization_revision)||
       !positive(t.policy_revision)||t.send_authorized!==false||
       t.production_authorized!==false||
       (phase==='RESERVE'?t.phase!=='PLAN':
        phase==='PRE_DISPATCH'?t.phase!=='RESERVE':true))return denyRecheck('INVALID_INPUT');
    const r=await read(t.selection_ref as string,phase,ports);
    if('reason' in r)return denyRecheck(r.reason);
    const {scope,policy,catalog}=r.snapshot;
    if(scope.case_ref!==t.case_ref||scope.lead_ref!==t.lead_ref||
       scope.case_version!==t.case_version||
       scope.authorization_revision!==t.authorization_revision||
       policy.policy_revision!==t.policy_revision)return denyRecheck('STALE_OR_CHANGED');
    if(!recheckPlannerTemplateCandidate(c,catalog,context(scope)))return denyRecheck('CATALOG_DENIED');
    return Object.freeze({
      decision:'LAB_RECHECKED' as const,
      internal_ticket:ticket(r.snapshot,c as PlannerCandidate,phase),
      send_authorized:false as const,production_authorized:false as const,
    });
  }catch{return denyRecheck('DEPENDENCY_UNAVAILABLE');}
}
