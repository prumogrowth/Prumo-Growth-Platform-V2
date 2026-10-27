/**
 * Cloud API incoming reaction inspection, OFFLINE ONLY.
 *
 * Consumes an already-signed webhook via the existing whole-batch HMAC and
 * trusted WABA/phone routing verifier. Never dispatches, acknowledges,
 * persists, correlates S0 records or asserts that a reaction took effect.
 * Opaque callback identifiers, phone numbers and emojis are sensitive.
 */
import {inspectCloudWebhookForHandoff,
 type CloudRouteScope,type CloudObservation}
 from './cloud-webhook-handoff.ts';

export type TechnicalReaction=Readonly<{
 kind:'incoming_reaction';
 waba_id:string;phone_number_id:string;
 /** The inbound reaction event's own ID, NOT the target's ID. */
 provider_message_id:string;provider_timestamp:string;
 participant_identifier:string;
 /** Claimed target message ID; no authoritative S0 binding was checked. */
 target_provider_message_id:string;
 /** Empty string is the Meta removal marker, not proof of prior reaction. */
 emoji:string;
 operation:'add_candidate'|'remove_candidate';
 position:CloudObservation['position'];
}>;
type Denial='VERIFICATION_DENIED'|'UNSUPPORTED_REACTION_SHAPE'|
 'INTERNAL_ALIGNMENT_DENIED';
type Flags=Readonly<{
 ack_allowed:false;send_authorized:false;s0_write_authorized:false;
 retry_external:false;production_authorized:false;
 delivery_confirmed:false;case_transition_authorized:false;
 commercial_effect_authorized:false;consent_verified:false;
 deduplicated:false;target_message_correlated:false;
 reaction_effect_confirmed:false;
}>;
export type ReactionHandoff=Flags&(
 Readonly<{decision:'DENIED';reason:Denial;
  observations:readonly [];raw_sha256:null}>|
 Readonly<{decision:'SIGNED_REACTIONS_NOT_DURABLE';reason:null;
  observations:readonly TechnicalReaction[];raw_sha256:string}>
);
const FLAGS=Object.freeze({
 ack_allowed:false,send_authorized:false,s0_write_authorized:false,
 retry_external:false,production_authorized:false,
 delivery_confirmed:false,case_transition_authorized:false,
 commercial_effect_authorized:false,consent_verified:false,
 deduplicated:false,target_message_correlated:false,
 reaction_effect_confirmed:false,
} as const);
const deny=(reason:Denial):ReactionHandoff=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
 observations:Object.freeze([]) as readonly [],raw_sha256:null,
});
const rec=(v:unknown):v is Record<string,unknown>=>
 typeof v==='object'&&v!==null&&!Array.isArray(v);
const exact=(v:Record<string,unknown>,keys:readonly string[])=>
 Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const wamid=(v:unknown):v is string=>
 typeof v==='string'&&/^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$/.test(v);
const unicodeValid=(s:string)=>
 !/[\u0000-\u001f\u007f]/.test(s)&&
 !/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/.test(s);
/**
 * A nonempty string is only a claimed reaction glyph. We do not pretend
 * to have validated its support against the current Meta emoji repertoire.
 */
const reactionEmoji=(v:unknown):v is string=>
 typeof v==='string'&&[...v].length<=32&&unicodeValid(v);

/**
 * HMAC validation precedes all technical extraction. As in the existing
 * selection handoff, the entire verified batch must align or nothing is
 * returned. An empty observation list does not confer ACK permission.
 */
export async function inspectSignedMetaReactions(
 rawBody:Uint8Array,signature:string|null,appSecret:string,
 trustedRoute:CloudRouteScope,limits?:{maxBodyBytes?:number;maxEvents?:number},
):Promise<ReactionHandoff>{
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
 const results:TechnicalReaction[]=[];
 for(const evt of verified.observations){
  if(evt.kind!=='inbound_message')continue;
  const pos=evt.position;
  const entry=parsed.entry[pos.entry_index];
  const change=rec(entry)&&Array.isArray(entry.changes)
   ?entry.changes[pos.change_index]:null;
  const value=rec(change)?change.value:null;
  const message=rec(value)&&Array.isArray(value.messages)
   ?value.messages[pos.item_index]:null;
  if(!rec(message)||message.id!==evt.provider_message_id||
     message.type!==evt.provider_kind||
     message.from!==evt.participant_identifier)
   return deny('INTERNAL_ALIGNMENT_DENIED');
  if(evt.provider_kind!=='reaction')continue;
  const item=message.reaction;
  if(!rec(item)||!exact(item,['message_id','emoji'])||
     !wamid(item.message_id)||!reactionEmoji(item.emoji))
   return deny('UNSUPPORTED_REACTION_SHAPE');
  results.push(Object.freeze({
   kind:'incoming_reaction' as const,
   waba_id:evt.waba_id,phone_number_id:evt.phone_number_id,
   provider_message_id:evt.provider_message_id,
   provider_timestamp:evt.provider_timestamp,
   participant_identifier:evt.participant_identifier,
   target_provider_message_id:item.message_id,
   emoji:item.emoji,
   operation:item.emoji===''?'remove_candidate' as const:'add_candidate' as const,
   position:Object.freeze({...pos}),
  }));
 }
 return Object.freeze({...FLAGS,decision:'SIGNED_REACTIONS_NOT_DURABLE',
  reason:null,observations:Object.freeze(results),
  raw_sha256:verified.raw_sha256});
}
