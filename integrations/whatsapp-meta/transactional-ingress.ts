/**
 * WA-05A: NON-DURABLE, OFFLINE S0 inbox transaction boundary simulation.
 * This module is a TEST HARNESS: never route a real Meta webhook to it.
 * Neither a valid HMAC nor this fake commit is proof of a durable ACK.
 */
import { inspectRoutedMetaPost, type RoutablePost, type TrustedRoutingPorts,
  type ScopedTechnicalEvent } from './routed-webhook.ts';
import { selectMetaCredential, resolveSignedMetaChannel,
  type TrustedMetaScope } from './credential-routing.ts';
import { FakeVersionedMetaRegistry } from './lifecycle-simulation.ts';

export type FakeIngressResult = Readonly<{
  decision: 'SIMULATED_COMMIT' | 'SIMULATED_REPLAY' | 'BLOCKED' | 'CONFLICT' | 'SIMULATED_WRITE_FAILURE';
  reason: 'LAB_COMMIT' | 'SAME_BATCH' | 'INVALID_INPUT' | 'HMAC_OR_ROUTING_DENIED' |
    'BINDING_REVOKED_OR_CHANGED' | 'PAYLOAD_UNAVAILABLE' | 'DUPLICATE_POSITION' |
    'BATCH_REF_CONFLICT' | 'LAB_WRITE_FAILURE' | 'CAPACITY_REACHED';
  simulated_occurrences: number;
  /** A fake in-memory commit NEVER permits HTTP 200 or production use. */
  ack_allowed: false;
  production_authorized: false;
}>;

type FakeOccurrence = {
  occurrence_ref: string;
  batch_ref: string;
  index: number;
  position: string;
  app_ref: string;
  scope: TrustedMetaScope;
  provider_message_id: string;
};

type BatchMarker = { fingerprint: string; count: number };
const REF = /^[A-Za-z0-9_.:-]{1,128}$/;
const reject = (reason: FakeIngressResult['reason'], decision: FakeIngressResult['decision'] = 'BLOCKED'): FakeIngressResult =>
  ({ decision, reason, simulated_occurrences: 0, ack_allowed: false, production_authorized: false });
const scopesEqual = (a: TrustedMetaScope, b: TrustedMetaScope): boolean =>
  a.app_ref === b.app_ref && a.concessionaria_id === b.concessionaria_id &&
  a.canal_id === b.canal_id && a.waba_id === b.waba_id &&
  a.phone_number_id === b.phone_number_id;
const bytesEqual = (a: Uint8Array, b: Uint8Array): boolean => {
  if (a.length !== b.length) return false;
  let differs = 0;
  for (let i = 0; i < a.length; i++) differs |= a[i] ^ b[i];
  return differs === 0;
};

/** Fake protected payload store. NEVER put customer data here. Memory only. */
export class FakeProtectedPayloads {
  private readonly bodies = new Map<string, Uint8Array>();
  putFixture(ref: string, raw: Uint8Array): boolean {
    if (typeof ref !== 'string' || !REF.test(ref) || !(raw instanceof Uint8Array) ||
        raw.length === 0 || raw.length > 256 * 1024 || this.bodies.has(ref)) return false;
    this.bodies.set(ref, Uint8Array.from(raw));
    return true;
  }
  matchesFixture(ref: string, raw: Uint8Array): boolean {
    const found = this.bodies.get(ref);
    return !!found && bytesEqual(found, raw);
  }
}

/** Fake idempotency store. No database, audit trail, locks or crash recovery. */
export class FakeTransactionalInbox {
  private readonly batches = new Map<string, BatchMarker>();
  private readonly records: FakeOccurrence[] = [];
  private serial = 0;
  get occurrenceCount(): number { return this.records.length; }
  get batchCount(): number { return this.batches.size; }
  /** Only a count is exposed; details/PII remain inside this synthetic fixture. */
  get countByBatch(): Readonly<Record<string, number>> {
    return Object.fromEntries([...this.batches.entries()].map(([key, b]) => [key, b.count]));
  }

