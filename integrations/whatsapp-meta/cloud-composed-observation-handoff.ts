/**
 * Meta Cloud webhook technical composition: ONE ordered observation per
 * SIGNED raw callback occurrence, no lost generic items or doubled slots.
 *
 * Existing narrow readers independently authenticate the same immutable
 * raw snapshot (including HMAC and trusted WABA/phone routing) ONLY WHEN
 * the already-authenticated base envelope contains their supported kind.
 * No bypass of any invoked reader's HMAC and no implicit S0 handoff.
 * Collisions, component denials, divergent raw hashes or missing expected
 * evidence deny the ENTIRE aggregate; nothing is persisted or ACKed.
 */
import {inspectCloudWebhookForHandoff,
 type CloudRouteScope,type CloudObservation}
 from './cloud-webhook-handoff.ts';
import {isMetaWamid} from './status-evidence.ts';
import {inspectSignedMetaSelections,
 type TechnicalSelection} from './cloud-button-reply-handoff.ts';
import {inspectSignedMetaReactions,
 type TechnicalReaction} from './cloud-reaction-handoff.ts';
import {inspectSignedMetaMediaMetadata,
 type TechnicalMediaMetadata} from './cloud-media-metadata-handoff.ts';
import {inspectSignedMetaUnsupportedMessages,
 type TechnicalUnsupportedMessage} from './cloud-unsupported-inbound-handoff.ts';
import {inspectSignedMetaFailedStatusErrors,
 type FailedStatusErrorObservation} from './cloud-failed-status-errors-handoff.ts';
import {inspectSignedMetaQuotedContexts,
 type SignedReplyContextObservation} from './cloud-quoted-context-handoff.ts';

export type SpecializedEvidence=TechnicalSelection|TechnicalReaction|
 TechnicalMediaMetadata|TechnicalUnsupportedMessage|FailedStatusErrorObservation;
export type AggregateKind=SpecializedEvidence['kind']|
 'uninterpreted_inbound'|'uninterpreted_status';
export type ComposedWebhookOccurrence=Readonly<{
 kind:AggregateKind;
 source_kind:CloudObservation['kind'];
 provider_kind:string;
 waba_id:string;phone_number_id:string;
 provider_message_id:string;provider_timestamp:string;
 participant_identifier:string;
 position:CloudObservation['position'];
 /** Present ONLY for one recognized narrow inspector, never synthesized. */
 evidence:SpecializedEvidence|null;
 /** Complementary quote metadata; NOT another event or correlated S0 record. */
 quoted_reference:SignedReplyContextObservation|null;
}>;
const FLAGS=Object.freeze({
 ack_allowed:false,send_authorized:false,s0_write_authorized:false,
 retry_external:false,production_authorized:false,
 delivery_confirmed:false,case_transition_authorized:false,
 commercial_effect_authorized:false,consent_verified:false,
 deduplicated:false,exactly_once_guaranteed:false,
 provider_failure_effect_confirmed:false,
 definitive_failure_count_increment:false,
 automatic_retry_authorized:false,
 quoted_message_correlated:false,quoted_content_recovered:false,
} as const);
type Flags=typeof FLAGS;
type Denial='VERIFICATION_DENIED'|'COMPONENT_DENIED'|
 'INCONSISTENT_SNAPSHOT'|'EVIDENCE_COLLISION_OR_GAP'|
 'INVALID_TECHNICAL_IDENTIFIERS';
export type ComposedWebhookHandoff=Flags&(
 Readonly<{decision:'DENIED';reason:Denial;
  occurrences:readonly [];raw_sha256:null}>|
 Readonly<{decision:'SIGNED_COMPOSED_NOT_DURABLE';reason:null;
  occurrences:readonly ComposedWebhookOccurrence[];
  raw_sha256:string;route_revision:number}>
);
const deny=(reason:Denial):ComposedWebhookHandoff=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
 occurrences:Object.freeze([]) as readonly [],raw_sha256:null,
});
const eventKey=(p:CloudObservation['position'])=>
 JSON.stringify([p.entry_index,p.change_index,p.array_kind,p.item_index]);
