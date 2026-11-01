/**
 * M18: offline reconciliation of an S0 PG17 LAB reservation with a prospective
 * Graph dispatch candidate. Absolutely NO network, tokens, vault, send, SQL,
 * "redeem" lease, ACK or authority acquisition. This module is not a sender.
 *
 * S0 candidate prumo.s0.pre-dispatch.pg17/0.1-lab-only is a synthetic ADMIN
 * PostgreSQL reservation: its success cannot grant external dispatch.
 * The extra scoped binding and rate budget are ALSO host-injected fixtures.
 */
import {createHash} from 'node:crypto';
import {classifyGraphSendResult} from './graph-outbound.ts';

export type Wa18Intent=Readonly<{
 contract_version:'wa18-dispatch-intent.lab.v0.1';
 selection_ref:string;attempt_ref:string;intent_ref:string;
 concessionaria_id:string;app_ref:string;waba_id:string;
 phone_number_id:string;case_ref:string;service_ref:string;
 template_ref:string;template_version_ref:string;
 template_purpose_ref:string;consent_purpose_ref:string;
 campaign_ref:string;plan_revision:number;
 case_revision:number;assignment_revision:number;policy_revision:number;
 suppression_revision:number;consent_revision:number;
 template_revision:number;campaign_revision:number;grant_revision:number;
 registry_revision:number;content_sha256:string;recipient_sha256:string;
 now_ms:number;max_age_ms:number;
}>;
export type Wa18S0Lab=Readonly<{
 contract_version:'prumo.s0.pre-dispatch.pg17/0.1-lab-only';
 decision:'LAB_RESERVATION_RECORDED_NO_DISPATCH'|'DENIED'|'UNAVAILABLE';
 reason:string|null;lab_reservation_recorded:boolean;
 send_authorized:false;graph_authorized:false;
 credential_resolution_authorized:false;
 pre_dispatch_operationally_authorized:false;
 provider_approval_verified:false;consent_proven_from_real_source:false;
 external_http_ack:false;production_authorized:false;
 commercial_transition_authorized:false;
}>;
export type Wa18Binding=Readonly<{
 contract_version:'wa18-s0-binding-claim.lab.v0.1';
 selection_ref:string;attempt_ref:string;intent_ref:string;
 concessionaria_id:string;app_ref:string;waba_id:string;
 phone_number_id:string;case_ref:string;service_ref:string;
 template_ref:string;template_version_ref:string;
 template_purpose_ref:string;consent_purpose_ref:string;
 campaign_ref:string;plan_revision:number;
 case_revision:number;assignment_revision:number;policy_revision:number;
 suppression_revision:number;consent_revision:number;
 template_revision:number;campaign_revision:number;grant_revision:number;
 registry_revision:number;content_sha256:string;recipient_sha256:string;
 reservation_state:'LAB_HELD_NO_DISPATCH';
 commit_state:'LAB_COMMIT_CLAIMED';observed_at_ms:number;
}>;
export type Wa18Rate=Readonly<{
 contract_version:'wa18-rate-budget.lab.v0.1';
 concessionaria_id:string;app_ref:string;phone_number_id:string;
 rate_revision:number;observed_at_ms:number;
 available_slots:number;throttled_until_ms:number|null;
 budget_state:'LAB_AVAILABLE'|'LAB_THROTTLED'|'LAB_UNKNOWN';
}>;
export type Wa18Candidate=Readonly<{
 contract_version:'wa18-dispatch-preview.lab.v0.1';
 candidate_sha256:string;scope_sha256:string;
 rate_revision:number;registry_revision:number;
 rate_budget_evaluated:true;reservation_claim_coherent:true;
 requires_s0_recheck:true;requires_independent_commit_readback:true;
 s0_source_authenticated:false;reservation_committed_verified:false;
 credential_resolution_authorized:false;graph_dispatch_authorized:false;
 send_authorized:false;production_authorized:false;
 automatic_retry_authorized:false;ack_allowed:false;
}>;
export type Wa18Reason='INVALID_INPUT'|'S0_LAB_NOT_ACCEPTABLE'|
 'BINDING_SCOPE_CHANGED'|'RESERVATION_NOT_REDEEMABLE'|
 'RATE_LIMIT_OR_UNKNOWN'|'SNAPSHOT_STALE_OR_FUTURE'|
 'PREVIOUS_CANDIDATE_INVALID'|'REVISION_OR_CONTEXT_CHANGED';
