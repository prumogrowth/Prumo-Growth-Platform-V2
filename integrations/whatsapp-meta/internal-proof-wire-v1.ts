/**
 * WA-06B: deterministic proposed wire encoding for Meta -> S0 proof inputs.
 * Pure bytes only. This module DOES NOT authenticate a workload, sign, verify,
 * persist nonces, authorize access, prove COMMIT or permit webhook ACK.
 */
import type { S0HandoffCandidate } from './s0-handoff-contract.ts';

export const WA06B_PROOF_VERSION = 'prumo.meta-s0.proof.v1-candidate' as const;
export const WA06B_CANONICAL_VERSION = 'prumo.meta-s0.binlen.v1-candidate' as const;
export type S0ServiceProofClaimsV1 = Readonly<{
  proof_version: typeof WA06B_PROOF_VERSION;
  canonicalization_version: typeof WA06B_CANONICAL_VERSION;
  service_ref: string;
  request_ref: string;
  nonce_ref: string;
  key_epoch: number;
  purpose: 'meta_s0.ingest';
  audience: 's0_internal_ingress';
  issued_at_ms: number;
  expires_at_ms: number;
}>;
const INVALID = 'INVALID_WA06B_PROOF_ENVELOPE';
const REF = /^[A-Za-z0-9_.:-]{1,128}$/;
const WAMID = /^wamid\.[A-Za-z0-9+\/_=:.-]{1,1024}$/;
const HEX = /^[a-f0-9]{64}$/;
const ISO = /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/;
const CLAIMS = ['proof_version','canonicalization_version','service_ref','request_ref',
  'nonce_ref','key_epoch','purpose','audience','issued_at_ms','expires_at_ms'] as const;
const CANDIDATE = ['contract_version','batch_ref','route_ref','route_revision',
  'app_ref','protected_payload_ref','payload_sha256','scope_sha256',
  'event_count','occurrences','ack_allowed','production_authorized'] as const;
const OCCURRENCE = ['position','event_kind','app_ref','concessionaria_id',
  'canal_id','waba_id','phone_number_id','provider_message_id',
  'provider_timestamp','provider_kind'] as const;
const POSITION = ['entry_index','change_index','array_kind','item_index'] as const;

function reject(): never { throw new Error(INVALID); }
function record(value: unknown, keys: readonly string[]): Record<string,unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return reject();
  const p = Object.getPrototypeOf(value);
  if (p !== null && p !== Object.prototype) return reject();
  const names = Reflect.ownKeys(value);
  if (names.length !== keys.length || names.some(k => typeof k !== 'string' || !keys.includes(k))) return reject();
  const descriptors = Object.getOwnPropertyDescriptors(value);
  const out: Record<string,unknown> = Object.create(null);
  for (const key of keys) {
    const d = descriptors[key];
    if (!d || !Object.hasOwn(d,'value') || !d.enumerable) return reject();
    out[key] = d.value;
  }
  return out;
}
function items(value: unknown): unknown[] {
  if (!Array.isArray(value) || Object.getPrototypeOf(value)!==Array.prototype ||
      value.length < 1 || value.length > 100) return reject();
  const descriptors = Object.getOwnPropertyDescriptors(value);
  if (Reflect.ownKeys(value).length !== value.length + 1) return reject();
  const out:unknown[]=[];
  for (let i=0; i<value.length; i++) {
    const d=descriptors[String(i)];
    if (!d || !Object.hasOwn(d,'value') || !d.enumerable) return reject();
    out.push(d.value);
  }
  return out;
}
function reference(value:unknown):string {
  if (typeof value!=='string' || !REF.test(value)) return reject();
  return value;
}
function wamid(value:unknown):string {
  if (typeof value!=='string' || !WAMID.test(value)) return reject();
  return value;
}
function hash(value:unknown):string {
  if (typeof value!=='string' || !HEX.test(value)) return reject();
  return value;
}
function integer(value:unknown, positive=false):number {
  if (typeof value!=='number' || !Number.isSafeInteger(value) || value < (positive?1:0)) return reject();
  return value;
}
function timestamp(value:unknown):string {
  if (typeof value!=='string' || !ISO.test(value) ||
      !Number.isFinite(Date.parse(value)) || new Date(value).toISOString()!==value) return reject();
  return value;
}

