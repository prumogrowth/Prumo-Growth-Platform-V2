/**
 * Offline technical evidence for incoming Cloud API "unsupported" messages.
 * No ACK, transport, S0 persistence, commercial classification or auto-reply.
 * HMAC, raw-byte snapshot, trusted WABA/phone scope and batch limits are
 * delegated unchanged to cloud-webhook-handoff.ts.
 */
import {inspectCloudWebhookForHandoff,
 type CloudRouteScope,type CloudObservation}
 from './cloud-webhook-handoff.ts';

export type UnsupportedErrorCode=Readonly<{
 /** Claimed provider code, not a provider-authenticated remediation policy. */
 code:number;error_subcode:number|null;
}>;
export type TechnicalUnsupportedMessage=Readonly<{
 kind:'incoming_unsupported_message';
 waba_id:string;phone_number_id:string;
 provider_message_id:string;provider_timestamp:string;
 participant_identifier:string;
 provider_subtype_untrusted:string|null;
 errors:readonly UnsupportedErrorCode[];
 position:CloudObservation['position'];
}>;
type Reason='VERIFICATION_DENIED'|'UNSUPPORTED_ERROR_SHAPE'|
 'INTERNAL_ALIGNMENT_DENIED';
const FLAGS=Object.freeze({
 ack_allowed:false,send_authorized:false,s0_write_authorized:false,
 retry_external:false,production_authorized:false,
 delivery_confirmed:false,case_transition_authorized:false,
 commercial_effect_authorized:false,consent_verified:false,
 deduplicated:false,provider_error_action_authorized:false,
 inbound_content_recovered:false,auto_reply_authorized:false,
 definitive_failure_count_increment:false,
} as const);
type Flags=typeof FLAGS;
export type UnsupportedHandoff=Flags&(
 Readonly<{decision:'DENIED';reason:Reason;
  observations:readonly [];raw_sha256:null}>|
 Readonly<{decision:'SIGNED_UNSUPPORTED_NOT_DURABLE';reason:null;
  observations:readonly TechnicalUnsupportedMessage[];raw_sha256:string}>
);
const deny=(reason:Reason):UnsupportedHandoff=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
 observations:Object.freeze([]) as readonly [],raw_sha256:null,
});
const obj=(v:unknown):v is Record<string,unknown>=>
 typeof v==='object'&&v!==null&&!Array.isArray(v);
const keysAllowed=(v:Record<string,unknown>,allowed:readonly string[])=>
 Object.keys(v).every(k=>allowed.includes(k));
const code=(v:unknown):v is number=>
 typeof v==='number'&&Number.isSafeInteger(v)&&v>0;
const isText=(v:unknown,max:number):v is string=>
 typeof v==='string'&&[...v].length<=max&&
 !/[\u0000-\u001f\u007f]/.test(v)&&
 !/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/.test(v);
function parseErrors(message:Record<string,unknown>):
 {subtype:string|null;codes:readonly UnsupportedErrorCode[]}|null{
 const errors=message.errors;
 if(!Array.isArray(errors)||errors.length<1||errors.length>8)return null;
 let subtype:string|null=null;
 if(message.unsupported!==undefined){
  const u=message.unsupported;
  if(!obj(u)||Object.keys(u).length!==1||!Object.hasOwn(u,'type')||
     typeof u.type!=='string'||!/^[A-Za-z0-9_.:-]{1,64}$/.test(u.type))
   return null;
  subtype=u.type;
 }
 const out:UnsupportedErrorCode[]=[];
 for(const value of errors){
  if(!obj(value)||!code(value.code)||!keysAllowed(value,[
   'code','error_subcode','title','message','error_data','fbtrace_id',
  ]))return null;
  if(value.error_subcode!==undefined&&!code(value.error_subcode))return null;
  if(value.title!==undefined&&!isText(value.title,512))return null;
  if(value.message!==undefined&&!isText(value.message,1024))return null;
  if(value.fbtrace_id!==undefined&&!isText(value.fbtrace_id,256))return null;
  if(value.error_data!==undefined){
   const data=value.error_data;
   if(!obj(data)||!keysAllowed(data,['details','messaging_product'])||
      data.details!==undefined&&!isText(data.details,2048)||
      data.messaging_product!==undefined&&data.messaging_product!=='whatsapp')
    return null;
  }
  // Deliberately return no free-form titles, details, trace IDs or text.
  out.push(Object.freeze({
   code:value.code,error_subcode:value.error_subcode??null,
  }) as UnsupportedErrorCode);
 }
 return {subtype,codes:Object.freeze(out)};
}

/**
 * Observes signed unsupported inbound events without assuming their content
 * exists or that the numeric error authorizes a business/customer response.
 * Mixed batches are all-or-nothing: malformed errors deny the entire result.
 */
export async function inspectSignedMetaUnsupportedMessages(
 rawBody:Uint8Array,signature:string|null,appSecret:string,
 trustedRoute:CloudRouteScope,limits?:{maxBodyBytes?:number;maxEvents?:number},
):Promise<UnsupportedHandoff>{
 if(!(rawBody instanceof Uint8Array))return deny('VERIFICATION_DENIED');
 const max=limits?.maxBodyBytes??256*1024;
 if(!Number.isSafeInteger(max)||max<1||rawBody.byteLength>max)
  return deny('VERIFICATION_DENIED');
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
 if(!obj(parsed)||!Array.isArray(parsed.entry))
  return deny('INTERNAL_ALIGNMENT_DENIED');
 const result:TechnicalUnsupportedMessage[]=[];
 for(const evt of verified.observations){
  if(evt.kind!=='inbound_message')continue;
  const pos=evt.position;
  const entry=parsed.entry[pos.entry_index];
  const change=obj(entry)&&Array.isArray(entry.changes)
   ?entry.changes[pos.change_index]:null;
  const value=obj(change)?change.value:null;
  const message=obj(value)&&Array.isArray(value.messages)
   ?value.messages[pos.item_index]:null;
  if(!obj(message)||message.type!==evt.provider_kind||
     message.id!==evt.provider_message_id||
     message.from!==evt.participant_identifier)
   return deny('INTERNAL_ALIGNMENT_DENIED');
  if(evt.provider_kind!=='unsupported')continue;
  const diagnosed=parseErrors(message);
  if(!diagnosed)return deny('UNSUPPORTED_ERROR_SHAPE');
  result.push(Object.freeze({
   kind:'incoming_unsupported_message' as const,
   waba_id:evt.waba_id,phone_number_id:evt.phone_number_id,
   provider_message_id:evt.provider_message_id,
   provider_timestamp:evt.provider_timestamp,
   participant_identifier:evt.participant_identifier,
   provider_subtype_untrusted:diagnosed.subtype,
   errors:diagnosed.codes,position:Object.freeze({...pos}),
  }));
 }
 return Object.freeze({...FLAGS,
  decision:'SIGNED_UNSUPPORTED_NOT_DURABLE' as const,
  reason:null,observations:Object.freeze(result),
  raw_sha256:verified.raw_sha256});
}
