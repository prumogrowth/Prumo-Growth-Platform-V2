/**
 * WA-05B — MEMORY-ONLY laboratory for crash/replay of already admitted S0 batches.
 * No trusted S0 receipt, external ACK, network, Meta secrets or actual durability.
 * Callers are fictional trusted S0 fixtures; this does NOT authenticate a webhook.
 */
export type SimulatedEvent = Readonly<{
  array_kind: 'messages' | 'statuses'; entry_index: number;
  change_index: number; item_index: number; provider_message_id: string;
}>;
export type SimulatedBatch = Readonly<{
  batch_ref: string; app_ref: string; concessionaria_id: string; canal_id: string;
  protected_payload_ref: string; /** fixture content binding, not cryptographic proof */
  payload_digest: string; events: readonly SimulatedEvent[];
}>;
export type LabAdmission = Readonly<{
  decision: 'LAB_COMMITTED' | 'LAB_ALREADY_COMMITTED' | 'LAB_RESULT_UNKNOWN' | 'LAB_NOT_COMMITTED' | 'LAB_CONFLICT' | 'LAB_INVALID';
  reason: 'COMMITTED' | 'SAME_BATCH' | 'RESULT_LOST' | 'BEFORE_COMMIT' | 'BATCH_COLLISION' | 'INVALID';
  count: number; ack_allowed: false; production_authorized: false;
}>;
export type LabRecovery = Readonly<{
  decision: 'LAB_FOUND' | 'LAB_ABSENT' | 'LAB_MISMATCH';
  pending: number; done: number; ack_allowed: false; production_authorized: false;
}>;
export type TrustedWorkerScope = Readonly<{app_ref: string; concessionaria_id: string; canal_id: string}>;
export type LabClaim = Readonly<{
  decision: 'CLAIMED' | 'NO_WORK' | 'INVALID';
  occurrence_ref?: string; lease_ref?: string; production_authorized: false;
}>;
export type LabFinish = Readonly<{
  decision: 'APPLIED_IN_LAB' | 'LAB_RESULT_UNKNOWN' | 'ALREADY_DONE' | 'STALE_LEASE' | 'INVALID';
  production_authorized: false; retry_external: false;
}>;

type Occurrence = {
  readonly ref: string; readonly batch: string; readonly scope: TrustedWorkerScope; done: boolean;
  lease?: { owner: string; token: string; expires_at: number };
};
type StoredBatch = { readonly snapshot: SimulatedBatch; readonly fingerprint: string;
  readonly occurrenceRefs: string[] };
const IDENT = /^[A-Za-z0-9_.:-]{1,128}$/;
const safe = (value: unknown): value is string => typeof value === 'string' && IDENT.test(value);
const providerId = (value: unknown): value is string => typeof value === 'string' &&
  !/[\s\u0000-\u001f\u007f]/.test(value) &&
  /^wamid\.[A-Za-z0-9+\/_=:.-]{1,1024}$/.test(value);
const index = (value: unknown): value is number => Number.isSafeInteger(value) && (value as number) >= 0;
// Fixture inputs must be inert, JSON-like data objects. Accessor properties
// and Proxies must not change the version checked versus the version stored.
const plainData = (value: unknown): value is Record<string, unknown> => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const proto = Object.getPrototypeOf(value);
  if (proto !== Object.prototype && proto !== null) return false;
  return Object.values(Object.getOwnPropertyDescriptors(value)).every(d => 'value' in d);
};
const copyFixture = (input: SimulatedBatch): SimulatedBatch | undefined => {
  try {
    if (!plainData(input) || !Array.isArray(input.events) ||
        !input.events.every(e => plainData(e))) return undefined;
    // Reject unexpected fixture data before cloning; do not retain raw customer
    // text, phone numbers, tokens, or arbitrary payload as journal metadata.
    const batchFields = new Set(['batch_ref','app_ref','concessionaria_id','canal_id',
      'protected_payload_ref','payload_digest','events']);
    const eventFields = new Set(['array_kind','entry_index','change_index',
      'item_index','provider_message_id']);
    if (Object.keys(input).some(key => !batchFields.has(key)) ||
        input.events.some(e => Object.keys(e).some(key => !eventFields.has(key)))) return undefined;
    return structuredClone(input);
  } catch { return undefined; }
};
const validScope = (scope: unknown): scope is TrustedWorkerScope => {
  try {
    if (!plainData(scope)) return false;
    const s = scope as TrustedWorkerScope;
    return safe(s.app_ref) && safe(s.concessionaria_id) && safe(s.canal_id);
  } catch { return false; }
};
const sameScope = (a: TrustedWorkerScope, b: TrustedWorkerScope): boolean =>
  a.app_ref === b.app_ref && a.concessionaria_id === b.concessionaria_id && a.canal_id === b.canal_id;
const complete = (input: SimulatedBatch): boolean => {
  if (!input || !safe(input.batch_ref) || !safe(input.app_ref) ||
    !safe(input.concessionaria_id) || !safe(input.canal_id) ||
    !safe(input.protected_payload_ref) ||
    typeof input.payload_digest !== 'string' || !/^[a-f0-9]{64}$/.test(input.payload_digest) ||
    !Array.isArray(input.events) || input.events.length < 1 || input.events.length > 100) return false;
  const positions = new Set<string>();
  for (const e of input.events) {
    if (!e || !['messages', 'statuses'].includes(e.array_kind) ||
      !index(e.entry_index) || !index(e.change_index) || !index(e.item_index) ||
      !providerId(e.provider_message_id)) return false;
    const pos = JSON.stringify([e.array_kind, e.entry_index, e.change_index, e.item_index]);
    if (positions.has(pos)) return false;
    positions.add(pos);
  }
  return true;
};
const fingerprint = (b: SimulatedBatch): string => JSON.stringify([
  b.app_ref,b.concessionaria_id,b.canal_id,b.protected_payload_ref,b.payload_digest,
  b.events.map(e => [e.array_kind,e.entry_index,e.change_index,e.item_index,e.provider_message_id]),
]);
const admitted = (decision: LabAdmission['decision'], reason: LabAdmission['reason'], count = 0): LabAdmission =>
  ({ decision, reason, count, ack_allowed: false, production_authorized: false });
