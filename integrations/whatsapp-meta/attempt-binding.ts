/**
 * WA-10: An in-memory, technical inverse index for an already accepted Graph
 * observation. Reject one S0 attempt being associated with two provider wamids.
 * No network, credentials, HTTP ACK, commercial state, DB or persistence.
 * This is NOT authorization to send, nor proof of message delivery.
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
const valid = (v: unknown): v is AttemptIdentity => {
  try {
    if (!v || typeof v !== 'object' || Array.isArray(v)) return false;
    const proto = Object.getPrototypeOf(v);
    if (proto !== Object.prototype && proto !== null) return false;
    const d = Object.getOwnPropertyDescriptors(v);
    if (Reflect.ownKeys(v).length !== fields.length || Object.keys(d).length !== fields.length ||
        !fields.every(k => Object.hasOwn(d,k) && Object.hasOwn(d[k],'value'))) return false;
    const x = v as AttemptIdentity;
    return REF.test(x.app_ref) && REF.test(x.concessionaria_id) &&
      REF.test(x.canal_id) && REF.test(x.waba_id) && SENDER.test(x.phone_number_id) &&
      REF.test(x.intent_id) && REF.test(x.attempt_id) && REF.test(x.correlation_id) &&
      RECIPIENT.test(x.recipient_verified) && WAMID.test(x.provider_message_id);
  } catch { return false; }
};

export class FakeAttemptBindingLedger {
  private readonly attempts = new Map<string,string>();
  get size(): number { return this.attempts.size; }
  /** One attempt per App/dealership, even if channel or recipient changes. */
  claim(value: unknown): AttemptClaim {
    if (!valid(value)) return 'INVALID';
    const key=JSON.stringify([value.app_ref,value.concessionaria_id,value.attempt_id]);
    const binding=JSON.stringify(fields.map(field => value[field]));
    const existing=this.attempts.get(key);
    if (existing !== undefined) return existing === binding ? 'SAME' : 'CONFLICT';
    if (this.attempts.size >= 100) return 'INVALID';
    this.attempts.set(key,binding);
    return 'NEW';
  }
}
