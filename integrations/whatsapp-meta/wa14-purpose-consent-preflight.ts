/**
 * WA14 / M14: OFFLINE multi-purpose consent, per-shop suppression and grant
 * coherence. Caller supplies ALL scope, policy and ledger data as UNTRUSTED
 * synthetic fixtures. NO authenticated S0, identity, RLS, DB, Graph, durable
 * version, real consent proof, business approval or PRE_DISPATCH.
 *
 * WA26 checks coarse consent, opt-out, template and campaign fixtures. This
 * module complements WA26 with independent consent-purpose records; it does
 * NOT replace or wire into WA26 and NEVER authorizes sending.
 */
export type Wa14Request=Readonly<{
 contract_version:'wa14-request.lab.v0.1';
 selection_ref:string;concessionaria_id:string;waba_ref:string;
 lead_ref:string;case_ref:string;case_version:number;
 authorization_revision:number;template_ref:string;template_version_ref:string;
 template_purpose_ref:string;consent_purpose_ref:string;
 actor_kind:'PLANNER'|'AI_ATTENDANT'|'CONSULTOR'|'GESTOR'|'DIRETOR';
 actor_ref:string;flow_ref:string;campaign_ref:string|null;
 now_ms:number;max_age_ms:number;
}>;
export type Wa14Consent=Readonly<{
 consent_purpose_ref:string;
 state:'GRANTED'|'DENIED'|'UNKNOWN'|'REVOKED';
 valid_from_ms:number;valid_until_ms:number;revision:number;
}>;
export type Wa14Suppression=Readonly<{
 /** null means shop-wide for this lead; otherwise consent-purpose-scoped. */
 consent_purpose_ref:string|null;active:boolean;revision:number;
}>;
export type Wa14Grant=Readonly<{
 template_ref:string;template_version_ref:string;
 template_purpose_ref:string;consent_purpose_ref:string;
 actor_kind:Wa14Request['actor_kind'];actor_ref:string;
 flow_ref:string;campaign_ref:string|null;
 state:'ACTIVE'|'REVOKED';revision:number;
}>;
export type Wa14Ledger=Readonly<{
 contract_version:'wa14-s0-ledger.lab.v0.1';
 selection_ref:string;concessionaria_id:string;waba_ref:string;
 lead_ref:string;case_ref:string;case_version:number;
 authorization_revision:number;
 policy_revision:number;consent_revision:number;
 suppression_revision:number;grant_revision:number;
 observed_at_ms:number;
 case_authorized:boolean;audience_eligible:boolean;
 campaign_eligibility:'NOT_APPLICABLE'|'ELIGIBLE'|'DENIED'|'UNKNOWN';
 consents:readonly Wa14Consent[];
 suppressions:readonly Wa14Suppression[];
 grants:readonly Wa14Grant[];
}>;
export type Wa14Reason='INVALID_INPUT'|'SCOPE_MISMATCH'|
 'STALE_OR_FUTURE_SNAPSHOT'|'AMBIGUOUS_LEDGER'|'CASE_OR_AUDIENCE_DENIED'|
 'CAMPAIGN_DENIED'|'CONSENT_DENIED'|'SUPPRESSED'|'GRANT_DENIED'|
 'REVISION_OR_CONTEXT_CHANGED';
const FLAGS=Object.freeze({
 consent_verified:false,consent_source_authenticated:false,
 s0_source_authenticated:false,principal_verified:false,
 tenant_binding_verified:false,suppression_source_authenticated:false,
 grant_source_authenticated:false,template_approval_verified:false,
 campaign_authorized:false,send_authorized:false,production_authorized:false,
 s0_write_authorized:false,ack_allowed:false,http_response_authorized:false,
 graph_dispatch_authorized:false,automatic_retry_authorized:false,
});
export type Wa14Result=Readonly<typeof FLAGS & {
 decision:'DENIED'|'LAB_POLICY_COHERENT_UNVERIFIED'|'LAB_RECHECKED_UNVERIFIED';
 reason:Wa14Reason|null;
}>;
const deny=(reason:Wa14Reason):Wa14Result=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
});
const pass=(decision:'LAB_POLICY_COHERENT_UNVERIFIED'|'LAB_RECHECKED_UNVERIFIED'):
 Wa14Result=>Object.freeze({...FLAGS,decision,reason:null});
