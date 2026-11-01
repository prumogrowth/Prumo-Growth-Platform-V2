/**
 * M15 / WA15: OFFLINE rehearsal of a MINIMAL F02 planning preview.
 * Everything is injected LAB data, not authenticated S0, real Meta, consent
 * or an approved F02 wire contract. This code NEVER creates a dispatch.
 *
 * WA26 tests coarse S0 policy and purpose grants; M13 checks template identity,
 * version and components; M14 tests purpose-specific consent and suppression.
 * Only mutually consistent candidates are exposed. Private WA26 tickets,
 * case, lead, actor, consent details, WABA and component digests are NOT output.
 * F02 cannot infer permission, approval or delivery from this preview.
 */
import {isDeepStrictEqual} from 'node:util';
import {prepareS0TemplateCandidatesFixture,
 type Wa26FixturePorts,type Wa26Scope,type Wa26Phase} from
 './s0-template-purpose-bridge.ts';
import {reconcileWa13CatalogOffline,type Wa13Candidate} from
 './wa13-template-catalog-reconciliation.ts';
import {inspectWa14ConsentOffline} from './wa14-purpose-consent-preflight.ts';

export type Wa15Request=Readonly<{
 contract_version:'wa15-f02-planning-request.lab.v0.1';
 selection_ref:string;concessionaria_id:string;app_ref:string;waba_id:string;
 catalog_revision:number;language:string;purpose_ref:string;
 consent_purpose_ref:string;
 actor_kind:'PLANNER'|'AI_ATTENDANT'|'CONSULTOR'|'GESTOR'|'DIRETOR';
 actor_ref:string;flow_ref:string;campaign_ref:string|null;
 case_ref:string;lead_ref:string;case_version:number;
 authorization_revision:number;plan_revision:number;
 now_ms:number;max_age_ms:number;
}>;
export type Wa15PreviewCandidate=Readonly<{
 template_ref:string;version_ref:string;catalog_revision:number;
 meta_category:'UTILITY'|'MARKETING';purpose_ref:string;
 send_authorized:false;production_authorized:false;
 requires_s0_recheck:true;
}>;
export type Wa15PlannerPreview=Readonly<{
 contract_version:'wa15-f02-preview.lab.v0.1';
 planning_flow_ref:string;campaign_ref:string|null;
 plan_revision:number;catalog_revision:number;
 candidates:readonly Wa15PreviewCandidate[];
 send_authorized:false;production_authorized:false;
 meta_approval_verified:false;consent_verified:false;
 s0_source_authenticated:false;graph_dispatch_authorized:false;
 requires_s0_recheck:true;provider_sync_performed:false;
}>;
export type Wa15Reason='INVALID_REQUEST'|'UNTRUSTED_SCOPE'|
 'WA26_POLICY_OR_CATALOG_DENIED'|'M13_CATALOG_DENIED'|
 'CATALOG_VERSION_OR_SCOPE_MISMATCH'|'M14_CONSENT_OR_GRANT_DENIED'|
 'AMBIGUOUS_CANDIDATES'|'DEPENDENCY_UNAVAILABLE'|
 'INPUT_CHANGED_DURING_PREVIEW';
export type Wa15Result=Readonly<{
 decision:'DENIED'|'LAB_F02_PREVIEW_UNVERIFIED';reason:Wa15Reason|null;
 preview:Wa15PlannerPreview|null;send_authorized:false;
 production_authorized:false;graph_dispatch_authorized:false;
 s0_source_authenticated:false;
}>;
const REQ=['contract_version','selection_ref','concessionaria_id',
 'app_ref','waba_id','catalog_revision','language','purpose_ref',
 'consent_purpose_ref','actor_kind','actor_ref','flow_ref','campaign_ref',
 'case_ref','lead_ref','case_version','authorization_revision',
 'plan_revision','now_ms','max_age_ms'] as const;
const SCOPE=['selection_ref','concessionaria_id','waba_ref',
 'catalog_revision','language','purpose_ref','actor_kind','actor_ref',
 'flow_ref','campaign_ref','case_ref','lead_ref',
 'case_version','authorization_revision'] as const;
const POLICY=['selection_ref','concessionaria_id','waba_ref','case_ref',
 'lead_ref','case_version','authorization_revision','policy_revision',
 'consent_state','opted_out','case_authorized','audience_eligible',
 'campaign_eligibility'] as const;
const LEDGER=['contract_version','selection_ref','concessionaria_id',
 'waba_ref','lead_ref','case_ref','case_version','authorization_revision',
 'policy_revision','consent_revision','suppression_revision',
 'grant_revision','observed_at_ms','case_authorized',
 'audience_eligible','campaign_eligibility','consents',
 'suppressions','grants'] as const;
