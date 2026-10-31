/**
 * WA12 / M12 OFFLINE ANTEPARO for ONE physical Meta POST.
 *
 * Three technical checks (WA11 envelope/HMAC, WA05C handoff candidate,
 * independent final signed channel-scope preflight) must agree with a
 * separately injected host-capture fixture. All claims remain UNTRUSTED:
 * no actual M2M identity, S0 registry, SQL transaction, readback, KMS, ACK,
 * HTTP response, Graph/send, retry, replay suppression or durable ingress.
 *
 * This is NOT a network handler or an authorization token issuer.
 */
import {createHash} from 'node:crypto';
import {inspectWa11OfflineWebhookEnvelope}
 from './wa11-offline-webhook-envelope.ts';
import {prepareS0HandoffFixture}
 from './s0-handoff-contract.ts';
import {inspectSignedMetaBatchChannelScope}
 from './cloud-batch-scope-preflight.ts';
import type {TrustedRoutingPorts,RoutablePost}
 from './routed-webhook.ts';

export type Wa12HostCapture=Readonly<{
 contract_version:'wa12-host-physical-capture.lab.v0.1';
 route_ref:string;route_revision:number;
 raw_sha256:string;expected_event_count:number;
 batch_ref:string;protected_payload_ref:string;
}>;
export type Wa12BarrierResult=Readonly<{
 decision:'DENIED'|'LAB_PHYSICAL_BATCH_COHERENT_UNCOMMITTED';
 reason:null|'INVALID_INPUT'|'CAPTURE_MISMATCH'|
   'ENVELOPE_DENIED'|'HANDOFF_DENIED'|'HANDOFF_MISMATCH'|
   'FINAL_SCOPE_DENIED'|'SCOPE_CHANGED';
 event_count:number;scope_count:number;raw_sha256:string|null;
 ack_allowed:false;http_ack_allowed:false;http_response_authorized:false;
 persisted:false;durable_receipt_verified:false;commit_verified:false;
 readback_verified:false;idempotency_verified:false;
 replay_suppression_authorized:false;recovery_authorized:false;
 automatic_retry_authorized:false;partial_ack_allowed:false;
 m2m_verified:false;s0_write_authorized:false;send_authorized:false;
 production_authorized:false;commercial_transition_authorized:false;
}>;
const FLAGS=Object.freeze({
 ack_allowed:false,http_ack_allowed:false,http_response_authorized:false,
 persisted:false,durable_receipt_verified:false,commit_verified:false,
 readback_verified:false,idempotency_verified:false,
 replay_suppression_authorized:false,recovery_authorized:false,
 automatic_retry_authorized:false,partial_ack_allowed:false,
 m2m_verified:false,s0_write_authorized:false,send_authorized:false,
 production_authorized:false,commercial_transition_authorized:false,
} as const);
type Reason=Exclude<Wa12BarrierResult['reason'],null>;
const denied=(reason:Reason):Wa12BarrierResult=>Object.freeze({
 decision:'DENIED' as const,reason,event_count:0,scope_count:0,
 raw_sha256:null,...FLAGS,
});
const coherent=(count:number,scopes:number,hash:string):Wa12BarrierResult=>
 Object.freeze({decision:'LAB_PHYSICAL_BATCH_COHERENT_UNCOMMITTED' as const,
  reason:null,event_count:count,scope_count:scopes,
  raw_sha256:hash,...FLAGS});
const ID=/^[A-Za-z0-9_.:-]{1,128}$/;
const SHA=/^[a-f0-9]{64}$/;
const pos=(v:unknown):v is number=>
 typeof v==='number'&&Number.isSafeInteger(v)&&v>0;
const id=(v:unknown):v is string=>
 typeof v==='string'&&ID.test(v);
function plain(raw:unknown,keys:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const d=Object.getOwnPropertyDescriptors(raw);
  const names=Reflect.ownKeys(raw);
  if(names.length!==keys.length||
     names.some(x=>typeof x!=='string'||!keys.includes(x))||
     keys.some(x=>!Object.hasOwn(d,x)||!Object.hasOwn(d[x],'value')))
   return null;
  return Object.fromEntries(keys.map(x=>[x,d[x].value]));
 }catch{return null;}
}
function dense(raw:unknown,min:number,max:number):unknown[]|null{
 try{
  if(!Array.isArray(raw))return null;
  const d=Object.getOwnPropertyDescriptors(raw),n=d.length?.value;
  if(!Number.isSafeInteger(n)||n<min||n>max||
     Reflect.ownKeys(raw).length!==n+1)return null;
  const out:unknown[]=[];
  for(let i=0;i<n;i++){
   const x=d[String(i)];
   if(!x||!Object.hasOwn(x,'value'))return null;
   out.push(x.value);
  }
  return out;
 }catch{return null;}
}
type Snapshot={
 route:{route_ref:string;expected_revision:number};
 raw:Uint8Array;signature:string;
 headers:[string,string][];
};
function snapshotEnvelope(raw:unknown):Snapshot|null{
 const envelope=plain(raw,['method','route','raw_query','raw_body','headers']);
 if(!envelope||envelope.method!=='POST'||envelope.raw_query!==null)
  return null;
 const route=plain(envelope.route,['route_ref','expected_revision']);
 if(!route||!id(route.route_ref)||!pos(route.expected_revision)||
    !(envelope.raw_body instanceof Uint8Array)||
    envelope.raw_body.byteLength<1||envelope.raw_body.byteLength>256*1024)
  return null;
 const entries=dense(envelope.headers,0,32);
 if(!entries)return null;
 const headers:[string,string][]=[];
 let signature:string|null=null;
 for(const item of entries){
  const pair=dense(item,2,2);
  if(!pair||typeof pair[0]!=='string'||typeof pair[1]!=='string')
   return null;
  headers.push([pair[0],pair[1]]);
  if(pair[0].toLowerCase()==='x-hub-signature-256'){
   if(signature!==null)return null;
   signature=pair[1];
  }
 }
 if(signature===null)return null;
 return {route:{route_ref:route.route_ref as string,
   expected_revision:route.expected_revision as number},
  raw:Uint8Array.from(envelope.raw_body),signature,headers};
}
function scopeKey(app:string,tenant:string,channel:string,waba:string,phone:string){
 return JSON.stringify([app,tenant,channel,waba,phone]);
}
/**
 * The hostCapture is a synthetic copy of metadata that a future authorized
 * hosting runtime would need to attest independently of the webhook payload.
 * Comparing two caller-supplied values does NOT prove independent custody.
 */
