/**
 * Forensic-only comparison of TWO independently signed Meta physical POSTs
 * and strictly non-authoritative review of alleged S0 batch receipts.
 *
 * No S0/SQL/IAM mutation. No ACK, retry, replay dedupe, network or storage.
 * Same SHA256 is a byte identity only, NOT an authenticated S0 commit receipt.
 * Different SHA256 (including a JSON reorder) is NOT proof of different
 * logical messages: semantic equivalence requires a separate S0 policy.
 */
import {inspectSignedMetaBatchChannelScope,
 type ScopePreflight,type ChannelDistribution}
 from './cloud-batch-scope-preflight.ts';
import type {RoutablePost,TrustedRoutingPorts}
 from './routed-webhook.ts';
import {reviewS0ReceiptFixture,type S0HandoffCandidate}
 from './s0-handoff-contract.ts';

const RIGHTS=Object.freeze({
 ack_allowed:false,partial_ack_allowed:false,
 http_response_authorized:false,send_authorized:false,
 s0_write_authorized:false,production_authorized:false,
 retry_external:false,automatic_retry_authorized:false,
 replay_suppression_authorized:false,deduplicated:false,
 durable_receipt_verified:false,commit_verified:false,
 service_identity_verified:false,m2m_verified:false,
 commercial_effect_authorized:false,channel_policy_ratified:false,
} as const);
type Rights=typeof RIGHTS;
type PairDecision='EXACT_SIGNED_RAW_BYTES_UNVERIFIED'|
 'DIFFERENT_SIGNED_RAW_BYTES_UNVERIFIED'|
 'SIGNED_SCOPE_CHANGED_UNVERIFIED';
export type SignedPhysicalComparison=Rights&(
 Readonly<{decision:'DENIED';reason:'INVALID_INPUT'|
  'SIGNED_BATCH_DENIED'|'INTEGRITY_MISMATCH';
  prior_raw_sha256:null;current_raw_sha256:null;
  prior_event_count:0;current_event_count:0;
  same_raw_bytes:false;same_scope:false}>|
 Readonly<{decision:PairDecision;reason:null;
  prior_raw_sha256:string;current_raw_sha256:string;
  prior_event_count:number;current_event_count:number;
  same_raw_bytes:boolean;same_scope:boolean}>
);
const rejectPair=(reason:Extract<SignedPhysicalComparison,{decision:'DENIED'}>['reason']):
 SignedPhysicalComparison=>Object.freeze({
 ...RIGHTS,decision:'DENIED' as const,reason,
 prior_raw_sha256:null,current_raw_sha256:null,
 prior_event_count:0 as const,current_event_count:0 as const,
 same_raw_bytes:false as const,same_scope:false as const,
});
const id=(x:unknown)=>typeof x==='string'&&
 /^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const revision=(x:unknown)=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>0;
function copiedRequest(raw:RoutablePost):RoutablePost|null{
 try{
  if(!raw||!raw.route||!id(raw.route.route_ref)||
    !revision(raw.route.expected_revision)||
    !(raw.raw_body instanceof Uint8Array)||
    raw.raw_body.byteLength<1||raw.raw_body.byteLength>256*1024||
    (raw.signature_header!==null&&
     typeof raw.signature_header!=='string'))return null;
  return Object.freeze({
   raw_body:Uint8Array.from(raw.raw_body),
   signature_header:raw.signature_header,
   route:Object.freeze({
    route_ref:raw.route.route_ref,
    expected_revision:raw.route.expected_revision,
   }),
  });
 }catch{return null;}
}
function scopeKey(r:Extract<ScopePreflight,{reason:null}>){
 const keys=r.channels.map((c:ChannelDistribution)=>
  JSON.stringify([c.app_ref,c.concessionaria_id,c.canal_id,
   c.waba_id,c.phone_number_id,c.inbound_message_count,
   c.status_callback_count]));
 return JSON.stringify(keys.sort());
}
export async function compareSignedMetaPhysicalDeliveries(
 previous:RoutablePost,current:RoutablePost,ports:TrustedRoutingPorts,
):Promise<SignedPhysicalComparison>{
 // Fix both bodies AND route identities synchronously before ANY await.
 const first=copiedRequest(previous),second=copiedRequest(current);
 if(!first||!second)return rejectPair('INVALID_INPUT');
 let a:ScopePreflight,b:ScopePreflight;
 try{
  // Do NOT reuse the verdict of the first verification as a signature
  // credential for the second. Verify each physical request independently.
  [a,b]=await Promise.all([
   inspectSignedMetaBatchChannelScope(first,ports),
   inspectSignedMetaBatchChannelScope(second,ports),
  ]);
 }catch{return rejectPair('SIGNED_BATCH_DENIED');}
 if(a.decision==='DENIED'||b.decision==='DENIED')
  return rejectPair('SIGNED_BATCH_DENIED');
 const same_raw_bytes=a.raw_sha256===b.raw_sha256;
 const same_scope=first.route.route_ref===second.route.route_ref&&
  first.route.expected_revision===second.route.expected_revision&&
  scopeKey(a)===scopeKey(b);
 // Identical raw bytes SHOULD imply the same event cardinality if parsed
 // under compatible scopes. Any inconsistency refuses forensic assertion.
 if(same_raw_bytes&&same_scope&&a.event_count!==b.event_count)
  return rejectPair('INTEGRITY_MISMATCH');
 const decision:PairDecision=!same_scope
  ?'SIGNED_SCOPE_CHANGED_UNVERIFIED'
  :same_raw_bytes
   ?'EXACT_SIGNED_RAW_BYTES_UNVERIFIED'
   :'DIFFERENT_SIGNED_RAW_BYTES_UNVERIFIED';
 return Object.freeze({...RIGHTS,decision,reason:null,
  prior_raw_sha256:a.raw_sha256,current_raw_sha256:b.raw_sha256,
  prior_event_count:a.event_count,current_event_count:b.event_count,
  same_raw_bytes,same_scope});
}

