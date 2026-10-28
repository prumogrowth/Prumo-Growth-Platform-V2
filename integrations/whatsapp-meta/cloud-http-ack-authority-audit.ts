/**
 * WA-ACK-TRUST-AUDIT — OFFLINE fail-closed perimeter around HTTP ACK claims.
 *
 * This is NOT an HTTP handler. None of the inputs attest S0 authority:
 * - a signed Meta POST authenticates provenance, not S0 persistence;
 * - a handoff candidate is metadata, not a transaction;
 * - a claimed receipt/COMMITTED/M2M proof is caller-provided, not verified;
 * - the historical decideBatchAck() is shape-only and MUST NOT grant HTTP.
 *
 * No network, PostgREST, SQL, Graph, tokens, HTTP status, retry or ACK output.
 * S0 code and contracts stay unchanged and are consulted in READ-ONLY mode.
 */
import {reviewAllegedS0ReceiptWithoutAck}
 from './cloud-physical-replay-receipt-audit.ts';
import type {S0HandoffCandidate} from './s0-handoff-contract.ts';
import type {ScopePreflight} from './cloud-batch-scope-preflight.ts';

const CLOSED=Object.freeze({
 ack_allowed:false,http_ack_allowed:false,
 http_response_authorized:false,partial_ack_allowed:false,
 send_authorized:false,s0_write_authorized:false,
 production_authorized:false,service_identity_verified:false,
 m2m_verified:false,commit_verified:false,
 durable_receipt_verified:false,integrity_verified:false,
 replay_suppression_authorized:false,retry_external:false,
 automatic_retry_authorized:false,channel_policy_ratified:false,
 commercial_effect_authorized:false,consent_verified:false,
} as const);
type Closed=typeof CLOSED;
type Code=
 'INVALID_BOUNDARY_INPUT'|
 'UNTRUSTED_HTTP_ACTION'|
 'SIGNED_ENVELOPE_NOT_CONFIRMED'|
 'S0_CANDIDATE_NOT_CONFIRMED'|
 'CLAIMED_RECEIPT_ABSENT'|
 'CLAIMED_RECEIPT_INCONSISTENT'|
 'MULTICHANNEL_POLICY_NOT_RATIFIED'|
 'M2M_CLAIM_NOT_VERIFIED'|
 'S0_COMMIT_AUTHORITY_NOT_VERIFIED';
export type OfflineAckBoundaryAudit=Closed&Readonly<{
 disposition:'NO_HTTP_ACTION_AUTHORIZED';
 reason:Code;
 receipt_shape:'ABSENT'|'REJECTED'|'MATCHES_UNVERIFIED';
 scope_shape:'ABSENT'|'SINGLE_CHANNEL'|'MULTICHANNEL_UNRATIFIED';
}>;
export type OfflineAckBoundaryClaims=Readonly<{
 signed_batch?:unknown;
 s0_handoff_candidate?:unknown;
 alleged_receipt?:unknown;
 trusted_route?:unknown;
 /** This is NOT a verifier. Even an apparently valid proof is untrusted. */
 alleged_m2m_proof?:unknown;
 /** The caller may try to inject a prior ACK decision (or status=200). */
 alleged_http_decision?:unknown;
}>;

const result=(reason:Code,receipt_shape:OfflineAckBoundaryAudit['receipt_shape'],
 scope_shape:OfflineAckBoundaryAudit['scope_shape']):OfflineAckBoundaryAudit=>
 Object.freeze({...CLOSED,disposition:'NO_HTTP_ACTION_AUTHORIZED' as const,
  reason,receipt_shape,scope_shape});

function plain(v:unknown):v is Record<string,unknown>{
 try{
  if(!v||typeof v!=='object'||Array.isArray(v))return false;
  const p=Object.getPrototypeOf(v);
  if(p!==Object.prototype&&p!==null)return false;
  return Object.values(Object.getOwnPropertyDescriptors(v))
   .every(d=>Object.hasOwn(d,'value'));
 }catch{return false;}
}
function hasExact(v:Record<string,unknown>,fields:readonly string[]){
 try{
  const keys=Reflect.ownKeys(v);
  return keys.length===fields.length&&
   keys.every(k=>typeof k==='string'&&fields.includes(k))&&
   fields.every(k=>Object.hasOwn(v,k));
 }catch{return false;}
}
const safeId=(v:unknown)=>
 typeof v==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(v);
