/**
 * Read-only SHAPE inspection of a synthetic Meta message-template GET record.
 *
 * This is NOT a Graph client, trusted source, authenticated observation,
 * template approval, S0 catalog sync, business authorization or dispatch.
 * A valid "APPROVED" string in an arbitrary JSON object grants NOTHING.
 * This module does not implement the S0 candidate contract T1-T6 (PR #19).
 *
 * Intended input shape: an individual template record (GET /<TEMPLATE_ID>),
 * not a paginated GET /<WABA_ID>/message_templates response. The trusted
 * host must independently bind WABA, credential, route, response and ID.
 */
export type ObservedComponent =
 | Readonly<{type:'HEADER';format:'TEXT';text:string}>
 | Readonly<{type:'BODY'|'FOOTER';text:string}>
 | Readonly<{type:'BUTTONS';buttons:readonly Readonly<{type:'QUICK_REPLY';text:string}>[]}>;

type NoAuthority=Readonly<{
 meta_approval_verified:false;production_authorized:false;
 send_authorized:false;ack_allowed:false;retry_external:false;
 s0_write_authorized:false;commercial_effect_authorized:false;
}>;

export type ProviderTemplateObservation=NoAuthority&(
 Readonly<{decision:'DENIED';reason:
 'INVALID_INPUT'|'INCOMPLETE_PROVIDER_RECORD'|'UNSUPPORTED_PROVIDER_SHAPE'|
 'IDENTITY_MISMATCH'|'UNSUPPORTED_COMPONENTS';
 observed:null}> |
 Readonly<{decision:'SHAPE_ONLY_UNVERIFIED';reason:null;
 observed:Readonly<{
  provider_template_id:string;
  template_name:string;language_code:string;
  reported_status:'APPROVED'|'PENDING'|'PAUSED'|'REJECTED'|'DISABLED';
  reported_category:'MARKETING'|'UTILITY'|'AUTHENTICATION';
  approved_components_candidate:readonly ObservedComponent[];
  /** This module never asserts that a provider fetch was authenticated. */
  provider_source_authenticated:false;
  /** Provenance, WABA, revision and approval are responsibilities of S0 T1-T6. */
  provider_manifest_complete_verified:false;
 }>}>
);

const FLAGS=Object.freeze({
 meta_approval_verified:false,production_authorized:false,
 send_authorized:false,ack_allowed:false,retry_external:false,
 s0_write_authorized:false,commercial_effect_authorized:false,
} as const);
const name=/^[a-z][a-z0-9_]{0,127}$/;
const locale=/^[a-z]{2}(?:_[A-Z]{2})?$/;
const providerId=/^[0-9]{5,25}$/;
const allowedStatus=new Set(['APPROVED','PENDING','PAUSED','REJECTED','DISABLED']);
const allowedCategory=new Set(['MARKETING','UTILITY','AUTHENTICATION']);
const invalidUtf16=/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/;
class Invalid extends Error {
 constructor(readonly code:Extract<ProviderTemplateObservation,{decision:'DENIED'}>['reason']){
  super(code);
 }
}
function fail(code:Invalid['code']):never {throw new Invalid(code);}
function deny(code:Invalid['code']):ProviderTemplateObservation{
 return Object.freeze({...FLAGS,decision:'DENIED' as const,reason:code,observed:null});
}
/** Copy only plain own DATA descriptors, rejecting accessors and sparse arrays. */
function ownData(input:unknown,depth=0,counter={nodes:0}):any{
 if(++counter.nodes>512||depth>10)fail('INVALID_INPUT');
 if(input===null||typeof input==='boolean')return input;
 if(typeof input==='number'){
  if(!Number.isSafeInteger(input))fail('INVALID_INPUT');
  return input;
 }
 if(typeof input==='string'){
  if(input.length>8192||invalidUtf16.test(input))fail('INVALID_INPUT');
  return input;
 }
 if(!input||typeof input!=='object')fail('INVALID_INPUT');
 const array=Array.isArray(input),proto=Object.getPrototypeOf(input);
 if(array?proto!==Array.prototype:proto!==Object.prototype&&proto!==null)
  fail('INVALID_INPUT');
 const d=Object.getOwnPropertyDescriptors(input),keys=Reflect.ownKeys(input);
 if(keys.some(k=>typeof k!=='string'||!Object.hasOwn(d[k],'value')))
  fail('INVALID_INPUT');
 if(array){
  if(input.length>100||keys.length!==input.length+1)fail('INVALID_INPUT');
  if(Array.from({length:input.length},(_,i)=>Object.hasOwn(d,String(i))).some(x=>!x))
   fail('INVALID_INPUT');
  return Array.from({length:input.length},(_,i)=>ownData(d[String(i)].value,depth+1,counter));
 }
 if(keys.length>32)fail('INVALID_INPUT');
 return Object.fromEntries((keys as string[]).map(k=>[k,ownData(d[k].value,depth+1,counter)]));
}
function keys(o:any,required:string[],optional:string[]=[]){
 if(!o||typeof o!=='object'||Array.isArray(o)||
    required.some(k=>!Object.hasOwn(o,k))||
    Object.keys(o).some(k=>!required.includes(k)&&!optional.includes(k)))
  fail('UNSUPPORTED_PROVIDER_SHAPE');
}
function templateText(v:unknown):v is string{
 return typeof v==='string'&&v.length>0&&v.length<=4096&&
 !/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/.test(v);
}
function freeze<T>(v:T):T{
 if(v&&typeof v==='object'){
  for(const child of Object.values(v))freeze(child);
  Object.freeze(v);
 }
 return v;
}