  /**
   * The scoped events come from inspectRoutedMetaPost with a fake secret port.
   * At "commit", re-read the exact registry and enforce all bindings *again*.
   * The protected payload is also checked as present in a fake storage fixture.
   * No bridge to DurableBatchReceipt or decideBatchAck is provided on purpose.
   */
  async inspectAndCommitFixture(input: {
    batch_ref: string;
    protected_payload_ref: string;
    request: RoutablePost;
  }, registry: FakeVersionedMetaRegistry, payloads: FakeProtectedPayloads,
  ports: Pick<TrustedRoutingPorts, 'resolveSecret' | 'nowMs'>,
  options: { beforeCommit?: () => void; failWrite?: boolean } = {}): Promise<FakeIngressResult> {
    if (!input || typeof input.batch_ref !== 'string' || !REF.test(input.batch_ref) ||
        typeof input.protected_payload_ref !== 'string' || !REF.test(input.protected_payload_ref) ||
        !input.request || !(input.request.raw_body instanceof Uint8Array) ||
        input.request.raw_body.length === 0 || input.request.raw_body.length > 256 * 1024 ||
        !input.request.route || typeof input.request.route.route_ref !== 'string' ||
        !REF.test(input.request.route.route_ref) ||
        !Number.isSafeInteger(input.request.route.expected_revision) ||
        input.request.route.expected_revision <= 0 ||
        !registry || !payloads || !ports || typeof ports.resolveSecret !== 'function' ||
        typeof ports.nowMs !== 'function') return reject('INVALID_INPUT');

    // Snapshot original bytes before the first await. Metadata is also frozen
    // so a caller mutation cannot change the route during asynchronous HMAC.
    const raw = Uint8Array.from(input.request.raw_body);
    const batchRef = input.batch_ref;
    const payloadRef = input.protected_payload_ref;
    const route = { route_ref: input.request.route.route_ref,
      expected_revision: input.request.route.expected_revision };
    const signature = input.request.signature_header;
    const prepared: RoutablePost = { raw_body: raw, route, signature_header: signature };
    const routablePorts: TrustedRoutingPorts = {
      currentRegistry: () => registry.snapshot(),
      resolveSecret: ports.resolveSecret,
      nowMs: ports.nowMs,
    };
    const inspection = await inspectRoutedMetaPost(prepared, routablePorts);
    if (!inspection.ok) return reject('HMAC_OR_ROUTING_DENIED');
    if (inspection.events.length === 0 || inspection.events.length > 100)
      return reject('INVALID_INPUT');

    // The original raw payload must be present in the fake protected store.
    // A mere receipt containing counts/metadata cannot pass this gate.
    if (!payloads.matchesFixture(payloadRef, raw)) return reject('PAYLOAD_UNAVAILABLE');
    const digestBytes = new Uint8Array(await crypto.subtle.digest('SHA-256', raw));
    const digest = Array.from(digestBytes, b => b.toString(16).padStart(2, '0')).join('');
    const fingerprint = JSON.stringify([route.route_ref, route.expected_revision,
      inspection.authenticated_app_ref, payloadRef, digest]);

    // Simulates a revocation/rotation immediately before the commit boundary.
    try { options.beforeCommit?.(); } catch { return reject('INVALID_INPUT'); }
    const existing = this.batches.get(batchRef);
    if (existing) {
      // Even exact replays are gated by current auth below (no untrusted ACK).
      if (existing.fingerprint !== fingerprint) return reject('BATCH_REF_CONFLICT', 'CONFLICT');
    }
    // Read the trusted clock BEFORE the final snapshot; fixture clocks may
    // trigger test-only concurrent revocation callbacks.
    let commitTime: number;
    let current;
    try { commitTime = ports.nowMs(); current = registry.snapshot(); } catch { return reject('BINDING_REVOKED_OR_CHANGED'); }
    const selected = selectMetaCredential(current, {
      purpose: 'POST_APP_SECRET', trusted_route_ref: route.route_ref,
      expected_revision: route.expected_revision, at_ms: commitTime,
    });
    if (!selected.ok || selected.app_ref !== inspection.authenticated_app_ref)
      return reject('BINDING_REVOKED_OR_CHANGED');
    const uniquePositions = new Set<string>();
    for (const item of inspection.events) {
      if (!this.exactBinding(item, inspection.authenticated_app_ref, route, current, commitTime))
        return reject('BINDING_REVOKED_OR_CHANGED');
      const pos = item.event.position;
      if (!pos || !['messages','statuses'].includes(pos.array_kind) ||
          ![pos.entry_index, pos.change_index, pos.item_index].every(x => Number.isSafeInteger(x) && x >= 0))
        return reject('INVALID_INPUT');
      const key = JSON.stringify([pos.entry_index, pos.change_index, pos.array_kind, pos.item_index]);
      if (uniquePositions.has(key)) return reject('DUPLICATE_POSITION');
      uniquePositions.add(key);
    }
    if (existing) return { decision: 'SIMULATED_REPLAY', reason: 'SAME_BATCH',
      simulated_occurrences: existing.count, ack_allowed: false, production_authorized: false };
    if (this.batches.size >= 100 || this.records.length + inspection.events.length > 1000)
      return reject('CAPACITY_REACHED');
    if (options.failWrite) return reject('LAB_WRITE_FAILURE', 'SIMULATED_WRITE_FAILURE');

    // Single-process, synchronous fake commit: no await occurs between the
    // last binding verification and this insertion. NOT a real DB transaction.
    const additions = inspection.events.map((item, index): FakeOccurrence => ({
      occurrence_ref: 'FAKE_OCC_' + (this.serial + index + 1),
      batch_ref: batchRef, index,
      position: JSON.stringify(item.event.position),
      app_ref: inspection.authenticated_app_ref,
      scope: structuredClone(item.scope),
      provider_message_id: item.event.provider_message_id,
    }));
    this.records.push(...additions);
    this.serial += additions.length;
    this.batches.set(batchRef, { fingerprint, count: additions.length });
    return { decision: 'SIMULATED_COMMIT', reason: 'LAB_COMMIT',
      simulated_occurrences: additions.length, ack_allowed: false, production_authorized: false };
  }

  private exactBinding(item: ScopedTechnicalEvent, appRef: string,
    route: { route_ref: string; expected_revision: number },
    current: ReturnType<FakeVersionedMetaRegistry['snapshot']>, atMs: number): boolean {
    const binding = resolveSignedMetaChannel(current, {
      trusted_route_ref: route.route_ref, authenticated_app_ref: appRef,
      waba_id: item.event.waba_id, phone_number_id: item.event.phone_number_id,
      expected_revision: route.expected_revision, at_ms: atMs,
    });
    return binding.ok && scopesEqual(binding.scope, item.scope);
  }
}
