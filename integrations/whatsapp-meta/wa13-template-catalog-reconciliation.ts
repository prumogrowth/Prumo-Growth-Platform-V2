/**
 * M13 / WA13 — OFFLINE catalog / provider-detail reconciliation.
 *
 * Both inputs and the "host" clock/scope are caller-supplied synthetic
 * fixtures, NOT independently authenticated S0/Meta authority. No Graph,
 * requests, credentials, S0 writes, grants, opt-out, send, SQL or HTTP ACK.
 *
 * A matched APPROVED string is NOT a verified Meta approval. Only a future
 * S0-authenticated, revision-locked catalog may present eligible templates.
 * Fail the ENTIRE snapshot on inconsistent identities/versions/scope.
 */
import {createHash} from 'node:crypto';
import {inspectMetaTemplateProviderRecord}
 from './graph-template-provider-observation.ts';

export type Wa13HostScope=Readonly<{
 contract_version:'wa13-host-scope.lab.v0.1';
 concessionaria_id:string;app_ref:string;waba_id:string;
 catalog_revision:number;now_ms:number;max_age_ms:number;
}>;
export type Wa13S0Entry=Readonly<{
 template_ref:string;version_ref:string;template_revision:number;
 provider_template_id:string;template_name:string;language_code:string;
 /** LAB-only binding: SHA-256 over normalized supported components. */
 provider_components_sha256:string;
 meta_category:'MARKETING'|'UTILITY';
 local_status:'PENDING'|'APPROVED'|'REJECTED'|'PAUSED'|'DISABLED';
 locally_active:boolean;current_version:boolean;
 valid_from_ms:number;valid_until_ms:number;
}>;
export type Wa13S0Snapshot=Readonly<{
 contract_version:'wa13-s0-catalog.lab.v0.1';
 concessionaria_id:string;app_ref:string;waba_id:string;
 catalog_revision:number;observed_at_ms:number;
 templates:readonly Wa13S0Entry[];
}>;
export type Wa13ProviderSnapshot=Readonly<{
 contract_version:'wa13-meta-detail-batch.lab.v0.1';
 waba_id:string;observed_at_ms:number;
 details:readonly unknown[];
}>;
export type Wa13Candidate=Readonly<{
 template_ref:string;version_ref:string;template_revision:number;
 catalog_revision:number;provider_template_id:string;
 concessionaria_id:string;app_ref:string;waba_id:string;
 template_name:string;language_code:string;
 provider_components_sha256:string;
 meta_category:'MARKETING'|'UTILITY';
 approval_verified:false;send_authorized:false;
 production_authorized:false;requires_s0_recheck:true;
}>;
type Reason='INVALID_INPUT'|'SCOPE_MISMATCH'|'STALE_OR_FUTURE_SNAPSHOT'|
 'DUPLICATE_OR_CONFLICTING_TEMPLATE'|'INCOMPLETE_PROVIDER_DETAILS'|
 'PROVIDER_IDENTITY_MISMATCH'|'PROVIDER_SHAPE_DENIED'|
 'COMPONENT_VERSION_MISMATCH';
const FLAGS=Object.freeze({
 meta_approval_verified:false,provider_source_authenticated:false,
 s0_source_authenticated:false,tenant_binding_verified:false,
 provider_page_chain_authenticated:false,
 catalog_publication_authorized:false,send_authorized:false,
 production_authorized:false,s0_write_authorized:false,
 ack_allowed:false,http_response_authorized:false,
 m2m_verified:false,consent_verified:false,grants_verified:false,
 actual_sync_performed:false,
} as const);
export type Wa13Result=Readonly<typeof FLAGS & {
 decision:'DENIED'|'LAB_CATALOG_RECONCILED_UNVERIFIED';
 reason:Reason|null;
 candidates:readonly Wa13Candidate[];
 observed_entries:number;withheld_entries:number;
}>;
const EMPTY=Object.freeze([]) as readonly [];
const deny=(reason:Reason):Wa13Result=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,candidates:EMPTY,
 observed_entries:0,withheld_entries:0,
});
const ID=/^[A-Za-z0-9_.:-]{1,128}$/;
const P_ID=/^[0-9]{5,25}$/;
const NAME=/^[a-z][a-z0-9_]{0,127}$/;
const LOCALE=/^[a-z]{2}(?:_[A-Z]{2})?$/;
const SHA=/^[a-f0-9]{64}$/;
/** LAB-only, versioned normalization provided by the existing Graph detail
 * inspector. It authenticates neither the provider nor an S0 release. */