export type Wa18Result=Readonly<{
 decision:'DENIED'|'LAB_DISPATCH_COHERENT_NOT_AUTHORIZED'|
 'LAB_RECHECKED_NOT_AUTHORIZED';
 reason:Wa18Reason|null;candidate:Wa18Candidate|null;
 graph_dispatch_authorized:false;send_authorized:false;
 production_authorized:false;automatic_retry_authorized:false;
}>;
const K_INTENT=['contract_version','selection_ref','attempt_ref','intent_ref',
 'concessionaria_id','app_ref','waba_id','phone_number_id','case_ref',
 'service_ref','template_ref','template_version_ref','template_purpose_ref',
 'consent_purpose_ref','campaign_ref','plan_revision','case_revision',
 'assignment_revision','policy_revision','suppression_revision',
 'consent_revision','template_revision','campaign_revision','grant_revision',
 'registry_revision','content_sha256','recipient_sha256','now_ms','max_age_ms'] as const;
const K_LAB=['contract_version','decision','reason','lab_reservation_recorded',
 'send_authorized','graph_authorized','credential_resolution_authorized',
 'pre_dispatch_operationally_authorized','provider_approval_verified',
 'consent_proven_from_real_source','external_http_ack','production_authorized',
 'commercial_transition_authorized'] as const;
const K_BIND=[...K_INTENT.filter(x=>x!=='now_ms'&&x!=='max_age_ms'),
 'reservation_state','commit_state','observed_at_ms'] as const;
const K_RATE=['contract_version','concessionaria_id','app_ref',
 'phone_number_id','rate_revision','observed_at_ms','available_slots',
 'throttled_until_ms','budget_state'] as const;
const K_CAND=['contract_version','candidate_sha256','scope_sha256',
 'rate_revision','registry_revision','rate_budget_evaluated',
 'reservation_claim_coherent','requires_s0_recheck',
 'requires_independent_commit_readback','s0_source_authenticated',
 'reservation_committed_verified','credential_resolution_authorized',
 'graph_dispatch_authorized','send_authorized','production_authorized',
 'automatic_retry_authorized','ack_allowed'] as const;
const REF=/^[A-Za-z0-9_.:-]{1,128}$/,PHONE=/^\d{5,25}$/,
 HEX=/^[a-f0-9]{64}$/;
const ids=['selection_ref','attempt_ref','intent_ref','app_ref','case_ref',
 'service_ref','template_ref','template_version_ref','template_purpose_ref',
 'consent_purpose_ref','campaign_ref'] as const;
const refs=['plan_revision','case_revision','assignment_revision',
 'policy_revision','suppression_revision','consent_revision',
 'template_revision','campaign_revision','grant_revision',
 'registry_revision'] as const;
const scope=[...ids,'concessionaria_id','waba_id','phone_number_id',
 ...refs,'content_sha256','recipient_sha256'] as const;
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const positive=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>0;
const nonneg=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>=0;
function own(raw:unknown,keys:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const ds=Object.getOwnPropertyDescriptors(raw),names=Reflect.ownKeys(raw);
  if(names.length!==keys.length||names.some(k=>
   typeof k!=='string'||!keys.includes(k)||
   !Object.hasOwn(ds[k],'value'))||
   keys.some(k=>!Object.hasOwn(ds,k)))return null;
  return Object.fromEntries(keys.map(k=>[k,ds[k].value]));
 }catch{return null;}
}
const hash=(x:unknown):string=>
 createHash('sha256').update(JSON.stringify(x),'utf8').digest('hex');
const FLAGS=Object.freeze({graph_dispatch_authorized:false,
 send_authorized:false,production_authorized:false,
 automatic_retry_authorized:false} as const);