const REF=/^[A-Za-z0-9_.:-]{1,128}$/,WABA=/^[0-9]{5,25}$/,
 LOCALE=/^[a-z]{2,3}(?:_[A-Z]{2})?$/;
const ACTORS=['PLANNER','AI_ATTENDANT','CONSULTOR','GESTOR','DIRETOR'];
const ref=(x:unknown):x is string=>typeof x==='string'&&REF.test(x);
const pos=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>0;
const nonneg=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>=0;
function own(raw:unknown,keys:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const d=Object.getOwnPropertyDescriptors(raw),k=Reflect.ownKeys(raw);
  if(k.length!==keys.length||k.some(x=>typeof x!=='string'||
     !keys.includes(x)||!Object.hasOwn(d[x],'value'))||
     keys.some(x=>!Object.hasOwn(d,x)))return null;
  return Object.fromEntries(keys.map(x=>[x,d[x].value]));
 }catch{return null;}
}
/** Clone own DATA descriptors into immutable LAB snapshots. Never execute
 * getters, proxies' value hooks or toJSON; no external data is authenticated.
 * Bound depth and node count avoid accidental fixture resource exhaustion.
 * Compare against re-cloned original inputs at exit to detect drift across
 * async WA26 ports. This is NOT a transaction or ABA defense. */
function cloneLabData(
 raw:unknown,budget:{left:number}={left:30000},
 depth=0,ancestors=new WeakSet<object>(),
):any{
 if(--budget.left<0||depth>32)throw Error('LAB_LIMIT');
 if(raw===null||typeof raw==='string'||typeof raw==='boolean'||
    raw===undefined)return raw;
 if(typeof raw==='number'&&Number.isFinite(raw))return raw;
 if(typeof raw!=='object')throw Error('INVALID_LAB_VALUE');
 if(ancestors.has(raw))throw Error('CYCLIC_LAB_VALUE');
 const array=Array.isArray(raw),proto=Object.getPrototypeOf(raw);
 if(array?proto!==Array.prototype:
   proto!==Object.prototype&&proto!==null)throw Error('INVALID_LAB_PROTO');
 const d=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
 if(keys.some(k=>typeof k!=='string'))throw Error('INVALID_LAB_SYMBOL');
 if(array){
  const len=d.length?.value;
  if(!Number.isSafeInteger(len)||len<0||len>10000||
     keys.length!==len+1||
     Array.from({length:len},(_,i)=>String(i)).some(k=>
      !Object.hasOwn(d,k)||!Object.hasOwn(d[k],'value')))
   throw Error('INVALID_LAB_ARRAY');
 }else if(keys.length>10000)throw Error('INVALID_LAB_OBJECT');
 const copy:any=array?[]:Object.create(proto);
 ancestors.add(raw);
 for(const key of keys){
  if(array&&key==='length')continue;
  if(!Object.hasOwn(d[key],'value'))throw Error('INVALID_LAB_ACCESSOR');
  Object.defineProperty(copy,key,{
   value:cloneLabData(d[key].value,budget,depth+1,ancestors),
   enumerable:true,writable:false,configurable:false,
  });
 }
 ancestors.delete(raw);
 return Object.freeze(copy);
}
function request(raw:unknown):Wa15Request|null{
 const x=own(raw,REQ);
 if(!x||x.contract_version!=='wa15-f02-planning-request.lab.v0.1'||
    !['selection_ref','concessionaria_id','app_ref','purpose_ref',
      'consent_purpose_ref','actor_ref','flow_ref','case_ref','lead_ref']
      .every(k=>ref(x[k]))||
    typeof x.waba_id!=='string'||!WABA.test(x.waba_id)||
    typeof x.language!=='string'||!LOCALE.test(x.language)||
    !ACTORS.includes(x.actor_kind as string)||
    !(x.campaign_ref===null||ref(x.campaign_ref))||
    !pos(x.catalog_revision)||!pos(x.case_version)||
    !pos(x.authorization_revision)||!pos(x.plan_revision)||
    !nonneg(x.now_ms)||!pos(x.max_age_ms)||x.max_age_ms>300000)
   return null;
 return x as Wa15Request;
}
const NO=Object.freeze({send_authorized:false,production_authorized:false,
 graph_dispatch_authorized:false,s0_source_authenticated:false} as const);
const deny=(reason:Wa15Reason):Wa15Result=>Object.freeze({
 ...NO,decision:'DENIED' as const,reason,preview:null,
});
function scopeMatches(raw:unknown,q:Wa15Request):boolean{
 const s=own(raw,SCOPE);
 return !!s&&s.selection_ref===q.selection_ref&&
  s.concessionaria_id===q.concessionaria_id&&s.waba_ref===q.waba_id&&
  s.catalog_revision===q.catalog_revision&&s.language===q.language&&
  s.purpose_ref===q.purpose_ref&&s.actor_kind===q.actor_kind&&
  s.actor_ref===q.actor_ref&&s.flow_ref===q.flow_ref&&
  s.campaign_ref===q.campaign_ref&&s.case_ref===q.case_ref&&
  s.lead_ref===q.lead_ref&&s.case_version===q.case_version&&
  s.authorization_revision===q.authorization_revision;
}
const S0_KEYS=['selection_ref','concessionaria_id','waba_ref','lead_ref',
 'case_ref','case_version','authorization_revision'] as const;