export function wa13NormalizedComponentsDigest(components:readonly unknown[]):string{
 return createHash('sha256').update(JSON.stringify(components),'utf8').digest('hex');
}
const STATES=['PENDING','APPROVED','REJECTED','PAUSED','DISABLED'];
const CATS=['MARKETING','UTILITY'];
const key=(x:unknown):x is string=>typeof x==='string'&&ID.test(x);
const pid=(x:unknown):x is string=>typeof x==='string'&&P_ID.test(x);
const pos=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>0;
const nonneg=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>=0;
/** Own descriptors only, with exact keys; no accessor, extra or symbol. */
function record(raw:unknown,expected:readonly string[],
 optional:readonly string[]=[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const desc=Object.getOwnPropertyDescriptors(raw);
  const own=Reflect.ownKeys(raw);
  if(own.length<expected.length||
     own.length>expected.length+optional.length||
     own.some(x=>typeof x!=='string'||
      (!expected.includes(x)&&!optional.includes(x))||
      !Object.hasOwn(desc[x],'value'))||
     expected.some(x=>!Object.hasOwn(desc,x)))
   return null;
  return Object.fromEntries((own as string[]).map(x=>[x,desc[x].value]));
 }catch{return null;}
}
/** Bound dense, own-data element copy; avoids getters, sparse arrays or symbols. */
function dense(raw:unknown,max:number):unknown[]|null{
 try{
  if(!Array.isArray(raw)||Object.getPrototypeOf(raw)!==Array.prototype)
   return null;
  const d=Object.getOwnPropertyDescriptors(raw);
  const n=d.length?.value;
  if(!Number.isSafeInteger(n)||n<0||n>max||
     Reflect.ownKeys(raw).length!==n+1)return null;
  const out:unknown[]=[];
  for(let i=0;i<n;i++){
   const e=d[String(i)];
   if(!e||!Object.hasOwn(e,'value'))return null;
   out.push(e.value);
  }
  return out;
 }catch{return null;}
}
const HOST=['contract_version','concessionaria_id','app_ref','waba_id',
 'catalog_revision','now_ms','max_age_ms'] as const;
const S0=['contract_version','concessionaria_id','app_ref','waba_id',
 'catalog_revision','observed_at_ms','templates'] as const;
const PROVIDER=['contract_version','waba_id','observed_at_ms','details'] as const;
const ENTRY=['template_ref','version_ref','template_revision',
 'provider_template_id','template_name','language_code','provider_components_sha256','meta_category',
 'local_status','locally_active','current_version','valid_from_ms',
 'valid_until_ms'] as const;
function checkedEntry(raw:unknown):Wa13S0Entry|null{
 const x=record(raw,ENTRY);
 if(!x||!key(x.template_ref)||!key(x.version_ref)||!pos(x.template_revision)||
    !pid(x.provider_template_id)||typeof x.template_name!=='string'||
    !NAME.test(x.template_name)||
    typeof x.provider_components_sha256!=='string'||
    !SHA.test(x.provider_components_sha256)||
    typeof x.language_code!=='string'||
    !LOCALE.test(x.language_code)||!CATS.includes(x.meta_category as string)||
    !STATES.includes(x.local_status as string)||
    typeof x.locally_active!=='boolean'||typeof x.current_version!=='boolean'||
    !nonneg(x.valid_from_ms)||!pos(x.valid_until_ms)||
    (x.valid_until_ms as number)<=(x.valid_from_ms as number))
  return null;
 return x as Wa13S0Entry;
}
function recent(t:unknown,now:number,maxAge:number):boolean{
 return nonneg(t)&&t<=now&&now-t<=maxAge;
}
/**
 * Strict comparison of two UNAUTHENTICATED snapshots, not a synchronizer.
 * The host must bind S0 and provider observations independently in future.
 */