const safeRevision=(v:unknown)=>typeof v==='number'&&
 Number.isSafeInteger(v)&&v>0;

/**
 * The only accepted request is data-only with six exact fields. Unknown
 * extras, accessors, forged Proxies, or arbitrary HTTP decisions fail closed.
 * No branch returns even a proposed status code: transport policy is S0-owned.
 */
export function auditHttpAckClaimsOffline(input:unknown):OfflineAckBoundaryAudit{
 const empty=()=>result('INVALID_BOUNDARY_INPUT','ABSENT','ABSENT');
 try{
  if(!plain(input)||!hasExact(input,[
   'signed_batch','s0_handoff_candidate','alleged_receipt',
   'trusted_route','alleged_m2m_proof','alleged_http_decision',
  ]))return empty();

  // NEVER accept status 200 or ACK as a caller assertion, whether supplied
  // by Meta, a legacy helper, a worker, or a purportedly trusted fixture.
  if(input.alleged_http_decision!==null&&
     input.alleged_http_decision!==undefined)
   return result('UNTRUSTED_HTTP_ACTION','ABSENT','ABSENT');

  const signed=input.signed_batch;
  if(!plain(signed)||!hasExact(signed,[
   'ack_allowed','partial_ack_allowed','send_authorized',
   's0_write_authorized','production_authorized',
   'commercial_effect_authorized','delivery_confirmed',
   'consent_verified','service_identity_verified','m2m_verified',
   'persisted','durable_receipt_verified',
   'batch_partition_authorized','channel_policy_ratified',
   'automatic_retry_authorized','deduplicated',
   'decision','reason','event_count','scope_count','channels',
   'raw_sha256',
  ])||signed.decision==='DENIED'||
    !['SIGNED_SINGLE_CHANNEL_TECHNICAL',
      'SIGNED_MULTI_CHANNEL_UNRATIFIED'].includes(signed.decision as string)||
    signed.ack_allowed!==false||signed.production_authorized!==false||
    signed.m2m_verified!==false||signed.durable_receipt_verified!==false)
   return result('SIGNED_ENVELOPE_NOT_CONFIRMED','ABSENT','ABSENT');

  const sc=signed as unknown as ScopePreflight;
  const scope:OfflineAckBoundaryAudit['scope_shape']=
   sc.decision==='SIGNED_MULTI_CHANNEL_UNRATIFIED'
    ?'MULTICHANNEL_UNRATIFIED':'SINGLE_CHANNEL';

  if(!plain(input.trusted_route)||
    !hasExact(input.trusted_route,['route_ref','expected_revision'])||
    !safeId(input.trusted_route.route_ref)||
    !safeRevision(input.trusted_route.expected_revision))
   return result('INVALID_BOUNDARY_INPUT','ABSENT',scope);

  if(!plain(input.s0_handoff_candidate))
   return result('S0_CANDIDATE_NOT_CONFIRMED','ABSENT',scope);

  // Local structural check only; no proven source of the allegedly signed
  // or committed data is supplied by this offline API.
  const checked=reviewAllegedS0ReceiptWithoutAck(
   sc,input.s0_handoff_candidate as S0HandoffCandidate,
   input.alleged_receipt,input.trusted_route as {
    route_ref:string;expected_revision:number;
   },
  );
  if(checked.reason==='CLAIMED_RECEIPT_MISSING')
   return result('CLAIMED_RECEIPT_ABSENT','ABSENT',scope);
  if(checked.decision==='DENIED')
   return result('CLAIMED_RECEIPT_INCONSISTENT','REJECTED',scope);
  if(scope==='MULTICHANNEL_UNRATIFIED')
   return result('MULTICHANNEL_POLICY_NOT_RATIFIED',
    'MATCHES_UNVERIFIED',scope);

  // A bare proof-shaped object, bearer, JWT, string, or even a valid-looking
  // HMAC cannot establish internal S0 authority. Only a future privileged
  // verifier of the source+nonce+commit could do that. This module has none.
  if(input.alleged_m2m_proof!==null&&
     input.alleged_m2m_proof!==undefined)
   return result('M2M_CLAIM_NOT_VERIFIED','MATCHES_UNVERIFIED',scope);

  return result('S0_COMMIT_AUTHORITY_NOT_VERIFIED',
   'MATCHES_UNVERIFIED',scope);
 }catch{return empty();}
}
