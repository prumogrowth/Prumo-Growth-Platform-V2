/**
 * WA-17A: offline, human-authored WhatsApp template catalog contract.
 * NO Graph/SQL/HTTP, credentials, dispatch, or authentication here.
 * The service must authenticate administrator and Meta status provenance.
 * v0: BODY-only positional {{1}} variables; other components later.
 */
export type TemplateCategory='UTILITY'|'MARKETING';
export type MetaTemplateStatus='PENDING'|'APPROVED'|'REJECTED'|'PAUSED'|'DISABLED';
export type Stage='DRAFT'|'IN_REVIEW'|MetaTemplateStatus;
export type SourceDefinition=Readonly<{source_key:string;value_type:'text';enabled:boolean}>;
export type Mapping=Readonly<{position:number;source_key:string}>;
export type Template=Readonly<{
 local_id:string;concessionaria_id:string;meta_account_ref:string;
 name:string;language:string;category:TemplateCategory;body:string;
 examples:readonly string[];positions:readonly number[];
 mappings:readonly Mapping[];mapping_revision:number;content_version:number;
 stage:Stage;provider_template_id:string|null;
}>;
export type ManualTemplateInput=Readonly<{
 local_id:string;concessionaria_id:string;meta_account_ref:string;
 name:string;language:string;category:TemplateCategory;
 body:string;examples:readonly string[];
}>;

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const NUM=/^[0-9]{5,25}$/;
const NAME=/^[a-z][a-z0-9_]{0,127}$/;
const LOCALE=/^[a-z]{2}_[A-Z]{2}$/;
const SOURCE=/^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){1,3}$/;
function requireValid(ok:unknown,reason:string):asserts ok{
 if(!ok)throw new Error(reason);
}
function slots(body:string):number[]{
 const nums=[...body.matchAll(/\{\{(\d+)\}\}/g)].map(m=>Number(m[1]));
 const rest=body.replace(/\{\{\d+\}\}/g,'');
 requireValid(!rest.includes('{{')&&!rest.includes('}}'),'INVALID_PLACEHOLDER');
 const unique=[...new Set(nums)].sort((a,b)=>a-b);
 requireValid(unique.length<=20&&unique.every((x,i)=>x===i+1),
   'VARIABLES_MUST_BE_POSITIONAL_AND_CONTIGUOUS');
 return unique;
}
function freeze(t:Template):Template{
 return Object.freeze({...t,
  examples:Object.freeze([...t.examples]),
  positions:Object.freeze([...t.positions]),
  mappings:Object.freeze(t.mappings.map(m=>Object.freeze({...m}))),
 });
}
/** Text and examples come exclusively from a responsible human's input. */
export function createManualTemplate(input:ManualTemplateInput):Template{
 // The future HTTP/UI boundary must not inject access tokens, fake approval
 // flags or getters into a persisted template draft.
 const allowed=['local_id','concessionaria_id','meta_account_ref','name',
   'language','category','body','examples'];
 requireValid(!!input&&typeof input==='object'&&!Array.isArray(input),
   'INVALID_DRAFT_OBJECT');
 const prototype=Object.getPrototypeOf(input);
 requireValid(prototype===Object.prototype||prototype===null,'INVALID_DRAFT_PROTOTYPE');
 const descriptors=Object.getOwnPropertyDescriptors(input);
 requireValid(Reflect.ownKeys(input).length===allowed.length&&
   allowed.every(k=>Object.hasOwn(descriptors,k)&&
     Object.hasOwn(descriptors[k],'value')),'UNKNOWN_DRAFT_FIELDS');
 requireValid(UUID.test(input.local_id)&&UUID.test(input.concessionaria_id),
   'INVALID_LOCAL_OR_TENANT_ID');
 requireValid(NUM.test(input.meta_account_ref),'INVALID_META_ACCOUNT');
 requireValid(NAME.test(input.name),'INVALID_TEMPLATE_NAME');
 requireValid(LOCALE.test(input.language),'INVALID_LOCALE');
 requireValid(input.category==='MARKETING'||input.category==='UTILITY',
   'UNSUPPORTED_CATEGORY');
 requireValid(typeof input.body==='string'&&input.body.trim().length>0&&
   input.body.length<=1024,'INVALID_BODY');
 const positions=slots(input.body);
 requireValid(Array.isArray(input.examples)&&input.examples.length===positions.length,
   'MISSING_META_EXAMPLES');
 requireValid(input.examples.every(x=>typeof x==='string'&&x.trim().length>0&&
   x.length<=100&&!x.includes('{{')&&!x.includes('}}')),'INVALID_EXAMPLE');
 return freeze({...input,positions,mappings:[],mapping_revision:0,
   content_version:1,stage:'DRAFT',provider_template_id:null});
}