export function reconcileWa13CatalogOffline(
 hostRaw:unknown,s0Raw:unknown,providerRaw:unknown,
):Wa13Result{
 try{
  const host=record(hostRaw,HOST),s0=record(s0Raw,S0),
   provider=record(providerRaw,PROVIDER);
  if(!host||!s0||!provider||
     host.contract_version!=='wa13-host-scope.lab.v0.1'||
     s0.contract_version!=='wa13-s0-catalog.lab.v0.1'||
     provider.contract_version!=='wa13-meta-detail-batch.lab.v0.1'||
     !key(host.concessionaria_id)||!key(host.app_ref)||!pid(host.waba_id)||
     !pos(host.catalog_revision)||!nonneg(host.now_ms)||
     !pos(host.max_age_ms)||host.max_age_ms>300000)
   return deny('INVALID_INPUT');
  if(s0.concessionaria_id!==host.concessionaria_id||
     s0.app_ref!==host.app_ref||s0.waba_id!==host.waba_id||
     s0.catalog_revision!==host.catalog_revision||
     provider.waba_id!==host.waba_id)return deny('SCOPE_MISMATCH');
  const now=host.now_ms as number,maxAge=host.max_age_ms as number;
  if(!recent(s0.observed_at_ms,now,maxAge)||
     !recent(provider.observed_at_ms,now,maxAge))
   return deny('STALE_OR_FUTURE_SNAPSHOT');
  const entries=dense(s0.templates,100),details=dense(provider.details,100);
  if(!entries||!details)return deny('INVALID_INPUT');
  if(entries.length!==details.length)return deny('INCOMPLETE_PROVIDER_DETAILS');
  const parsed:Wa13S0Entry[]=[];
  const refs=new Set<string>(),providers=new Set<string>(),
   versions=new Set<string>(),names=new Set<string>();
  for(const item of entries){
   const t=checkedEntry(item);
   if(!t)return deny('INVALID_INPUT');
   const nameKey=JSON.stringify([t.template_name,t.language_code]);
   if(refs.has(t.template_ref)||providers.has(t.provider_template_id)||
      versions.has(t.version_ref)||names.has(nameKey))
    return deny('DUPLICATE_OR_CONFLICTING_TEMPLATE');
   refs.add(t.template_ref);providers.add(t.provider_template_id);
   versions.add(t.version_ref);names.add(nameKey);parsed.push(t);
  }
  // Every listed provider detail must correspond to EXACTLY one S0 identity.
  // The candidate provider identity itself comes from untrusted JSON; the
  // individual inspector validates shape and components, never authenticity.
  const byId=new Map(parsed.map(x=>[x.provider_template_id,x]));
  const visited=new Set<string>();
  const candidates:Wa13Candidate[]=[];
  for(const raw of details){
   const identity=record(raw,['id','name','language','status','category',
     'components'],['parameter_format','quality_score','rejected_reason']);
   // Accept only OPTIONAL detail metadata already recognized by the existing
   // provider shape inspector; it is NEVER used to assert approval or rights.
   if(!identity)return deny('PROVIDER_SHAPE_DENIED');
   if(!pid(identity.id)||visited.has(identity.id))
    return deny('DUPLICATE_OR_CONFLICTING_TEMPLATE');
   const t=byId.get(identity.id as string);
   if(!t)return deny('PROVIDER_IDENTITY_MISMATCH');
   visited.add(t.provider_template_id);
   const observed=inspectMetaTemplateProviderRecord(raw,{
    provider_template_id:t.provider_template_id,
    template_name:t.template_name,language_code:t.language_code,
   });
   if(observed.decision==='DENIED'||!observed.observed)
    return deny('PROVIDER_SHAPE_DENIED');
   if(observed.observed.reported_category!==t.meta_category||
      observed.observed.reported_status!==t.local_status)
    return deny('PROVIDER_IDENTITY_MISMATCH');
   // A reported APPROVED status is not enough to bind the exact reviewed
   // component version: BODY/HEADER/FOOTER/BUTTONS must match S0's LAB digest.
   if(wa13NormalizedComponentsDigest(
     observed.observed.approved_components_candidate)!==t.provider_components_sha256)
    return deny('COMPONENT_VERSION_MISMATCH');
   if(t.local_status!=='APPROVED'||!t.locally_active||!t.current_version||
      t.valid_from_ms>now||t.valid_until_ms<=now)continue;
   candidates.push(Object.freeze({
    template_ref:t.template_ref,version_ref:t.version_ref,
    template_revision:t.template_revision,
    catalog_revision:host.catalog_revision as number,
    provider_template_id:t.provider_template_id,
    concessionaria_id:host.concessionaria_id as string,
    app_ref:host.app_ref as string,waba_id:host.waba_id as string,
    provider_components_sha256:t.provider_components_sha256,
    template_name:t.template_name,language_code:t.language_code,
    meta_category:t.meta_category,approval_verified:false as const,
    send_authorized:false as const,production_authorized:false as const,
    requires_s0_recheck:true as const,
   }));
  }
  if(visited.size!==parsed.length)return deny('INCOMPLETE_PROVIDER_DETAILS');
  candidates.sort((a,b)=>a.template_ref.localeCompare(b.template_ref));
  return Object.freeze({...FLAGS,
   decision:'LAB_CATALOG_RECONCILED_UNVERIFIED' as const,reason:null,
   candidates:Object.freeze(candidates),observed_entries:parsed.length,
   withheld_entries:parsed.length-candidates.length,
  });
 }catch{return deny('INVALID_INPUT');}
}

