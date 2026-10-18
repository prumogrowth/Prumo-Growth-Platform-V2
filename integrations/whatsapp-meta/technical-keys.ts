/**
 * WA-01C — candidate correlation keys for already HMAC-validated Meta events.
 * Never a commercial identity resolver, replay proof, DB dedupe decision or ACK.
 * A trusted caller supplies the app reference from verified endpoint config.
 */
import type { MetaIngressEvent } from './inbound.ts';

export type TechnicalKeyHint = {
  readonly contract_version: 'wa-technical-key.v0.1-proposed';
  readonly candidate_sha256: string;
  readonly interpretation: 'INBOUND_MESSAGE_ID' | 'STATUS_OBSERVATION_HINT';
  readonly safe_to_auto_dedupe: false;
};

function assertNonempty(value: string, name: string): void {
  if (typeof value !== 'string' || value.length === 0 || value.length > 256) {
    throw new TypeError('Invalid ' + name);
  }
}

function hex(bytes: Uint8Array): string {
  return Array.from(bytes, n => n.toString(16).padStart(2, '0')).join('');
}

/**
 * No raw provider IDs, participant numbers, tokens or user message contents
 * appear in the return value. Encoded array boundaries prevent concatenation
 * ambiguity. Status event IDs are NOT inferred: an observation hint may collide
 * with another genuine callback sharing message ID, status and second.
 *
 * Caller MUST first authenticate Meta app HMAC, then use the backend's scoped
 * active binding to determine canal_id and concessionaria_id. This hint is not
 * sufficient to claim durable ingress, deduplicate, or assign a lead.
 */
export async function technicalKeyHint(
  event: Readonly<MetaIngressEvent>,
  trustedAppRef: string,
): Promise<TechnicalKeyHint> {
  assertNonempty(trustedAppRef, 'trusted app reference');
  if (event.source !== 'meta_whatsapp' ||
      !['inbound_message', 'status_callback'].includes(event.event_kind)) {
    throw new TypeError('Invalid technical event');
  }
  assertNonempty(event.waba_id, 'WABA');
  assertNonempty(event.phone_number_id, 'sender');
  assertNonempty(event.provider_message_id, 'provider message ID');
  if (event.event_kind === 'status_callback') {
    assertNonempty(event.provider_kind, 'status');
    assertNonempty(event.provider_timestamp, 'provider timestamp');
  }

  const fields = [
    'wa-technical-key.v0.1-proposed', 'meta_whatsapp', trustedAppRef,
    event.waba_id, event.phone_number_id, event.event_kind,
    event.provider_message_id,
    // Inbound identity is message ID, NOT the sender number, text or timestamp.
    ...(event.event_kind === 'status_callback'
      ? [event.provider_kind, event.provider_timestamp]
      : []),
  ];
  const bytes = new TextEncoder().encode(JSON.stringify(fields));
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return {
    contract_version: 'wa-technical-key.v0.1-proposed',
    candidate_sha256: hex(new Uint8Array(digest)),
    interpretation: event.event_kind === 'inbound_message'
      ? 'INBOUND_MESSAGE_ID' : 'STATUS_OBSERVATION_HINT',
    safe_to_auto_dedupe: false,
  };
}
