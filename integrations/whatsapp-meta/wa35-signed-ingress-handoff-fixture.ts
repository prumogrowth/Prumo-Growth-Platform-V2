/**
 * WA35 OFFLINE experiment: actual Meta HMAC routing -> exact S0 fixture
 * attempt -> independent synthetic WA34 internal HMAC ticket.
 * This code DOES NOT authenticate a service principal, persist any evidence,
 * verify nonce in SQL, grant ACK, or authorize Meta Graph sending.
 * Inputs marked "trusted" require a privileged FUTURE service boundary.
 */
import {inspectRoutedMetaPost,type RoutablePost,type TrustedRoutingPorts}
 from './routed-webhook.ts';
import {selectMetaCredential,resolveSignedMetaChannel,type TrustedMetaScope}
 from './credential-routing.ts';
import {isMetaWamid,isMetaPhoneNumberId,isStatusPosition}
 from './status-evidence.ts';
import {issueWa34SyntheticFixture,type Wa34Scope,type Wa34SignedPacket}
 from './wa34-service-forensic-handoff.ts';
import type {Wa32AttemptLookup,Wa32S0FixturePort}
 from './wa32-signed-status-s0-forensic-bridge.ts';

export type Wa35SyntheticPorts=Readonly<{
  routing:TrustedRoutingPorts;
  s0:Wa32S0FixturePort;
  /** Privileged TEST only: independently protected from App Secret. */
  internalKey:()=>Promise<Uint8Array>;
  /** Unique TEST nonce; never accepts a client-provided nonce. */
  nonce:()=>Promise<string>;
}>;
export type Wa35Decision=Readonly<{
  decision:'LAB_TICKET_FOR_S0_RECHECK_ONLY'|'LAB_ROUTING_DENIED'|
   'LAB_UNSUPPORTED_EVENT'|'LAB_BINDING_DENIED'|'LAB_STALE'|
   'LAB_INTERNAL_UNAVAILABLE';
  ticket:Wa34SignedPacket|null;
  ack_allowed:false;
  send_authorized:false;
  retry_external:false;
  production_authorized:false;
  delivery_confirmed:false;
  case_transition_authorized:false;
  definitive_failure_count_increment:false;
}>;
function result(decision:Wa35Decision['decision'],
 ticket:Wa34SignedPacket|null=null):Wa35Decision{
 return Object.freeze({decision,ticket,ack_allowed:false,send_authorized:false,
  retry_external:false,production_authorized:false,delivery_confirmed:false,
  case_transition_authorized:false,definitive_failure_count_increment:false});
}
const bindingKeys=['app_ref','concessionaria_id','canal_id','waba_id',
 'phone_number_id','provider_message_id','recipient_verified','case_ref',
 'attempt_ref','binding_revision','claim_state'] as const;
const ident=(s:unknown):s is string=>typeof s==='string'&&
 /^[A-Za-z0-9_.:-]{1,128}$/.test(s);
const digits=(s:unknown):s is string=>typeof s==='string'&&/^\d{8,15}$/.test(s);
function binding(raw:unknown,scope:TrustedMetaScope,wamid:string,recipient:string):
 Wa32AttemptLookup|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const d=Object.getOwnPropertyDescriptors(raw);
  if(Reflect.ownKeys(raw).length!==bindingKeys.length||
   !bindingKeys.every(k=>Object.hasOwn(d,k)&&Object.hasOwn(d[k],'value')))
   return null;
  const v=Object.fromEntries(bindingKeys.map(k=>[k,d[k].value])) as Wa32AttemptLookup;
  if(!ident(v.app_ref)||!ident(v.concessionaria_id)||!ident(v.canal_id)||
   !ident(v.waba_id)||!isMetaPhoneNumberId(v.phone_number_id)||
   !isMetaWamid(v.provider_message_id)||!digits(v.recipient_verified)||
   !ident(v.case_ref)||!ident(v.attempt_ref)||
   !Number.isSafeInteger(v.binding_revision)||v.binding_revision<=0||
   !['LAB_CLAIMED','LAB_INVALIDATED'].includes(v.claim_state)||
   v.app_ref!==scope.app_ref||
   v.concessionaria_id!==scope.concessionaria_id||
   v.canal_id!==scope.canal_id||v.waba_id!==scope.waba_id||
   v.phone_number_id!==scope.phone_number_id||
   v.provider_message_id!==wamid||v.recipient_verified!==recipient)return null;
  return Object.freeze(v);
 }catch{return null;}
}
const unchanged=(a:Wa32AttemptLookup,b:Wa32AttemptLookup)=>
 bindingKeys.every(k=>a[k]===b[k]);
const hex=(bytes:Uint8Array)=>Array.from(bytes,
 n=>n.toString(16).padStart(2,'0')).join('');
async function sha(raw:Uint8Array):Promise<string>{
 return hex(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)));
}
function validTime(stamp:unknown):stamp is string{
 return typeof stamp==='string'&&
 /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(stamp)&&
 !Number.isNaN(Date.parse(stamp))&&new Date(stamp).toISOString()===stamp;
}
function stillTrusted(reg:Awaited<ReturnType<TrustedRoutingPorts['currentRegistry']>>,
 route:{route_ref:string,expected_revision:number},authenticated:string,
 scope:TrustedMetaScope,now:number):boolean{
 const c=selectMetaCredential(reg,{
  purpose:'POST_APP_SECRET',trusted_route_ref:route.route_ref,
  expected_revision:route.expected_revision,at_ms:now,
 });
 if(!c.ok||c.app_ref!==authenticated)return false;
 const check=resolveSignedMetaChannel(reg,{
  trusted_route_ref:route.route_ref,authenticated_app_ref:authenticated,
  waba_id:scope.waba_id,phone_number_id:scope.phone_number_id,
  expected_revision:route.expected_revision,at_ms:now,
 });
 return check.ok&&Object.keys(scope).length===5&&
  Object.keys(scope).every(k=>
    (scope as unknown as Record<string,string>)[k]===
    (check.scope as unknown as Record<string,string>)[k]);
}