export async function inspectWa12PhysicalIngressBarrier(
 envelope:unknown,hostCapture:unknown,ports:TrustedRoutingPorts,
):Promise<Wa12BarrierResult>{
 try{
  const snap=snapshotEnvelope(envelope);
  const host=plain(hostCapture,[
   'contract_version','route_ref','route_revision','raw_sha256',
   'expected_event_count','batch_ref','protected_payload_ref',
  ]);
  if(!snap||!host||
     host.contract_version!=='wa12-host-physical-capture.lab.v0.1'||
     !id(host.route_ref)||!pos(host.route_revision)||
     typeof host.raw_sha256!=='string'||!SHA.test(host.raw_sha256)||
     !pos(host.expected_event_count)||host.expected_event_count>100||
     !id(host.batch_ref)||!id(host.protected_payload_ref)||
     !ports||typeof ports.currentRegistry!=='function'||
     typeof ports.resolveSecret!=='function'||
     typeof ports.nowMs!=='function')
   return denied('INVALID_INPUT');
  // All potentially mutable caller data is snapped BEFORE first await.
  if(snap.route.route_ref!==host.route_ref||
     snap.route.expected_revision!==host.route_revision||
     createHash('sha256').update(snap.raw).digest('hex')!==host.raw_sha256)
   return denied('CAPTURE_MISMATCH');
  const stablePorts:TrustedRoutingPorts=Object.freeze({
   currentRegistry:ports.currentRegistry.bind(ports),
   resolveSecret:ports.resolveSecret.bind(ports),
   nowMs:ports.nowMs.bind(ports),
  });
  const inspected=await inspectWa11OfflineWebhookEnvelope({
   method:'POST',route:snap.route,raw_query:null,
   raw_body:snap.raw,headers:snap.headers,
  },stablePorts);
  if(inspected.decision==='DENIED'||
     inspected.decision==='LAB_GET_CHALLENGE_VERIFIED_UNRATIFIED')
   return denied('ENVELOPE_DENIED');
  if(inspected.raw_sha256!==host.raw_sha256||
     inspected.event_count!==host.expected_event_count)
   return denied('CAPTURE_MISMATCH');

  const physical:RoutablePost={
   route:snap.route,raw_body:snap.raw,signature_header:snap.signature,
  };
  const handoff=await prepareS0HandoffFixture({
   request:physical,batch_ref:host.batch_ref as string,
   protected_payload_ref:host.protected_payload_ref as string,
  },stablePorts);
  if(!handoff.ok)return denied('HANDOFF_DENIED');
  const cand=handoff.candidate;
  if(cand.payload_sha256!==host.raw_sha256||
     cand.event_count!==host.expected_event_count||
     cand.route_ref!==snap.route.route_ref||
     cand.route_revision!==snap.route.expected_revision||
     cand.batch_ref!==host.batch_ref||
     cand.protected_payload_ref!==host.protected_payload_ref||
     cand.ack_allowed!==false||cand.production_authorized!==false)
   return denied('HANDOFF_MISMATCH');

  // Re-evaluate full scope after creating the candidate. A revocation or
  // binding change may be visible during the second or third check.
  // This is a DETECTION EXERCISE, not an atomic S0 readback.
  const final=await inspectSignedMetaBatchChannelScope(physical,stablePorts);
  if(final.decision==='DENIED')return denied('FINAL_SCOPE_DENIED');
  if(final.raw_sha256!==host.raw_sha256||
     final.event_count!==cand.event_count||
     final.scope_count!==inspected.scope_count)
   return denied('SCOPE_CHANGED');

  const counts=new Map<string,{inbound:number;status:number}>();
  const positions=new Set<string>();
  for(const occ of cand.occurrences){
   if(occ.app_ref!==cand.app_ref)return denied('SCOPE_CHANGED');
   const p=occ.position;
   const position=JSON.stringify([p.entry_index,p.change_index,p.array_kind,p.item_index]);
   if(positions.has(position))return denied('SCOPE_CHANGED');
   positions.add(position);
   const k=scopeKey(occ.app_ref,occ.concessionaria_id,occ.canal_id,
    occ.waba_id,occ.phone_number_id);
   const value=counts.get(k)??{inbound:0,status:0};
   if(occ.event_kind==='inbound_message')value.inbound++;
   else if(occ.event_kind==='status_callback')value.status++;
   else return denied('SCOPE_CHANGED');
   counts.set(k,value);
  }
  if(counts.size!==final.scope_count)return denied('SCOPE_CHANGED');
  for(const s of final.channels){
   const value=counts.get(scopeKey(s.app_ref,s.concessionaria_id,
    s.canal_id,s.waba_id,s.phone_number_id));
   if(!value||value.inbound!==s.inbound_message_count||
      value.status!==s.status_callback_count)
    return denied('SCOPE_CHANGED');
  }
  return coherent(cand.event_count,final.scope_count,host.raw_sha256 as string);
 }catch{return denied('INVALID_INPUT');}
}
