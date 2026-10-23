/**
 * WA32 - OFFLINE-only cryptographic Meta POST -> privileged fake S0 attempt
 * binding, for *forensic inspection* (not durable ingestion, HTTP ACK, sent,
 * retry, billing, business state or any authorization to dispatch).
 *
 * The HMAC is checked by the ACTUAL routed-webhook.ts using test App secrets.
 * S0 lookups are INJECTED TEST PORTS. They are NOT an authenticated S0 API.
 * The exact provider message ID and recipient must match in same App/WABA/
 * sender/channel/tenant. Two separately sourced lookups + final route check
 * narrow races but do NOT implement an atomic handoff/commit.
 */
import {inspectRoutedMetaPost, type RoutablePost, type TrustedRoutingPorts}
  from './routed-webhook.ts';
import {selectMetaCredential,resolveSignedMetaChannel,type TrustedMetaScope}
  from './credential-routing.ts';
import {isMetaWamid,isStatusPosition,isMetaPhoneNumberId}
  from './status-evidence.ts';

export type Wa32AttemptLookup = Readonly<{
  app_ref: string;
  concessionaria_id: string;
  canal_id: string;
  waba_id: string;
  phone_number_id: string;
  provider_message_id: string;
  recipient_verified: string;
  case_ref: string;
  attempt_ref: string;
  binding_revision: number;
  claim_state: 'LAB_CLAIMED' | 'LAB_INVALIDATED';
}>;
export type Wa32S0FixturePort = Readonly<{
  /** Only a future privileged S0 resolver may satisfy this trust contract. */
  lookupExactAttempt: (
    scope:Readonly<TrustedMetaScope>,
    providerMessageId:string,
    phase:'LOOKUP'|'RECHECK',
  ) => Promise<readonly Wa32AttemptLookup[]>;
}>;
export type Wa32ForensicDecision=Readonly<{
  decision:
    | 'LAB_FORENSIC_SCOPED' | 'LAB_ROUTING_DENIED' | 'LAB_UNSUPPORTED_BATCH'
    | 'LAB_S0_BINDING_DENIED' | 'LAB_STALE_OR_CHANGED' | 'LAB_PORT_UNAVAILABLE';
  scoped_event_count: number;
  invalidated_attempts: number;
  ack_allowed: false;
  retry_external: false;
  send_authorized: false;
  production_authorized: false;
  delivery_confirmed: false;
  definitive_failure_count_increment: false;
  case_transition_authorized: false;
}>;
const out=(decision:Wa32ForensicDecision['decision'],n=0,invalidated=0):
 Wa32ForensicDecision=>Object.freeze({
    decision,scoped_event_count:n,invalidated_attempts:invalidated,
    ack_allowed:false,retry_external:false,send_authorized:false,
    production_authorized:false,delivery_confirmed:false,
    definitive_failure_count_increment:false,case_transition_authorized:false,
 });
const id=(s:unknown):s is string=>typeof s==='string'&&
  /^[A-Za-z0-9_.:-]{1,128}$/.test(s);
const recipient=(s:unknown):s is string=>typeof s==='string'&&/^\d{8,15}$/.test(s);
const state=(s:unknown):s is Wa32AttemptLookup['claim_state'] =>
  s==='LAB_CLAIMED'||s==='LAB_INVALIDATED';
const iso=(s:unknown):s is string=>typeof s==='string'&&
  /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(s)&&
  !Number.isNaN(Date.parse(s))&&new Date(s).toISOString()===s;
const sameScope=(s:TrustedMetaScope,b:Wa32AttemptLookup):boolean=>
  s.app_ref===b.app_ref&&s.concessionaria_id===b.concessionaria_id&&
  s.canal_id===b.canal_id&&s.waba_id===b.waba_id&&
  s.phone_number_id===b.phone_number_id;
const keys=['app_ref','concessionaria_id','canal_id','waba_id',
 'phone_number_id','provider_message_id','recipient_verified','case_ref',
 'attempt_ref','binding_revision','claim_state'] as const;
