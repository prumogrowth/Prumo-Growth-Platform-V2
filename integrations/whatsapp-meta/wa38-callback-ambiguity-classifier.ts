/**
 * WA38: classify ONLY an aggregate PG17 forensic readback from the
 * synthetic laboratory. No authority to infer delivery, re-dispatch,
 * commercial case changes or ACK. A matching synthetic callback fingerprint
 * cannot prove the provider gave an actual unique event identifier.
 */
export type Wa38Readout=Readonly<{
 decision:'LAB_NO_EVIDENCE'|'LAB_OBSERVATION_UNVERIFIED'|
  'LAB_LATE_EVIDENCE_UNVERIFIED'|'LAB_QUARANTINE_HOLD'|
  'LAB_UNTRUSTED_SNAPSHOT';
 retry_external:false;
 send_authorized:false;
 ack_allowed:false;
 production_authorized:false;
 delivery_confirmed:false;
 definitive_failure_count_increment:false;
 case_transition_authorized:false;
}>;
const decisions:Readonly<Record<string,Wa38Readout['decision']>>=
 Object.freeze({
  LAB_NONE:'LAB_NO_EVIDENCE',
  LAB_SINGLE_UNVERIFIED:'LAB_OBSERVATION_UNVERIFIED',
  LAB_LATE_UNVERIFIED:'LAB_LATE_EVIDENCE_UNVERIFIED',
  LAB_MULTIPLE_OR_CONFLICT_QUARANTINED:'LAB_QUARANTINE_HOLD',
 });
const required=['outcome','retry_external','send_authorized','ack_allowed',
 'production_authorized','delivery_confirmed',
 'definitive_failure_count_increment','case_transition_authorized'] as const;
const deny=(decision:Wa38Readout['decision']):Wa38Readout=>Object.freeze({
 decision,retry_external:false,send_authorized:false,ack_allowed:false,
 production_authorized:false,delivery_confirmed:false,
 definitive_failure_count_increment:false,case_transition_authorized:false,
});
export function classifyWa38CallbackAggregate(raw:unknown):Wa38Readout{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))
   return deny('LAB_UNTRUSTED_SNAPSHOT');
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)
   return deny('LAB_UNTRUSTED_SNAPSHOT');
  const d=Object.getOwnPropertyDescriptors(raw);
  if(Reflect.ownKeys(raw).length!==required.length||
     Object.keys(d).length!==required.length||
     !required.every(k=>Object.hasOwn(d,k)&&Object.hasOwn(d[k],'value'))||
     required.slice(1).some(k=>d[k].value!==false))
   return deny('LAB_UNTRUSTED_SNAPSHOT');
  const status=d.outcome.value;
  if(typeof status!=='string'||!Object.hasOwn(decisions,status))
   return deny('LAB_UNTRUSTED_SNAPSHOT');
  return deny(decisions[status]);
 }catch{return deny('LAB_UNTRUSTED_SNAPSHOT');}
}
