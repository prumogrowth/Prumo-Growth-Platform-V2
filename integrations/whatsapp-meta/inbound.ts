/**
 * WA-01A: Meta WhatsApp inbound inspection, isolated from database and network.
 * No HTTP response/ACK, persistence, lead resolution, sending or Meta token access.
 * This is a candidate technical boundary, not an approved S0 internal API.
 */

const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', { fatal: true });
const DEFAULT_MAX_BODY_BYTES = 256 * 1024;
const DEFAULT_MAX_EVENTS = 100;

type RecordValue = Record<string, unknown>;
type EventPosition = {
  entry_index: number;
  change_index: number;
  item_index: number;
};

export type MetaIngressEvent = {
  source: 'meta_whatsapp';
  event_kind: 'inbound_message' | 'status_callback';
  waba_id: string;
  phone_number_id: string;
  provider_message_id: string;
  /** UTC timestamp from the provider; not the time of ingestion. */
  provider_timestamp: string;
  /** Technical identifier only. Not proof of civil identity or a sending destination. */
  participant_identifier: string;
  /** Message type or delivery state as provided by Meta; not a commercial state. */
  provider_kind: string;
  position: EventPosition;
};

export type IngressFailureCode =
  | 'BODY_TOO_LARGE'
  | 'MISSING_SIGNATURE'
  | 'INVALID_SIGNATURE_FORMAT'
  | 'INVALID_SIGNATURE'
  | 'INVALID_UTF8'
  | 'INVALID_JSON'
  | 'INVALID_ENVELOPE'
  | 'INVALID_ENTRY'
  | 'INVALID_CHANGE'
  | 'UNSUPPORTED_CHANGE_FIELD'
  | 'INVALID_MESSAGE'
  | 'INVALID_STATUS'
  | 'NO_EVENTS'
  | 'TOO_MANY_EVENTS';

export type IngressFailure = {
  code: IngressFailureCode;
  /** Indices only; never include payload, token, phone, or message body. */
  position?: Partial<EventPosition>;
};

export type InspectionResult =
  | { ok: true; events: MetaIngressEvent[] }
  | { ok: false; failure: IngressFailure };

export type InspectOptions = {
  maxBodyBytes?: number;
  maxEvents?: number;
};

