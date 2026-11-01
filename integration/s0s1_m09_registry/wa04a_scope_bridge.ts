/**
 * M09-05: offline, transport-free S0 -> Meta scoped AUDIT projection.
 *
 * Accepts the M09-04 signed-read LAB response as untrusted JSON. This module
 * DOES NOT authenticate that response or independently verify an Ed25519 proof.
 * It never creates legacy TrustedMetaRegistry (which demands 3 secret slots),
 * grants GET/POST/Graph access or approves provider assets.
 *
 * Intended only to surface structural incompatibility and check a candidate
 * against an independently supplied scope and the five expected revisions.
 */
export type ScopedMetaAudit = Readonly<{
  contract_version: 'prumo.s0.meta.wa04a-scope-audit/0.1-candidate';
  decision: 'LAB_SCOPE_MATCHED_UNVERIFIED' | 'DENIED';
  reason: 'SCOPED_SHAPE_MATCHED' | 'INVALID_INPUT' | 'SOURCE_NOT_ACCEPTED' |
    'SCOPE_MISMATCH' | 'STALE_REVISION' | 'LEGACY_PURPOSE_NOT_SUPPORTED';
  route_revision: number | null;
  app_revision: number | null;
  binding_revision: number | null;
  grant_revision: number | null;
  principal_revision: number | null;
  legacy_wa04a_directly_compatible: false;
  legacy_wa09_directly_compatible: false;
  s0_proof_verified_by_adapter: false;
  provider_ownership_verified: false;
  delegation_verified: false;
  m2m_operationally_verified: false;
  production_authorized: false;
  send_authorized: false;
  ack_allowed: false;
  graph_authorized: false;
  s0_write_authorized: false;
}>;
type Obj = Record<string, unknown>;
type Key = 'route' | 'app' | 'binding' | 'grant' | 'principal';
const REVISION_KEYS = ['route','app','binding','grant','principal'] as const;
const EXPECTED_SCOPE_KEYS = [
  'concessionaria_id','app_ref','route_ref','canal_id','waba_id',
  'phone_number_id',
] as const;
const SNAPSHOT_KEYS = [
  ...EXPECTED_SCOPE_KEYS,'revisions','source_revision','snapshot_ref',
  'ownership_evidence_state','delegation_evidence_state',
] as const;
const SOURCE_KEYS = [
  'contract_version','decision','reason','snapshot',
  'production_authorized','send_authorized','external_http_ack',
  'commercial_transition_authorized',
] as const;
const AUTH_FLAGS = [
  'production_authorized','send_authorized','external_http_ack',
  'commercial_transition_authorized',
] as const;
const VERSION = 'prumo.s0.meta.wa04a-scope-audit/0.1-candidate' as const;
const DENIAL = Object.freeze({
  legacy_wa04a_directly_compatible: false as const,
  legacy_wa09_directly_compatible: false as const,
  s0_proof_verified_by_adapter: false as const,
  provider_ownership_verified: false as const,
  delegation_verified: false as const,
  m2m_operationally_verified: false as const,
  production_authorized: false as const,
  send_authorized: false as const,
  ack_allowed: false as const,
  graph_authorized: false as const,
  s0_write_authorized: false as const,
});
const id = (v: unknown): v is string =>
  typeof v === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(v);
const phone = (v: unknown): v is string =>
  typeof v === 'string' && /^\d{5,25}$/.test(v);
const digest = (v: unknown): v is string =>
  typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const revision = (v: unknown): v is number =>
  typeof v === 'number' && Number.isSafeInteger(v) && v > 0;

