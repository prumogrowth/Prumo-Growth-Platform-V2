/**
 * WA-36: a read-only, fail-closed INTERFRONT RATIFICATION CHECKLIST.
 *
 * Inputs are self-declared proposals, NOT evidence of an S0/S1 signature.
 * This module has NO path to production authorization, even with all fields
 * completed. Never promote a human CFI01 GoTrue role into a Meta service role.
 */
export const WA36_REQUIREMENTS=Object.freeze([
 {id:'WA36-M2M-IDENTITY',owner:'S0_INFRA',basis:'WA35'},
 {id:'WA36-META-PROVENANCE',owner:'META_S0',basis:'WA32'},
 {id:'WA36-KEY-SEPARATION',owner:'META_INFRA',basis:'WA34'},
 {id:'WA36-SCOPE-BINDING',owner:'S0_S1',basis:'WA33'},
 {id:'WA36-MACHINE-ROLE',owner:'S0_S1',basis:'S1_PR5'},
 {id:'WA36-NONCE-ATOMICITY',owner:'S0',basis:'WA34'},
 {id:'WA36-LOCK-ORDER',owner:'S0_S1',basis:'S0_PR12'},
 {id:'WA36-RLS-MIN-PRIVILEGE',owner:'S0_S1',basis:'S0_PR12'},
 {id:'WA36-CALLBACK-DEDUPE',owner:'META_S0',basis:'WA35'},
 {id:'WA36-ACK-RETRY',owner:'META_S0_INFRA',basis:'WA30'},
 {id:'WA36-RETENTION-LGPD',owner:'S0_LEGAL',basis:'WA31'},
 {id:'WA36-REVOCATION',owner:'S0_S1_META',basis:'WA29'},
] as const);
export type Wa36RequirementId=(typeof WA36_REQUIREMENTS)[number]['id'];
export type Wa36EvidenceEntry=Readonly<{
  id:Wa36RequirementId;
  disposition:'PENDING_EXTERNAL_RATIFICATION'|'REQUIRES_OWNER_DECISION';
  reference:'NONE'|'LAB_EVIDENCE_ONLY'|'DRAFT_OTHER_FRONT';
}>;
export type Wa36Proposal=Readonly<{
  contract:'wa36.ratification-manifest.lab.v1';
  evidence:readonly Wa36EvidenceEntry[];
}>;
export type Wa36GateResult=Readonly<{
 decision:'LAB_REVIEW_PACKET_ONLY'|'LAB_REJECTED_MANIFEST';
 required_owner_decisions:number;
 ack_allowed:false;
 send_authorized:false;
 retry_external:false;
 production_authorized:false;
 service_authenticated:false;
 s0_write_authorized:false;
 meta_delivery_confirmed:false;
 case_transition_authorized:false;
}>;
const denied=(decision:Wa36GateResult['decision'],count:number):Wa36GateResult=>
 Object.freeze({
  decision,required_owner_decisions:count,ack_allowed:false,
  send_authorized:false,retry_external:false,production_authorized:false,
  service_authenticated:false,s0_write_authorized:false,
  meta_delivery_confirmed:false,case_transition_authorized:false,
 });
function dataOnly(value:unknown,fields:readonly string[]):Record<string,unknown>|null{
 try{
  if(!value||typeof value!=='object'||Array.isArray(value))return null;
  const proto=Object.getPrototypeOf(value);
  if(proto!==Object.prototype&&proto!==null)return null;
  const desc=Object.getOwnPropertyDescriptors(value);
  if(Reflect.ownKeys(value).length!==fields.length||
   !fields.every(f=>Object.hasOwn(desc,f)&&Object.hasOwn(desc[f],'value')))
    return null;
  return Object.fromEntries(fields.map(k=>[k,desc[k].value]));
 }catch{return null;}
}
/**
 * Validates ONLY proposal format. Even every item claiming LAB_EVIDENCE_ONLY
 * returns LAB_REVIEW_PACKET_ONLY, never a permission or ratified decision.
 */
export function evaluateWa36RatificationProposal(raw:unknown):Wa36GateResult{
 try{
  const top=dataOnly(raw,['contract','evidence']);
  if(!top||top.contract!=='wa36.ratification-manifest.lab.v1'||
    !Array.isArray(top.evidence)||
    top.evidence.length!==WA36_REQUIREMENTS.length)
   return denied('LAB_REJECTED_MANIFEST',WA36_REQUIREMENTS.length);
  const seen=new Set<string>();
  for(const value of top.evidence){
    const record=dataOnly(value,['id','disposition','reference']);
    if(!record||typeof record.id!=='string'||seen.has(record.id)||
      !WA36_REQUIREMENTS.some(x=>x.id===record.id)||
      !['PENDING_EXTERNAL_RATIFICATION','REQUIRES_OWNER_DECISION']
        .includes(String(record.disposition))||
      !['NONE','LAB_EVIDENCE_ONLY','DRAFT_OTHER_FRONT']
        .includes(String(record.reference)))
      return denied('LAB_REJECTED_MANIFEST',WA36_REQUIREMENTS.length);
    seen.add(record.id);
  }
  if(seen.size!==WA36_REQUIREMENTS.length)
    return denied('LAB_REJECTED_MANIFEST',WA36_REQUIREMENTS.length);
  return denied('LAB_REVIEW_PACKET_ONLY',WA36_REQUIREMENTS.length);
 }catch{return denied('LAB_REJECTED_MANIFEST',WA36_REQUIREMENTS.length);}
}
export function createWa36PendingDraft():Wa36Proposal{
 return Object.freeze({
  contract:'wa36.ratification-manifest.lab.v1',
  evidence:Object.freeze(WA36_REQUIREMENTS.map(({id})=>Object.freeze({
   id,disposition:'REQUIRES_OWNER_DECISION' as const,reference:'NONE' as const,
  }))),
 });
}
