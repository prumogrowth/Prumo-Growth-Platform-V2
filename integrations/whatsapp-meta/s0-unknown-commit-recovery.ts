/**
 * WA-16A: fail-closed LOCAL fixture classification for a *lost S0 write reply*.
 * This does NOT resolve real network ambiguity. A recovery read can discover an
 * exact durable write, but LAB_ABSENT NEVER proves that Graph did not accept a
 * message. The caller must NOT resend Graph or grant an HTTP webhook ACK.
 *
 * This pure module never accesses PostgreSQL, Graph, credentials or commerce.
 * A trusted internal gateway must authenticate and perform the read under S0
 * scope; a caller-supplied JSON object is NOT proof of database authenticity.
 */
export type Wa16RecoveryDecision = Readonly<{
  decision: 'LAB_CONFIRMED_DURABLE' | 'LAB_ABSENT_STILL_UNCERTAIN' |
    'LAB_CONFLICT_QUARANTINE' | 'LAB_UNTRUSTED_RECOVERY';
  retry_external: false;
  ack_allowed: false;
  production_authorized: false;
  delivery_confirmed: false;
}>;

const result=(decision:Wa16RecoveryDecision['decision']):Wa16RecoveryDecision =>
  Object.freeze({decision,retry_external:false,ack_allowed:false,
    production_authorized:false,delivery_confirmed:false});

/** Exactly the four fields returned by S0-041/042 read-only recovery. */
export function classifyUnknownCommitRecovery(raw:unknown):Wa16RecoveryDecision {
  try {
    if (!raw || typeof raw!=='object' || Array.isArray(raw)) return result('LAB_UNTRUSTED_RECOVERY');
    const proto=Object.getPrototypeOf(raw);
    if (proto!==Object.prototype && proto!==null) return result('LAB_UNTRUSTED_RECOVERY');
    const d=Object.getOwnPropertyDescriptors(raw);
    const keys=['outcome','ack_allowed','retry_external','production_authorized'];
    if(Reflect.ownKeys(raw).length!==keys.length || Object.keys(d).length!==keys.length ||
       !keys.every(k=>Object.hasOwn(d,k) && Object.hasOwn(d[k],'value')))
      return result('LAB_UNTRUSTED_RECOVERY');
    if(d.ack_allowed.value!==false || d.retry_external.value!==false ||
       d.production_authorized.value!==false)
      return result('LAB_UNTRUSTED_RECOVERY');
    switch(d.outcome.value){
      case 'LAB_FOUND_EXACT': return result('LAB_CONFIRMED_DURABLE');
      case 'LAB_ABSENT': return result('LAB_ABSENT_STILL_UNCERTAIN');
      case 'LAB_CONFLICT': return result('LAB_CONFLICT_QUARANTINE');
      default: return result('LAB_UNTRUSTED_RECOVERY');
    }
  } catch {return result('LAB_UNTRUSTED_RECOVERY');}
}
