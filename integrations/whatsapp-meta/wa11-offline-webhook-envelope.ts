/**
 * WA11 / M11 — OFFLINE wire-envelope review for a hypothetical privileged HTTP
 * host. This is NOT an HTTP handler, response selector, ACK policy or listener.
 *
 * Upstream trusted host must provide the route/revision independently of
 * query/payload/header claims, preserve the original raw bytes *before*
 * compression/charset transformation, source ports independently, and
 * enforce transport security. This module cannot attest any of those facts.
 *
 * GET verification is separate from POST HMAC. POST returns only a sanitized
 * analysis of the COMPLETE physical batch, never a per-channel ACK.
 * No HTTP response code, network, storage, send, retry, or commercial effect.
 */
import {inspectRoutedMetaGet,type TrustedRoutingPorts,
 type TrustedRoute} from './routed-webhook.ts';
import {inspectSignedMetaBatchChannelScope} from './cloud-batch-scope-preflight.ts';

export type Wa11FixtureRequest=Readonly<{
 method:'GET'|'POST';
 /** Trusted server routing only; never chosen by the WhatsApp sender. */
 route:TrustedRoute;
 /** Strings are UTF-8 encoded by the hosting runtime, not inferred here. */
 raw_query:string|null;
 raw_body:Uint8Array|null;
 /** Raw (name,value) header occurrences, NOT a collapsing Map/object. */
 headers:readonly (readonly [string,string])[];
}>;
type Failure='INVALID_ENVELOPE'|'AMBIGUOUS_HEADERS'|'UNSUPPORTED_FRAMING'|
 'INVALID_BODY'|'ROUTING_OR_VERIFICATION_DENIED'|'HMAC_OR_SCOPE_DENIED';
const FLAGS=Object.freeze({
 ack_allowed:false,http_ack_allowed:false,http_response_authorized:false,
 partial_ack_allowed:false,send_authorized:false,
 s0_write_authorized:false,production_authorized:false,
 persisted:false,commit_verified:false,durable_receipt_verified:false,
 m2m_verified:false,service_identity_verified:false,
 retry_external:false,automatic_retry_authorized:false,
 batch_partition_authorized:false,channel_policy_ratified:false,
 commercial_transition_authorized:false,
} as const);
export type Wa11Result=typeof FLAGS&Readonly<{
 decision:'DENIED'|'LAB_GET_CHALLENGE_VERIFIED_UNRATIFIED'|
  'LAB_SIGNED_SINGLE_CHANNEL_UNCOMMITTED'|
  'LAB_SIGNED_MULTICHANNEL_UNRATIFIED';
 reason:Failure|null;
 /** GET challenge only, not an HTTP response or proof of channel ownership. */
 challenge:string|null;
 event_count:number;scope_count:number;
 /** Digest of unchanged physical POST bytes, not a S0 durable receipt. */
 raw_sha256:string|null;
}>;
const deny=(reason:Failure):Wa11Result=>Object.freeze({
 ...FLAGS,decision:'DENIED' as const,reason,challenge:null,
 event_count:0,scope_count:0,raw_sha256:null,
});
const getOk=(challenge:string):Wa11Result=>Object.freeze({
 ...FLAGS,decision:'LAB_GET_CHALLENGE_VERIFIED_UNRATIFIED' as const,
 reason:null,challenge,event_count:0,scope_count:0,raw_sha256:null,
});
const postOk=(multichannel:boolean,eventCount:number,scopeCount:number,digest:string):Wa11Result=>
 Object.freeze({...FLAGS,
  decision:multichannel?'LAB_SIGNED_MULTICHANNEL_UNRATIFIED' as const:
   'LAB_SIGNED_SINGLE_CHANNEL_UNCOMMITTED' as const,
  reason:null,challenge:null,event_count:eventCount,
  scope_count:scopeCount,raw_sha256:digest,
 });
