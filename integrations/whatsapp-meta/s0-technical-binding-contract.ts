/**
 * WA-15B: zero-I/O, INTERNAL-only typed contract for S0/042 PostgreSQL fixture.
 * Converts a Graph API_ACCEPTED observation + claimed trusted S0 scope into
 * positional parameter values. This module NEVER runs SQL or trusts the scope:
 * PostgreSQL S0 must authenticate/re-resolve App/WABA/phone/channel/intent.
 * No Meta POST, HTTP ACK, retry, authorization, commercial transition or logs.
 */
import type { CorrelationReference } from './technical-reconciliation.ts';
import type { GraphSendOutcome } from './graph-outbound.ts';
import { isAcceptedGraphEvidence } from './status-evidence.ts';

type SqlArgsWrite = readonly [
  string,string,string,string,string,string,string,string,string,number
];
type SqlArgsRead = readonly [
  string,string,string,string,string,string,string,string,string
];
export type Wa15Command =
  | Readonly<{ action:'REGISTER_FIXTURE'; function_name:'prumo_private.registrar_vinculo_meta_tecnico_fixture_s0'; args:SqlArgsWrite;
      ack_allowed:false; retry_external:false; production_authorized:false }>
  | Readonly<{ action:'RECOVER_FIXTURE'; function_name:'prumo_private.consultar_vinculo_meta_tecnico_fixture_s0'; args:SqlArgsRead;
      ack_allowed:false; retry_external:false; production_authorized:false }>;

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const TECH = /^[0-9]{5,25}$/;
const RECIPIENT = /^[0-9]{8,15}$/;
const REFERENCE = /^[A-Za-z0-9_.:-]{1,128}$/;

/** Snapshot plain, exact-key, data-only inputs. Never evaluate getters. */
function ownData(raw: unknown, keys: readonly string[]): Record<string,unknown>|undefined {
  try {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return;
    const proto = Object.getPrototypeOf(raw);
    if (proto !== Object.prototype && proto !== null) return;
    const own = Object.getOwnPropertyDescriptors(raw);
    if (Reflect.ownKeys(raw).length !== keys.length ||
        Object.keys(own).length !== keys.length) return;
    const r:Record<string,unknown> = Object.create(null);
    for (const key of keys) {
      const d=own[key];
      if (!d || !Object.hasOwn(d,'value')) return;
      r[key]=d.value;
    }
    return r;
  } catch { return; }
}

const refKeys=['app_ref','intent_id','recipient_verified','scope'];
const scopeKeys=['concessionaria_id','canal_id','meta_app_ref','meta_waba_id','phone_number_id'];
const graphKeys=['attempt_id','correlation_id','send_state','api_accepted','http_status',
  'provider_message_id','meta_error_code','meta_error_subcode','retry_automatically'];

/** No execution rights. Caller MUST use bound parameters, never SQL string interpolation. */
export function prepareWa15FixtureCommand(
  rawReference: CorrelationReference, rawOutcome: GraphSendOutcome,
  action: 'REGISTER_FIXTURE'|'RECOVER_FIXTURE',
): Wa15Command|undefined {
  const r=ownData(rawReference,refKeys);
  const s=ownData(r?.scope,scopeKeys);
  const o=ownData(rawOutcome,graphKeys);
  if (!r || !s || !o || (action!=='REGISTER_FIXTURE' && action!=='RECOVER_FIXTURE') ||
      typeof r.app_ref!=='string' || !TECH.test(r.app_ref) ||
      s.meta_app_ref !== r.app_ref ||
      typeof s.meta_waba_id!=='string' || !TECH.test(s.meta_waba_id) ||
      typeof s.phone_number_id!=='string' || !TECH.test(s.phone_number_id) ||
      typeof s.concessionaria_id!=='string' || !UUID.test(s.concessionaria_id) ||
      typeof s.canal_id!=='string' || !UUID.test(s.canal_id) ||
      typeof r.intent_id!=='string' || !UUID.test(r.intent_id) ||
      typeof r.recipient_verified!=='string' || !RECIPIENT.test(r.recipient_verified) ||
      !isAcceptedGraphEvidence(o) ||
      typeof o.attempt_id!=='string' || !REFERENCE.test(o.attempt_id) ||
      typeof o.correlation_id!=='string' || !REFERENCE.test(o.correlation_id) ||
      typeof o.provider_message_id!=='string' ||
      typeof o.http_status!=='number') return;

  // Shop UUID is validated as shape, not passed to SQL: S0 derives the owner
  // from its own private sender registry and checks intent FK at transaction time.
  const args = [
    r.app_ref, s.meta_waba_id, s.phone_number_id, s.canal_id, r.intent_id,
    o.attempt_id, o.correlation_id, r.recipient_verified, o.provider_message_id,
  ] as const;
  if (action==='RECOVER_FIXTURE') return Object.freeze({
    action, function_name:'prumo_private.consultar_vinculo_meta_tecnico_fixture_s0',
    args:Object.freeze([...args]) as unknown as SqlArgsRead,
    ack_allowed:false, retry_external:false, production_authorized:false,
  });
  return Object.freeze({
    action, function_name:'prumo_private.registrar_vinculo_meta_tecnico_fixture_s0',
    args:Object.freeze([...args,o.http_status]) as unknown as SqlArgsWrite,
    ack_allowed:false, retry_external:false, production_authorized:false,
  });
}
