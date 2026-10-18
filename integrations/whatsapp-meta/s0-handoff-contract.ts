/**
 * WA-05C: candidate S0 / Meta handoff boundary, synthetic and UNTRUSTED.
 * The fixture does execute the WA-04B HMAC inspector with injected fake ports,
 * but cannot attest S0 durability, protected payload storage, privileges or ACK.
 */
import { inspectRoutedMetaPost, type RoutablePost, type TrustedRoutingPorts } from './routed-webhook.ts';

export type S0HandoffOccurrence = Readonly<{
  position: Readonly<{ entry_index: number; change_index: number; array_kind: 'messages' | 'statuses'; item_index: number }>;
  event_kind: 'inbound_message' | 'status_callback';
  app_ref: string; concessionaria_id: string; canal_id: string;
  waba_id: string; phone_number_id: string;
  provider_message_id: string; provider_timestamp: string; provider_kind: string;
}>;
export type S0HandoffCandidate = Readonly<{
  contract_version: 'meta-s0-handoff.v0.1-proposed';
  batch_ref: string; route_ref: string; route_revision: number;
  app_ref: string; protected_payload_ref: string; payload_sha256: string; scope_sha256: string;
  event_count: number; occurrences: readonly S0HandoffOccurrence[];
  ack_allowed: false; production_authorized: false;
}>;
export type S0HandoffResult =
  | { readonly ok: true; readonly candidate: S0HandoffCandidate; readonly ack_allowed: false; readonly production_authorized: false }
  | { readonly ok: false; readonly reason: 'INVALID_INPUT' | 'HMAC_OR_ROUTE_DENIED' | 'EVENT_SCOPE_MISMATCH' | 'EVENT_POSITION_CONFLICT' | 'INTEGRITY_UNAVAILABLE'; readonly ack_allowed: false; readonly production_authorized: false };

export type S0ReceiptFixture = Readonly<{
  contract_version: 'meta-s0-receipt.v0.1-proposed';
  batch_ref: string; app_ref: string; protected_payload_ref: string; payload_sha256: string;
  route_ref: string; route_revision: number; scope_sha256: string;
  total: number; accepted: number; duplicates: number; quarantined: number;
  outcome: 'ACCEPTED_DURABLE' | 'ALREADY_ACCEPTED' | 'QUARANTINED_DURABLE';
  commit_state: 'COMMITTED';
}>;
export type S0ReceiptReview = Readonly<{
  verdict: 'STRUCTURE_MATCHES_BUT_UNVERIFIED' | 'DENIED';
  reason: 'NEEDS_AUTHENTICATED_S0_COMMIT_EVIDENCE' | 'INVALID_RECEIPT' | 'ENVELOPE_MISMATCH' | 'INCOMPLETE_BATCH' | 'QUARANTINE_POLICY_PENDING';
  ack_allowed: false; production_authorized: false;
}>;
const REF = /^[a-zA-Z0-9_.:-]{1,128}$/;
const ref = (x: unknown): x is string => typeof x === 'string' && REF.test(x);
const providerId = (x: unknown): x is string => typeof x === 'string' &&
  /^wamid\.[a-zA-Z0-9+\/_=:.-]{1,1024}$/.test(x);
const count = (x: unknown): x is number => typeof x === 'number' && Number.isSafeInteger(x) && x >= 0;
const deny = (reason: Extract<S0HandoffResult,{ok:false}>['reason']): S0HandoffResult =>
  ({ ok:false, reason, ack_allowed:false, production_authorized:false });
const noReceipt = (reason: S0ReceiptReview['reason']): S0ReceiptReview =>
  ({ verdict:'DENIED', reason, ack_allowed:false, production_authorized:false });
const plainData = (x: unknown): x is Record<string,unknown> => {
  if (!x || typeof x !== 'object' || Array.isArray(x)) return false;
  const p=Object.getPrototypeOf(x);
  return (p===Object.prototype || p===null) &&
    Object.values(Object.getOwnPropertyDescriptors(x)).every(d=>Object.hasOwn(d,'value'));
};
const hasOnly = (x: Record<string,unknown>, names: readonly string[]) =>
  Object.keys(x).every(key => names.includes(key));