function object(value: unknown): value is RecordValue {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function identifier(value: unknown, maxLength = 256): value is string {
  return typeof value === 'string' && value.length > 0 && value.length <= maxLength;
}

function metaTimestamp(value: unknown): string | null {
  if (typeof value !== 'string' || !/^\d{1,13}$/.test(value)) return null;
  const seconds = Number(value);
  if (!Number.isSafeInteger(seconds)) return null;
  const millis = seconds * 1000;
  if (!Number.isSafeInteger(millis)) return null;
  const date = new Date(millis);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function parseAuthenticatedBody(body: Uint8Array, maxEvents: number): InspectionResult {
  let payload: unknown;
  try {
    payload = JSON.parse(decoder.decode(body));
  } catch (error) {
    return { ok: false, failure: { code: error instanceof TypeError ? 'INVALID_UTF8' : 'INVALID_JSON' } };
  }
  if (!object(payload) || payload.object !== 'whatsapp_business_account' ||
      !Array.isArray(payload.entry) || payload.entry.length === 0) {
    return { ok: false, failure: { code: 'INVALID_ENVELOPE' } };
  }

  const events: MetaIngressEvent[] = [];
  for (let e = 0; e < payload.entry.length; e++) {
    const entry: unknown = payload.entry[e];
    if (!object(entry) || !identifier(entry.id) || !Array.isArray(entry.changes) ||
        entry.changes.length === 0) {
      return { ok: false, failure: { code: 'INVALID_ENTRY', position: { entry_index: e } } };
    }
    for (let c = 0; c < entry.changes.length; c++) {
      const change: unknown = entry.changes[c];
      const position = { entry_index: e, change_index: c };
      if (!object(change) || !identifier(change.field) || !object(change.value)) {
        return { ok: false, failure: { code: 'INVALID_CHANGE', position } };
      }
      // No silent discard of subscribed event types we have not yet contracted.
      if (change.field !== 'messages') {
        return { ok: false, failure: { code: 'UNSUPPORTED_CHANGE_FIELD', position } };
      }
      const value = change.value;
      if (!object(value.metadata) || !identifier(value.metadata.phone_number_id)) {
        return { ok: false, failure: { code: 'INVALID_CHANGE', position } };
      }
      if ((value.messages !== undefined && !Array.isArray(value.messages)) ||
          (value.statuses !== undefined && !Array.isArray(value.statuses))) {
        return { ok: false, failure: { code: 'INVALID_CHANGE', position } };
      }
      const messages: unknown[] = (value.messages as unknown[] | undefined) ?? [];
      const statuses: unknown[] = (value.statuses as unknown[] | undefined) ?? [];
      if (messages.length + statuses.length === 0) {
        return { ok: false, failure: { code: 'INVALID_CHANGE', position } };
      }
      if (events.length + messages.length + statuses.length > maxEvents) {
        return { ok: false, failure: { code: 'TOO_MANY_EVENTS', position } };
      }
      for (let i = 0; i < messages.length; i++) {
        const item: unknown = messages[i];
        const stamp = object(item) ? metaTimestamp(item.timestamp) : null;
        if (!object(item) || !identifier(item.id) || !identifier(item.from, 64) ||
            !identifier(item.type, 64) || stamp === null) {
          return { ok: false, failure: { code: 'INVALID_MESSAGE', position: { ...position, item_index: i } } };
        }
        events.push({
          source: 'meta_whatsapp',
          event_kind: 'inbound_message',
          waba_id: entry.id,
          phone_number_id: value.metadata.phone_number_id,
          provider_message_id: item.id,
          provider_timestamp: stamp,
          participant_identifier: item.from,
          provider_kind: item.type,
          position: { ...position, item_index: i },
        });
      }
      for (let i = 0; i < statuses.length; i++) {
        const item: unknown = statuses[i];
        const stamp = object(item) ? metaTimestamp(item.timestamp) : null;
        if (!object(item) || !identifier(item.id) || !identifier(item.recipient_id, 64) ||
            !identifier(item.status, 64) || stamp === null) {
          return { ok: false, failure: { code: 'INVALID_STATUS', position: { ...position, item_index: i } } };
        }
        events.push({
          source: 'meta_whatsapp',
          event_kind: 'status_callback',
          waba_id: entry.id,
          phone_number_id: value.metadata.phone_number_id,
          provider_message_id: item.id, // Message ID, NOT a unique callback ID.
          provider_timestamp: stamp,
          participant_identifier: item.recipient_id,
          provider_kind: item.status,
          position: { ...position, item_index: i },
        });
      }
    }
  }
  if (events.length === 0) return { ok: false, failure: { code: 'NO_EVENTS' } };
  return { ok: true, events };
}

/**
 * Authenticates raw HTTP bytes before parsing JSON. Never derive an app secret
 * from unauthenticated tenant identifiers. The caller provides the trusted app
 * secret selected by endpoint/configuration, not by a customer-supplied field.
 *
 * A successful result is NOT durable acceptance and MUST NOT trigger HTTP 200.
 */
export async function inspectMetaWebhook(
  rawBody: Uint8Array,
  signatureHeader: string | null,
  trustedAppSecret: string,
  options: InspectOptions = {},
): Promise<InspectionResult> {
  const maxBodyBytes = options.maxBodyBytes ?? DEFAULT_MAX_BODY_BYTES;
  const maxEvents = options.maxEvents ?? DEFAULT_MAX_EVENTS;
  if (!Number.isSafeInteger(maxBodyBytes) || maxBodyBytes <= 0 ||
      !Number.isSafeInteger(maxEvents) || maxEvents <= 0) {
    throw new RangeError('Invalid trusted ingress limits');
  }
  if (trustedAppSecret.length === 0) throw new Error('Meta app secret not configured');
  if (rawBody.byteLength > maxBodyBytes) {
    return { ok: false, failure: { code: 'BODY_TOO_LARGE' } };
  }
  if (signatureHeader === null) {
    return { ok: false, failure: { code: 'MISSING_SIGNATURE' } };
  }
  const match = /^sha256=([\da-fA-F]{64})$/.exec(signatureHeader);
  if (!match) {
    return { ok: false, failure: { code: 'INVALID_SIGNATURE_FORMAT' } };
  }
  const signature = Uint8Array.from(match[1].match(/../g)!, (pair) => parseInt(pair, 16));
  const key = await crypto.subtle.importKey(
    'raw', encoder.encode(trustedAppSecret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify'],
  );
  // WebCrypto performs HMAC verification; no value-dependent JS string compare.
  const valid = await crypto.subtle.verify('HMAC', key, signature, rawBody);
  if (!valid) return { ok: false, failure: { code: 'INVALID_SIGNATURE' } };
  return parseAuthenticatedBody(rawBody, maxEvents);
}
