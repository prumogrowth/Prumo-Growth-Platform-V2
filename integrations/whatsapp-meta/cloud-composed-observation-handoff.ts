/**
 * Meta Cloud webhook technical composition: ONE ordered observation per
 * SIGNED raw callback occurrence, no lost generic items or doubled slots.
 *
 * Independent existing narrow readers each verify the same immutable raw
 * snapshot (including HMAC and trusted WABA/phone routing). Expensive by
 * design: no bypass of their security boundaries and no implicit S0 handoff.
 * Collisions, component denials, divergent raw hashes or missing expected
 * evidence deny the ENTIRE aggregate; nothing is persisted or ACKed.
 */
import {inspectCloudWebhookForHandoff,
 type CloudRouteScope,type CloudObservation}
 from './cloud-webhook-handoff.ts';
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
} as const);
type Flags=typeof FLAGS;
type Denial='VERIFICATION_DENIED'|'COMPONENT_DENIED'|
 'INCONSISTENT_SNAPSHOT'|'EVIDENCE_COLLISION_OR_GAP';
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
const selectedMessage=(kind:string)=>kind==='button'||kind==='interactive';
const mediaMessage=(kind:string)=>['image','audio','video','document','sticker'].includes(kind);
const specialExpected=(v:CloudObservation)=>v.kind==='status_callback'
 ? v.provider_kind==='failed'
 : selectedMessage(v.provider_kind)||
   v.provider_kind==='reaction'||
   mediaMessage(v.provider_kind)||
   v.provider_kind==='unsupported';

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
 const max=limits?.maxBodyBytes??256*1024;
 if(!Number.isSafeInteger(max)||max<1||rawBody.byteLength>max)
  return deny('VERIFICATION_DENIED');
 const body=Uint8Array.from(rawBody);
 let base:Awaited<ReturnType<typeof inspectCloudWebhookForHandoff>>;
 try{base=await inspectCloudWebhookForHandoff(
  body,signature,appSecret,trustedRoute,limits);
 }catch{return deny('VERIFICATION_DENIED');}
 if(base.outcome!=='AUTHENTICATED_NOT_DURABLE')
  return deny('VERIFICATION_DENIED');
 let parts:Awaited<ReturnType<typeof inspectSignedMetaSelections>>|
  Awaited<ReturnType<typeof inspectSignedMetaReactions>>|
  Awaited<ReturnType<typeof inspectSignedMetaMediaMetadata>>|
  Awaited<ReturnType<typeof inspectSignedMetaUnsupportedMessages>>|
  Awaited<ReturnType<typeof inspectSignedMetaFailedStatusErrors>>;
 const readers=[
  inspectSignedMetaSelections,
  inspectSignedMetaReactions,
  inspectSignedMetaMediaMetadata,
  inspectSignedMetaUnsupportedMessages,
  inspectSignedMetaFailedStatusErrors,
 ] as const;
 const grouped:SpecializedEvidence[][]=[];
 try{
  for(const reader of readers){
   parts=await reader(body,signature,appSecret,trustedRoute,limits);
   if(parts.decision==='DENIED')return deny('COMPONENT_DENIED');
   if(parts.raw_sha256!==base.raw_sha256)
    return deny('INCONSISTENT_SNAPSHOT');
   grouped.push([...parts.observations] as SpecializedEvidence[]);
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
 const occurrences:ComposedWebhookOccurrence[]=[];
 for(const evt of base.observations){
  const evidence=evidenceBySlot.get(eventKey(evt.position))??null;
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
  }));
 }
 if(evidenceBySlot.size>occurrences.length||
    occurrences.length!==base.observations.length)
  return deny('EVIDENCE_COLLISION_OR_GAP');
 return Object.freeze({...FLAGS,
  decision:'SIGNED_COMPOSED_NOT_DURABLE' as const,
  reason:null,occurrences:Object.freeze(occurrences),
  raw_sha256:base.raw_sha256,route_revision:base.route_revision});
}