const rec=(v:unknown):v is Record<string,unknown>=>
 typeof v==='object'&&v!==null&&!Array.isArray(v);
/** Query ONLY the already authenticated payload for context fields. */
function detectContextSlots(body:Uint8Array,observations:readonly CloudObservation[]):
 Set<string>|null{
 let parsed:unknown;
 try{parsed=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(body));}
 catch{return null;}
 if(!rec(parsed)||!Array.isArray(parsed.entry))return null;
 const slots=new Set<string>();
 for(const evt of observations){
  if(evt.kind!=='inbound_message')continue;
  const p=evt.position,entry=parsed.entry[p.entry_index];
  const change=rec(entry)&&Array.isArray(entry.changes)
   ?entry.changes[p.change_index]:null;
  const value=rec(change)?change.value:null;
  const message=rec(value)&&Array.isArray(value.messages)
   ?value.messages[p.item_index]:null;
  if(!rec(message)||message.id!==evt.provider_message_id||
     message.type!==evt.provider_kind||
     message.from!==evt.participant_identifier)return null;
  if(Object.hasOwn(message,'context'))slots.add(eventKey(p));
 }
 return slots;
}
const selectedMessage=(kind:string)=>kind==='button'||kind==='interactive';
const mediaMessage=(kind:string)=>['image','audio','video','document','sticker'].includes(kind);
const specialExpected=(v:CloudObservation)=>v.kind==='status_callback'
 ? v.provider_kind==='failed'
 : selectedMessage(v.provider_kind)||
   v.provider_kind==='reaction'||
   mediaMessage(v.provider_kind)||
   v.provider_kind==='unsupported';
/**
 * Compositor-only strict technical grammar. The permissive base verifier
 * still authenticates and bounds the entire envelope; however its generic
 * observations must not expose malformed provider IDs, participants, or
 * uncontracted event kind strings as a trusted technical handoff.
 *
 * This is syntax checking, NEVER proof of civil identity or S0 correlation.
 */
const participantId=(s:string)=>/^[0-9]{8,15}$/.test(s);
const inboundKind=(s:string)=>/^[a-z][a-z0-9_]{0,63}$/.test(s);
const technicalIdsValid=(e:CloudObservation)=>
 isMetaWamid(e.provider_message_id)&&
 participantId(e.participant_identifier)&&
 (e.kind==='status_callback'||inboundKind(e.provider_kind));

/**
 * Read-only composition, not an ingress endpoint. All component readers run
 * against one caller-independent snapshot. The returned order follows the
 * original signed envelope (including message/status array boundaries).
 */