/**
 * One status per signed POST, to avoid partial batches. Returns an internal
 * candidate packet ONLY for fixture-to-fixture tests. No client/API route.
 */
export async function makeWa35SignedHandoffFixture(
 request:RoutablePost,ports:Wa35SyntheticPorts,
):Promise<Wa35Decision>{
 try{
  if(!request||!(request.raw_body instanceof Uint8Array)||
   request.raw_body.byteLength>256*1024||!request.route||
   typeof request.route.route_ref!=='string'||
   !Number.isSafeInteger(request.route.expected_revision)||
   (typeof request.signature_header!=='string'&&request.signature_header!==null)||
   !ports||!ports.routing||!ports.s0||
   typeof ports.s0.lookupExactAttempt!=='function'||
   typeof ports.internalKey!=='function'||typeof ports.nonce!=='function')
   return result('LAB_INTERNAL_UNAVAILABLE');
  // Important: the bytes used for SHA are EXACTLY the snapshot passed to
  // the independently HMAC-validating router; caller may mutate its own body.
  const raw_body=Uint8Array.from(request.raw_body);
  const route=Object.freeze({
   route_ref:request.route.route_ref,
   expected_revision:request.route.expected_revision,
  });
  const routed=await inspectRoutedMetaPost({
   raw_body,signature_header:request.signature_header,route,
  },ports.routing);
  if(!routed.ok)return result('LAB_ROUTING_DENIED');
  if(routed.events.length!==1)return result('LAB_UNSUPPORTED_EVENT');
  const item=routed.events[0],e=item.event,s=item.scope;
  if(e.event_kind!=='status_callback'||!isStatusPosition(e.position)||
   !['sent','delivered','read','failed'].includes(e.provider_kind)||
   !isMetaWamid(e.provider_message_id)||
   !digits(e.participant_identifier)||!validTime(e.provider_timestamp))
   return result('LAB_UNSUPPORTED_EVENT');
  const first=await ports.s0.lookupExactAttempt(s,e.provider_message_id,'LOOKUP');
  if(!Array.isArray(first)||first.length!==1)return result('LAB_BINDING_DENIED');
  const b=binding(first[0],s,e.provider_message_id,e.participant_identifier);
  if(!b)return result('LAB_BINDING_DENIED');
  const second=await ports.s0.lookupExactAttempt(s,e.provider_message_id,'RECHECK');
  if(!Array.isArray(second)||second.length!==1)return result('LAB_STALE');
  const checked=binding(second[0],s,e.provider_message_id,e.participant_identifier);
  if(!checked||!unchanged(b,checked))return result('LAB_STALE');
  // Derivation does not rely on a client-supplied event ID: it is a SHA256
  // of stable status fields, *not a Meta-provided unique callback ID*.
  const eventFields=[s.app_ref,s.waba_id,s.phone_number_id,
   e.provider_message_id,e.participant_identifier,
   e.provider_kind,e.provider_timestamp];
  const stableEvent='EVT_'+await sha(new TextEncoder().encode(
   JSON.stringify(eventFields)));
  const bodyHash=await sha(raw_body);
  const now=ports.routing.nowMs();
  if(!Number.isSafeInteger(now)||now<0)return result('LAB_INTERNAL_UNAVAILABLE');
  if(!stillTrusted(await ports.routing.currentRegistry(),route,
   routed.authenticated_app_ref,s,now))return result('LAB_STALE');
  const nonce=await ports.nonce();
  const key=await ports.internalKey();
  if(!(key instanceof Uint8Array)||key.byteLength<32||key.byteLength>128||
    !ident(nonce))return result('LAB_INTERNAL_UNAVAILABLE');
  // Re-read S0 and route after asynchronous key retrieval. Still NOT atomic
  // against S0 commit or secret rotation between final check and SQL append.
  const third=await ports.s0.lookupExactAttempt(s,e.provider_message_id,'RECHECK');
  if(!Array.isArray(third)||third.length!==1)return result('LAB_STALE');
  const last=binding(third[0],s,e.provider_message_id,e.participant_identifier);
  if(!last||!unchanged(b,last))return result('LAB_STALE');
  const endTime=ports.routing.nowMs();
  if(!Number.isSafeInteger(endTime)||endTime<now||
   !stillTrusted(await ports.routing.currentRegistry(),route,
     routed.authenticated_app_ref,s,endTime))return result('LAB_STALE');
  const scope:Wa34Scope={
   app_ref:s.app_ref,concessionaria_id:s.concessionaria_id,
   canal_id:s.canal_id,waba_id:s.waba_id,phone_number_id:s.phone_number_id,
   provider_message_id:b.provider_message_id,
   recipient_verified:b.recipient_verified,case_ref:b.case_ref,
   attempt_ref:b.attempt_ref,binding_revision:b.binding_revision,
   event_ref:stableEvent,provider_kind:e.provider_kind as Wa34Scope['provider_kind'],
   meta_body_sha256:bodyHash,
  };
  const ticket=await issueWa34SyntheticFixture(scope,nonce,endTime,60000,key);
  return ticket?result('LAB_TICKET_FOR_S0_RECHECK_ONLY',ticket):
   result('LAB_INTERNAL_UNAVAILABLE');
 }catch{return result('LAB_INTERNAL_UNAVAILABLE');}
}
