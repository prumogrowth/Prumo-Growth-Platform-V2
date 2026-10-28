/**
 * Offline read-only inspection of inbound quoted-reply context references.
 * Reuses the full signed webhook verifier: the caller must supply a trusted
 * WABA/phone scope and secret selected OUTSIDE untrusted inbound JSON.
 *
 * This is an uncorrelated technical observation. A quote's context.id
 * neither proves the original message exists nor grants S0/case authority.
 * Raw message text, product metadata, referral fields and mentions are never
 * copied to the output. No transport, ACK, durable write, retry, or Graph.
 */
import {
 inspectCloudWebhookForHandoff,
 type CloudRouteScope,type CloudObservation,
} from './cloud-webhook-handoff.ts';
import {isMetaWamid} from './status-evidence.ts';

export type SignedReplyContextObservation=Readonly<{
 kind:'incoming_quoted_reference';
 waba_id:string;phone_number_id:string;
 provider_message_id:string;provider_timestamp:string;
 participant_identifier:string;
 /** Untrusted ID of quoted/replied-to message; NOT an S0 binding. */
 quoted_provider_message_id:string;
 /** Optional claimed sender of the quoted message; NOT civil identity. */
 quoted_sender_identifier_untrusted:string|null;
 position:CloudObservation['position'];
}>;
type Reason='VERIFICATION_DENIED'|'INVALID_CONTEXT_SHAPE'|
 'INTERNAL_ALIGNMENT_DENIED';
const FLAGS=Object.freeze({
 ack_allowed:false,send_authorized:false,s0_write_authorized:false,
 retry_external:false,production_authorized:false,
 delivery_confirmed:false,case_transition_authorized:false,
 commercial_effect_authorized:false,consent_verified:false,
 deduplicated:false,quoted_message_correlated:false,
 quoted_content_recovered:false,quoted_sender_verified:false,
 auto_reply_authorized:false,provider_action_authorized:false,
} as const);
type Flags=typeof FLAGS;
export type QuotedContextHandoff=Flags&(
 Readonly<{decision:'DENIED';reason:Reason;
  observations:readonly [];raw_sha256:null}>|
 Readonly<{decision:'SIGNED_QUOTED_REFERENCES_NOT_DURABLE';reason:null;
  observations:readonly SignedReplyContextObservation[];
  raw_sha256:string}>
);
const deny=(reason:Reason):QuotedContextHandoff=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
 observations:Object.freeze([]) as readonly [],raw_sha256:null,
});
const record=(v:unknown):v is Record<string,unknown>=>
 typeof v==='object'&&v!==null&&!Array.isArray(v);
const participant=(v:unknown):v is string=>
 typeof v==='string'&&/^[0-9]{8,15}$/.test(v);
type ContextRead=Readonly<{quoted_provider_message_id:string;
 quoted_sender_identifier_untrusted:string|null}>|null;
/**
 * An object with forwarding/product metadata but NO context.id is NOT
 * silently treated as a quoted reply. Unknown ancillary context fields are
 * not trusted and not surfaced (forward-compatible).
 *
 * Invalid id/from combinations fail the entire webhook; no partial results.
 */
function parseContext(v:unknown):ContextRead|false{
 if(!record(v))return false;
 const hasId=Object.hasOwn(v,'id'),hasFrom=Object.hasOwn(v,'from');
 if(!hasId){
  // Context may be a forwarded-message marker without a quoted target.
  // A sender claim without any referenced message is incoherent.
  return hasFrom?false:null;
 }
 if(!isMetaWamid(v.id))return false;
 if(hasFrom&&!participant(v.from))return false;
 return Object.freeze({
  quoted_provider_message_id:v.id,
  quoted_sender_identifier_untrusted:hasFrom?v.from:null,
 }) as ContextRead;
}

/** Each specialized result is tied to the same original authenticated body. */
export async function inspectSignedMetaQuotedContexts(
 rawBody:Uint8Array,signature:string|null,appSecret:string,
 trustedRoute:CloudRouteScope,limits?:{maxBodyBytes?:number;maxEvents?:number},
):Promise<QuotedContextHandoff>{
 if(!(rawBody instanceof Uint8Array))return deny('VERIFICATION_DENIED');
 // An independent byte snapshot prevents mutation after asynchronous HMAC.
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
 if(!record(parsed)||!Array.isArray(parsed.entry))
  return deny('INTERNAL_ALIGNMENT_DENIED');
 const out:SignedReplyContextObservation[]=[];
 for(const evt of verified.observations){
  if(evt.kind!=='inbound_message')continue;
  const p=evt.position;
  if(p.array_kind!=='messages')return deny('INTERNAL_ALIGNMENT_DENIED');
  const entry=parsed.entry[p.entry_index];
  const change=record(entry)&&Array.isArray(entry.changes)
   ?entry.changes[p.change_index]:null;
  const value=record(change)?change.value:null;
  const m=record(value)&&Array.isArray(value.messages)
   ?value.messages[p.item_index]:null;
  if(!record(m)||m.id!==evt.provider_message_id||
     m.type!==evt.provider_kind||m.from!==evt.participant_identifier)
   return deny('INTERNAL_ALIGNMENT_DENIED');
  if(!Object.hasOwn(m,'context'))continue;
  const quoted=parseContext(m.context);
  if(quoted===false)return deny('INVALID_CONTEXT_SHAPE');
  if(quoted===null)continue;
  out.push(Object.freeze({
   kind:'incoming_quoted_reference' as const,
   waba_id:evt.waba_id,phone_number_id:evt.phone_number_id,
   provider_message_id:evt.provider_message_id,
   provider_timestamp:evt.provider_timestamp,
   participant_identifier:evt.participant_identifier,
   ...quoted,position:Object.freeze({...p}),
  }));
 }
 return Object.freeze({...FLAGS,
  decision:'SIGNED_QUOTED_REFERENCES_NOT_DURABLE' as const,
  reason:null,observations:Object.freeze(out),
  raw_sha256:verified.raw_sha256});
}