/** Bytes are domain-prefixed and length-prefixed in a fixed, versioned field order.
 * Any signature is created and verified OUTSIDE this module, after identity/ACL checks.
 * Existing WA-05C scope_sha256 is carried but NOT independently validated here.
 */
export function canonicalizeInternalProofV1(claims:unknown, candidate:unknown):Uint8Array {
  try {
    const h=record(claims,CLAIMS), c=record(candidate,CANDIDATE);
    if (h.proof_version!==WA06B_PROOF_VERSION ||
        h.canonicalization_version!==WA06B_CANONICAL_VERSION ||
        h.purpose!=='meta_s0.ingest' || h.audience!=='s0_internal_ingress' ||
        c.contract_version!=='meta-s0-handoff.v0.1-proposed' ||
        c.ack_allowed!==false || c.production_authorized!==false) return reject();
    const issued=integer(h.issued_at_ms), expires=integer(h.expires_at_ms,true);
    if (expires<=issued) return reject(); // Actual clock and max validity are S0 policy.
    const scope=items(c.occurrences);
    if (integer(c.event_count,true)!==scope.length) return reject();
    const normalized = [
      h.proof_version, h.canonicalization_version,
      reference(h.service_ref),reference(h.request_ref),reference(h.nonce_ref),
      integer(h.key_epoch,true),h.purpose,h.audience,issued,expires,
      c.contract_version,reference(c.batch_ref),reference(c.route_ref),
      integer(c.route_revision,true),reference(c.app_ref),
      reference(c.protected_payload_ref),hash(c.payload_sha256),hash(c.scope_sha256),
      scope.length, false, false
    ];
    const positions=new Set<string>();
    const occValues:(string|number)[][]=[];
    for (const raw of scope) {
      const o=record(raw,OCCURRENCE),p=record(o.position,POSITION);
      const entry=integer(p.entry_index),change=integer(p.change_index),item=integer(p.item_index);
      const kind=p.array_kind;
      if (kind!=='messages' && kind!=='statuses') return reject();
      const pos=[entry,change,kind,item].join(':');
      if (positions.has(pos)) return reject();
      positions.add(pos);
      const eventKind=kind==='messages'?'inbound_message':'status_callback';
      if (o.event_kind!==eventKind)return reject();
      const app=reference(o.app_ref);
      if (app!==c.app_ref) return reject();
      occValues.push([entry,change,kind,item,eventKind,app,
        reference(o.concessionaria_id),reference(o.canal_id),reference(o.waba_id),
        reference(o.phone_number_id),wamid(o.provider_message_id),
        timestamp(o.provider_timestamp),reference(o.provider_kind)]);
    }
    // Format: ASCII domain + NUL, then [4-byte BE UTF-8 length][UTF-8 bytes]
    // per scalar, in fixed order; occurrence count precedes its items.
    const parts:number[]=[...new TextEncoder().encode('PRUMO:WA06B:PROOF:V1\0')];
    const add=(value:string|number|boolean):void=>{
      const b=new TextEncoder().encode(String(value));
      if (b.length>65535) return reject();
      const len=b.length;
      parts.push((len>>>24)&255,(len>>>16)&255,(len>>>8)&255,len&255,...b);
    };
    for (const value of normalized) add(value as string|number|boolean);
    for (const row of occValues) for (const value of row) add(value);
    return Uint8Array.from(parts);
  } catch { return reject(); }
}

/** Only for type-checking interface compatibility with the WA-05C candidate. */
export type ProposedProofInputV1 = Readonly<{
  claims: S0ServiceProofClaimsV1;
  candidate: S0HandoffCandidate;
}>;