/**
 * Validate the *shape only* of one Graph template record against independently
 * selected id/name/language. No WABA verification is possible from this record.
 *
 * API metadata and component schemas may evolve: fail closed, adapt only
 * after a documented provider fixture (never silently drop unknown BUTTONS).
 */
export function inspectMetaTemplateProviderRecord(
 raw:unknown,expected:unknown,
):ProviderTemplateObservation{
 try{
  const match=ownData(expected),data=ownData(raw);
  keys(match,['provider_template_id','template_name','language_code']);
  if(typeof match.provider_template_id!=='string'||!providerId.test(match.provider_template_id)||
     typeof match.template_name!=='string'||!name.test(match.template_name)||
     typeof match.language_code!=='string'||!locale.test(match.language_code))
   fail('INVALID_INPUT');
  keys(data,['id','name','language','status','category','components'],
    ['parameter_format','quality_score','rejected_reason']);
  if(typeof data.id!=='string'||!providerId.test(data.id)||
     typeof data.name!=='string'||!name.test(data.name)||
     typeof data.language!=='string'||!locale.test(data.language))
   fail('INCOMPLETE_PROVIDER_RECORD');
  if(data.id!==match.provider_template_id||
     data.name!==match.template_name||data.language!==match.language_code)
   fail('IDENTITY_MISMATCH');
  if(typeof data.status!=='string'||!allowedStatus.has(data.status)||
     typeof data.category!=='string'||!allowedCategory.has(data.category)||
     !Array.isArray(data.components)||data.components.length<1||
     data.components.length>4)fail('UNSUPPORTED_PROVIDER_SHAPE');
  // Any metadata not explicitly modeled is NOT an approval or version.
  const out:ObservedComponent[]=[];
  const ordering=['HEADER','BODY','FOOTER','BUTTONS'];
  let last=-1;
  for(const component of data.components){
   if(!component||typeof component!=='object'||Array.isArray(component))
    fail('UNSUPPORTED_COMPONENTS');
   const type=component.type;
   const index=ordering.indexOf(type);
   if(index<0||index<=last)fail('UNSUPPORTED_COMPONENTS');
   last=index;
   if(type==='HEADER'){
    keys(component,['type','format','text'],['example']);
    if(component.format!=='TEXT'||!templateText(component.text))fail('UNSUPPORTED_COMPONENTS');
    out.push({type:'HEADER',format:'TEXT',text:component.text});
   }else if(type==='BODY'||type==='FOOTER'){
    keys(component,['type','text'],type==='BODY'?['example']:[]);
    if(!templateText(component.text))fail('UNSUPPORTED_COMPONENTS');
    out.push({type,text:component.text});
   }else {
    keys(component,['type','buttons']);
    if(!Array.isArray(component.buttons)||
       component.buttons.length<1||component.buttons.length>3)
      fail('UNSUPPORTED_COMPONENTS');
    const buttons=component.buttons.map((button:any)=>{
     keys(button,['type','text']);
     if(button.type!=='QUICK_REPLY'||!templateText(button.text)||
        button.text.length>25)fail('UNSUPPORTED_COMPONENTS');
     return {type:'QUICK_REPLY' as const,text:button.text};
    });
    out.push({type:'BUTTONS',buttons});
   }
  }
  if(!out.some(c=>c.type==='BODY'))fail('INCOMPLETE_PROVIDER_RECORD');
  // These are normalized candidate components, not approved Meta evidence.
  const observed=freeze({
   provider_template_id:data.id,template_name:data.name,language_code:data.language,
   reported_status:data.status as 'APPROVED'|'PENDING'|'PAUSED'|'REJECTED'|'DISABLED',
   reported_category:data.category as 'MARKETING'|'UTILITY'|'AUTHENTICATION',
   approved_components_candidate:out,
   provider_source_authenticated:false as const,
   provider_manifest_complete_verified:false as const,
  });
  return Object.freeze({...FLAGS,decision:'SHAPE_ONLY_UNVERIFIED',
    reason:null,observed});
 }catch(e){
  return deny(e instanceof Invalid?e.code:'INVALID_INPUT');
 }
}
