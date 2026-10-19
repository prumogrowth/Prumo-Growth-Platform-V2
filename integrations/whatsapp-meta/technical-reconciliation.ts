/**
 * WA-02D — in-memory, synthetic TECHNICAL callback correlation only.
 * Not an ingress endpoint, auth verifier, C07 commercial processor, durable store,
 * ACK authority, retry worker, Meta transport, or civil phone identity resolver.
 *
 * The caller must FIRST HMAC-verify the raw Meta POST with the app secret selected
 * by trusted routing, and FIRST persist it through the S0 durable ingestion port.
 * Neither condition can be established by this pure fixture module.
 */
import type { MetaIngressEvent } from './inbound.ts';
import type { GraphSendOutcome } from './graph-outbound.ts';
import type { TrustedTemplateScope } from './graph-template.ts';
import { isMetaWamid, isStatusPosition, isAcceptedGraphEvidence, isMetaPhoneNumberId } from './status-evidence.ts';

export type TechnicalProgress = 'NONE' | 'SENT' | 'DELIVERED' | 'READ';
export type TechnicalStatus = 'sent' | 'delivered' | 'read' | 'failed';
export type CallbackResult = {
  readonly decision: 'CORRELATED' | 'PENDING_RECONCILIATION' |
    'REJECTED_EVENT' | 'CAPACITY_REACHED';
  readonly reason: 'MATCHED' | 'UNMATCHED_SCOPE_OR_MESSAGE' |
    'UNSUPPORTED_STATUS' | 'INVALID_EVENT' | 'IN_MEMORY_LIMIT';
  readonly progress: TechnicalProgress;
  readonly failure_observed: boolean;
  readonly possible_repeat: boolean;
  readonly observation_count: number;
  readonly retry_automatically: false;
};
export type SendRegistration = {
  readonly decision: 'LINKED' | 'ALREADY_LINKED' | 'NOT_ACCEPTED' |
    'CONFLICT' | 'INVALID_REFERENCE' | 'CAPACITY_REACHED';
  readonly pending_correlated: number;
  readonly retry_automatically: false;
};
export type CorrelationReference = {
  /** Obtained from trusted app configuration, not from user payload. */
  readonly app_ref: string;
  readonly scope: TrustedTemplateScope;
  /** Already verified as the destination for this send. NOT automatically BR normalized. */
  readonly recipient_verified: string;
  readonly intent_id: string;
};
export type TechnicalProjection = {
  readonly progress: TechnicalProgress;
  readonly failure_observed: boolean;
  readonly observation_count: number;
};
type SavedObservation = { status: TechnicalStatus; timestamp: string };
type LinkedSend = {
  readonly intent_id: string;
  readonly attempt_id: string;
  readonly correlation_id: string;
  readonly recipient: string;
  readonly scope: TrustedTemplateScope;
  observations: SavedObservation[];
  progress: TechnicalProgress;
  failure_observed: boolean;
};
type Pending = { callback: MetaIngressEvent; app_ref: string };
const MAX_OBSERVATIONS_PER_MESSAGE = 100;
const MAX_PENDING = 100;
const MAX_LINKED = 100;
const rank: Record<Exclude<TechnicalStatus, 'failed'>, number> =
  { sent: 1, delivered: 2, read: 3 };
const statusFromRank: TechnicalProgress[] = ['NONE', 'SENT', 'DELIVERED', 'READ'];
const id = (s: unknown, max = 256): s is string =>
  typeof s === 'string' && s.length > 0 && s.length <= max &&
  !/[\u0000-\u001f\u007f]/.test(s);
const recipient = (s: unknown): s is string =>
  typeof s === 'string' && /^\d{8,15}$/.test(s);
const isoUTC = (s: unknown): s is string =>
  typeof s === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s) &&
  !Number.isNaN(Date.parse(s)) && new Date(s).toISOString() === s;
const sameScope = (a: TrustedTemplateScope, b: TrustedTemplateScope): boolean =>
  a.concessionaria_id === b.concessionaria_id && a.canal_id === b.canal_id &&
  a.meta_app_ref === b.meta_app_ref && a.meta_waba_id === b.meta_waba_id &&
  a.phone_number_id === b.phone_number_id;
const scopeKey = (app: string, waba: string, phone: string, message: string): string =>
  JSON.stringify([app, waba, phone, message]);
const defaultProjection = (): TechnicalProjection =>
  ({ progress: 'NONE', failure_observed: false, observation_count: 0 });

export class FakeMetaStatusReconciler {
  private readonly sends = new Map<string, LinkedSend>();
  private readonly pending: Pending[] = [];

