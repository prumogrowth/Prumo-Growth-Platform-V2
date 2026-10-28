/**
 * Meta Cloud API status/inbound boundary v1 — NO NETWORK, DB, S0 OR ACK.
 *
 * Reuses the existing raw-byte HMAC verifier/batch parser from inbound.ts.
 * A validated callback may contain several messages/statuses and optional
 * Meta metadata. All items are checked against ONE trusted server-selected
 * WABA/phone scope; mixed-scope payloads fail as a whole.
 *
 * Metadata here is TECHNICAL EVIDENCE, not authorization, a business status,
 * a Graph resend instruction, or evidence that S0 has persisted anything.
 */
import {createHash} from 'node:crypto';
import {inspectMetaWebhook, type MetaIngressEvent,
  type IngressFailureCode} from './inbound.ts';

export type CloudRouteScope=Readonly<{
  waba_id:string;
  phone_number_id:string;
  revision:number;
}>;
type Position=Readonly<{
  entry_index:number;change_index:number;item_index:number;
  array_kind:'messages'|'statuses';
}>;
export type CloudObservation=Readonly<{
  kind:'status_callback'|'inbound_message';
  waba_id:string;
  phone_number_id:string;
  provider_message_id:string;
  provider_timestamp:string;
  participant_identifier:string;
  provider_kind:string;
  position:Position;
  /** A local *candidate* key, never a Meta callback ID or S0 event_ref. */
  candidate_key:string;
}>;
type NoAuthority=Readonly<{
  ack_allowed:false;send_authorized:false;retry_external:false;
  s0_write_authorized:false;production_authorized:false;
  delivery_confirmed:false;case_transition_authorized:false;
}>;
export type CloudInspectionResult=NoAuthority & (
  Readonly<{outcome:'DENIED';reason:IngressFailureCode|
    'INVALID_TRUSTED_SCOPE'|'SCOPE_MISMATCH'|'UNSUPPORTED_STATUS'|
    'UNSUPPORTED_KIND';observations:readonly [];
    raw_sha256:null;route_revision:null}> |
  Readonly<{outcome:'AUTHENTICATED_NOT_DURABLE';reason:null;
    observations:readonly CloudObservation[];
    raw_sha256:string;route_revision:number}>
);
const FLAGS=Object.freeze({
 ack_allowed:false,send_authorized:false,retry_external:false,
 s0_write_authorized:false,production_authorized:false,
 delivery_confirmed:false,case_transition_authorized:false,
} as const);
const ident=(v:unknown)=>typeof v==='string'&&/^[0-9]{5,25}$/.test(v);
const validRoute=(x:CloudRouteScope)=>{
 try{return x!==null&&typeof x==='object'&&ident(x.waba_id)&&
 ident(x.phone_number_id)&&Number.isSafeInteger(x.revision)&&x.revision>0;}
 catch{return false;}
};
function reject(reason:Extract<CloudInspectionResult,{outcome:'DENIED'}>['reason']){
 return Object.freeze({...FLAGS,outcome:'DENIED' as const,reason,
  observations:Object.freeze([]) as readonly [],raw_sha256:null,route_revision:null});
}
const sha256=(v:Uint8Array)=>createHash('sha256').update(v).digest('hex');
const statusKinds=new Set(['sent','delivered','read','failed']);
function keyed(e:MetaIngressEvent):string{
 // Intentionally a proposal, NOT a durable event identity. Preserve the
 // observed order and full timestamp; do not silently dedupe callback items.
 return 'META_OBS_'+createHash('sha256').update(JSON.stringify([
  e.waba_id,e.phone_number_id,e.provider_message_id,
  e.participant_identifier,e.event_kind,e.provider_kind,
  e.provider_timestamp])).digest('hex');
}
export async function inspectCloudWebhookForHandoff(
 rawBody:Uint8Array,signature:string|null,appSecret:string,
 trustedRoute:CloudRouteScope,limits?:{maxBodyBytes?:number;maxEvents?:number},
):Promise<CloudInspectionResult>{
 if(!validRoute(trustedRoute))
  return reject('INVALID_TRUSTED_SCOPE');
 // The original payload might be a caller-owned byte view. One bounded,
 // immutable snapshot must be used for BOTH authentication and final hash.
 if(!(rawBody instanceof Uint8Array))return reject('INVALID_ENVELOPE');
 const max=limits?.maxBodyBytes??256*1024;
 if(!Number.isSafeInteger(max)||max<=0||rawBody.byteLength>max)
  return reject('BODY_TOO_LARGE');
 const copy=Uint8Array.from(rawBody);
 const parsed=await inspectMetaWebhook(copy,signature,appSecret,limits);
 if(!parsed.ok)return reject(parsed.failure.code);
 const list:CloudObservation[]=[];
 for(const e of parsed.events){
  if(e.waba_id!==trustedRoute.waba_id||
     e.phone_number_id!==trustedRoute.phone_number_id)
   return reject('SCOPE_MISMATCH');
  if(e.event_kind==='status_callback'){
   if(!statusKinds.has(e.provider_kind))return reject('UNSUPPORTED_STATUS');
  }else if(e.event_kind!=='inbound_message'){
   return reject('UNSUPPORTED_KIND');
  }
  list.push(Object.freeze({
   kind:e.event_kind,waba_id:e.waba_id,phone_number_id:e.phone_number_id,
   provider_message_id:e.provider_message_id,
   provider_timestamp:e.provider_timestamp,
   participant_identifier:e.participant_identifier,
   provider_kind:e.provider_kind,
   position:Object.freeze({...e.position}),candidate_key:keyed(e),
  }));
 }
 return Object.freeze({...FLAGS,outcome:'AUTHENTICATED_NOT_DURABLE',
  reason:null,observations:Object.freeze(list),raw_sha256:sha256(copy),
  route_revision:trustedRoute.revision});
}