/** Data properties ONLY: never invoke getters or silently skip sparse arrays. */
function exact(value: unknown, keys: readonly string[]): Obj | null {
  try {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) return null;
    const ownKeys = Reflect.ownKeys(value);
    if (ownKeys.length !== keys.length ||
        ownKeys.some(k => typeof k !== 'string' || !keys.includes(k))) return null;
    const descriptors = Object.getOwnPropertyDescriptors(value);
    const out: Obj = Object.create(null);
    for (const key of keys) {
      const d = descriptors[key];
      if (!d || !Object.hasOwn(d,'value')) return null;
      out[key] = d.value;
    }
    return out;
  } catch {
    return null;
  }
}
function deny(reason: ScopedMetaAudit['reason']): ScopedMetaAudit {
  return Object.freeze({
    contract_version: VERSION,decision:'DENIED',reason,
    route_revision:null,app_revision:null,binding_revision:null,
    grant_revision:null,principal_revision:null,...DENIAL,
  });
}
function expectedScope(input: unknown): Obj | null {
  const s = exact(input,EXPECTED_SCOPE_KEYS);
  if (!s || EXPECTED_SCOPE_KEYS.slice(0,5).some(k => !id(s[k])) ||
      !phone(s.phone_number_id)) return null;
  return s;
}
function expectedRevisions(input: unknown): Obj | null {
  const r = exact(input,REVISION_KEYS);
  if (!r || REVISION_KEYS.some(k => !revision(r[k]))) return null;
  return r;
}

/**
 * The caller MUST independently supply expected store/route/channel scope and
 * revision numbers. Even successful matching is merely an offline structural
 * audit; the JSON may be forged by anyone and is not authorization.
 *
 * WA04A legacy selection requires all 3 slot names and a single revision.
 * M09-04 correctly contains NO slot names and 5 distinct revisions. Therefore
 * the adapter NEVER supplies a fabricated TrustedMetaRegistry to WA04A/WA09.
 */
export function inspectM09ForMetaOffline(
  candidate: unknown, scopeInput: unknown, revisionInput: unknown,
  purpose: 'REGISTRY_READ' | 'GET_VERIFY_TOKEN' |
           'POST_APP_SECRET' | 'GRAPH_ACCESS_TOKEN' = 'REGISTRY_READ',
): ScopedMetaAudit {
  try {
    if (purpose !== 'REGISTRY_READ')
      return deny('LEGACY_PURPOSE_NOT_SUPPORTED');
    const scope = expectedScope(scopeInput);
    const revisions = expectedRevisions(revisionInput);
    if (!scope || !revisions) return deny('INVALID_INPUT');
    const source = exact(candidate,SOURCE_KEYS);
    if (!source ||
      source.contract_version !== 'prumo.s0.meta.registry.m2m-pg17/0.1-candidate' ||
      source.decision !== 'AUTHENTICATED_READ_LAB_ONLY' ||
      source.reason !== 'SIGNED_READ_COMMITTED' ||
      AUTH_FLAGS.some(k => source[k] !== false))
      return deny('SOURCE_NOT_ACCEPTED');
    const snap = exact(source.snapshot,SNAPSHOT_KEYS);
    if (!snap || !digest(snap.source_revision) ||
        snap.source_revision !== snap.snapshot_ref ||
        snap.ownership_evidence_state !== 'UNVERIFIED' ||
        snap.delegation_evidence_state !== 'UNVERIFIED')
      return deny('SOURCE_NOT_ACCEPTED');
    if (EXPECTED_SCOPE_KEYS.slice(0,5).some(k => !id(snap[k])) ||
        !phone(snap.phone_number_id)) return deny('SOURCE_NOT_ACCEPTED');
    if (EXPECTED_SCOPE_KEYS.some(k => snap[k] !== scope[k]))
      return deny('SCOPE_MISMATCH');
    const versions = exact(snap.revisions,REVISION_KEYS);
    if (!versions || REVISION_KEYS.some(k => !revision(versions[k])))
      return deny('SOURCE_NOT_ACCEPTED');
    if (REVISION_KEYS.some(k => versions[k] !== revisions[k]))
      return deny('STALE_REVISION');
    return Object.freeze({
      contract_version: VERSION,
      decision: 'LAB_SCOPE_MATCHED_UNVERIFIED' as const,
      reason: 'SCOPED_SHAPE_MATCHED' as const,
      route_revision: versions.route as number,
      app_revision: versions.app as number,
      binding_revision: versions.binding as number,
      grant_revision: versions.grant as number,
      principal_revision: versions.principal as number,
      ...DENIAL,
    });
  } catch {
    return deny('INVALID_INPUT');
  }
}