const ID=/^[A-Za-z0-9_.:-]{1,128}$/;
// Narrow laboratory header-name profile; rejects exotic names and ambiguity.
const headerName=/^[A-Za-z][A-Za-z0-9-]{0,127}$/;
function record(raw:unknown,fields:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const keys=Reflect.ownKeys(raw);
  if(keys.length!==fields.length||keys.some(k=>typeof k!=='string'||!fields.includes(k)))return null;
  const d=Object.getOwnPropertyDescriptors(raw);
  if(fields.some(k=>!Object.hasOwn(d,k)||!Object.hasOwn(d[k],'value')))return null;
  return Object.fromEntries(fields.map(k=>[k,d[k].value]));
 }catch{return null;}
}
function arrayPair(value:unknown):readonly [string,string]|null{
 try{
  if(!Array.isArray(value)||value.length!==2||
    Reflect.ownKeys(value).length!==3)return null;
  const d0=Object.getOwnPropertyDescriptor(value,'0');
  const d1=Object.getOwnPropertyDescriptor(value,'1');
  if(!d0||!d1||!Object.hasOwn(d0,'value')||!Object.hasOwn(d1,'value')||
     typeof d0.value!=='string'||typeof d1.value!=='string')return null;
  return [d0.value,d1.value];
 }catch{return null;}
}
type Headers={headers:Map<string,string>;reason:null}|{headers:null;reason:Failure};
function safeHeaders(value:unknown):Headers{
 try{
  if(!Array.isArray(value)||value.length>32||
     Reflect.ownKeys(value).length!==value.length+1)
   return {headers:null,reason:'INVALID_ENVELOPE'};
  const headers=new Map<string,string>();
  for(let i=0;i<value.length;i++){
   const d=Object.getOwnPropertyDescriptor(value,String(i));
   if(!d||!Object.hasOwn(d,'value'))return {headers:null,reason:'INVALID_ENVELOPE'};
   const p=arrayPair(d.value);
   if(!p)return {headers:null,reason:'INVALID_ENVELOPE'};
   const [name,headerValue]=p;
   const key=name.toLowerCase();
   if(!headerName.test(name)||headerValue.length>2048||
      /[\u0000-\u001f\u007f]/.test(headerValue))
    return {headers:null,reason:'INVALID_ENVELOPE'};
   if(headers.has(key))return {headers:null,reason:'AMBIGUOUS_HEADERS'};
   headers.set(key,headerValue);
  }
  return {headers,reason:null};
 }catch{return {headers:null,reason:'INVALID_ENVELOPE'};}
}
function framing(headers:Map<string,string>,method:'GET'|'POST',
 length:number):Failure|null{
 // Any forwarded encoding/framing override changes interpretation of the
 // bytes signed by the provider. Host must separately handle legal framing.
 if(headers.has('content-encoding')||headers.has('transfer-encoding')||
    headers.has('x-http-method-override'))
  return 'UNSUPPORTED_FRAMING';
 const len=headers.get('content-length');
 if(len!==undefined){
  if(!/^(0|[1-9][0-9]{0,6})$/.test(len)||Number(len)!==length)
   return 'UNSUPPORTED_FRAMING';
 }
 if(method==='GET'){
  if(headers.has('x-hub-signature-256')||headers.has('content-type')||
     (len!==undefined&&Number(len)!==0))
   return 'UNSUPPORTED_FRAMING';
 }else{
  const mime=headers.get('content-type');
  if(mime===undefined||!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(mime))
   return 'UNSUPPORTED_FRAMING';
  const sig=headers.get('x-hub-signature-256');
  if(sig===undefined||!/^sha256=[0-9a-f]{64}$/.test(sig))
   return 'UNSUPPORTED_FRAMING';
 }
 return null;
}
/**
 * The result is deliberately NOT actionable at any HTTP boundary.
 * GET challenge success may inform a separate, ratified GET-only handler;
 * POST success cannot inform a 2xx ACK or persistence conclusion.
 */
export async function inspectWa11OfflineWebhookEnvelope(
 request:unknown,ports:TrustedRoutingPorts,
):Promise<Wa11Result>{
 try{
  const input=record(request,['method','route','raw_query','raw_body','headers']);
  if(!input||!['GET','POST'].includes(input.method as string))
   return deny('INVALID_ENVELOPE');
  const route=record(input.route,['route_ref','expected_revision']);
  if(!route||typeof route.route_ref!=='string'||!ID.test(route.route_ref)||
     !Number.isSafeInteger(route.expected_revision)||Number(route.expected_revision)<1||
     !ports||typeof ports.currentRegistry!=='function'||
     typeof ports.resolveSecret!=='function'||typeof ports.nowMs!=='function')
   return deny('INVALID_ENVELOPE');
  const checked=safeHeaders(input.headers);
  if(!checked.headers)return deny(checked.reason!);
  const method=input.method as 'GET'|'POST';
  let body:Uint8Array|null=null;
  if(method==='GET'){
   if(typeof input.raw_query!=='string'||input.raw_body!==null||
      new TextEncoder().encode(input.raw_query).byteLength>8192)
    return deny('INVALID_ENVELOPE');
  }else{
   if(input.raw_query!==null||!(input.raw_body instanceof Uint8Array)||
      input.raw_body.byteLength<1||input.raw_body.byteLength>256*1024)
    return deny('INVALID_BODY');
   body=Uint8Array.from(input.raw_body);
  }
  const problem=framing(checked.headers,method,body?.byteLength??0);
  if(problem)return deny(problem);
  const stableRoute=Object.freeze({
   route_ref:route.route_ref as string,
   expected_revision:route.expected_revision as number,
  });
  // Snapshot dependencies before asynchronous work. These are privileged
  // fixture ports, NOT an actual authenticated S0 source or secret manager.
  const source:TrustedRoutingPorts=Object.freeze({
   currentRegistry:ports.currentRegistry.bind(ports),
   resolveSecret:ports.resolveSecret.bind(ports),
   nowMs:ports.nowMs.bind(ports),
  });
  if(method==='GET'){
   const verified=await inspectRoutedMetaGet({
    route:stableRoute,raw_query:input.raw_query as string,
   },source);
   return verified.ok?getOk(verified.challenge):deny('ROUTING_OR_VERIFICATION_DENIED');
  }
  // Signature header was uniquely selected from uncollapsed occurrences.
  // inspectSignedMetaBatchChannelScope revalidates all channels with one App
  // secret and a complete physical POST; no partitioning is ever permitted.
  const scoped=await inspectSignedMetaBatchChannelScope({
   route:stableRoute,raw_body:body!,
   signature_header:checked.headers.get('x-hub-signature-256')!,
  },source);
  if(scoped.decision==='DENIED')return deny('HMAC_OR_SCOPE_DENIED');
  return postOk(scoped.decision==='SIGNED_MULTI_CHANNEL_UNRATIFIED',
   scoped.event_count,scoped.scope_count,scoped.raw_sha256);
 }catch{return deny('INVALID_ENVELOPE');}
}