const deny=(reason:Wa18Reason):Wa18Result=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,candidate:null,
});
function validIntent(i:Record<string,unknown>):boolean{
 return i.contract_version==='wa18-dispatch-intent.lab.v0.1'&&
  ids.every(k=>typeof i[k]==='string'&&REF.test(i[k]))&&
  typeof i.concessionaria_id==='string'&&uuid.test(i.concessionaria_id)&&
  typeof i.waba_id==='string'&&REF.test(i.waba_id)&&
  typeof i.phone_number_id==='string'&&PHONE.test(i.phone_number_id)&&
  refs.every(k=>positive(i[k]))&&
  typeof i.content_sha256==='string'&&HEX.test(i.content_sha256)&&
  typeof i.recipient_sha256==='string'&&HEX.test(i.recipient_sha256)&&
  nonneg(i.now_ms)&&positive(i.max_age_ms)&&i.max_age_ms<=300000;
}
function validS0(x:Record<string,unknown>):boolean{
 if(x.contract_version!=='prumo.s0.pre-dispatch.pg17/0.1-lab-only'||
    !['LAB_RESERVATION_RECORDED_NO_DISPATCH','DENIED','UNAVAILABLE']
      .includes(x.decision as string))return false;
 return K_LAB.filter(k=>k!=='contract_version'&&k!=='decision'&&
   k!=='reason'&&k!=='lab_reservation_recorded')
   .every(k=>x[k]===false)&&
   (x.reason===null||(typeof x.reason==='string'&&REF.test(x.reason)))&&
   x.lab_reservation_recorded===
    (x.decision==='LAB_RESERVATION_RECORDED_NO_DISPATCH');
}
function validBinding(b:Record<string,unknown>,i:Record<string,unknown>):boolean{
 return b.contract_version==='wa18-s0-binding-claim.lab.v0.1'&&
  b.reservation_state==='LAB_HELD_NO_DISPATCH'&&
  b.commit_state==='LAB_COMMIT_CLAIMED'&&
  nonneg(b.observed_at_ms)&&
  scope.every(k=>b[k]===i[k]);
}
function validRate(r:Record<string,unknown>,i:Record<string,unknown>):boolean{
 return r.contract_version==='wa18-rate-budget.lab.v0.1'&&
  r.concessionaria_id===i.concessionaria_id&&r.app_ref===i.app_ref&&
  r.phone_number_id===i.phone_number_id&&
  positive(r.rate_revision)&&nonneg(r.observed_at_ms)&&
  nonneg(r.available_slots)&&r.available_slots<=100000&&
  (r.throttled_until_ms===null||nonneg(r.throttled_until_ms))&&
  ['LAB_AVAILABLE','LAB_THROTTLED','LAB_UNKNOWN'].includes(
   r.budget_state as string);
}
function validCandidate(x:Record<string,unknown>):boolean{
 return x.contract_version==='wa18-dispatch-preview.lab.v0.1'&&
  typeof x.candidate_sha256==='string'&&HEX.test(x.candidate_sha256)&&
  typeof x.scope_sha256==='string'&&HEX.test(x.scope_sha256)&&
  positive(x.rate_revision)&&positive(x.registry_revision)&&
  x.rate_budget_evaluated===true&&
  x.reservation_claim_coherent===true&&
  x.requires_s0_recheck===true&&
  x.requires_independent_commit_readback===true&&
  ['s0_source_authenticated','reservation_committed_verified',
  'credential_resolution_authorized','graph_dispatch_authorized',
  'send_authorized','production_authorized',
  'automatic_retry_authorized','ack_allowed'].every(k=>x[k]===false);
}
function candidate(i:Record<string,unknown>,rate:Record<string,unknown>):Wa18Candidate{
 const scopeSha=hash(['WA18_SCOPE_LAB_V0_1',scope.map(k=>i[k])]);
 const candidateSha=hash(['WA18_DISPATCH_NO_AUTH_V0_1',scopeSha,
  rate.rate_revision,rate.available_slots,rate.throttled_until_ms,
  rate.budget_state]);
 return Object.freeze({
  contract_version:'wa18-dispatch-preview.lab.v0.1',
  candidate_sha256:candidateSha,scope_sha256:scopeSha,
  rate_revision:rate.rate_revision as number,
  registry_revision:i.registry_revision as number,
  rate_budget_evaluated:true,reservation_claim_coherent:true,
  requires_s0_recheck:true,requires_independent_commit_readback:true,
  s0_source_authenticated:false,reservation_committed_verified:false,
  credential_resolution_authorized:false,graph_dispatch_authorized:false,
  send_authorized:false,production_authorized:false,
  automatic_retry_authorized:false,ack_allowed:false,
 });
}
/** All four inputs are synchronous, independent, untrusted LAB assertions.
 * Even the positive result explicitly refuses Graph, vault and retries. */