const REF=/^[A-Za-z0-9_.:-]{1,128}$/;
const ACTORS=['PLANNER','AI_ATTENDANT','CONSULTOR','GESTOR','DIRETOR'];
const CONSENT=['GRANTED','DENIED','UNKNOWN','REVOKED'];
const CAMPAIGN=['NOT_APPLICABLE','ELIGIBLE','DENIED','UNKNOWN'];
const GRANT=['ACTIVE','REVOKED'];
const id=(x:unknown):x is string=>typeof x==='string'&&REF.test(x);
const pos=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>0;
const nonneg=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>=0;
const nullable=(x:unknown):x is string|null=>x===null||id(x);
function record(raw:unknown,keys:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const d=Object.getOwnPropertyDescriptors(raw),own=Reflect.ownKeys(raw);
  if(own.length!==keys.length||own.some(x=>typeof x!=='string'||
     !keys.includes(x)||!Object.hasOwn(d[x],'value'))||
     keys.some(x=>!Object.hasOwn(d,x)))return null;
  return Object.fromEntries(keys.map(x=>[x,d[x].value]));
 }catch{return null;}
}
function dense(raw:unknown,max:number):unknown[]|null{
 try{
  if(!Array.isArray(raw)||Object.getPrototypeOf(raw)!==Array.prototype)
   return null;
  const d=Object.getOwnPropertyDescriptors(raw),len=d.length?.value;
  if(!Number.isSafeInteger(len)||len<0||len>max||
     Reflect.ownKeys(raw).length!==len+1)return null;
  const out:unknown[]=[];
  for(let i=0;i<len;i++){
   const x=d[String(i)];
   if(!x||!Object.hasOwn(x,'value'))return null;
   out.push(x.value);
  }
  return out;
 }catch{return null;}
}
const REQ=['contract_version','selection_ref','concessionaria_id','waba_ref',
 'lead_ref','case_ref','case_version','authorization_revision','template_ref',
 'template_version_ref','template_purpose_ref','consent_purpose_ref',
 'actor_kind','actor_ref','flow_ref','campaign_ref','now_ms','max_age_ms'];
const LEDGER=['contract_version','selection_ref','concessionaria_id','waba_ref',
 'lead_ref','case_ref','case_version','authorization_revision','policy_revision',
 'consent_revision','suppression_revision','grant_revision','observed_at_ms',
 'case_authorized','audience_eligible','campaign_eligibility','consents',
 'suppressions','grants'];
const CONSENT_FIELDS=['consent_purpose_ref','state','valid_from_ms',
 'valid_until_ms','revision'];
const SUPPRESSION_FIELDS=['consent_purpose_ref','active','revision'];
const GRANT_FIELDS=['template_ref','template_version_ref',
 'template_purpose_ref','consent_purpose_ref','actor_kind','actor_ref',
 'flow_ref','campaign_ref','state','revision'];
const MATCH=['selection_ref','concessionaria_id','waba_ref','lead_ref',
 'case_ref','case_version','authorization_revision'] as const;
const VERSIONS=['policy_revision','consent_revision','suppression_revision',
 'grant_revision'] as const;
