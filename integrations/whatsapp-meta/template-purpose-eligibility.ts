/**
 * WA-25 / WDC-10/11 — deterministic, OFFLINE template-purpose candidate gate.
 *
 * Sources MUST be provided by a trusted tenant-scoped catalog/identity service.
 * This pure function does not authenticate users, resolve consent, verify
 * campaigns, select lead audiences, contact Meta, or authorize an actual send.
 * A later trusted backend MUST repeat every eligibility gate at reservation
 * AND immediately before dispatch; all outputs have send_authorized:false.
 *
 * Meta category != internal template purpose != consent/opt-out purpose.
 */
export type ActorKind = 'PLANNER'|'AI_ATTENDANT'|'CONSULTOR'|'GESTOR'|'DIRETOR';
export type MetaCategory = 'MARKETING'|'UTILITY';
export type MetaState = 'PENDING'|'APPROVED'|'REJECTED'|'PAUSED'|'DISABLED';
export type PurposeGrant = Readonly<{
  purpose_ref:string;
  actor_kind:ActorKind;
  actor_ref:string;
  flow_ref:string;
  campaign_ref:string|null;
}>;
export type PurposeTemplateSnapshot = Readonly<{
  template_ref:string;
  version_ref:string;
  catalog_revision:number;
  concessionaria_id:string;
  waba_ref:string;
  language:string;
  meta_category:MetaCategory;
  meta_status:MetaState;
  locally_active:boolean;
  current_version:boolean;
  purpose_refs:readonly string[];
  grants:readonly PurposeGrant[];
}>;
export type TrustedSelectionContext = Readonly<{
  concessionaria_id:string;
  waba_ref:string;
  catalog_revision:number;
  language:string;
  purpose_ref:string;
  actor_kind:ActorKind;
  actor_ref:string;
  flow_ref:string;
  campaign_ref:string|null;
}>;
export type PlannerCandidate = Readonly<{
  template_ref:string;
  version_ref:string;
  catalog_revision:number;
  meta_category:MetaCategory;
  purpose_ref:string;
  /** Not an authorization; external consent, audience, campaign and send gates remain. */
  send_authorized:false;
  production_authorized:false;
}>;
export type FilterResult = Readonly<{
  candidates:readonly PlannerCandidate[];
  send_authorized:false;
  production_authorized:false;
  /** Even a positive catalog selection cannot skip the external S0 gates. */
  requires_external_recheck:true;
}>;

const REF=/^[A-Za-z0-9_.:-]{1,128}$/;
const LOCALE=/^[a-z]{2,3}(?:_[A-Z]{2})?$/;
const ACTORS:readonly ActorKind[]=['PLANNER','AI_ATTENDANT','CONSULTOR','GESTOR','DIRETOR'];
const STATES:readonly MetaState[]=['PENDING','APPROVED','REJECTED','PAUSED','DISABLED'];
const CATEGORIES:readonly MetaCategory[]=['MARKETING','UTILITY'];
const SNAP_KEYS=[
  'template_ref','version_ref','catalog_revision','concessionaria_id',
  'waba_ref','language','meta_category','meta_status','locally_active',
  'current_version','purpose_refs','grants',
];
const CONTEXT_KEYS=[
  'concessionaria_id','waba_ref','catalog_revision','language',
  'purpose_ref','actor_kind','actor_ref','flow_ref','campaign_ref',
];
const GRANT_KEYS=['purpose_ref','actor_kind','actor_ref','flow_ref','campaign_ref'];

const validRef=(v:unknown):v is string=>typeof v==='string'&&REF.test(v);
const validActor=(v:unknown):v is ActorKind=>
  typeof v==='string'&&ACTORS.includes(v as ActorKind);
const validRevision=(v:unknown):v is number=>
  typeof v==='number'&&Number.isSafeInteger(v)&&v>0;

/**
 * Only accept ordinary own DATA properties. Accessor values, extra properties,
 * inherited fields and suspicious prototypes cannot grant eligibility.
 * No untrusted exception, identifier or person data is exposed in the result.
 */