export function inspectWa18DispatchOffline(
 rawIntent:unknown,rawS0:unknown,rawBinding:unknown,rawRate:unknown,
):Wa18Result{
 const i=own(rawIntent,K_INTENT),s0=own(rawS0,K_LAB),
  binding=own(rawBinding,K_BIND),rate=own(rawRate,K_RATE);
 if(!i||!s0||!binding||!rate||!validIntent(i)||!validS0(s0))
  return deny('INVALID_INPUT');
 if(s0.decision!=='LAB_RESERVATION_RECORDED_NO_DISPATCH')
  return deny('S0_LAB_NOT_ACCEPTABLE');
 if(!validBinding(binding,i))return deny('BINDING_SCOPE_CHANGED');
 if(!validRate(rate,i))return deny('RATE_LIMIT_OR_UNKNOWN');
 if(binding.commit_state!=='LAB_COMMIT_CLAIMED'||
    binding.reservation_state!=='LAB_HELD_NO_DISPATCH')
  return deny('RESERVATION_NOT_REDEEMABLE');
 const now=i.now_ms as number,age=i.max_age_ms as number;
 if(binding.observed_at_ms!>now||now-(binding.observed_at_ms as number)>age||
    rate.observed_at_ms!>now||now-(rate.observed_at_ms as number)>age)
  return deny('SNAPSHOT_STALE_OR_FUTURE');
 if(rate.budget_state!=='LAB_AVAILABLE'||rate.available_slots===0||
    rate.throttled_until_ms!==null)
  return deny('RATE_LIMIT_OR_UNKNOWN');
 return Object.freeze({...FLAGS,
  decision:'LAB_DISPATCH_COHERENT_NOT_AUTHORIZED',
  reason:null,candidate:candidate(i,rate)});
}
/** Rechecks exact same scoped request against fresh LAB data. It is NOT S0
 * transactional PRE_DISPATCH and never obtains an external send lease. */
export function recheckWa18DispatchOffline(
 rawPrevious:unknown,rawIntent:unknown,
 rawS0:unknown,rawBinding:unknown,rawRate:unknown,
):Wa18Result{
 const p=own(rawPrevious,K_CAND);
 if(!p||!validCandidate(p))return deny('PREVIOUS_CANDIDATE_INVALID');
 const current=inspectWa18DispatchOffline(rawIntent,rawS0,rawBinding,rawRate);
 if(current.decision==='DENIED')return current;
 if(!current.candidate||K_CAND.some(k=>current.candidate![k]!==p[k]))
  return deny('REVISION_OR_CONTEXT_CHANGED');
 return Object.freeze({...FLAGS,decision:'LAB_RECHECKED_NOT_AUTHORIZED',
  reason:null,candidate:current.candidate});
}
export type Wa18GraphLabResult=Readonly<{
 decision:'LAB_API_ACCEPTED_NOT_SENT'|'LAB_PROVIDER_REJECTED_UNVERIFIED'|
  'LAB_EXTERNAL_UNCERTAIN'|'DENIED';
 attempt_correlation_valid:boolean;provider_status_verified:false;
 sent_verified:false;delivered_verified:false;read_verified:false;
 retry_external:false;graph_dispatch_authorized:false;
 production_authorized:false;commercial_transition_authorized:false;
}>;
function graphAnswer(
 decision:Wa18GraphLabResult['decision'],correlated:boolean,
):Wa18GraphLabResult{
 return Object.freeze({decision,attempt_correlation_valid:correlated,
  provider_status_verified:false,sent_verified:false,
  delivered_verified:false,read_verified:false,
  retry_external:false,graph_dispatch_authorized:false,
  production_authorized:false,commercial_transition_authorized:false});
}
/** Classification of an INJECTED mock observation only, never transport.
 * API 2xx/wamid does not prove sent, and timeout never authorizes resend. */
export function classifyWa18GraphMockOffline(
 rawIntent:unknown,rawObservation:unknown,
):Wa18GraphLabResult{
 const i=own(rawIntent,K_INTENT);
 if(!i||!validIntent(i))return graphAnswer('DENIED',false);
 const o=own(rawObservation,['kind','http_status','response_json'])||
  own(rawObservation,['kind']);
 if(!o)return graphAnswer('DENIED',false);
 if(o.kind!=='transport_error'&&o.kind!=='http_response')
  return graphAnswer('DENIED',false);
 if(o.kind==='transport_error')
  return graphAnswer('LAB_EXTERNAL_UNCERTAIN',true);
 try{
  const classified=classifyGraphSendResult(
   i.attempt_ref as string,i.intent_ref as string,
   {kind:'http_response',http_status:o.http_status as number,
    response_json:o.response_json});
  return graphAnswer(
   classified.send_state==='API_ACCEPTED'?'LAB_API_ACCEPTED_NOT_SENT':
   classified.send_state==='PROVIDER_REJECTED'?
    'LAB_PROVIDER_REJECTED_UNVERIFIED':'LAB_EXTERNAL_UNCERTAIN',true);
 }catch{return graphAnswer('DENIED',false);}
}
