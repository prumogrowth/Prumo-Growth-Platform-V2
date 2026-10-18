/**
 * WA-02A — offline Graph API outbound message candidate.
 * Does not use fetch, secrets, environment, network or Supabase.
 * The future S0 backend MUST revalidate intent, destination and state at dispatch.
 */

export type BusinessAction = 'C03' | 'C06' | 'C12';
export type GraphTextIntent = {
  contract_version: 'meta-s0.v0.1-proposed';
  intent_id: string;
  attempt_id: string;
  correlation_id: string;
  authorized_business_action: BusinessAction;
  authorized_state_version: number;
  /** Must be a currently bound Meta phone number ID, verified by trusted backend. */
  phone_number_id: string;
  /** Destination verified and authorized by backend. Do not guess BR 8↔9 variants. */
  recipient_verified: string;
  /** Protected text materialized only after the backend authorizes dispatch. */
  text_body: string;
};

export type GraphTextRequest = {
  method: 'POST';
  relative_path: string;
  content_type: 'application/json';
  body: {
    messaging_product: 'whatsapp';
    recipient_type: 'individual';
    to: string;
    type: 'text';
    text: { preview_url: false; body: string };
  };
};

export class OutboundPreflightError extends Error {
  readonly code: 'INVALID_INTENT' | 'UNSUPPORTED_ACTION' | 'INVALID_DESTINATION' | 'INVALID_MESSAGE';
  constructor(code: 'INVALID_INTENT' | 'UNSUPPORTED_ACTION' | 'INVALID_DESTINATION' | 'INVALID_MESSAGE') {
    super(code);
    this.code = code;
    this.name = 'OutboundPreflightError';
  }
}

function id(value: unknown, max = 128): value is string {
  return typeof value === 'string' && value.length > 0 && value.length <= max &&
    /^[A-Za-z0-9_.:-]+$/.test(value);
}

/**
 * Inert request description, NOT a grant to send. Returned body contains PII
 * and must never be logged, persisted in plaintext or exposed to clients.
 * Caller MUST verify latest backend authorization before actual HTTP dispatch.
 */
export function prepareGraphTextRequest(intent: GraphTextIntent, apiVersion: string): GraphTextRequest {
  if (!intent || intent.contract_version !== 'meta-s0.v0.1-proposed' ||
      !id(intent.intent_id) || !id(intent.attempt_id) || !id(intent.correlation_id) ||
      !Number.isSafeInteger(intent.authorized_state_version) || intent.authorized_state_version <= 0 ||
      !/^v\d{1,2}\.\d{1,2}$/.test(apiVersion)) {
    throw new OutboundPreflightError('INVALID_INTENT');
  }
  // C06 requires the separate template dispatch contract; never send free text.
  if (!['C03', 'C12'].includes(intent.authorized_business_action)) {
    throw new OutboundPreflightError('UNSUPPORTED_ACTION');
  }
  if (typeof intent.phone_number_id !== 'string' || !/^\d{5,25}$/.test(intent.phone_number_id) ||
      typeof intent.recipient_verified !== 'string' || !/^\d{8,15}$/.test(intent.recipient_verified)) {
    throw new OutboundPreflightError('INVALID_DESTINATION');
  }
  if (typeof intent.text_body !== 'string' || intent.text_body.trim().length === 0 ||
      [...intent.text_body].length > 4096) {
    throw new OutboundPreflightError('INVALID_MESSAGE');
  }
  return {
    method: 'POST',
    relative_path: '/' + apiVersion + '/' + intent.phone_number_id + '/messages',
    content_type: 'application/json',
    body: {
      messaging_product: 'whatsapp',
      recipient_type: 'individual',
      to: intent.recipient_verified,
      type: 'text',
      text: { preview_url: false, body: intent.text_body },
    },
  };
}

type GraphObservation =
  | { kind: 'transport_error' }
  | { kind: 'http_response'; http_status: number; response_json: unknown };

export type GraphSendOutcome = {
  attempt_id: string;
  correlation_id: string;
  send_state: 'API_ACCEPTED' | 'PROVIDER_REJECTED' | 'UNCERTAIN_EXTERNAL';
  api_accepted: boolean;
  /** Graph API HTTP response is not a delivery/read confirmation. */
  http_status: number | null;
  provider_message_id: string | null;
  meta_error_code: number | null;
  meta_error_subcode: number | null;
  retry_automatically: false;
};

function object(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}
function metaCode(v: unknown): number | null {
  return typeof v === 'number' && Number.isSafeInteger(v) && v >= 0 && v <= 999999999
    ? v : null;
}

/**
 * Interpret a SINGLE dispatch observation without copying provider error text.
 * Any network error or ambiguous HTTP result is UNCERTAIN_EXTERNAL. Never retry
 * automatically: Meta may have accepted before a connection was lost.
 * Called only for a dispatch already attempted by an approved transport.
 */
export function classifyGraphSendResult(
  attempt_id: string,
  correlation_id: string,
  observation: GraphObservation,
): GraphSendOutcome {
  if (!id(attempt_id) || !id(correlation_id)) {
    throw new OutboundPreflightError('INVALID_INTENT');
  }
  const base = {
    attempt_id, correlation_id, api_accepted: false,
    http_status: null as number | null,
    provider_message_id: null as string | null,
    meta_error_code: null as number | null,
    meta_error_subcode: null as number | null,
    retry_automatically: false as const,
  };
  if (observation.kind === 'transport_error') {
    return { ...base, send_state: 'UNCERTAIN_EXTERNAL' };
  }
  const status = observation.http_status;
  if (!Number.isInteger(status) || status < 100 || status > 599) {
    return { ...base, send_state: 'UNCERTAIN_EXTERNAL' };
  }
  const output = { ...base, http_status: status };
  if (status >= 200 && status < 300) {
    const payload = observation.response_json;
    const messages = object(payload) ? payload.messages : null;
    const message = Array.isArray(messages) && messages.length === 1 ? messages[0] : null;
    const wamid = object(message) ? message.id : null;
    if (typeof wamid === 'string' && /^wamid\.[A-Za-z0-9_.:-]{1,250}$/.test(wamid)) {
      return { ...output, send_state: 'API_ACCEPTED', api_accepted: true,
        provider_message_id: wamid };
    }
    return { ...output, send_state: 'UNCERTAIN_EXTERNAL' };
  }
  const err = object(observation.response_json) && object(observation.response_json.error)
    ? observation.response_json.error : null;
  const errorDetails = {
    ...output,
    meta_error_code: err ? metaCode(err.code) : null,
    meta_error_subcode: err ? metaCode(err.error_subcode) : null,
  };
  // HTTP 429, 5xx, and exceptional statuses may occur after provider acceptance.
  if (status === 429 || status >= 500 || status < 400) {
    return { ...errorDetails, send_state: 'UNCERTAIN_EXTERNAL' };
  }
  // Definitive 4xx HTTP rejection observed. No retry by this adapter.
  return { ...errorDetails, send_state: 'PROVIDER_REJECTED' };
}