function checkedRecord(value:unknown,expected:readonly string[]):Record<string,unknown>|null{
  try{
    if(!value||typeof value!=='object'||Array.isArray(value))return null;
    const proto=Object.getPrototypeOf(value);
    if(proto!==Object.prototype&&proto!==null)return null;
    const all=Reflect.ownKeys(value);
    if(all.length!==expected.length||all.some(k=>
      typeof k!=='string'||!expected.includes(k)))return null;
    const desc=Object.getOwnPropertyDescriptors(value);
    if(expected.some(k=>!Object.hasOwn(desc,k)||!Object.hasOwn(desc[k],'value')))return null;
    return Object.fromEntries(expected.map(k=>[k,desc[k].value]));
  }catch{return null;}
}
function validCampaign(v:unknown):v is string|null{
  return v===null||validRef(v);
}
function trustedContext(raw:unknown):TrustedSelectionContext|null{
  const x=checkedRecord(raw,CONTEXT_KEYS);
  if(!x||!validRef(x.concessionaria_id)||!validRef(x.waba_ref)||
      !validRevision(x.catalog_revision)||typeof x.language!=='string'||
      !LOCALE.test(x.language)||!validRef(x.purpose_ref)||
      !validActor(x.actor_kind)||!validRef(x.actor_ref)||
      !validRef(x.flow_ref)||!validCampaign(x.campaign_ref))return null;
  return x as TrustedSelectionContext;
}
function checkedGrant(raw:unknown):PurposeGrant|null{
  const x=checkedRecord(raw,GRANT_KEYS);
  if(!x||!validRef(x.purpose_ref)||!validActor(x.actor_kind)||
      !validRef(x.actor_ref)||!validRef(x.flow_ref)||
      !validCampaign(x.campaign_ref))return null;
  return x as PurposeGrant;
}
function checkedTemplate(raw:unknown):PurposeTemplateSnapshot|null{
  const x=checkedRecord(raw,SNAP_KEYS);
  if(!x||!validRef(x.template_ref)||!validRef(x.version_ref)||
      !validRevision(x.catalog_revision)||!validRef(x.concessionaria_id)||
      !validRef(x.waba_ref)||typeof x.language!=='string'||
      !LOCALE.test(x.language)||!CATEGORIES.includes(x.meta_category as MetaCategory)||
      !STATES.includes(x.meta_status as MetaState)||
      typeof x.locally_active!=='boolean'||typeof x.current_version!=='boolean'||
      !Array.isArray(x.purpose_refs)||!Array.isArray(x.grants)||
      x.purpose_refs.length>100||x.grants.length>500)return null;
  const purposes=(x.purpose_refs as unknown[]).slice();
  const rawGrants=(x.grants as unknown[]).slice();
  if(!purposes.every(validRef)||new Set(purposes).size!==purposes.length)return null;
  const grants=rawGrants.map(checkedGrant);
  if(grants.some(g=>g===null))return null;
  // Every grant must be attached to a purpose explicitly associated with
  // this template. An unrelated grant can never widen a template's scope.
  if(grants.some(g=>!purposes.includes(g!.purpose_ref)))return null;
  return {...x,purpose_refs:purposes,grants:grants as PurposeGrant[]} as PurposeTemplateSnapshot;
}
const EMPTY:FilterResult=Object.freeze({
  candidates:Object.freeze([]),send_authorized:false,
  production_authorized:false,requires_external_recheck:true,
});

function validForContext(t:PurposeTemplateSnapshot,c:TrustedSelectionContext):boolean{
  if(t.catalog_revision!==c.catalog_revision||
      t.concessionaria_id!==c.concessionaria_id||t.waba_ref!==c.waba_ref||
      t.language!==c.language||t.meta_status!=='APPROVED'||
      !t.locally_active||!t.current_version||
      !t.purpose_refs.includes(c.purpose_ref))return false;
  return t.grants.some(g=>
    g.purpose_ref===c.purpose_ref&&g.actor_kind===c.actor_kind&&
    g.actor_ref===c.actor_ref&&g.flow_ref===c.flow_ref&&
    g.campaign_ref===c.campaign_ref);
}

/**
 * Closed-world selector. Malformed catalog entries are denied. Duplicate
 * template refs (even different versions) are ambiguous and entirely withheld,
 * rather than arbitrarily selecting a version.
 */
export function selectPlannerTemplateCandidates(
  rawTemplates:unknown,rawContext:unknown,
):FilterResult{
  const c=trustedContext(rawContext);
  if(!c||!Array.isArray(rawTemplates)||rawTemplates.length>10000)return EMPTY;
  const checked=rawTemplates.map(checkedTemplate);
  const counts=new Map<string,number>();
  for(const t of checked){
    if(t)counts.set(t.template_ref,(counts.get(t.template_ref)??0)+1);
  }
  const candidates:PlannerCandidate[]=[];
  for(const t of checked){
    if(!t||counts.get(t.template_ref)!==1||!validForContext(t,c))continue;
    candidates.push(Object.freeze({
      template_ref:t.template_ref,version_ref:t.version_ref,
      catalog_revision:t.catalog_revision,meta_category:t.meta_category,
      purpose_ref:c.purpose_ref,
      send_authorized:false as const,production_authorized:false as const,
    }));
  }
  return Object.freeze({...EMPTY,candidates:Object.freeze(candidates)});
}

/**
 * Must be called using a freshly obtained tenant/authorization snapshot at the
 * next trusted boundary; a cached candidate itself never proves current access.
 */
export function recheckPlannerTemplateCandidate(
  candidate:unknown,rawTemplates:unknown,freshContext:unknown,
):boolean{
  const c=trustedContext(freshContext);
  const k=checkedRecord(candidate,[
    'template_ref','version_ref','catalog_revision','meta_category',
    'purpose_ref','send_authorized','production_authorized',
  ]);
  if(!c||!k||!validRef(k.template_ref)||!validRef(k.version_ref)||
     !validRevision(k.catalog_revision)||!CATEGORIES.includes(k.meta_category as MetaCategory)||
     !validRef(k.purpose_ref)||k.send_authorized!==false||
     k.production_authorized!==false||k.catalog_revision!==c.catalog_revision||
     k.purpose_ref!==c.purpose_ref)return false;
  return selectPlannerTemplateCandidates(rawTemplates,c).candidates.some(
    t=>t.template_ref===k.template_ref&&t.version_ref===k.version_ref&&
      t.meta_category===k.meta_category);
}
