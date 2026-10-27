/**
 * Signed failed-delivery STATUS error references only. OFFLINE.
 *
 * A status callback may report a failure after an earlier Graph HTTP accept.
 * HMAC, WABA/phone isolation and event positions are checked by the existing
 * whole-batch ingress handoff. Observing error codes is NOT S0 correlation,
 * an increment of commercial failure counters, retry or delivery evidence.
 */
import {inspectCloudWebhookForHandoff,
 type CloudRouteScope,type CloudObservation}
 from './cloud-webhook-handoff.ts';
import {isMetaWamid} from './status-evidence.ts';

export type ReportedStatusErrorCode=Readonly<{
 code:number;
 /** Deprecated by Meta; kept only when present as a technical claim. */
 error_subcode:number|null;
}>;
export type FailedStatusErrorObservation=Readonly<{
 kind:'provider_reported_failed_status_errors';
 reported_status:'failed';
 waba_id:string;phone_number_id:string;
 /** Status id refers to the SENT message; it is NOT a callback event id. */
 provider_message_id:string;
 provider_timestamp:string;
 recipient_identifier:string;
 codes:readonly ReportedStatusErrorCode[];
 position:CloudObservation['position'];
}>;
type Reason='VERIFICATION_DENIED'|'MALFORMED_STATUS_ERRORS'|
 'INCONSISTENT_STATUS_ERRORS'|'INTERNAL_ALIGNMENT_DENIED';
const FLAGS=Object.freeze({
 ack_allowed:false,send_authorized:false,s0_write_authorized:false,
 retry_external:false,production_authorized:false,
 delivery_confirmed:false,case_transition_authorized:false,
 commercial_effect_authorized:false,consent_verified:false,
 deduplicated:false,attempt_correlated:false,
 provider_failure_effect_confirmed:false,
 definitive_failure_count_increment:false,
 automatic_retry_authorized:false,
} as const);
type Flags=typeof FLAGS;
export type FailedStatusErrorsHandoff=Flags&(
 Readonly<{decision:'DENIED';reason:Reason;
  observations:readonly [];raw_sha256:null}> |
 Readonly<{decision:'SIGNED_FAILED_STATUS_ERRORS_NOT_DURABLE';reason:null;
  observations:readonly FailedStatusErrorObservation[];
  raw_sha256:string}>
);
const deny=(reason:Reason):FailedStatusErrorsHandoff=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
 observations:Object.freeze([]) as readonly [],raw_sha256:null,
});
const rec=(v:unknown):v is Record<string,unknown>=>
 typeof v==='object'&&v!==null&&!Array.isArray(v);
const allowed=(v:Record<string,unknown>,keys:readonly string[])=>
 Object.keys(v).every(k=>keys.includes(k));
const numeric=(v:unknown):v is number=>
 typeof v==='number'&&Number.isSafeInteger(v)&&v>0;
const text=(v:unknown,max:number):v is string=>
 typeof v==='string'&&[...v].length<=max&&
 !/[\u0000-\u001f\u007f]/.test(v)&&
 !/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/.test(v);
function inspectedErrors(input:unknown):readonly ReportedStatusErrorCode[]|null{
 if(!Array.isArray(input)||input.length<1||input.length>8)return null;
 const codes:ReportedStatusErrorCode[]=[];
 for(const error of input){
  if(!rec(error)||!numeric(error.code)||!allowed(error,[
   'code','error_subcode','title','message','type',
   'error_data','fbtrace_id','href',
  ]))return null;
  if(error.error_subcode!==undefined&&!numeric(error.error_subcode))
   return null;
  if(error.title!==undefined&&!text(error.title,512))return null;
  if(error.message!==undefined&&!text(error.message,1024))return null;
  if(error.type!==undefined&&!text(error.type,128))return null;
  if(error.fbtrace_id!==undefined&&!text(error.fbtrace_id,256))return null;
  // The optional help link is never opened or returned.
  if(error.href!==undefined&&!text(error.href,2048))return null;
  if(error.error_data!==undefined){
   const d=error.error_data;
   if(!rec(d)||!allowed(d,['details','messaging_product'])||
      (d.details!==undefined&&!text(d.details,2048))||
      (d.messaging_product!==undefined&&d.messaging_product!=='whatsapp'))
    return null;
  }
  // No free-form diagnostics, links, titles or trace IDs are emitted.
  codes.push(Object.freeze({
   code:error.code,error_subcode:error.error_subcode??null,
  }) as ReportedStatusErrorCode);
 }
 return Object.freeze(codes);
}

/**
 * One invalid status/errors item denies the entire signed batch, without
 * revealing recipient, error details, or partial observations on failure.
 * Absence of failed-status observations is not a durable ingress acceptance.
 */
export async function inspectSignedMetaFailedStatusErrors(
 rawBody:Uint8Array,signature:string|null,appSecret:string,
 trustedRoute:CloudRouteScope,limits?:{maxBodyBytes?:number;maxEvents?:number},
):Promise<FailedStatusErrorsHandoff>{
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
 if(!rec(parsed)||!Array.isArray(parsed.entry))
  return deny('INTERNAL_ALIGNMENT_DENIED');
 const items:FailedStatusErrorObservation[]=[];
 for(const evt of verified.observations){
  if(evt.kind!=='status_callback')continue;
  const pos=evt.position;
  if(pos.array_kind!=='statuses')return deny('INTERNAL_ALIGNMENT_DENIED');
  const entry=parsed.entry[pos.entry_index];
  const change=rec(entry)&&Array.isArray(entry.changes)
   ?entry.changes[pos.change_index]:null;
  const value=rec(change)?change.value:null;
  const s=rec(value)&&Array.isArray(value.statuses)
   ?value.statuses[pos.item_index]:null;
  if(!rec(s)||s.id!==evt.provider_message_id||
     s.recipient_id!==evt.participant_identifier||
     s.status!==evt.provider_kind)
   return deny('INTERNAL_ALIGNMENT_DENIED');
  if(evt.provider_kind!=='failed'){
   // Never silently ignore an unexpected error array on a success/progress
   // callback; such ambiguity is not evidence of delivery.
   if(Object.hasOwn(s,'errors'))return deny('INCONSISTENT_STATUS_ERRORS');
   continue;
  }
  if(!isMetaWamid(evt.provider_message_id))
   return deny('MALFORMED_STATUS_ERRORS');
  const codes=inspectedErrors(s.errors);
  if(!codes)return deny('MALFORMED_STATUS_ERRORS');
  items.push(Object.freeze({
   kind:'provider_reported_failed_status_errors' as const,
   reported_status:'failed' as const,
   waba_id:evt.waba_id,phone_number_id:evt.phone_number_id,
   provider_message_id:evt.provider_message_id,
   provider_timestamp:evt.provider_timestamp,
   recipient_identifier:evt.participant_identifier,
   codes,position:Object.freeze({...pos}),
  }));
 }
 return Object.freeze({...FLAGS,
  decision:'SIGNED_FAILED_STATUS_ERRORS_NOT_DURABLE' as const,
  reason:null,observations:Object.freeze(items),
  raw_sha256:verified.raw_sha256});
}