/** One extra LAB-only read comparison; not an S0 transaction or reservation.
 * Candidate snapshots NEVER become grants, even when recheck matches. */
export type Wa13RecheckResult=Readonly<typeof FLAGS & {
 decision:'DENIED'|'LAB_RECHECKED_UNVERIFIED';
 reason:null|'INVALID_CANDIDATE'|'CURRENT_CATALOG_DENIED'|'STALE_OR_REVOKED';
}>;
const CANDIDATE=['template_ref','version_ref','template_revision',
 'catalog_revision','provider_template_id','concessionaria_id','app_ref','waba_id',
 'template_name','language_code','provider_components_sha256','meta_category',
 'approval_verified','send_authorized','production_authorized',
 'requires_s0_recheck'] as const;
const denyRecheck=(reason:Exclude<Wa13RecheckResult['reason'],null>):
 Wa13RecheckResult=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
});
export function recheckWa13CandidateOffline(
 rawCandidate:unknown,freshHost:unknown,freshS0:unknown,freshProvider:unknown,
):Wa13RecheckResult{
 try{
  const c=record(rawCandidate,CANDIDATE);
  if(!c||!key(c.template_ref)||!key(c.version_ref)||
     !pos(c.template_revision)||!pos(c.catalog_revision)||
     !pid(c.provider_template_id)||!key(c.concessionaria_id)||
     !key(c.app_ref)||!pid(c.waba_id)||
     typeof c.template_name!=='string'||!NAME.test(c.template_name)||
     typeof c.language_code!=='string'||!LOCALE.test(c.language_code)||
     typeof c.provider_components_sha256!=='string'||
     !SHA.test(c.provider_components_sha256)||
     !CATS.includes(c.meta_category as string)||
     c.approval_verified!==false||c.send_authorized!==false||
     c.production_authorized!==false||c.requires_s0_recheck!==true)
   return denyRecheck('INVALID_CANDIDATE');
  const checked=reconcileWa13CatalogOffline(freshHost,freshS0,freshProvider);
  if(checked.decision==='DENIED')return denyRecheck('CURRENT_CATALOG_DENIED');
  const isCurrent=checked.candidates.some(f=>
   CANDIDATE.every(k=>f[k as keyof Wa13Candidate]===c[k]));
  if(!isCurrent)return denyRecheck('STALE_OR_REVOKED');
  return Object.freeze({
   ...FLAGS,decision:'LAB_RECHECKED_UNVERIFIED' as const,reason:null,
  });
 }catch{return denyRecheck('INVALID_CANDIDATE');}
}