const recovering = (decision: LabRecovery['decision'], pending=0, done=0): LabRecovery =>
  ({ decision, pending, done, ack_allowed: false, production_authorized: false });
/** Holds only fake metadata; shared across FakeRecoveryWorker instances to simulate restart. */
export class FakeS0RecoveryJournal {
  private readonly batches = new Map<string, StoredBatch>();
  private readonly occurrences = new Map<string, Occurrence>();
  private nextOccurrence = 0;
  private nextLease = 0;
  private effectCountValue = 0;
  get occurrenceCount(): number { return this.occurrences.size; }
  get batchCount(): number { return this.batches.size; }
  get appliedEffects(): number { return this.effectCountValue; }

  /** Simulate crash before commit or loss of response AFTER atomic in-memory commit. */
  admit(input: SimulatedBatch, fault: 'none' | 'before_commit' | 'after_commit' = 'none'): LabAdmission {
    const copy = copyFixture(input);
    if (!copy || !complete(copy) || !['none','before_commit','after_commit'].includes(fault))
      return admitted('LAB_INVALID','INVALID');
    const f = fingerprint(copy);
    const prior = this.batches.get(copy.batch_ref);
    if (prior) return prior.fingerprint === f
      ? admitted('LAB_ALREADY_COMMITTED','SAME_BATCH',prior.occurrenceRefs.length)
      : admitted('LAB_CONFLICT','BATCH_COLLISION');
    if (fault === 'before_commit') return admitted('LAB_NOT_COMMITTED','BEFORE_COMMIT');
    if (this.batches.size >= 100 || this.occurrences.size + copy.events.length > 1000)
      return admitted('LAB_INVALID','INVALID');
    // No await: fake all-or-none in one JS process, NOT a database transaction.
    const refs = copy.events.map((_, n) => 'FAKE_OCC_' + (this.nextOccurrence + n + 1));
    const scope: TrustedWorkerScope = {app_ref:copy.app_ref,
      concessionaria_id:copy.concessionaria_id,canal_id:copy.canal_id};
    for (const ref of refs) this.occurrences.set(ref,{ref,batch:copy.batch_ref,scope,done:false});
    this.nextOccurrence += refs.length;
    this.batches.set(copy.batch_ref,{snapshot:copy,fingerprint:f,occurrenceRefs:refs});
    return fault === 'after_commit'
      ? admitted('LAB_RESULT_UNKNOWN','RESULT_LOST')
      : admitted('LAB_COMMITTED','COMMITTED',refs.length);
  }

  /** A recovery lookup requires all original scope/payload identifiers to match. */
  recover(input: SimulatedBatch): LabRecovery {
    const copy = copyFixture(input);
    if (!copy || !complete(copy)) return recovering('LAB_MISMATCH');
    const prior = this.batches.get(copy.batch_ref);
    if (!prior) return recovering('LAB_ABSENT');
    if (prior.fingerprint !== fingerprint(copy)) return recovering('LAB_MISMATCH');
    const items = prior.occurrenceRefs.map(ref=>this.occurrences.get(ref));
    return recovering('LAB_FOUND',items.filter(x=>x && !x.done).length,items.filter(x=>x?.done).length);
  }

  claim(owner: string, tick: number, leaseDuration: number, scope?: TrustedWorkerScope): LabClaim {
    // TrustedWorkerScope MUST be supplied by a privileged S0 worker context;
    // this in-memory check does not authenticate the owner or the scope.
    if (!safe(owner) || !validScope(scope) || !index(tick) || !index(leaseDuration) || leaseDuration < 1 ||
      !Number.isSafeInteger(tick + leaseDuration)) return {decision:'INVALID',production_authorized:false};
    for (const row of this.occurrences.values()) {
      if (!sameScope(row.scope, scope) || row.done || (row.lease && row.lease.expires_at > tick)) continue;
      const token = 'FAKE_LEASE_' + (++this.nextLease);
      row.lease = {owner,token,expires_at:tick+leaseDuration};
      return {decision:'CLAIMED',occurrence_ref:row.ref,lease_ref:token,production_authorized:false};
    }
    return {decision:'NO_WORK',production_authorized:false};
  }
  /** Effect + done flag happen together in fake memory. No external side effects. */
  finish(owner: string, occurrenceRef: string, leaseRef: string, tick: number,
    fault: 'none' | 'after_apply' = 'none', scope?: TrustedWorkerScope): LabFinish {
    const output=(decision: LabFinish['decision']):LabFinish =>
      ({decision,production_authorized:false,retry_external:false});
    if (!safe(owner) || !safe(occurrenceRef) || !safe(leaseRef) || !validScope(scope) || !index(tick) ||
        !['none','after_apply'].includes(fault)) return output('INVALID');
    const row=this.occurrences.get(occurrenceRef);
    if (!row || !sameScope(row.scope, scope)) return output('INVALID');
    if (row.done) return output('ALREADY_DONE');
    if (!row.lease || row.lease.owner !== owner || row.lease.token !== leaseRef ||
        row.lease.expires_at <= tick) return output('STALE_LEASE');
    row.done=true; row.lease=undefined;
    this.effectCountValue++;
    return output(fault==='after_apply'?'LAB_RESULT_UNKNOWN':'APPLIED_IN_LAB');
  }
}
