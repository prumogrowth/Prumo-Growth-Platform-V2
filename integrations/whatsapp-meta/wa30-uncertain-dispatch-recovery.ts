/**
 * WA-30: classify a *synthetic* post-claim recovery snapshot without granting
 * Graph dispatch, retry, webhook ACK or commercial/failure-cadence authority.
 * A caller-supplied JSON object is NOT S0 authentication or Meta evidence.
 */
export type Wa30RecoveryDecision = Readonly<{
  decision:
    | 'LAB_HOLD_UNRESOLVED'
    | 'LAB_ABSENT_STILL_UNCERTAIN'
    | 'LAB_ACCEPTED_NOT_SENT'
    | 'LAB_SENT_REPORTED_UNVERIFIED'
    | 'LAB_FAILURE_REPORTED_UNVERIFIED'
    | 'LAB_INVALIDATED_HOLD'
    | 'LAB_CONFLICT_QUARANTINE'
    | 'LAB_UNTRUSTED_SNAPSHOT';
  retry_external: false;
  send_authorized: false;
  ack_allowed: false;
  production_authorized: false;
  delivery_confirmed: false;
  definitive_failure_count_increment: false;
  case_transition_authorized: false;
}>;

const denied = (decision: Wa30RecoveryDecision['decision']): Wa30RecoveryDecision =>
  Object.freeze({
    decision, retry_external:false, send_authorized:false, ack_allowed:false,
    production_authorized:false, delivery_confirmed:false,
    definitive_failure_count_increment:false, case_transition_authorized:false,
  });

/** Shape deliberately avoids identifiers, Graph IDs, credentials and content. */
export function classifyWa30RecoverySnapshot(raw:unknown): Wa30RecoveryDecision {
  try {
    if (!raw || typeof raw!=='object' || Array.isArray(raw)) return denied('LAB_UNTRUSTED_SNAPSHOT');
    const proto=Object.getPrototypeOf(raw);
    if (proto!==Object.prototype && proto!==null) return denied('LAB_UNTRUSTED_SNAPSHOT');
    const descriptors=Object.getOwnPropertyDescriptors(raw);
    const keys=['outcome','retry_external','send_authorized','ack_allowed',
      'production_authorized','delivery_confirmed',
      'definitive_failure_count_increment','case_transition_authorized'] as const;
    if(Reflect.ownKeys(raw).length!==keys.length ||
       Object.keys(descriptors).length!==keys.length ||
       !keys.every(k=>Object.hasOwn(descriptors,k) && Object.hasOwn(descriptors[k],'value')))
      return denied('LAB_UNTRUSTED_SNAPSHOT');
    if(keys.slice(1).some(k=>descriptors[k].value!==false))
      return denied('LAB_UNTRUSTED_SNAPSHOT');

    switch(descriptors.outcome.value){
      case 'LAB_CLAIM_UNRESOLVED': return denied('LAB_HOLD_UNRESOLVED');
      case 'LAB_ABSENT_UNKNOWN': return denied('LAB_ABSENT_STILL_UNCERTAIN');
      case 'LAB_PROVIDER_ACCEPTED_UNVERIFIED': return denied('LAB_ACCEPTED_NOT_SENT');
      case 'LAB_SENT_UNVERIFIED': return denied('LAB_SENT_REPORTED_UNVERIFIED');
      case 'LAB_FAILURE_UNVERIFIED': return denied('LAB_FAILURE_REPORTED_UNVERIFIED');
      case 'LAB_INVALIDATED': return denied('LAB_INVALIDATED_HOLD');
      case 'LAB_CONFLICT': return denied('LAB_CONFLICT_QUARANTINE');
      default: return denied('LAB_UNTRUSTED_SNAPSHOT');
    }
  } catch {return denied('LAB_UNTRUSTED_SNAPSHOT');}
}
