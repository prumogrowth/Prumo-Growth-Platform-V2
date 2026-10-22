/**
 * WA31: classify minimal PG17 synthetic forensic readback after an attempted
 * Meta template claim. Late reports remain unverified even after revocation.
 * NO authorization, Graph transport, retry, delivery or case-state effects.
 * This classifier is not a trusted event signature / S0 authentication layer.
 */
export type Wa31LateDecision = Readonly<{
  decision:
    | 'LAB_NO_OBSERVATIONS'
    | 'LAB_ACTIVE_EVIDENCE_UNVERIFIED'
    | 'LAB_INVALIDATED_NO_OBSERVATIONS'
    | 'LAB_INVALIDATED_HISTORICAL_UNVERIFIED'
    | 'LAB_POST_REVOCATION_UNVERIFIED'
    | 'LAB_QUARANTINE_CONFLICT'
    | 'LAB_ABSENT_OR_WRONG_SCOPE'
    | 'LAB_UNTRUSTED_SNAPSHOT';
  retry_external: false;
  send_authorized: false;
  ack_allowed: false;
  production_authorized: false;
  delivery_confirmed: false;
  definitive_failure_count_increment: false;
  case_transition_authorized: false;
}>;

const reject=(decision:Wa31LateDecision['decision']):Wa31LateDecision=>
  Object.freeze({
    decision,retry_external:false,send_authorized:false,ack_allowed:false,
    production_authorized:false,delivery_confirmed:false,
    definitive_failure_count_increment:false,case_transition_authorized:false,
  });

const mapping:Readonly<Record<string,Wa31LateDecision['decision']>>=Object.freeze({
  LAB_EMPTY_CLAIM:'LAB_NO_OBSERVATIONS',
  LAB_ACTIVE_OBSERVATION:'LAB_ACTIVE_EVIDENCE_UNVERIFIED',
  LAB_INVALIDATED_EMPTY:'LAB_INVALIDATED_NO_OBSERVATIONS',
  LAB_INVALIDATED_HISTORICAL:'LAB_INVALIDATED_HISTORICAL_UNVERIFIED',
  LAB_LATE_OBSERVATION:'LAB_POST_REVOCATION_UNVERIFIED',
  LAB_KIND_CONFLICT:'LAB_QUARANTINE_CONFLICT',
  LAB_NO_CLAIM:'LAB_ABSENT_OR_WRONG_SCOPE',
});
export function classifyWa31LateEvidence(raw:unknown):Wa31LateDecision{
  try{
    if(!raw||typeof raw!=='object'||Array.isArray(raw))
      return reject('LAB_UNTRUSTED_SNAPSHOT');
    const proto=Object.getPrototypeOf(raw);
    if(proto!==Object.prototype&&proto!==null)
      return reject('LAB_UNTRUSTED_SNAPSHOT');
    const d=Object.getOwnPropertyDescriptors(raw);
    const keys=['outcome','retry_external','send_authorized','ack_allowed',
      'production_authorized','delivery_confirmed',
      'definitive_failure_count_increment','case_transition_authorized'] as const;
    if(Reflect.ownKeys(raw).length!==keys.length||
       Object.keys(d).length!==keys.length||
       !keys.every(k=>Object.hasOwn(d,k)&&Object.hasOwn(d[k],'value'))||
       keys.slice(1).some(k=>d[k].value!==false))
      return reject('LAB_UNTRUSTED_SNAPSHOT');
    const value=d.outcome.value;
    if(typeof value!=='string'||!Object.hasOwn(mapping,value))
      return reject('LAB_UNTRUSTED_SNAPSHOT');
    return reject(mapping[value]);
  }catch{return reject('LAB_UNTRUSTED_SNAPSHOT');}
}