  /** Graph API accepted + wamid is not proof of delivery. */
  registerAcceptedSend(reference: CorrelationReference, outcome: GraphSendOutcome): SendRegistration {
    const result = (decision: SendRegistration['decision'], pending_correlated = 0): SendRegistration =>
      ({ decision, pending_correlated, retry_automatically: false });
    const s = reference?.scope;
    if (!reference || !s || !id(reference.app_ref) || !id(reference.intent_id) ||
        !id(s.concessionaria_id) || !id(s.canal_id) || !id(s.meta_app_ref) ||
        !id(s.meta_waba_id) || !isMetaPhoneNumberId(s.phone_number_id) ||
        s.meta_app_ref !== reference.app_ref || !recipient(reference.recipient_verified) ||
        !outcome || !id(outcome.attempt_id) ||
        !isMetaWamid(outcome.provider_message_id) || !id(outcome.correlation_id) ||
        outcome.retry_automatically !== false ||
        (outcome.meta_error_code !== null || outcome.meta_error_subcode !== null)) {
      return result('INVALID_REFERENCE');
    }
    if (!isAcceptedGraphEvidence(outcome)) {
      return result('NOT_ACCEPTED');
    }
    const key = scopeKey(reference.app_ref, s.meta_waba_id,
      s.phone_number_id, outcome.provider_message_id!);
    const present = this.sends.get(key);
    if (present) {
      if (present.intent_id === reference.intent_id &&
          present.attempt_id === outcome.attempt_id &&
          present.correlation_id === outcome.correlation_id &&
          present.recipient === reference.recipient_verified &&
          sameScope(present.scope, s)) return result('ALREADY_LINKED');
      return result('CONFLICT');
    }
    if (this.sends.size >= MAX_LINKED) return result('CAPACITY_REACHED');
    const linked: LinkedSend = {
      intent_id: reference.intent_id, attempt_id: outcome.attempt_id,
      correlation_id: outcome.correlation_id,
      recipient: reference.recipient_verified, scope: structuredClone(s),
      observations: [], progress: 'NONE', failure_observed: false,
    };
    this.sends.set(key, linked);
    let pending_correlated = 0;
    // Reconcile only exact app/WABA/phone/message AND recipient. Unmatched
    // records remain pending; phone 8↔9 variants never imply equality.
    for (let i = 0; i < this.pending.length;) {
      const p = this.pending[i];
      if (p.app_ref === reference.app_ref &&
          p.callback.waba_id === s.meta_waba_id &&
          p.callback.phone_number_id === s.phone_number_id &&
          p.callback.provider_message_id === outcome.provider_message_id &&
          p.callback.participant_identifier === reference.recipient_verified &&
          linked.observations.length < MAX_OBSERVATIONS_PER_MESSAGE) {
        this.apply(linked, p.callback.provider_kind as TechnicalStatus,
          p.callback.provider_timestamp);
        this.pending.splice(i, 1);
        pending_correlated++;
      } else i++;
    }
    return result('LINKED', pending_correlated);
  }

  /** The app ref here must be sourced from trusted routing *after* Meta HMAC. */
  observeAuthenticatedFixture(callback: MetaIngressEvent, trustedAppRef: string): CallbackResult {
    const result = (decision: CallbackResult['decision'], reason: CallbackResult['reason'],
      projection: TechnicalProjection = defaultProjection(), possible_repeat = false): CallbackResult =>
      ({ decision, reason, ...projection, possible_repeat, retry_automatically: false });
    if (!callback || callback.source !== 'meta_whatsapp' ||
        callback.event_kind !== 'status_callback' || !id(trustedAppRef) ||
        !id(callback.waba_id) || !isMetaPhoneNumberId(callback.phone_number_id) ||
        !isMetaWamid(callback.provider_message_id) || !isStatusPosition(callback.position) ||
        !recipient(callback.participant_identifier) || !isoUTC(callback.provider_timestamp)) {
      return result('REJECTED_EVENT', 'INVALID_EVENT');
    }
    const status = callback.provider_kind;
    if (!['sent', 'delivered', 'read', 'failed'].includes(status)) {
      // An unknown status is NOT safely interpreted or acknowledged by this
      // fixture. The real S0 quarantine policy must preserve its raw event.
      return result('REJECTED_EVENT', 'UNSUPPORTED_STATUS');
    }
    const key = scopeKey(trustedAppRef, callback.waba_id,
      callback.phone_number_id, callback.provider_message_id);
    const linked = this.sends.get(key);
    if (linked && linked.recipient === callback.participant_identifier) {
      if (linked.observations.length >= MAX_OBSERVATIONS_PER_MESSAGE)
        return result('CAPACITY_REACHED', 'IN_MEMORY_LIMIT', this.project(linked));
      const possible_repeat = linked.observations.some(x =>
        x.status === status && x.timestamp === callback.provider_timestamp);
      this.apply(linked, status as TechnicalStatus, callback.provider_timestamp);
      return result('CORRELATED', 'MATCHED', this.project(linked), possible_repeat);
    }
    if (this.pending.length >= MAX_PENDING)
      return result('CAPACITY_REACHED', 'IN_MEMORY_LIMIT');
    this.pending.push({ callback: structuredClone(callback), app_ref: trustedAppRef });
    // Return no raw IDs/numbers/tokens. A pending status must not be assigned
    // to an unrelated tenant by matching wamid alone.
    return result('PENDING_RECONCILIATION', 'UNMATCHED_SCOPE_OR_MESSAGE');
  }

  projectionFor(reference: CorrelationReference, providerMessageId: string): TechnicalProjection | undefined {
    const s = reference?.scope;
    if (!s || !id(reference.app_ref) || !isMetaWamid(providerMessageId) ||
        s.meta_app_ref !== reference.app_ref) return undefined;
    const linked = this.sends.get(scopeKey(reference.app_ref, s.meta_waba_id,
      s.phone_number_id, providerMessageId));
    return linked && linked.intent_id === reference.intent_id &&
      linked.recipient === reference.recipient_verified &&
      sameScope(linked.scope, s) ? this.project(linked) : undefined;
  }

  get pendingCount(): number { return this.pending.length; }
  get linkedCount(): number { return this.sends.size; }

  private apply(linked: LinkedSend, status: TechnicalStatus, timestamp: string): void {
    linked.observations.push({ status, timestamp });
    if (status === 'failed') linked.failure_observed = true;
    else if (rank[status] > statusFromRank.indexOf(linked.progress)) {
      linked.progress = statusFromRank[rank[status]];
    }
  }
  private project(linked: LinkedSend): TechnicalProjection {
    return { progress: linked.progress,
      failure_observed: linked.failure_observed,
      observation_count: linked.observations.length };
  }
}
