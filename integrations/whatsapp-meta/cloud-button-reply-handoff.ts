/**
 * WhatsApp Cloud API BUTTON REPLY technical handoff (offline only).
 *
 * Reuses cloud-webhook-handoff.ts for HMAC verification of exact raw bytes,
 * trusted WABA/phone routing and whole-batch event shape verification.
 * No endpoint, HTTP response/ACK, Graph, DB, authorization or case transition.
 *
 * Two intentionally distinct inbound forms:
 * 1. Template quick reply: message.type=button, button={text,payload}.
 * 2. Standalone interactive button: type=interactive,
 *    interactive={type:button_reply,button_reply:{id,title}}.
 *
 * A signed Meta message is not a verified consent, catalog policy choice,
 * authorized sales action, or unique callback proof. Technical observations
 * retain content/participant data and MUST NOT be logged.
 */
import {inspectCloudWebhookForHandoff,
 type CloudRouteScope,type CloudObservation}
 from './cloud-webhook-handoff.ts';

export type TechnicalButtonReply=Readonly<{
 kind:'template_quick_reply'|'interactive_button_reply';
 waba_id:string;phone_number_id:string;
 provider_message_id:string;provider_timestamp:string;
 participant_identifier:string;
 /** TECHNICAL candidate; actual acceptance requires trusted S0/catalog binding. */
 button_value:string;display_text:string;
 reply_to_provider_message_id:string|null;
 position:CloudObservation['position'];
}>;
type Denial='VERIFICATION_DENIED'|'UNSUPPORTED_REPLY_SHAPE'|
 'UNSUPPORTED_INTERACTIVE_VARIANT'|'INTERNAL_ALIGNMENT_DENIED';
type Flags=Readonly<{
 ack_allowed:false;send_authorized:false;s0_write_authorized:false;
 retry_external:false;production_authorized:false;
 delivery_confirmed:false;case_transition_authorized:false;
 commercial_effect_authorized:false;catalog_choice_verified:false;
 consent_verified:false;deduplicated:false;
}>;
export type ButtonReplyHandoff=Flags&(
 Readonly<{decision:'DENIED';reason:Denial;observations:readonly [];raw_sha256:null}>|
 Readonly<{decision:'SIGNED_CANDIDATES_NOT_DURABLE';reason:null;
 observations:readonly TechnicalButtonReply[];raw_sha256:string}>
);
const FLAGS=Object.freeze({
 ack_allowed:false,send_authorized:false,s0_write_authorized:false,
 retry_external:false,production_authorized:false,
 delivery_confirmed:false,case_transition_authorized:false,
 commercial_effect_authorized:false,catalog_choice_verified:false,
 consent_verified:false,deduplicated:false,
} as const);
const deny=(reason:Denial):ButtonReplyHandoff=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
 observations:Object.freeze([]) as readonly [],raw_sha256:null,
});
const rec=(v:unknown):v is Record<string,unknown> =>
 typeof v==='object'&&v!==null&&!Array.isArray(v);
const ascii=(v:unknown):v is string =>
 typeof v==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(v);
const label=(v:unknown):v is string =>
 typeof v==='string'&&v.length>0&&[...v].length<=60&&
 !/[\u0000-\u001f\u007f]/.test(v)&&
 !/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/.test(v);
const wamid=(v:unknown):v is string =>
 typeof v==='string'&&/^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$/.test(v);
const fields=(v:Record<string,unknown>,keys:readonly string[]) =>
 Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
/**
 * Does NOT validate button membership in an approved template. The backend
 * must reconcile the payload with the current S0 catalog and originating
 * sent attempt, which remain unimplemented/unratified.
 */
export async function inspectSignedMetaButtonReplies(
 rawBody:Uint8Array,signature:string|null,appSecret:string,
 trustedRoute:CloudRouteScope,limits?:{maxBodyBytes?:number;maxEvents?:number},
):Promise<ButtonReplyHandoff>{
 if(!(rawBody instanceof Uint8Array))return deny('VERIFICATION_DENIED');
 const max=limits?.maxBodyBytes??256*1024;
 if(!Number.isSafeInteger(max)||max<1||rawBody.byteLength>max)
  return deny('VERIFICATION_DENIED');
 // Snapshot before any async HMAC; the same bytes are re-read only *after*
 // existing verifier authenticates that snapshot.
 const body=Uint8Array.from(rawBody);
 let verified:Awaited<ReturnType<typeof inspectCloudWebhookForHandoff>>;
 try{
  verified=await inspectCloudWebhookForHandoff(
   body,signature,appSecret,trustedRoute,limits);
 }catch{return deny('VERIFICATION_DENIED');}
 if(verified.outcome!=='AUTHENTICATED_NOT_DURABLE')
  return deny('VERIFICATION_DENIED');
 let parsed:unknown;
 try{parsed=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(body));}
 catch{return deny('INTERNAL_ALIGNMENT_DENIED');}
 if(!rec(parsed)||!Array.isArray(parsed.entry))
  return deny('INTERNAL_ALIGNMENT_DENIED');
 const out:TechnicalButtonReply[]=[];
 for(const evt of verified.observations){
  if(evt.kind!=='inbound_message')continue;
  const p=evt.position;
  const entry=parsed.entry[p.entry_index];
  const change=rec(entry)&&Array.isArray(entry.changes)
   ?entry.changes[p.change_index]:null;
  const value=rec(change)?change.value:null;
  const message=rec(value)&&Array.isArray(value.messages)
   ?value.messages[p.item_index]:null;
  if(!rec(message)||message.type!==evt.provider_kind||
      message.id!==evt.provider_message_id||
      message.from!==evt.participant_identifier)
   return deny('INTERNAL_ALIGNMENT_DENIED');
  if(evt.provider_kind!=='button'&&evt.provider_kind!=='interactive')
   continue;
  let kind:TechnicalButtonReply['kind'],buttonValue:string,displayText:string;
  if(evt.provider_kind==='button'){
   if(!rec(message.button)||!fields(message.button,['text','payload'])||
      !ascii(message.button.payload)||!label(message.button.text))
    return deny('UNSUPPORTED_REPLY_SHAPE');
   kind='template_quick_reply';
   buttonValue=message.button.payload;
   displayText=message.button.text;
  }else{
   if(!rec(message.interactive)||
      !fields(message.interactive,['type','button_reply'])||
      message.interactive.type!=='button_reply')
    return deny('UNSUPPORTED_INTERACTIVE_VARIANT');
   const reply=message.interactive.button_reply;
   if(!rec(reply)||!fields(reply,['id','title'])||
      !ascii(reply.id)||!label(reply.title))
    return deny('UNSUPPORTED_REPLY_SHAPE');
   kind='interactive_button_reply';
   buttonValue=reply.id;
   displayText=reply.title;
  }
  let contextId:string|null=null;
  if(message.context!==undefined){
   if(!rec(message.context)||!wamid(message.context.id))
    return deny('UNSUPPORTED_REPLY_SHAPE');
   contextId=message.context.id;
  }
  out.push(Object.freeze({
   kind,waba_id:evt.waba_id,phone_number_id:evt.phone_number_id,
   provider_message_id:evt.provider_message_id,
   provider_timestamp:evt.provider_timestamp,
   participant_identifier:evt.participant_identifier,
   button_value:buttonValue,display_text:displayText,
   reply_to_provider_message_id:contextId,
   position:Object.freeze({...p}),
  }));
 }
 return Object.freeze({...FLAGS,decision:'SIGNED_CANDIDATES_NOT_DURABLE',
  reason:null,observations:Object.freeze(out),raw_sha256:verified.raw_sha256});
}