function snapshot(raw:unknown,s:TrustedMetaScope,message:string,
  recipientId:string):Wa32AttemptLookup|null{
  try{
    if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
    const proto=Object.getPrototypeOf(raw);
    if(proto!==Object.prototype&&proto!==null)return null;
    const d=Object.getOwnPropertyDescriptors(raw);
    if(Reflect.ownKeys(raw).length!==keys.length||
       Object.keys(d).length!==keys.length||
       !keys.every(k=>Object.hasOwn(d,k)&&Object.hasOwn(d[k],'value')))
      return null;
    const b=Object.fromEntries(keys.map(k=>[k,d[k].value])) as Wa32AttemptLookup;
    if(!id(b.app_ref)||!id(b.concessionaria_id)||!id(b.canal_id)||
       !id(b.waba_id)||!isMetaPhoneNumberId(b.phone_number_id)||
       !isMetaWamid(b.provider_message_id)||!recipient(b.recipient_verified)||
       !id(b.case_ref)||!id(b.attempt_ref)||
       !Number.isSafeInteger(b.binding_revision)||b.binding_revision<=0||
       !state(b.claim_state)||!sameScope(s,b)||
       b.provider_message_id!==message||b.recipient_verified!==recipientId)return null;
    return Object.freeze(b);
  }catch{return null;}
}
const sameBinding=(a:Wa32AttemptLookup,b:Wa32AttemptLookup)=>
  keys.every(k=>a[k]===b[k]);

/** Returns only aggregate counters. No callbacks, IDs, case or recipient leak. */
export async function inspectWa32SignedStatusForensicFixture(
  request:RoutablePost,routing:TrustedRoutingPorts,s0:Wa32S0FixturePort,
):Promise<Wa32ForensicDecision>{
  try{
    // A trusted server must construct request.route, never accept it from JSON.
    if(!s0||typeof s0.lookupExactAttempt!=='function')
      return out('LAB_PORT_UNAVAILABLE');
    const route={route_ref:request.route.route_ref,
                 expected_revision:request.route.expected_revision};
    const routed=await inspectRoutedMetaPost(request,routing);
    if(!routed.ok)return out('LAB_ROUTING_DENIED');
    if(!Array.isArray(routed.events)||routed.events.length===0||
       routed.events.length>100)return out('LAB_UNSUPPORTED_BATCH');
    const items=routed.events.map(({scope,event})=>({
      scope:Object.freeze({...scope}),
      event_kind:event.event_kind,
      position:event.position,
      provider_kind:event.provider_kind,
      provider_message_id:event.provider_message_id,
      participant_identifier:event.participant_identifier,
      provider_timestamp:event.provider_timestamp,
    }));
    if(items.some(({event_kind,position,provider_kind,provider_message_id,
      participant_identifier,provider_timestamp})=>
      event_kind!=='status_callback'||!isStatusPosition(position)||
      !['sent','delivered','read','failed'].includes(provider_kind)||
      !isMetaWamid(provider_message_id)||!recipient(participant_identifier)||
      !iso(provider_timestamp)))
      return out('LAB_UNSUPPORTED_BATCH');
    const lookup:Wa32AttemptLookup[]=[];
    for(const item of items){
      const first=await s0.lookupExactAttempt(item.scope,item.provider_message_id,'LOOKUP');
      if(!Array.isArray(first)||first.length!==1)return out('LAB_S0_BINDING_DENIED');
      const b=snapshot(first[0],item.scope,item.provider_message_id,
        item.participant_identifier);
      if(!b)return out('LAB_S0_BINDING_DENIED');
      lookup.push(b);
    }
    for(let i=0;i<items.length;i++){
      const item=items[i];
      const second=await s0.lookupExactAttempt(item.scope,item.provider_message_id,'RECHECK');
      if(!Array.isArray(second)||second.length!==1)return out('LAB_STALE_OR_CHANGED');
      const b=snapshot(second[0],item.scope,item.provider_message_id,
        item.participant_identifier);
      if(!b||!sameBinding(lookup[i],b))return out('LAB_STALE_OR_CHANGED');
    }
    // Privileged registry recheck, AFTER S0 lookups. Still not an S0
    // transaction: S0 must reauthorize before durable append/ACK.
    const registry=await routing.currentRegistry();
    const at=routing.nowMs();
    const latest=selectMetaCredential(registry,{
      purpose:'POST_APP_SECRET',trusted_route_ref:route.route_ref,
      expected_revision:route.expected_revision,at_ms:at,
    });
    if(!latest.ok||latest.app_ref!==routed.authenticated_app_ref)
      return out('LAB_STALE_OR_CHANGED');
    for(const item of items){
      const check=resolveSignedMetaChannel(registry,{
        trusted_route_ref:route.route_ref,
        authenticated_app_ref:routed.authenticated_app_ref,
        waba_id:item.scope.waba_id,phone_number_id:item.scope.phone_number_id,
        expected_revision:route.expected_revision,at_ms:at,
      });
      if(!check.ok||Object.keys(item.scope).some(k=>
        (check.scope as unknown as Record<string,string>)[k] !==
        (item.scope as unknown as Record<string,string>)[k]))
        return out('LAB_STALE_OR_CHANGED');
    }
    return out('LAB_FORENSIC_SCOPED',items.length,
      lookup.filter(x=>x.claim_state==='LAB_INVALIDATED').length);
  }catch{return out('LAB_PORT_UNAVAILABLE');}
}