const hex = (a: Uint8Array) => Array.from(a, b=>b.toString(16).padStart(2,'0')).join('');
const arrayPos = (p: S0HandoffOccurrence['position']) =>
  JSON.stringify([p.entry_index,p.change_index,p.array_kind,p.item_index]);

/**
 * Host must bind request.route and ports to PRIVILEGED trusted routing,
 * not to JSON/query claims. The original payload must separately be stored by
 * S0 in protected durable storage; this function stores NOTHING.
 */
export async function prepareS0HandoffFixture(input: {
  readonly request: RoutablePost; readonly batch_ref: string;
  readonly protected_payload_ref: string;
}, ports: TrustedRoutingPorts): Promise<S0HandoffResult> {
  try {
    if (!input || !ref(input.batch_ref) || !ref(input.protected_payload_ref) ||
        !input.request || !(input.request.raw_body instanceof Uint8Array) ||
        input.request.raw_body.length===0 || input.request.raw_body.length>256*1024 ||
        !input.request.route || !ref(input.request.route.route_ref) ||
        !Number.isSafeInteger(input.request.route.expected_revision) ||
        input.request.route.expected_revision<1 ||
        !ports || typeof ports.currentRegistry!=='function' ||
        typeof ports.resolveSecret!=='function' || typeof ports.nowMs!=='function') return deny('INVALID_INPUT');
    // Capture ALL host-supplied metadata and raw bytes before the first await.
    const batch_ref=input.batch_ref;
    const protected_payload_ref=input.protected_payload_ref;
    const route={route_ref:input.request.route.route_ref,
      expected_revision:input.request.route.expected_revision};
    const request: RoutablePost={raw_body:Uint8Array.from(input.request.raw_body),
      route,signature_header:input.request.signature_header};
    if (request.signature_header!==null && typeof request.signature_header!=='string') return deny('INVALID_INPUT');
    const inspected=await inspectRoutedMetaPost(request,ports);
    if (!inspected.ok) return deny('HMAC_OR_ROUTE_DENIED');
    if (!ref(inspected.authenticated_app_ref) || inspected.events.length<1 || inspected.events.length>100)
      return deny('EVENT_SCOPE_MISMATCH');
    const positions=new Set<string>();
    const occurrences:S0HandoffOccurrence[]=[];
    for (const item of inspected.events) {
      const e=item.event, s=item.scope, p=e.position;
      if (s.app_ref!==inspected.authenticated_app_ref ||
          e.waba_id!==s.waba_id || e.phone_number_id!==s.phone_number_id ||
          !ref(s.concessionaria_id) || !ref(s.canal_id) || !ref(s.waba_id) ||
          !ref(s.phone_number_id) || !providerId(e.provider_message_id) ||
          !ref(e.provider_kind) ||
          !['inbound_message','status_callback'].includes(e.event_kind) ||
          !p || !['messages','statuses'].includes(p.array_kind) ||
          (p.array_kind==='messages') !== (e.event_kind==='inbound_message') ||
          ![p.entry_index,p.change_index,p.item_index].every(count) ||
          typeof e.provider_timestamp!=='string' ||
          !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(e.provider_timestamp))
        return deny('EVENT_SCOPE_MISMATCH');
      const position={entry_index:p.entry_index,change_index:p.change_index,
        array_kind:p.array_kind,item_index:p.item_index};
      const key=arrayPos(position);
      if (positions.has(key)) return deny('EVENT_POSITION_CONFLICT');
      positions.add(key);
      // Only minimally necessary technical metadata. Excludes participants,
      // message content, raw phone of customer, App secret and signature.
      occurrences.push({position,event_kind:e.event_kind,app_ref:s.app_ref,
        concessionaria_id:s.concessionaria_id,canal_id:s.canal_id,waba_id:s.waba_id,
        phone_number_id:s.phone_number_id,provider_message_id:e.provider_message_id,
        provider_timestamp:e.provider_timestamp,provider_kind:e.provider_kind});
    }
    // This digest alone is NOT proof that a protected replayable body exists.
    const digest=hex(new Uint8Array(await crypto.subtle.digest('SHA-256',request.raw_body)));
    const scopeData=JSON.stringify([batch_ref,route.route_ref,route.expected_revision,
      inspected.authenticated_app_ref,occurrences.map(x=>[x.position.entry_index,
      x.position.change_index,x.position.array_kind,x.position.item_index,
      x.app_ref,x.concessionaria_id,x.canal_id,x.waba_id,x.phone_number_id,
      x.event_kind,x.provider_message_id,x.provider_timestamp,x.provider_kind])]);
    const scope_sha256=hex(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(scopeData))));
    const candidate:S0HandoffCandidate={contract_version:'meta-s0-handoff.v0.1-proposed',
      batch_ref,route_ref:route.route_ref,route_revision:route.expected_revision,
      app_ref:inspected.authenticated_app_ref,protected_payload_ref,
      payload_sha256:digest,scope_sha256,event_count:occurrences.length,occurrences,
      ack_allowed:false,production_authorized:false};
    return {ok:true,candidate,ack_allowed:false,production_authorized:false};
  } catch { return deny('INTEGRITY_UNAVAILABLE'); }
}