function request(raw:unknown):Wa14Request|null{
 const x=record(raw,REQ);
 if(!x||x.contract_version!=='wa14-request.lab.v0.1'||
    !['selection_ref','concessionaria_id','waba_ref','lead_ref',
      'case_ref','template_ref','template_version_ref',
      'template_purpose_ref','consent_purpose_ref',
      'actor_ref','flow_ref'].every(k=>id(x[k]))||
    !pos(x.case_version)||!pos(x.authorization_revision)||
    !ACTORS.includes(x.actor_kind as string)||!nullable(x.campaign_ref)||
    !nonneg(x.now_ms)||!pos(x.max_age_ms)||x.max_age_ms>300000)
  return null;
 return x as Wa14Request;
}
function ledger(raw:unknown):Wa14Ledger|null{
 const x=record(raw,LEDGER);
 if(!x||x.contract_version!=='wa14-s0-ledger.lab.v0.1'||
    !['selection_ref','concessionaria_id','waba_ref','lead_ref',
      'case_ref'].every(k=>id(x[k]))||
    !pos(x.case_version)||!pos(x.authorization_revision)||
    !VERSIONS.every(k=>pos(x[k]))||!nonneg(x.observed_at_ms)||
    typeof x.case_authorized!=='boolean'||
    typeof x.audience_eligible!=='boolean'||
    !CAMPAIGN.includes(x.campaign_eligibility as string))return null;
 const consents=dense(x.consents,100),suppressions=dense(x.suppressions,100),
  grants=dense(x.grants,200);
 if(!consents||!suppressions||!grants)return null;
 const seenConsents=new Set<string>(),seenSuppressions=new Set<string>(),
  seenGrants=new Set<string>();
 const consentData:Wa14Consent[]=[],suppressionData:Wa14Suppression[]=[],
  grantData:Wa14Grant[]=[];
 for(const rawConsent of consents){
  const c=record(rawConsent,CONSENT_FIELDS);
  if(!c||!id(c.consent_purpose_ref)||!CONSENT.includes(c.state as string)||
     !nonneg(c.valid_from_ms)||!pos(c.valid_until_ms)||
     c.valid_until_ms<=c.valid_from_ms||!pos(c.revision)||
     c.revision>x.consent_revision||seenConsents.has(c.consent_purpose_ref))
   return null;
  seenConsents.add(c.consent_purpose_ref);
  consentData.push(c as Wa14Consent);
 }
 for(const rawSuppression of suppressions){
  const s=record(rawSuppression,SUPPRESSION_FIELDS);
  if(!s||!nullable(s.consent_purpose_ref)||
     typeof s.active!=='boolean'||!pos(s.revision)||
     s.revision>x.suppression_revision)return null;
  const k=JSON.stringify([s.consent_purpose_ref]);
  if(seenSuppressions.has(k))return null;
  seenSuppressions.add(k);suppressionData.push(s as Wa14Suppression);
 }
 for(const rawGrant of grants){
  const g=record(rawGrant,GRANT_FIELDS);
  if(!g||!['template_ref','template_version_ref','template_purpose_ref',
      'consent_purpose_ref','actor_ref','flow_ref'].every(k=>id(g[k]))||
     !ACTORS.includes(g.actor_kind as string)||!nullable(g.campaign_ref)||
     !GRANT.includes(g.state as string)||!pos(g.revision)||
     g.revision>x.grant_revision)return null;
  const k=JSON.stringify([g.template_ref,g.template_version_ref,
   g.template_purpose_ref,g.consent_purpose_ref,g.actor_kind,
   g.actor_ref,g.flow_ref,g.campaign_ref]);
  if(seenGrants.has(k))return null;
  seenGrants.add(k);grantData.push(g as Wa14Grant);
 }
 return {...x,consents:consentData,suppressions:suppressionData,
  grants:grantData} as Wa14Ledger;
}
function evaluate(req:Wa14Request,snap:Wa14Ledger):Wa14Result{
 if(MATCH.some(k=>req[k]!==snap[k]))return deny('SCOPE_MISMATCH');
 if(snap.observed_at_ms>req.now_ms||
    req.now_ms-snap.observed_at_ms>req.max_age_ms)
  return deny('STALE_OR_FUTURE_SNAPSHOT');
 if(!snap.case_authorized||!snap.audience_eligible)
  return deny('CASE_OR_AUDIENCE_DENIED');
 if(req.campaign_ref===null
   ?snap.campaign_eligibility!=='NOT_APPLICABLE'
   :snap.campaign_eligibility!=='ELIGIBLE')
  return deny('CAMPAIGN_DENIED');
 const grant=snap.grants.find(g=>
  g.template_ref===req.template_ref&&
  g.template_version_ref===req.template_version_ref&&
  g.template_purpose_ref===req.template_purpose_ref&&
  g.consent_purpose_ref===req.consent_purpose_ref&&
  g.actor_kind===req.actor_kind&&g.actor_ref===req.actor_ref&&
  g.flow_ref===req.flow_ref&&g.campaign_ref===req.campaign_ref);
 if(!grant||grant.state!=='ACTIVE')return deny('GRANT_DENIED');
 if(snap.suppressions.some(s=>s.active&&
    (s.consent_purpose_ref===null||
     s.consent_purpose_ref===req.consent_purpose_ref)))
  return deny('SUPPRESSED');
 const consent=snap.consents.find(c=>
  c.consent_purpose_ref===req.consent_purpose_ref);
 if(!consent||consent.state!=='GRANTED'||
    consent.valid_from_ms>req.now_ms||
    consent.valid_until_ms<=req.now_ms)
  return deny('CONSENT_DENIED');
 return pass('LAB_POLICY_COHERENT_UNVERIFIED');
}
/** All records are cloned from own DATA descriptors before any evaluation.
 * An apparent match is only a consistency exercise, NEVER consent proof. */
export function inspectWa14ConsentOffline(
 rawRequest:unknown,rawLedger:unknown,
):Wa14Result{
 try{
  const req=request(rawRequest),snap=ledger(rawLedger);
  if(!req||!snap)return deny('INVALID_INPUT');
  return evaluate(req,snap);
 }catch{return deny('INVALID_INPUT');}
}
/** Independent synthetic read comparison; no lock, identity or reservation.
 * Revision changes require a new candidate, never automatic continuation.
 * Even identical reads can miss an ABA change or a later revocation. */
export function recheckWa14ConsentOffline(
 initialRequest:unknown,initialLedger:unknown,
 freshRequest:unknown,freshLedger:unknown,
):Wa14Result{
 try{
  const beforeReq=request(initialRequest),before=ledger(initialLedger),
   nowReq=request(freshRequest),now=ledger(freshLedger);
  if(!beforeReq||!before||!nowReq||!now)
   return deny('INVALID_INPUT');
  const initial=evaluate(beforeReq,before);
  if(initial.decision==='DENIED')return initial;
  // Only the trusted LAB clock is allowed to advance on a recheck. Neither
  // actor, lead, case, selected purpose nor max-age can change implicitly.
  if(REQ.some(k=>k!=='now_ms'&&beforeReq[k as keyof Wa14Request]!==
     nowReq[k as keyof Wa14Request])||
     nowReq.now_ms<beforeReq.now_ms||
     now.observed_at_ms<before.observed_at_ms||
     VERSIONS.some(k=>before[k]!==now[k]))
   return deny('REVISION_OR_CONTEXT_CHANGED');
  const current=evaluate(nowReq,now);
  if(current.decision==='DENIED')return current;
  return pass('LAB_RECHECKED_UNVERIFIED');
 }catch{return deny('INVALID_INPUT');}
}