/** Constructs an approval submission payload, but NEVER calls Meta. */
export function prepareMetaReviewPayload(template:Template){
 requireValid(template.stage==='DRAFT'&&template.provider_template_id===null,
   'SUBMISSION_ONLY_FOR_DRAFT');
 const component=template.positions.length?
  {type:'BODY',text:template.body,example:{body_text:[template.examples]}}:
  {type:'BODY',text:template.body};
 return Object.freeze({
  operation:'CREATE_FOR_REVIEW' as const,meta_account_ref:template.meta_account_ref,
  payload:Object.freeze({name:template.name,language:template.language,
   category:template.category,components:Object.freeze([component])}),
  network_performed:false as const,approved:false as const,
 });
}
/** Call only after the authenticated Meta adapter confirms a creation receipt. */
export function recordReviewSubmission(template:Template,providerId:string):Template{
 requireValid(template.stage==='DRAFT'&&template.provider_template_id===null,
   'ALREADY_SUBMITTED');
 requireValid(NUM.test(providerId),'INVALID_META_TEMPLATE_ID');
 return freeze({...template,stage:'IN_REVIEW',provider_template_id:providerId});
}
/** Requires trusted Meta status sync in the service; strings alone are not proof. */
export function applyVerifiedMetaStatus(template:Template,providerId:string,status:MetaTemplateStatus):Template{
 requireValid(template.provider_template_id!==null&&template.provider_template_id===providerId,
   'UNTRUSTED_STATUS_SCOPE');
 requireValid(['PENDING','APPROVED','REJECTED','PAUSED','DISABLED'].includes(status),
   'UNKNOWN_META_STATUS');
 return freeze({...template,stage:status});
}
/** Edits ONLY source bindings. Registry comes from an authenticated tenant backend. */
export function configureVariableSources(
 template:Template,expectedRevision:number,mappings:readonly Mapping[],
 trustedRegistry:readonly SourceDefinition[],
):Template{
 requireValid(expectedRevision===template.mapping_revision,'STALE_MAPPING_REVISION');
 requireValid(Array.isArray(mappings)&&mappings.length===template.positions.length,
   'INCOMPLETE_VARIABLE_BINDINGS');
 const sources=new Set(trustedRegistry.filter(x=>x.enabled&&x.value_type==='text')
   .map(x=>x.source_key));
 const ordered=[...mappings].sort((a,b)=>a.position-b.position);
 requireValid(ordered.every((x,i)=>Number.isInteger(x.position)&&
   x.position===template.positions[i]&&typeof x.source_key==='string'&&
   SOURCE.test(x.source_key)&&sources.has(x.source_key)),
  'UNREGISTERED_VARIABLE_SOURCE');
 return freeze({...template,mappings:ordered,mapping_revision:expectedRevision+1});
}
/** A changed Meta-visible text is a NEW draft, never a mutation of approval. */
export function createEditedContentVersion(previous:Template,next:ManualTemplateInput):Template{
 requireValid(previous.concessionaria_id===next.concessionaria_id&&
   previous.meta_account_ref===next.meta_account_ref,'CROSS_TENANT_EDIT_DENIED');
 requireValid(previous.local_id!==next.local_id&&previous.name!==next.name,
   'NEW_CONTENT_REQUIRES_NEW_ID_AND_NAME');
 const draft=createManualTemplate(next);
 return freeze({...draft,content_version:previous.content_version+1});
}
/** Parameter preparation ONLY; consent/channel/window/authorization are later gates. */
export function prepareApprovedTemplateParameters(
 template:Template,values:Readonly<Record<string,unknown>>,
){
 requireValid(template.stage==='APPROVED'&&template.provider_template_id!==null,
   'TEMPLATE_NOT_APPROVED');
 requireValid(template.positions.length===template.mappings.length,
   'UNCONFIGURED_VARIABLES');
 const params=template.mappings.map(({position,source_key})=>{
  requireValid(template.positions.includes(position),'UNKNOWN_SLOT');
  requireValid(Object.hasOwn(values,source_key),'MISSING_VARIABLE_VALUE');
  const v=values[source_key];
  requireValid(typeof v==='string'&&v.trim().length>0&&v.length<=1024,
   'INVALID_VARIABLE_VALUE');
  return Object.freeze({type:'text' as const,text:v});
 });
 return Object.freeze({
  template_name:template.name,language:template.language,
  meta_account_ref:template.meta_account_ref,
  content_version:template.content_version,
  mapping_revision:template.mapping_revision,
  components:Object.freeze(params.length?[
    Object.freeze({type:'body',parameters:Object.freeze(params)}),
  ]:[]),
  network_performed:false as const,send_authorized:false as const,
 });
}