/** WA26's policy source and WA14's ledger are both LAB fakes; insist that
 * even their claimed case/audience/campaign/policy revision agree. */
function policyMatches(raw:unknown,ledger:Record<string,unknown>,
 q:Wa15Request):boolean{
 const p=own(raw,POLICY);
 if(!p||S0_KEYS.some(k=>p[k]!==ledger[k])||
    p.selection_ref!==q.selection_ref||p.concessionaria_id!==q.concessionaria_id||
    p.waba_ref!==q.waba_id||p.policy_revision!==ledger.policy_revision||
    p.case_authorized!==ledger.case_authorized||
    p.audience_eligible!==ledger.audience_eligible||
    p.campaign_eligibility!==ledger.campaign_eligibility)
   return false;
 // WA26 coarse policy may not claim revoked/unknown once M14 proves a
 // synthetic active consent; M14 remains a strictly additional gate.
 return p.consent_state==='VALID'&&p.opted_out===false;
}
function m13Matches(q:Wa15Request,t:Wa13Candidate,
 candidate:Wa15PreviewCandidate):boolean{
 return t.concessionaria_id===q.concessionaria_id&&
  t.app_ref===q.app_ref&&t.waba_id===q.waba_id&&
  t.language_code===q.language&&t.catalog_revision===q.catalog_revision&&
  t.template_ref===candidate.template_ref&&
  t.version_ref===candidate.version_ref&&
  t.meta_category===candidate.meta_category&&
  t.approval_verified===false&&t.send_authorized===false&&
  t.production_authorized===false&&t.requires_s0_recheck===true;
}
/** Only an untrusted fixture preview, never a ratified S0 response/F02 grant.
 * Injected ports are wrapped to detect discrepancies between WA26 and WA14
 * without exposing the private WA26 ticket into the preview or to the caller.
 */
