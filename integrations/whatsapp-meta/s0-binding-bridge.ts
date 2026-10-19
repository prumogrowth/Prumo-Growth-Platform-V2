/**
 * WA-13 — OFFLINE integration of WA-12 commit uncertainty with WA-02D
 * callback reconciliation, using the SAME in-memory WA-11 attempt ledger.
 * This is NOT the real S0 persistence service, a Meta endpoint, HMAC proof,
 * HTTP ACK or permission to send. No network, storage or automatic retry.
 * The caller must supply references from trusted S0 scope and already
 * authenticated/durably accepted callback occurrences in real deployment.
 */
import { FakeAttemptBindingLedger, type AttemptIdentity } from './attempt-binding.ts';
import { FakeAttemptCommitBoundary, type FakeCommitFault,
  type FakeCommitResult } from './attempt-commit-simulation.ts';
import { FakeMetaStatusReconciler, type CorrelationReference,
  type TechnicalProjection, type CallbackResult } from './technical-reconciliation.ts';
import type { GraphSendOutcome } from './graph-outbound.ts';
import type { MetaIngressEvent } from './inbound.ts';
import { isSafeEvidenceRef, isMetaPhoneNumberId,
  isMetaWamid } from './status-evidence.ts';

export type FakeBridgeDecision = Readonly<{
  decision: 'LAB_LINKED' | 'LAB_ALREADY_LINKED' | 'LAB_COMMIT_ABSENT' |
    'LAB_BINDING_CONFLICT' | 'LAB_INVALID' | 'LAB_LIMIT';
  pending_correlated: number;
  retry_external: false;
  ack_allowed: false;
  production_authorized: false;
}>;
const response = (decision: FakeBridgeDecision['decision'], pending_correlated = 0): FakeBridgeDecision =>
  ({ decision, pending_correlated, retry_external: false, ack_allowed: false,
    production_authorized: false });

/** Data-only snapshots prevent caller getters/Proxies from shifting the scope. */
function data(value: unknown, fields: readonly string[]): Record<string,unknown> | undefined {
  try {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return;
    const proto = Object.getPrototypeOf(value);
    if (proto !== Object.prototype && proto !== null) return;
    const all = Object.getOwnPropertyDescriptors(value);
    if (Reflect.ownKeys(value).length !== fields.length ||
        Object.keys(all).length !== fields.length) return;
    const stable: Record<string,unknown> = Object.create(null);
    for (const key of fields) {
      if (!Object.hasOwn(all, key) || !Object.hasOwn(all[key], 'value')) return;
      stable[key] = all[key].value;
    }
    return stable;
  } catch { return; }
}
const referenceKeys = ['app_ref','intent_id','recipient_verified','scope'];
const scopeKeys = ['concessionaria_id','canal_id','meta_app_ref','meta_waba_id','phone_number_id'];
const outcomeKeys = ['attempt_id','correlation_id','send_state','api_accepted','http_status',
  'provider_message_id','meta_error_code','meta_error_subcode','retry_automatically'];
function prepare(reference: unknown, rawOutcome: unknown): {
  identity: AttemptIdentity; reference: CorrelationReference; outcome: GraphSendOutcome;
} | undefined {
  const r = data(reference,referenceKeys);
  const s = data(r?.scope,scopeKeys);
  const o = data(rawOutcome,outcomeKeys);
  if (!r || !s || !o ||
      !isSafeEvidenceRef(r.app_ref) || !isSafeEvidenceRef(r.intent_id) ||
      !isSafeEvidenceRef(s.concessionaria_id) || !isSafeEvidenceRef(s.canal_id) ||
      !isSafeEvidenceRef(s.meta_app_ref) || !isSafeEvidenceRef(s.meta_waba_id) ||
      !isMetaPhoneNumberId(s.phone_number_id) ||
      !isSafeEvidenceRef(o.attempt_id) || !isSafeEvidenceRef(o.correlation_id) ||
      !isMetaWamid(o.provider_message_id) ||
      s.meta_app_ref !== r.app_ref ||
      typeof r.recipient_verified !== 'string' || !/^\d{8,15}$/.test(r.recipient_verified)) return;
  const scope = Object.freeze({...s}) as CorrelationReference['scope'];
  const stableReference = Object.freeze({
    app_ref:r.app_ref, intent_id:r.intent_id, recipient_verified:r.recipient_verified, scope,
  }) as CorrelationReference;
  const outcome = Object.freeze({...o}) as GraphSendOutcome;
  const identity: AttemptIdentity = Object.freeze({
    app_ref:stableReference.app_ref,
    concessionaria_id:scope.concessionaria_id, canal_id:scope.canal_id,
    waba_id:scope.meta_waba_id, phone_number_id:scope.phone_number_id,
    intent_id:stableReference.intent_id, attempt_id:outcome.attempt_id,
    correlation_id:outcome.correlation_id,
    recipient_verified:stableReference.recipient_verified,
    provider_message_id:outcome.provider_message_id!,
  });
  return { identity, reference:stableReference, outcome };
}

export class FakeMetaS0BindingBridge {
  private readonly ledger = new FakeAttemptBindingLedger();
  private readonly commit = new FakeAttemptCommitBoundary(this.ledger);
  private readonly reconciler = new FakeMetaStatusReconciler(this.ledger);

  /** Lab observation of Graph acceptance and ambiguous S0 write result. */
  recordAcceptedFixture(reference: CorrelationReference, outcome: GraphSendOutcome,
    fault: FakeCommitFault = 'none'): FakeCommitResult {
    const prepared = prepare(reference,outcome);
    return prepared ? this.commit.recordAcceptedFixture(prepared.identity,prepared.outcome,fault) :
      {decision:'LAB_REJECTED',retry_external:false,ack_allowed:false,production_authorized:false};
  }

  /** Absolutely no record or Graph resend: only a verified exact existing
   * lab binding can be projected into the technical callback reconciler. */
  recoverAndLinkFixture(reference: CorrelationReference, outcome: GraphSendOutcome): FakeBridgeDecision {
    const prepared = prepare(reference,outcome);
    if (!prepared) return response('LAB_INVALID');
    const check = this.commit.recoverExactFixture(prepared.identity);
    if (check.decision === 'LAB_ABSENT') return response('LAB_COMMIT_ABSENT');
    if (check.decision === 'LAB_CONFLICT') return response('LAB_BINDING_CONFLICT');
    if (check.decision !== 'LAB_FOUND_EXACT') return response('LAB_INVALID');
    const linked = this.reconciler.registerAcceptedSend(prepared.reference,prepared.outcome);
    if (linked.decision === 'LINKED') return response('LAB_LINKED',linked.pending_correlated);
    if (linked.decision === 'ALREADY_LINKED') return response('LAB_ALREADY_LINKED');
    if (linked.decision === 'CAPACITY_REACHED') return response('LAB_LIMIT');
    return response(linked.decision === 'CONFLICT' ? 'LAB_BINDING_CONFLICT':'LAB_INVALID');
  }

  /** Assumes separately validated HMAC and preserved positional S0 occurrence. */
  observeAuthenticatedFixture(event: MetaIngressEvent, trustedAppRef: string): CallbackResult {
    return this.reconciler.observeAuthenticatedFixture(event,trustedAppRef);
  }
  projectionFor(reference: CorrelationReference, wamid: string): TechnicalProjection | undefined {
    return this.reconciler.projectionFor(reference,wamid);
  }
  get linkedCount(): number { return this.reconciler.linkedCount; }
  get bindingCount(): number { return this.commit.bindingCount; }
  get pendingCount(): number { return this.reconciler.pendingCount; }
}
