/**
 * WA-04D: single-process, scripted versioned registry of FAKE Meta bindings.
 * Memory-only teaching harness. APPLIED_SIMULATED is NOT an admin action,
 * durable compare-and-swap, credential rotation, or distributed lock.
 */
import { planMetaLifecycleTransition, type LifecycleProposalRequest } from './credential-lifecycle.ts';
import type { TrustedMetaRegistry } from './credential-routing.ts';

export type FakeLifecycleResult = Readonly<{
  decision: 'APPLIED_SIMULATED' | 'REPLAYED_SIMULATED' | 'DENIED' | 'OPERATION_CONFLICT';
  reason: 'APPLIED' | 'SAME_PROPOSAL' | 'INVALID_OR_STALE' | 'OPERATION_REF_REUSED';
  app_ref?: string;
  new_revision?: number;
  production_authorized: false;
  retry_automatically: false;
}>;

type RecordedOperation = { readonly fingerprint: string; readonly app_ref: string; readonly revision: number };
const safeRef = (v: unknown): v is string => typeof v === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(v);
const fingerprintFor = (r: LifecycleProposalRequest): string => JSON.stringify([
  r.action, r.app_ref, r.concessionaria_id, r.expected_revision,
  ...(r.action === 'REVOKE_CHANNEL' ? [r.canal_id] : []),
  ...(r.action === 'STAGE_ROTATION' ? [r.next_secret_slots.get_verify_token,
    r.next_secret_slots.post_app_secret, r.next_secret_slots.graph_access_token] : []),
]);

/**
 * The mutation below applies ONLY to this class's own private fake snapshot.
 * A real S0 service needs tenant-admin authentication, database transactions,
 * expected version predicates, audit journal, recovery and credential revocation.
 */
export class FakeVersionedMetaRegistry {
  private snapshotValue: TrustedMetaRegistry;
  private readonly operations = new Map<string, RecordedOperation>();

  constructor(initial: TrustedMetaRegistry) {
    this.snapshotValue = structuredClone(initial);
  }
  snapshot(): TrustedMetaRegistry {
    return structuredClone(this.snapshotValue);
  }
  get appliedOperations(): number { return this.operations.size; }

  proposeAndSwap(request: LifecycleProposalRequest): FakeLifecycleResult {
    const rejected: FakeLifecycleResult = { decision: 'DENIED', reason: 'INVALID_OR_STALE',
      production_authorized: false, retry_automatically: false };
    if (!request || !safeRef(request.operation_ref)) return rejected;
    let fingerprint: string;
    try { fingerprint = fingerprintFor(request); } catch { return rejected; }
    const previous = this.operations.get(request.operation_ref);
    if (previous) {
      if (previous.fingerprint !== fingerprint) return {
        decision: 'OPERATION_CONFLICT', reason: 'OPERATION_REF_REUSED',
        production_authorized: false, retry_automatically: false,
      };
      return { decision: 'REPLAYED_SIMULATED', reason: 'SAME_PROPOSAL',
        app_ref: previous.app_ref, new_revision: previous.revision,
        production_authorized: false, retry_automatically: false };
    }
    try {
      // Synchronous compare/plan/swap is atomic ONLY for one JS event loop,
      // not a transaction against Supabase or an external Meta call.
      const plan = planMetaLifecycleTransition(this.snapshotValue, request);
      if (!plan.ok) return rejected;
      const candidate = structuredClone(plan.candidate_registry);
      this.snapshotValue = candidate;
      this.operations.set(request.operation_ref, {
        fingerprint, app_ref: plan.app_ref, revision: plan.next_revision,
      });
      return { decision: 'APPLIED_SIMULATED', reason: 'APPLIED',
        app_ref: plan.app_ref, new_revision: plan.next_revision,
        production_authorized: false, retry_automatically: false };
    } catch { return rejected; }
  }
}
