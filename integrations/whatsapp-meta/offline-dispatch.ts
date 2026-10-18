/**
 * WA-02C: IN-MEMORY simulation of the boundary S0 -> Meta Graph adapter.
 * Only scripted observations; no fetch, credentials, Supabase or real transport.
 * FakeS0 state is test data, NOT a production authorization implementation.
 */
import { prepareGraphTextRequest, classifyGraphSendResult,
  type GraphTextIntent, type GraphSendOutcome } from './graph-outbound.ts';
import { prepareGraphTemplateRequest,
  type TemplateIntent, type TrustedTemplateSnapshot,
  type TrustedTemplateScope } from './graph-template.ts';

export type OfflineCommand =
  | { kind: 'text'; intent: GraphTextIntent; asserted_scope: TrustedTemplateScope }
  | { kind: 'template'; intent: TemplateIntent; asserted_scope: TrustedTemplateScope };

export type FakeS0Decision = {
  intent_id: string;
  attempt_id: string;
  correlation_id: string;
  authorized_business_action: 'C03' | 'C06' | 'C12';
  current_state_version: number;
  allowed_now: boolean;
  scope: TrustedTemplateScope;
  recipient_verified: string;
  template_snapshot?: TrustedTemplateSnapshot;
};

export type ScriptedObservation =
  | { kind: 'transport_error' }
  | { kind: 'http_response'; http_status: number; response_json: unknown };

type PreparedRequest = {
  method: 'POST'; relative_path: string; content_type: 'application/json';
  body: { type: 'text' | 'template' };
};

export type OfflineDispatchResult = {
  readonly decision: 'BLOCKED' | 'SIMULATED' | 'RECORD_UNCERTAIN';
  readonly reason:
    | 'S0_DENIED' | 'SCOPE_MISMATCH' | 'STALE_INTENT' | 'INVALID_PREPARATION'
    | 'ATTEMPT_ALREADY_RESERVED' | 'SIMULATED_OBSERVATION' | 'RECORD_FAILURE';
  readonly attempt_id: string;
  readonly correlation_id: string;
  readonly observation?: GraphSendOutcome;
  readonly retry_automatically: false;
};

const scopeKeys = ['concessionaria_id', 'canal_id', 'meta_app_ref',
  'meta_waba_id', 'phone_number_id'] as const;
function sameScope(a: TrustedTemplateScope, b: TrustedTemplateScope): boolean {
  return !!a && !!b && scopeKeys.every(k => typeof a[k] === 'string' &&
    a[k].length > 0 && a[k] === b[k]);
}
function safeId(value: unknown): value is string {
  return typeof value === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(value);
}

/** Fake in-memory S0 adapter; no database or authorization rules. */
export class FakeS0Outbox {
  private readonly states = new Map<string, FakeS0Decision>();
  private readonly reservedIntents = new Set<string>();
  private readonly recorded = new Map<string, GraphSendOutcome>();
  failNextRecording = false;

  upsertCurrent(decision: FakeS0Decision): void {
    if (!safeId(decision.intent_id)) throw new Error('INVALID_FIXTURE_ID');
    this.states.set(decision.intent_id, structuredClone(decision));
  }
  current(intentId: string): FakeS0Decision | undefined {
    const found = this.states.get(intentId);
    return found ? structuredClone(found) : undefined;
  }
  reserve(intentId: string): boolean {
    if (this.reservedIntents.has(intentId)) return false;
    this.reservedIntents.add(intentId);
    return true;
  }
  record(intentId: string, outcome: GraphSendOutcome): void {
    if (this.failNextRecording) {
      this.failNextRecording = false;
      throw new Error('SYNTHETIC_RECORD_FAILURE');
    }
    this.recorded.set(intentId, structuredClone(outcome));
  }
  recordedFor(intentId: string): GraphSendOutcome | undefined {
    const found = this.recorded.get(intentId);
    return found ? structuredClone(found) : undefined;
  }
}

