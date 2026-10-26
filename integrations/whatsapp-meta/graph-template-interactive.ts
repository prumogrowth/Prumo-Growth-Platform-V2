/**
 * Meta WhatsApp interactive TEMPLATE quick-reply payload preparation, offline.
 *
 * Additive projection over the existing (approved text body/header) preflight:
 * the trusted catalog supplied by a future S0 service must attest to the
 * COMPLETE quick-reply schema. The existing text-only schema is a base
 * projection, NOT on its own approval for a button template.
 *
 * This returns an INERT relative Graph request: no token, URL origin, network,
 * send authority, ACK, DB operation, dynamic client-controlled button payload
 * or bypass of business policy/opt-in. The request body contains PII; NEVER log.
 *
 * Official Meta reference for component shape:
 * https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive
 */
import {
 prepareGraphTemplateRequest, TemplatePreflightError,
 type TemplateIntent, type TrustedTemplateSnapshot,
 type TrustedTemplateScope,
} from './graph-template.ts';

type Button = Readonly<{kind:'QUICK_REPLY';index:number;payload:string}>;
export type TrustedQuickReplyCatalog=Readonly<{
 contract:'prumo.meta.quickreply.catalog.offline.v1';
 approval:'APPROVED';
 schema_complete:true;
 template_name:string;
 language_code:string;
 template_revision_ref:string;
 scope:TrustedTemplateScope;
 buttons:readonly Button[];
}>;
export type QuickReplyParameter=Readonly<{
 type:'button';sub_type:'quick_reply';index:string;
 parameters:readonly [Readonly<{type:'payload';payload:string}>];
}>;
type TemplateBase=ReturnType<typeof prepareGraphTemplateRequest>;
export type GraphQuickReplyRequest=Readonly<{
 method:TemplateBase['method'];
 relative_path:string;content_type:TemplateBase['content_type'];
 body:Readonly<{
  messaging_product:'whatsapp';recipient_type:'individual';to:string;
  type:'template';
  template:Readonly<{
   name:string;language:Readonly<{code:string}>;
   components:readonly (NonNullable<TemplateBase['body']['template']['components']>[number]|QuickReplyParameter)[];
  }>;
 }>;
}>;

const SCOPE_KEYS=['concessionaria_id','canal_id','meta_app_ref','meta_waba_id','phone_number_id'] as const;
const INTENT_KEYS=[
 'contract_version','intent_id','attempt_id','correlation_id',
 'authorized_business_action','authorized_state_version',
 ...SCOPE_KEYS,'recipient_verified','template_name','language_code',
 'template_revision_ref','header_text_parameter','body_text_parameters'
] as const;
const err=(code:TemplatePreflightError['code']='UNSUPPORTED_COMPONENTS'):never=>{
 throw new TemplatePreflightError(code);
};
/** Reject accessors, symbols, prototypes and unknown/injected fields. */
function fields(raw:unknown,allowed:readonly string[],required:readonly string[]):Record<string,unknown>{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return err();
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return err();
  const d=Object.getOwnPropertyDescriptors(raw);
  const keys=Reflect.ownKeys(raw);
  if(keys.some(k=>typeof k!=='string'||!allowed.includes(k))||
     required.some(k=>!Object.hasOwn(d,k))||
     keys.some(k=>!Object.hasOwn(d[k as string],'value')))return err();
  return Object.fromEntries(keys.map(k=>[k,d[k as string].value]));
 }catch{return err();}
}
function validateCatalog(
 raw:TrustedQuickReplyCatalog,intent:TemplateIntent,scope:TrustedTemplateScope
):readonly QuickReplyParameter[]{
 const c=fields(raw,[
  'contract','approval','schema_complete','template_name','language_code',
  'template_revision_ref','scope','buttons'
 ],['contract','approval','schema_complete','template_name','language_code',
  'template_revision_ref','scope','buttons']);
 if(c.contract!=='prumo.meta.quickreply.catalog.offline.v1'||
    c.approval!=='APPROVED'||c.schema_complete!==true)
  return err('TEMPLATE_NOT_APPROVED');
 if(c.template_name!==intent.template_name||
    c.language_code!==intent.language_code||
    c.template_revision_ref!==intent.template_revision_ref)
  return err('TEMPLATE_REVISION_MISMATCH');
 const catScope=fields(c.scope,SCOPE_KEYS,SCOPE_KEYS);
 const live=fields(scope,SCOPE_KEYS,SCOPE_KEYS);
 for(const k of SCOPE_KEYS){
  if(typeof catScope[k]!=='string'||!catScope[k]||
     catScope[k]!==live[k]||catScope[k]!==intent[k])return err('SCOPE_MISMATCH');
 }
 if(!Array.isArray(c.buttons)||c.buttons.length<1||c.buttons.length>3)
  return err();
 return Object.freeze(c.buttons.map((rawButton,i)=>{
  const b=fields(rawButton,['kind','index','payload'],['kind','index','payload']);
  // All declared buttons are required, and index order must match the
  // complete approved snapshot. Never silently omit a business CTA.
  if(b.kind!=='QUICK_REPLY'||b.index!==i||
     typeof b.payload!=='string'||!/^[A-Za-z0-9_.:-]{1,128}$/.test(b.payload))
   return err('INVALID_PARAMETERS');
  return Object.freeze({
   type:'button' as const,sub_type:'quick_reply' as const,index:String(i),
   parameters:Object.freeze([Object.freeze({type:'payload' as const,payload:b.payload})]) as
    readonly [Readonly<{type:'payload';payload:string}>],
  });
 }));
}
/**
 * Only static opaque quick-reply payloads provided by a trusted catalog.
 * No dynamic caller-supplied button list; scope, revision, approval, schema
 * and body parameters are checked against both trusted inputs.
 */
export function prepareGraphQuickReplyTemplateRequest(
 intent:TemplateIntent,
 trustedBaseTextSnapshot:TrustedTemplateSnapshot,
 trustedScope:TrustedTemplateScope,
 trustedCompleteButtonCatalog:TrustedQuickReplyCatalog,
 apiVersion:string,
):GraphQuickReplyRequest{
 const safe=fields(intent,INTENT_KEYS,[
  'contract_version','intent_id','attempt_id','correlation_id',
  'authorized_business_action','authorized_state_version',
  ...SCOPE_KEYS,'recipient_verified','template_name','language_code',
  'template_revision_ref'
 ]) as unknown as TemplateIntent;
 // Core builder still enforces policy-free structural constraints of
 // C06, recipient, text placeholders, version and base catalog scope.
 const base=prepareGraphTemplateRequest(
  safe,trustedBaseTextSnapshot,trustedScope,apiVersion);
 const buttons=validateCatalog(trustedCompleteButtonCatalog,safe,trustedScope);
 const existing=base.body.template.components??[];
 const components=Object.freeze([...existing,...buttons]);
 return Object.freeze({
  method:base.method,relative_path:base.relative_path,
  content_type:base.content_type,
  body:Object.freeze({
   messaging_product:'whatsapp' as const,
   recipient_type:'individual' as const,to:base.body.to,
   type:'template' as const,
   template:Object.freeze({
    name:base.body.template.name,
    language:Object.freeze({code:base.body.template.language.code}),
    components,
   }),
  }),
 });
}
