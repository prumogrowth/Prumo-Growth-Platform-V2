/**
 * WA-10/11: Memory-only, bi-directional attempt <-> scoped wamid uniqueness
 * for ALREADY accepted Graph observations. Both indexes change together.
 * No network, credentials, ACK, commercial state, database or durability.
 * Not permission to send or evidence of delivery. Real S0 must enforce this
 * transactionally, under the trusted App/WABA/sender mapping at commit.
 */
export type AttemptIdentity = Readonly<{
  app_ref: string;
  concessionaria_id: string;
  canal_id: string;
  waba_id: string;
  phone_number_id: string;
  intent_id: string;
  attempt_id: string;
  correlation_id: string;
  recipient_verified: string;
  provider_message_id: string;
}>;
export type AttemptClaim = 'NEW' | 'SAME' | 'CONFLICT' | 'INVALID';
const REF = /^[A-Za-z0-9_.:-]{1,128}$/;
const WAMID = /^wamid\.[A-Za-z0-9+\/_=:.-]{1,1024}$/;
const SENDER = /^\d{5,25}$/;
const RECIPIENT = /^\d{8,15}$/;
const fields: readonly (keyof AttemptIdentity)[] = [
  'app_ref','concessionaria_id','canal_id','waba_id','phone_number_id',
  'intent_id','attempt_id','correlation_id','recipient_verified','provider_message_id',
];

/** Read own DATA descriptors once. Never re-read a caller's mutable/proxied keys. */
const snapshot = (value: unknown): AttemptIdentity | undefined => {
  try {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return;
    const proto = Object.getPrototypeOf(value);
    if (proto !== Object.prototype && proto !== null) return;
    const descriptors = Object.getOwnPropertyDescriptors(value);
    if (Reflect.ownKeys(value).length !== fields.length ||
        Object.keys(descriptors).length !== fields.length) return;
    const result = Object.create(null) as Record<keyof AttemptIdentity, string>;
    for (const field of fields) {
      if (!Object.hasOwn(descriptors, field)) return;
      const d = descriptors[field];
      if (!d || !Object.hasOwn(d, 'value') || typeof d.value !== 'string') return;
      result[field] = d.value;
    }
    if (!REF.test(result.app_ref) || !REF.test(result.concessionaria_id) ||
        !REF.test(result.canal_id) || !REF.test(result.waba_id) ||
        !SENDER.test(result.phone_number_id) || !REF.test(result.intent_id) ||
        !REF.test(result.attempt_id) || !REF.test(result.correlation_id) ||
        !RECIPIENT.test(result.recipient_verified) ||
        !WAMID.test(result.provider_message_id)) return;
    return result;
  } catch { return; }
};

export class FakeAttemptBindingLedger {
  private readonly attempts = new Map<string,string>();
  private readonly scopedMessages = new Map<string,string>();
  get size(): number { return this.attempts.size; }
  /** One attempt per App/dealership; one wamid per App/WABA/emitter. */
  claim(value: unknown): AttemptClaim {
    const stable = snapshot(value);
    if (!stable) return 'INVALID';
    const attemptKey = JSON.stringify([
      stable.app_ref, stable.concessionaria_id, stable.attempt_id,
    ]);
    const messageKey = JSON.stringify([
      stable.app_ref, stable.waba_id, stable.phone_number_id, stable.provider_message_id,
    ]);
    const binding = JSON.stringify(fields.map(field => stable[field]));
    const priorAttempt = this.attempts.get(attemptKey);
    const priorMessage = this.scopedMessages.get(messageKey);
    // Every exact replay must agree in BOTH directions; conflicting claims
    // must not reserve either side of the mapping.
    if (priorAttempt !== undefined || priorMessage !== undefined)
      return priorAttempt === binding && priorMessage === binding ? 'SAME' : 'CONFLICT';
    if (this.attempts.size >= 100) return 'INVALID';
    // Synchronous fixture mutation, NOT a real transaction or durable commit.
    this.attempts.set(attemptKey, binding);
    this.scopedMessages.set(messageKey, binding);
    return 'NEW';
  }
}
