/**
 * Offline Meta/S0 compatibility preflight for a complete signed webhook POST.
 *
 * The existing routed ingress authenticates ONE App secret and resolves every
 * event against the trusted registry, including multi-WABA batches. This
 * classifies the channel distribution WITHOUT ratifying an S0 policy for
 * multi-channel ingress or making a transport / durable / ACK decision.
 *
 * No business-level message ID, participant, content, Graph response or
 * sensitive payload is returned. The report is for trusted internal review,
 * not UI/customer logs. Never partition, persist or ACK a physical POST.
 */
import {inspectRoutedMetaPost,type RoutablePost,
 type TrustedRoutingPorts,type ScopedTechnicalEvent}
 from './routed-webhook.ts';

const FLAGS=Object.freeze({
 ack_allowed:false,partial_ack_allowed:false,
 send_authorized:false,s0_write_authorized:false,
 production_authorized:false,commercial_effect_authorized:false,
 delivery_confirmed:false,consent_verified:false,
 service_identity_verified:false,m2m_verified:false,
 persisted:false,durable_receipt_verified:false,
 batch_partition_authorized:false,channel_policy_ratified:false,
 automatic_retry_authorized:false,deduplicated:false,
} as const);
type Flags=typeof FLAGS;

export type ChannelDistribution=Readonly<{
 app_ref:string;concessionaria_id:string;canal_id:string;
 waba_id:string;phone_number_id:string;
 inbound_message_count:number;status_callback_count:number;
 occurrence_count:number;
}>;
export type ScopePreflight=Flags&(
 Readonly<{decision:'DENIED';reason:'INVALID_INPUT'|
  'SIGNATURE_OR_ROUTING_DENIED'|'INTEGRITY_DENIED';
  event_count:0;scope_count:0;channels:readonly [];
  raw_sha256:null;}>|
 Readonly<{decision:'SIGNED_SINGLE_CHANNEL_TECHNICAL'|
  'SIGNED_MULTI_CHANNEL_UNRATIFIED';reason:null;
  event_count:number;scope_count:number;
  channels:readonly ChannelDistribution[];
  raw_sha256:string;}>
);
const deny=(reason:Extract<ScopePreflight,{decision:'DENIED'}>['reason']):ScopePreflight=>
 Object.freeze({...FLAGS,decision:'DENIED' as const,reason,
  event_count:0 as const,scope_count:0 as const,
  channels:Object.freeze([]) as readonly [],raw_sha256:null});
const safeRef=(v:unknown)=>
 typeof v==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(v);
const goodNumber=(n:unknown)=>typeof n==='number'&&
 Number.isSafeInteger(n)&&n>0;
function positionKey(evt:ScopedTechnicalEvent['event']){
 const p=evt.position;
 if(!p||![p.entry_index,p.change_index,p.item_index]
  .every(n=>Number.isSafeInteger(n)&&n>=0)||
  (p.array_kind!=='messages'&&p.array_kind!=='statuses')||
  (p.array_kind==='messages')!==(evt.event_kind==='inbound_message'))
  return null;
 return JSON.stringify([p.entry_index,p.change_index,p.array_kind,p.item_index]);
}
const channelKey=(v:ScopedTechnicalEvent['scope'])=>
 JSON.stringify([v.app_ref,v.concessionaria_id,
  v.canal_id,v.waba_id,v.phone_number_id]);
const hex=(bytes:Uint8Array)=>Array.from(bytes,b=>
 b.toString(16).padStart(2,'0')).join('');

/**
 * Always inspect the ENTIRE original POST with an App-level trusted route.
 * One endpoint decision per POST, not per WABA or message.
 */
