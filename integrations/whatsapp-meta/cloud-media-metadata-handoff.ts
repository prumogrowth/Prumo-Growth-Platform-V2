/**
 * WhatsApp Cloud API signed INBOUND MEDIA METADATA only (offline).
 *
 * Never issues GET /{media-id}, downloads files, resolves URLs, stores media,
 * authorizes S0 operations, acknowledges HTTP, or exposes bytes to clients.
 * Reuses the existing HMAC and entire-batch WABA/phone scope inspection.
 * All returned identifiers, captions and filenames are sensitive UNTRUSTED
 * observations, not evidence of media content, safety or business identity.
 */
import {inspectCloudWebhookForHandoff,
 type CloudRouteScope,type CloudObservation}
 from './cloud-webhook-handoff.ts';

const TYPES=['image','audio','video','document','sticker'] as const;
export type CloudMediaKind=typeof TYPES[number];
export type TechnicalMediaMetadata=Readonly<{
 kind:'inbound_media_metadata';
 media_kind:CloudMediaKind;
 waba_id:string;phone_number_id:string;
 provider_message_id:string;provider_timestamp:string;
 participant_identifier:string;
 media_id:string;
 /** Claimed MIME type, NOT determined by inspecting bytes. */
 mime_type_claim:string|null;
 /** Claimed media SHA-256, NOT computed from downloaded bytes. */
 sha256_claim:string|null;
 caption_untrusted:string|null;
 filename_untrusted:string|null;
 voice_hint:boolean|null;
 animated_hint:boolean|null;
 position:CloudObservation['position'];
}>;
type Denial='VERIFICATION_DENIED'|'UNSUPPORTED_MEDIA_SHAPE'|
 'INTERNAL_ALIGNMENT_DENIED';
type Flags=Readonly<{
 ack_allowed:false;send_authorized:false;s0_write_authorized:false;
 retry_external:false;production_authorized:false;
 delivery_confirmed:false;case_transition_authorized:false;
 commercial_effect_authorized:false;consent_verified:false;
 deduplicated:false;media_download_authorized:false;
 media_downloaded:false;media_content_verified:false;
 mime_verified:false;checksum_verified:false;malware_scanned:false;
}>;
export type MediaMetadataHandoff=Flags&(
 Readonly<{decision:'DENIED';reason:Denial;
  observations:readonly [];raw_sha256:null}>|
 Readonly<{decision:'SIGNED_MEDIA_REFERENCES_NOT_DURABLE';reason:null;
  observations:readonly TechnicalMediaMetadata[];raw_sha256:string}>
);
const FLAGS=Object.freeze({
 ack_allowed:false,send_authorized:false,s0_write_authorized:false,
 retry_external:false,production_authorized:false,
 delivery_confirmed:false,case_transition_authorized:false,
 commercial_effect_authorized:false,consent_verified:false,
 deduplicated:false,media_download_authorized:false,
 media_downloaded:false,media_content_verified:false,
 mime_verified:false,checksum_verified:false,malware_scanned:false,
} as const);
const deny=(reason:Denial):MediaMetadataHandoff=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,
 observations:Object.freeze([]) as readonly [],raw_sha256:null,
});
const rec=(v:unknown):v is Record<string,unknown>=>
 typeof v==='object'&&v!==null&&!Array.isArray(v);
const kind=(v:unknown):v is CloudMediaKind=>
 typeof v==='string'&&(TYPES as readonly string[]).includes(v);
const id=(v:unknown):v is string=>
 typeof v==='string'&&/^[0-9]{1,64}$/.test(v);
/** MIME syntax only. Not a file type or content verification. */
const mime=(v:unknown):v is string=>
 typeof v==='string'&&v.length<=128&&
 /^[A-Za-z0-9!#$&^_.+-]+\/[A-Za-z0-9!#$&^_.+-]+(?:;\s*[A-Za-z0-9!#$&^_.+-]+=[A-Za-z0-9!#$&^_.+-]+)*$/.test(v);
/** Structural notation only, not proof that a file has this checksum. */
const checksum=(v:unknown):v is string=>
 typeof v==='string'&&(
 /^[A-Za-z0-9+/]{43}=$/.test(v)||/^[0-9a-fA-F]{64}$/.test(v)
 );
const validUnicode=(s:string)=>
 !/[\u0000-\u0008\u000B-\u001F\u007F]/.test(s)&&
 !/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/.test(s);
const boundedText=(v:unknown,max:number):v is string=>
 typeof v==='string'&&[...v].length<=max&&validUnicode(v);
function mediaFields(mediaKind:CloudMediaKind,value:unknown):
 {media_id:string;mime_type_claim:string|null;sha256_claim:string|null;
 caption_untrusted:string|null;filename_untrusted:string|null;
 voice_hint:boolean|null;animated_hint:boolean|null}|null{
 if(!rec(value)||!id(value.id))return null;
 const allowed=new Set(['id','mime_type','sha256']);
 if(mediaKind==='image'||mediaKind==='video'||mediaKind==='document')
  allowed.add('caption');
 if(mediaKind==='document')allowed.add('filename');
 if(mediaKind==='audio')allowed.add('voice');
 if(mediaKind==='sticker')allowed.add('animated');
 if(Object.keys(value).some(k=>!allowed.has(k)))return null;
 if(value.mime_type!==undefined&&!mime(value.mime_type))return null;
 if(value.sha256!==undefined&&!checksum(value.sha256))return null;
 if(value.caption!==undefined&&!boundedText(value.caption,1024))return null;
 if(value.filename!==undefined&&!boundedText(value.filename,255))return null;
 if(value.voice!==undefined&&typeof value.voice!=='boolean')return null;
 if(value.animated!==undefined&&typeof value.animated!=='boolean')return null;
 return {
  media_id:value.id,
  mime_type_claim:value.mime_type??null,
  sha256_claim:value.sha256??null,
  caption_untrusted:value.caption??null,
  filename_untrusted:value.filename??null,
  voice_hint:value.voice??null,
  animated_hint:value.animated??null,
 } as {media_id:string;mime_type_claim:string|null;sha256_claim:string|null;
  caption_untrusted:string|null;filename_untrusted:string|null;
  voice_hint:boolean|null;animated_hint:boolean|null};
}

/**
 * Only observes references embedded in the signed webhook. Other message
 * kinds and status callbacks yield no media candidates, not an ACK permit.
 * Unsupported media fields or invalid signed siblings deny the entire batch.
 */
export async function inspectSignedMetaMediaMetadata(
 rawBody:Uint8Array,signature:string|null,appSecret:string,
 trustedRoute:CloudRouteScope,limits?:{maxBodyBytes?:number;maxEvents?:number},
):Promise<MediaMetadataHandoff>{
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
 const results:TechnicalMediaMetadata[]=[];
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
  if(!kind(evt.provider_kind))continue;
  const observed=mediaFields(evt.provider_kind,message[evt.provider_kind]);
  if(!observed)return deny('UNSUPPORTED_MEDIA_SHAPE');
  results.push(Object.freeze({
   kind:'inbound_media_metadata' as const,
   media_kind:evt.provider_kind,
   waba_id:evt.waba_id,phone_number_id:evt.phone_number_id,
   provider_message_id:evt.provider_message_id,
   provider_timestamp:evt.provider_timestamp,
   participant_identifier:evt.participant_identifier,
   ...observed,
   position:Object.freeze({...pos}),
  }));
 }
 return Object.freeze({...FLAGS,
  decision:'SIGNED_MEDIA_REFERENCES_NOT_DURABLE',
  reason:null,observations:Object.freeze(results),
  raw_sha256:verified.raw_sha256});
}