export async function inspectSignedMetaComposedWebhook(
 rawBody:Uint8Array,signature:string|null,appSecret:string,
 trustedRoute:CloudRouteScope,limits?:{maxBodyBytes?:number;maxEvents?:number},
):Promise<ComposedWebhookHandoff>{
 if(!(rawBody instanceof Uint8Array))return deny('VERIFICATION_DENIED');
 // Snapshot caller-owned trusted configuration BEFORE the first await. The
 // same route/revision/limits MUST be used by the base and every narrow
 // inspector; late caller mutations cannot alter provenance or decisions.
 let scope:CloudRouteScope;
 let cap:{maxBodyBytes?:number;maxEvents?:number}|undefined;
 try{
  scope=Object.freeze({
   waba_id:trustedRoute.waba_id,
   phone_number_id:trustedRoute.phone_number_id,
   revision:trustedRoute.revision,
  });
  cap=limits===undefined?undefined:Object.freeze({
   maxBodyBytes:limits.maxBodyBytes,
   maxEvents:limits.maxEvents,
  });
 }catch{return deny('VERIFICATION_DENIED');}
 const max=cap?.maxBodyBytes??256*1024;
 if(!Number.isSafeInteger(max)||max<1||rawBody.byteLength>max)
  return deny('VERIFICATION_DENIED');
 const body=Uint8Array.from(rawBody);
 let base:Awaited<ReturnType<typeof inspectCloudWebhookForHandoff>>;
 try{base=await inspectCloudWebhookForHandoff(
  body,signature,appSecret,scope,cap);
 }catch{return deny('VERIFICATION_DENIED');}
 if(base.outcome!=='AUTHENTICATED_NOT_DURABLE')
  return deny('VERIFICATION_DENIED');
 // Every signed occurrence must pass the same technical identity grammar,
 // INCLUDING generic/unknown kinds that no specialist currently parses.
 // Reject all before any narrow readers: no partial candidate escapes.
 if(base.observations.some(e=>!technicalIdsValid(e)))
  return deny('INVALID_TECHNICAL_IDENTIFIERS');
 const contextualSlots=detectContextSlots(body,base.observations);
 if(contextualSlots===null)return deny('INCONSISTENT_SNAPSHOT');
 let parts:Awaited<ReturnType<typeof inspectSignedMetaSelections>>|
  Awaited<ReturnType<typeof inspectSignedMetaReactions>>|
  Awaited<ReturnType<typeof inspectSignedMetaMediaMetadata>>|
  Awaited<ReturnType<typeof inspectSignedMetaUnsupportedMessages>>|
  Awaited<ReturnType<typeof inspectSignedMetaFailedStatusErrors>>;
 // Dispatch only readers relevant to an AUTHENTICATED event class.
 // This never trusts unsigned JSON and never skips the status guard when
 // sent/delivered/read callbacks need malformed-errors detection.
 // HMAC checks: 1 for generic-only; up to 7 if all kinds AND context occur.
 const readers=[
  {needed:(e:CloudObservation)=>e.kind==='inbound_message'&&
    selectedMessage(e.provider_kind),inspect:inspectSignedMetaSelections},
  {needed:(e:CloudObservation)=>e.kind==='inbound_message'&&
    e.provider_kind==='reaction',inspect:inspectSignedMetaReactions},
  {needed:(e:CloudObservation)=>e.kind==='inbound_message'&&
    mediaMessage(e.provider_kind),inspect:inspectSignedMetaMediaMetadata},
  {needed:(e:CloudObservation)=>e.kind==='inbound_message'&&
    e.provider_kind==='unsupported',inspect:inspectSignedMetaUnsupportedMessages},
  {needed:(e:CloudObservation)=>e.kind==='status_callback',
   inspect:inspectSignedMetaFailedStatusErrors},
 ] as const;
 const grouped:SpecializedEvidence[][]=[];
 let quotes:readonly SignedReplyContextObservation[]=[];
 try{
  for(const reader of readers){
   if(!base.observations.some(reader.needed))continue;
   parts=await reader.inspect(body,signature,appSecret,scope,cap);
   if(parts.decision==='DENIED')return deny('COMPONENT_DENIED');
   if(parts.raw_sha256!==base.raw_sha256)
    return deny('INCONSISTENT_SNAPSHOT');
   grouped.push([...parts.observations] as SpecializedEvidence[]);
  }
  // Context is a complementary dimension. It may coexist with ONE main
  // selection/media/reaction observation at the same position.
  // Never run this independent HMAC unless the verified body has context.
  if(contextualSlots.size>0){
   const q=await inspectSignedMetaQuotedContexts(
    body,signature,appSecret,scope,cap);
   if(q.decision==='DENIED')return deny('COMPONENT_DENIED');
   if(q.raw_sha256!==base.raw_sha256)
    return deny('INCONSISTENT_SNAPSHOT');
   quotes=q.observations;
  }
 }catch{return deny('COMPONENT_DENIED');}
 // A position is an occurrence address, NOT a durable dedupe key.
 const positions=new Map<string,CloudObservation>();
 for(const evt of base.observations){
  const key=eventKey(evt.position);
  if(positions.has(key))return deny('EVIDENCE_COLLISION_OR_GAP');
  positions.set(key,evt);
 }
 const evidenceBySlot=new Map<string,SpecializedEvidence>();
 for(const events of grouped){
  for(const evidence of events){
   const key=eventKey(evidence.position);
   const original=positions.get(key);
   if(!original||evidenceBySlot.has(key)||original.waba_id!==evidence.waba_id||
      original.phone_number_id!==evidence.phone_number_id||
      original.provider_message_id!==evidence.provider_message_id||
      original.kind!==(evidence.kind==='provider_reported_failed_status_errors'
       ? 'status_callback':'inbound_message'))
    return deny('EVIDENCE_COLLISION_OR_GAP');
   const participant='recipient_identifier' in evidence
    ? evidence.recipient_identifier:evidence.participant_identifier;
   if(original.participant_identifier!==participant||
      original.provider_timestamp!==evidence.provider_timestamp)
    return deny('EVIDENCE_COLLISION_OR_GAP');
   evidenceBySlot.set(key,evidence);
  }
 }
 const quotesBySlot=new Map<string,SignedReplyContextObservation>();
 for(const q of quotes){
  const key=eventKey(q.position),origin=positions.get(key);
  if(!contextualSlots.has(key)||!origin||
     origin.kind!=='inbound_message'||quotesBySlot.has(key)||
     origin.waba_id!==q.waba_id||
     origin.phone_number_id!==q.phone_number_id||
     origin.provider_message_id!==q.provider_message_id||
     origin.participant_identifier!==q.participant_identifier||
     origin.provider_timestamp!==q.provider_timestamp)
    return deny('EVIDENCE_COLLISION_OR_GAP');
  quotesBySlot.set(key,q);
 }
 const occurrences:ComposedWebhookOccurrence[]=[];
 for(const evt of base.observations){
  const slot=eventKey(evt.position);
  const evidence=evidenceBySlot.get(slot)??null;
  const quoted=quotesBySlot.get(slot)??null;
  if(quoted&&evidence&&'reply_to_provider_message_id' in evidence&&
     evidence.reply_to_provider_message_id!==quoted.quoted_provider_message_id)
   return deny('EVIDENCE_COLLISION_OR_GAP');
  if(specialExpected(evt)!==Boolean(evidence))
   return deny('EVIDENCE_COLLISION_OR_GAP');
  if(evidence){
   const allowed=evt.kind==='status_callback'
    ? evidence.kind==='provider_reported_failed_status_errors'&&
      evt.provider_kind==='failed'
    : (evidence.kind==='incoming_reaction'&&evt.provider_kind==='reaction')||
      (evidence.kind==='inbound_media_metadata'&&mediaMessage(evt.provider_kind)&&
       evidence.media_kind===evt.provider_kind)||
      (evidence.kind==='incoming_unsupported_message'&&evt.provider_kind==='unsupported')||
      (['template_quick_reply','interactive_button_reply','interactive_list_reply']
        .includes(evidence.kind)&&selectedMessage(evt.provider_kind)&&(
         evidence.kind==='template_quick_reply'?
          evt.provider_kind==='button':evt.provider_kind==='interactive'));
   if(!allowed)return deny('EVIDENCE_COLLISION_OR_GAP');
  }
  occurrences.push(Object.freeze({
   kind:evidence?.kind??(evt.kind==='status_callback'
    ?'uninterpreted_status' as const:'uninterpreted_inbound' as const),
   source_kind:evt.kind,provider_kind:evt.provider_kind,
   waba_id:evt.waba_id,phone_number_id:evt.phone_number_id,
   provider_message_id:evt.provider_message_id,
   provider_timestamp:evt.provider_timestamp,
   participant_identifier:evt.participant_identifier,
   position:Object.freeze({...evt.position}),evidence,
   quoted_reference:quoted,
  }));
 }
 if(evidenceBySlot.size>occurrences.length||
    quotesBySlot.size>occurrences.length||
    occurrences.length!==base.observations.length)
  return deny('EVIDENCE_COLLISION_OR_GAP');
 return Object.freeze({...FLAGS,
  decision:'SIGNED_COMPOSED_NOT_DURABLE' as const,
  reason:null,occurrences:Object.freeze(occurrences),
  raw_sha256:base.raw_sha256,route_revision:base.route_revision});
}