export async function inspectSignedMetaBatchChannelScope(
 request:RoutablePost,ports:TrustedRoutingPorts,
):Promise<ScopePreflight>{
 let stable:RoutablePost,source:TrustedRoutingPorts;
 try{
  if(!request||!request.route||!safeRef(request.route.route_ref)||
     !goodNumber(request.route.expected_revision)||
     !(request.raw_body instanceof Uint8Array)||
     request.raw_body.byteLength<1||
     request.raw_body.byteLength>256*1024||
     (request.signature_header!==null&&
      typeof request.signature_header!=='string')||
     !ports||typeof ports.currentRegistry!=='function'||
     typeof ports.resolveSecret!=='function'||
     typeof ports.nowMs!=='function')
    return deny('INVALID_INPUT');
  // Caller-controlled fields MUST be fixed synchronously before awaiting.
  stable=Object.freeze({
   route:Object.freeze({
    route_ref:request.route.route_ref,
    expected_revision:request.route.expected_revision,
   }),
   raw_body:Uint8Array.from(request.raw_body),
   signature_header:request.signature_header,
  });
  const registry=ports.currentRegistry;
  const secret=ports.resolveSecret;
  const clock=ports.nowMs;
  source=Object.freeze({
   currentRegistry:registry.bind(ports),
   resolveSecret:secret.bind(ports),
   nowMs:clock.bind(ports),
  });
 }catch{return deny('INVALID_INPUT');}
 let verdict:Awaited<ReturnType<typeof inspectRoutedMetaPost>>;
 try{verdict=await inspectRoutedMetaPost(stable,source);}
 catch{return deny('SIGNATURE_OR_ROUTING_DENIED');}
 if(!verdict.ok)return deny('SIGNATURE_OR_ROUTING_DENIED');
 const events=verdict.events;
 if(events.length<1||events.length>100||
   !safeRef(verdict.authenticated_app_ref))return deny('INTEGRITY_DENIED');
 const byChannel=new Map<string,{
  scope:ScopedTechnicalEvent['scope'];messages:number;statuses:number;
 }>();
 const positions=new Set<string>();
 for(const item of events){
  const p=positionKey(item.event);
  const s=item.scope,e=item.event;
  if(!p||positions.has(p)||e.waba_id!==s.waba_id||
     e.phone_number_id!==s.phone_number_id||
     s.app_ref!==verdict.authenticated_app_ref||
     ![s.app_ref,s.concessionaria_id,s.canal_id,s.waba_id,
       s.phone_number_id].every(safeRef)||
     !['inbound_message','status_callback'].includes(e.event_kind))
   return deny('INTEGRITY_DENIED');
  positions.add(p);
  const k=channelKey(s);
  const g=byChannel.get(k)??{scope:s,messages:0,statuses:0};
  if(e.event_kind==='inbound_message')g.messages++;
  else g.statuses++;
  byChannel.set(k,g);
 }
 if(byChannel.size<1||byChannel.size>events.length)
  return deny('INTEGRITY_DENIED');
 const channels=Array.from(byChannel.values(),({scope,messages,statuses})=>
  Object.freeze({
   app_ref:scope.app_ref,
   concessionaria_id:scope.concessionaria_id,
   canal_id:scope.canal_id,
   waba_id:scope.waba_id,phone_number_id:scope.phone_number_id,
   inbound_message_count:messages,
   status_callback_count:statuses,occurrence_count:messages+statuses,
  }));
 if(channels.reduce((n,c)=>n+c.occurrence_count,0)!==events.length)
  return deny('INTEGRITY_DENIED');
 let raw_sha256:string;
 try{raw_sha256=hex(new Uint8Array(
  await crypto.subtle.digest('SHA-256',stable.raw_body)));}
 catch{return deny('INTEGRITY_DENIED');}
 return Object.freeze({...FLAGS,
  decision:channels.length===1
   ?'SIGNED_SINGLE_CHANNEL_TECHNICAL' as const
   :'SIGNED_MULTI_CHANNEL_UNRATIFIED' as const,
  reason:null,event_count:events.length,
  scope_count:channels.length,
  channels:Object.freeze(channels),
  raw_sha256,
 });
}