/**
 * Structural consistency ONLY. Even an apparently COMMITTED S0 reply is NOT
 * proof of its source or ACID durability. NO code path returns ACK/HTTP 200.
 */
export function reviewS0ReceiptFixture(
  candidate: S0HandoffCandidate, allegedReceipt: unknown,
): S0ReceiptReview {
  try {
    if (!candidate || !plainData(allegedReceipt) ||
        !hasOnly(allegedReceipt,['contract_version','batch_ref','app_ref','protected_payload_ref',
          'payload_sha256','route_ref','route_revision','scope_sha256','total','accepted','duplicates','quarantined','outcome','commit_state']))
      return noReceipt('INVALID_RECEIPT');
    const r=allegedReceipt;
    if (r.contract_version!=='meta-s0-receipt.v0.1-proposed' ||
        r.commit_state!=='COMMITTED' ||
        !['ACCEPTED_DURABLE','ALREADY_ACCEPTED','QUARANTINED_DURABLE'].includes(r.outcome as string) ||
        ![r.total,r.accepted,r.duplicates,r.quarantined].every(count))
      return noReceipt('INVALID_RECEIPT');
    if (r.batch_ref!==candidate.batch_ref || r.app_ref!==candidate.app_ref ||
        r.protected_payload_ref!==candidate.protected_payload_ref ||
        r.payload_sha256!==candidate.payload_sha256 ||
        r.scope_sha256!==candidate.scope_sha256 ||
        r.route_ref!==candidate.route_ref || r.route_revision!==candidate.route_revision) return noReceipt('ENVELOPE_MISMATCH');
    if (r.total!==candidate.event_count ||
        (r.accepted as number)>r.total || (r.duplicates as number)>r.total ||
        (r.quarantined as number)>r.total ||
        (r.accepted as number)+(r.duplicates as number)+(r.quarantined as number)!==r.total)
      return noReceipt('INCOMPLETE_BATCH');
    if ((r.quarantined as number)>0 || r.outcome==='QUARANTINED_DURABLE')
      return noReceipt('QUARANTINE_POLICY_PENDING');
    if ((r.outcome==='ALREADY_ACCEPTED' && r.accepted!==0) ||
        (r.outcome==='ACCEPTED_DURABLE' && r.accepted===0))
      return noReceipt('INVALID_RECEIPT');
    return {verdict:'STRUCTURE_MATCHES_BUT_UNVERIFIED',
      reason:'NEEDS_AUTHENTICATED_S0_COMMIT_EVIDENCE',ack_allowed:false,production_authorized:false};
  } catch { return noReceipt('INVALID_RECEIPT'); }
}