/** Fake Graph port: ONLY returns preloaded outcomes; never stores the payload. */
export class ScriptedFakeGraph {
  readonly kinds: ('text' | 'template')[] = [];
  private readonly queue: ScriptedObservation[];
  constructor(observations: readonly ScriptedObservation[]) {
    this.queue = observations.map(item => structuredClone(item));
  }
  observe(request: PreparedRequest): ScriptedObservation {
    this.kinds.push(request.body.type);
    // Empty script simulates a lost connection/unknown external acceptance.
    return this.queue.shift() ?? { kind: 'transport_error' };
  }
  get calls(): number { return this.kinds.length; }
}

/**
 * A test-only dispatcher that always re-reads the FAKE S0 state at dispatch.
 * It models gates and a single reserved attempt, but is neither transactional
 * nor authorized for network use. It deliberately takes NO HTTP client/token.
 * Avoid exposing/logging request: it contains a recipient and message text.
 */
export function simulateOfflineDispatch(
  command: OfflineCommand,
  fakeS0: FakeS0Outbox,
  fakeGraph: ScriptedFakeGraph,
  apiVersion: string,
): OfflineDispatchResult {
  const intent = command?.intent;
  const attempt_id = safeId(intent?.attempt_id) ? intent.attempt_id : 'invalid-attempt';
  const correlation_id = safeId(intent?.correlation_id) ? intent.correlation_id : 'invalid-correlation';
  const blocked = (reason: OfflineDispatchResult['reason']): OfflineDispatchResult => ({
    decision: 'BLOCKED', reason, attempt_id, correlation_id, retry_automatically: false,
  });
  if (!intent || !safeId(intent.intent_id) || !safeId(intent.attempt_id) ||
      !safeId(intent.correlation_id)) return blocked('INVALID_PREPARATION');

  const current = fakeS0.current(intent.intent_id);
  if (!current || !current.allowed_now) return blocked('S0_DENIED');
  if (current.intent_id !== intent.intent_id || current.attempt_id !== intent.attempt_id ||
      current.correlation_id !== intent.correlation_id ||
      current.authorized_business_action !== intent.authorized_business_action ||
      current.current_state_version !== intent.authorized_state_version) {
    return blocked('STALE_INTENT');
  }
  if (!sameScope(current.scope, command.asserted_scope) ||
      current.scope.phone_number_id !== intent.phone_number_id ||
      current.recipient_verified !== intent.recipient_verified) {
    return blocked('SCOPE_MISMATCH');
  }

  let request: PreparedRequest;
  try {
    if (command.kind === 'template') {
      if (!current.template_snapshot) return blocked('INVALID_PREPARATION');
      request = prepareGraphTemplateRequest(
        command.intent, current.template_snapshot, current.scope, apiVersion,
      );
    } else if (command.kind === 'text') {
      request = prepareGraphTextRequest(command.intent, apiVersion);
    } else {
      return blocked('INVALID_PREPARATION');
    }
  } catch {
    // Do not expose raw validation errors containing fixture text/PII.
    return blocked('INVALID_PREPARATION');
  }

  if (!fakeS0.reserve(intent.intent_id)) return blocked('ATTEMPT_ALREADY_RESERVED');
  let observation: ScriptedObservation;
  try {
    observation = fakeGraph.observe(request);
  } catch {
    observation = { kind: 'transport_error' };
  }
  const outcome = classifyGraphSendResult(attempt_id, correlation_id, observation);
  try {
    fakeS0.record(intent.intent_id, outcome);
  } catch {
    // Attempt stays reserved after uncertain persistence; never resend blindly.
    return { decision: 'RECORD_UNCERTAIN', reason: 'RECORD_FAILURE',
      attempt_id, correlation_id, retry_automatically: false };
  }
  return { decision: 'SIMULATED', reason: 'SIMULATED_OBSERVATION',
    attempt_id, correlation_id, observation: outcome, retry_automatically: false };
}