export async function prepareWa15F02PreviewOffline(
 rawRequest:unknown,ports:Wa26FixturePorts,
 m13Host:unknown,m13S0:unknown,m13Provider:unknown,m14Ledger:unknown,
):Promise<Wa15Result>{
 const q=request(rawRequest),ledger=own(m14Ledger,LEDGER);
 if(!q||!ledger||!ports||
    typeof ports.resolveSelection!=='function'||
    typeof ports.readScopedPolicy!=='function'||
    typeof ports.readScopedCatalog!=='function')
  return deny('INVALID_REQUEST');
 if(ledger.selection_ref!==q.selection_ref||
    ledger.concessionaria_id!==q.concessionaria_id||
    ledger.waba_ref!==q.waba_id||
    ledger.case_ref!==q.case_ref||ledger.lead_ref!==q.lead_ref||
    ledger.case_version!==q.case_version||
    ledger.authorization_revision!==q.authorization_revision)
   return deny('UNTRUSTED_SCOPE');
 try{
  const guards:{source:unknown;frozen:unknown}[]=[];
  const capture=(source:unknown):any=>{
   const frozen=cloneLabData(source);
   guards.push({source,frozen});
   return frozen;
  };
  // Freeze all inputs before the first asynchronous WA26 port. In
  // particular, do NOT evaluate M14 against a mutable live caller ledger.
  const snapRequest=capture(rawRequest);
  const snapLedger=capture(m14Ledger);
  const snapHost=capture(m13Host);
  const snapS0=capture(m13S0);
  const snapProvider=capture(m13Provider);
  if(!request(snapRequest)||!own(snapLedger,LEDGER))
   return deny('INVALID_REQUEST');
  const ledgerCopy=own(snapLedger,LEDGER)!;
  const unchanged=()=>guards.every(g=>
   isDeepStrictEqual(g.frozen,cloneLabData(g.source)));
  const reconciled=reconcileWa13CatalogOffline(
   snapHost,snapS0,snapProvider);
  if(reconciled.decision!=='LAB_CATALOG_RECONCILED_UNVERIFIED')
   return deny('M13_CATALOG_DENIED');
  // Fail closed even when both mismatched sources report zero candidates.
  const scope13=own(snapHost,['contract_version','concessionaria_id',
   'app_ref','waba_id','catalog_revision','now_ms','max_age_ms']);
  if(!scope13||scope13.concessionaria_id!==q.concessionaria_id||
     scope13.app_ref!==q.app_ref||scope13.waba_id!==q.waba_id||
     scope13.catalog_revision!==q.catalog_revision||
     scope13.now_ms!==q.now_ms||scope13.max_age_ms!==q.max_age_ms)
   return deny('CATALOG_VERSION_OR_SCOPE_MISMATCH');
  // No mutable caller input is trusted as S0 authority: wrappers verify
  // cross-claim coherence before forwarding to the existing WA26 parser.
  let mismatch=false;
  const checkedPorts:Wa26FixturePorts={
   async resolveSelection(selection_ref:string,phase:Wa26Phase){
    const raw=await ports.resolveSelection(selection_ref,phase);
    const snapshot=capture(raw);
    if(!scopeMatches(snapshot,q)){mismatch=true;throw Error('SCOPE');}
    return snapshot as Wa26Scope;
   },
   async readScopedPolicy(scope:Wa26Scope,phase:Wa26Phase){
    const raw=await ports.readScopedPolicy(scope,phase);
    const snapshot=capture(raw);
    if(!policyMatches(snapshot,ledgerCopy,q)){
     mismatch=true;throw Error('POLICY');
    }
    return snapshot;
   },
   async readScopedCatalog(scope:Wa26Scope,phase:Wa26Phase){
    return capture(await ports.readScopedCatalog(scope,phase));
   },
  };
  const planned=await prepareS0TemplateCandidatesFixture(
   q.selection_ref,checkedPorts);
  if(mismatch)return deny('UNTRUSTED_SCOPE');
  if(!unchanged())return deny('INPUT_CHANGED_DURING_PREVIEW');
  if(planned.decision!=='LAB_CANDIDATES'||planned.candidates.length<1||
     planned.candidates.length>100)
    return deny('WA26_POLICY_OR_CATALOG_DENIED');
  const byTemplate=new Map(reconciled.candidates.map(
   x=>[x.template_ref,x]));
  const seen=new Set<string>(),out:Wa15PreviewCandidate[]=[];
  for(const p of planned.candidates){
   if(seen.has(p.template_ref))return deny('AMBIGUOUS_CANDIDATES');
   seen.add(p.template_ref);
   const candidate:Wa15PreviewCandidate={
    template_ref:p.template_ref,version_ref:p.version_ref,
    catalog_revision:p.catalog_revision,meta_category:p.meta_category,
    purpose_ref:p.purpose_ref,send_authorized:false,
    production_authorized:false,requires_s0_recheck:true,
   };
   const detail=byTemplate.get(p.template_ref);
   if(!detail||!m13Matches(q,detail,candidate))
    return deny('CATALOG_VERSION_OR_SCOPE_MISMATCH');
   const policy=inspectWa14ConsentOffline({
    contract_version:'wa14-request.lab.v0.1',
    selection_ref:q.selection_ref,concessionaria_id:q.concessionaria_id,
    waba_ref:q.waba_id,lead_ref:q.lead_ref,case_ref:q.case_ref,
    case_version:q.case_version,authorization_revision:q.authorization_revision,
    template_ref:p.template_ref,template_version_ref:p.version_ref,
    template_purpose_ref:q.purpose_ref,
    consent_purpose_ref:q.consent_purpose_ref,
    actor_kind:q.actor_kind,actor_ref:q.actor_ref,flow_ref:q.flow_ref,
    campaign_ref:q.campaign_ref,now_ms:q.now_ms,max_age_ms:q.max_age_ms,
   },snapLedger);
   if(policy.decision!=='LAB_POLICY_COHERENT_UNVERIFIED')
    return deny('M14_CONSENT_OR_GRANT_DENIED');
   out.push(Object.freeze(candidate));
  }
  // A port or caller may have mutated previously inspected policy, provider,
  // catalog or consent structures while the await chain was suspended.
  // The snapshots above remain consistent; deny instead of returning a
  // mixed-time positive result, even when the changed field was unselected.
  if(!unchanged())return deny('INPUT_CHANGED_DURING_PREVIEW');
  out.sort((a,b)=>a.template_ref<b.template_ref?-1:a.template_ref>b.template_ref?1:0);
  const preview:Wa15PlannerPreview=Object.freeze({
   contract_version:'wa15-f02-preview.lab.v0.1',
   planning_flow_ref:q.flow_ref,campaign_ref:q.campaign_ref,
   plan_revision:q.plan_revision,catalog_revision:q.catalog_revision,
   candidates:Object.freeze(out),send_authorized:false,
   production_authorized:false,meta_approval_verified:false,
   consent_verified:false,s0_source_authenticated:false,
   graph_dispatch_authorized:false,requires_s0_recheck:true,
   provider_sync_performed:false,
  });
  return Object.freeze({...NO,decision:'LAB_F02_PREVIEW_UNVERIFIED',
   reason:null,preview});
 }catch{return deny('DEPENDENCY_UNAVAILABLE');}
}
