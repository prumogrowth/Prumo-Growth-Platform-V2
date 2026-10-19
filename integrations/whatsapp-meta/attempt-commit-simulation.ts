/**
 * WA-12: fake write-result uncertainty at the Graph accepted -> S0 attempt
 * binding seam. Uses WA-11 ledger; does not duplicate S0 ingress/outbox.
 * This laboratory cannot prove a durable commit, issue ACKs, dispatch Graph,
 * infer message delivery, or authorize business transitions. No network/DB.
 */
import { FakeAttemptBindingLedger, snapshotAttemptIdentity } from './attempt-binding.ts';
import { isAcceptedGraphEvidence } from './status-evidence.ts';

export type FakeCommitFault = 'none' | 'before_commit_response_lost' | 'after_commit_response_lost';
export type FakeCommitResult = Readonly<{
  decision: 'LAB_COMMITTED' | 'LAB_COMMIT_UNKNOWN' | 'LAB_CONFLICT' | 'LAB_REJECTED';
  retry_external: false;
  ack_allowed: false;
  production_authorized: false;
}>;
export type FakeRecoverResult = Readonly<{
  decision: 'LAB_FOUND_EXACT' | 'LAB_ABSENT' | 'LAB_CONFLICT' | 'LAB_INVALID';
  retry_external: false;
  ack_allowed: false;
  production_authorized: false;
}>;
const commit = (decision: FakeCommitResult['decision']): FakeCommitResult =>
  ({decision, retry_external:false, ack_allowed:false, production_authorized:false});
const recovery = (decision: FakeRecoverResult['decision']): FakeRecoverResult =>
  ({decision, retry_external:false, ack_allowed:false, production_authorized:false});
const graphFields = [
  'attempt_id','correlation_id','send_state','api_accepted','http_status',
  'provider_message_id','meta_error_code','meta_error_subcode','retry_automatically',
] as const;

/** Stable, data-only Graph observation; never trusts getter or extra fields. */
function snapshotAcceptedEvidence(raw: unknown): Record<string,unknown> | undefined {
  try {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return;
    const proto = Object.getPrototypeOf(raw);
    if (proto !== Object.prototype && proto !== null) return;
    const descriptors = Object.getOwnPropertyDescriptors(raw);
    if (Reflect.ownKeys(raw).length !== graphFields.length ||
        Object.keys(descriptors).length !== graphFields.length) return;
    const stable: Record<string,unknown> = Object.create(null);
    for (const key of graphFields) {
      const d = descriptors[key];
      if (!d || !Object.hasOwn(d,'value')) return;
      stable[key] = d.value;
    }
    return isAcceptedGraphEvidence(stable) ? stable : undefined;
  } catch { return; }
}

/**
 * Scope and Graph observation MUST have been obtained from trusted internal
 * services; this fixture only checks their coherence and simulates failures.
 */
export class FakeAttemptCommitBoundary {
  private readonly store = new FakeAttemptBindingLedger();
  get bindingCount(): number { return this.store.size; }

  recordAcceptedFixture(identity: unknown, graphEvidence: unknown,
    fault: FakeCommitFault = 'none'): FakeCommitResult {
    const stable = snapshotAttemptIdentity(identity);
    const evidence = snapshotAcceptedEvidence(graphEvidence);
    if (!stable || !evidence ||
        !['none','before_commit_response_lost','after_commit_response_lost'].includes(fault) ||
        stable.attempt_id !== evidence.attempt_id ||
        stable.correlation_id !== evidence.correlation_id ||
        stable.provider_message_id !== evidence.provider_message_id) return commit('LAB_REJECTED');
    // A missing write confirmation must NEVER trigger a Graph resend.
    if (fault === 'before_commit_response_lost') return commit('LAB_COMMIT_UNKNOWN');
    const claim = this.store.claim(stable);
    if (claim === 'CONFLICT') return commit('LAB_CONFLICT');
    if (claim !== 'NEW' && claim !== 'SAME') return commit('LAB_REJECTED');
    return commit(fault === 'after_commit_response_lost' ? 'LAB_COMMIT_UNKNOWN' : 'LAB_COMMITTED');
  }

  /** Pure read-only, exact-scope check. Does not insert a missing record. */
  recoverExactFixture(identity: unknown): FakeRecoverResult {
    const result = this.store.lookup(identity);
    if (result === 'SAME') return recovery('LAB_FOUND_EXACT');
    if (result === 'CONFLICT') return recovery('LAB_CONFLICT');
    return recovery(result === 'ABSENT' ? 'LAB_ABSENT' : 'LAB_INVALID');
  }
}