export type S0ClaimReview=Rights&Readonly<{
 decision:'DENIED'|'CLAIMED_RECEIPT_SHAPE_ONLY_UNVERIFIED';
 reason:'INVALID_INPUT'|'CANDIDATE_SCOPE_MISMATCH'|
  'CLAIMED_RECEIPT_MISSING'|'CLAIMED_RECEIPT_REJECTED'|
  'QUARANTINE_POLICY_PENDING'|
  'NO_AUTHENTICATED_DURABLE_EVIDENCE';
 event_count:number;
}>;
const denyClaim=(reason:S0ClaimReview['reason']):S0ClaimReview=>
 Object.freeze({...RIGHTS,decision:'DENIED' as const,reason,event_count:0});

/**
 * Only compares S0 WA-05C fixture metadata against an already computed
 * App-level signed preflight. Both receipt AND candidate are untrusted claims;
 * a positive shape is NEVER a real S0 commit / HTTP 200 authority.
 *
 * This function does not invoke the historical decideBatchAck() helper,
 * whose shape-only 200 result has no provider authenticity.
 */
export function reviewAllegedS0ReceiptWithoutAck(
 signed:ScopePreflight,candidate:S0HandoffCandidate,
 allegedReceipt:unknown,
 trustedRoute:Readonly<{route_ref:string;expected_revision:number}>,
):S0ClaimReview{
 try{
  if(!signed||signed.decision==='DENIED'||!candidate||
   !Array.isArray(candidate.occurrences)||
   signed.event_count<1||signed.event_count>100)
   return denyClaim('INVALID_INPUT');
  // Route identity/revision cannot be inferred from signed channel counts.
  // Require an explicitly supplied trusted route, while retaining NO ACK.
  if(!trustedRoute||!id(trustedRoute.route_ref)||
     !revision(trustedRoute.expected_revision))
   return denyClaim('INVALID_INPUT');
  if(candidate.route_ref!==trustedRoute.route_ref||
     candidate.route_revision!==trustedRoute.expected_revision)
   return denyClaim('CANDIDATE_SCOPE_MISMATCH');
  if(typeof candidate.payload_sha256!=='string'||
    candidate.payload_sha256!==signed.raw_sha256||
    candidate.event_count!==signed.event_count||
    candidate.app_ref!==signed.channels[0]?.app_ref||
    candidate.ack_allowed!==false||
    candidate.production_authorized!==false)
   return denyClaim('CANDIDATE_SCOPE_MISMATCH');
  // Validate all occurrence addresses and their channel counts; a summary
  // with the same overall total but swapped tenants/locations must NOT match.
  const counters=new Map<string,{messages:number;statuses:number}>();
  const slots=new Set<string>();
  for(const e of candidate.occurrences){
   const p=e.position;
   if(!p||!revision(candidate.route_revision)||
      ![p.entry_index,p.change_index,p.item_index].every(n=>
       Number.isSafeInteger(n)&&n>=0)||
      ((p.array_kind==='messages')!==(e.event_kind==='inbound_message'))||
      !['inbound_message','status_callback'].includes(e.event_kind)||
      e.app_ref!==candidate.app_ref)
    return denyClaim('CANDIDATE_SCOPE_MISMATCH');
   const slot=JSON.stringify([p.entry_index,p.change_index,p.array_kind,p.item_index]);
   if(slots.has(slot))return denyClaim('CANDIDATE_SCOPE_MISMATCH');
   slots.add(slot);
   const key=JSON.stringify([e.app_ref,e.concessionaria_id,
    e.canal_id,e.waba_id,e.phone_number_id]);
   const counter=counters.get(key)??{messages:0,statuses:0};
   if(e.event_kind==='inbound_message')counter.messages++;
   else counter.statuses++;
   counters.set(key,counter);
  }
  if(candidate.occurrences.length!==signed.event_count||
    counters.size!==signed.channels.length)
   return denyClaim('CANDIDATE_SCOPE_MISMATCH');
  for(const channel of signed.channels){
   const key=JSON.stringify([channel.app_ref,channel.concessionaria_id,
    channel.canal_id,channel.waba_id,channel.phone_number_id]);
   const counter=counters.get(key);
   if(!counter||counter.messages!==channel.inbound_message_count||
      counter.statuses!==channel.status_callback_count)
    return denyClaim('CANDIDATE_SCOPE_MISMATCH');
  }
  if(allegedReceipt===null||allegedReceipt===undefined)
   return denyClaim('CLAIMED_RECEIPT_MISSING');
  const result=reviewS0ReceiptFixture(candidate,allegedReceipt);
  if(result.verdict==='DENIED')
   return denyClaim(result.reason==='QUARANTINE_POLICY_PENDING'
    ?'QUARANTINE_POLICY_PENDING':'CLAIMED_RECEIPT_REJECTED');
  return Object.freeze({...RIGHTS,
   decision:'CLAIMED_RECEIPT_SHAPE_ONLY_UNVERIFIED' as const,
   reason:'NO_AUTHENTICATED_DURABLE_EVIDENCE' as const,
   event_count:signed.event_count});
 }catch{return denyClaim('INVALID_INPUT');}
}
