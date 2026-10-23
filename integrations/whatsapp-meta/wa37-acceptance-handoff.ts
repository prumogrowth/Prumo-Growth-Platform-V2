/**
 * WA37 - proposed cross-front acceptance packet (offline; no authority).
 *
 * All owner names below are REVIEW REQUESTS, not decisions or permissions.
 * A complete packet can ONLY be queued for review; ratification by the real
 * S0/S1/Meta/Infra owners and an authenticated production control plane
 * are deliberately outside this module.
 */
import {WA36_REQUIREMENTS} from './wa36-ratification-gate.ts';

export const WA37_CHECKS=Object.freeze(([
 {id:'WA36-M2M-IDENTITY',owner:'S0_INFRA',positive:'WA37-P01',negative:'WA37-N01',
  criterion:'Service principal independently authenticated at S0 boundary; synthetic issuer and human GoTrue denied'},
 {id:'WA36-META-PROVENANCE',owner:'META_S0',positive:'WA37-P02',negative:'WA37-N02',
  criterion:'Trusted App route and exact raw-body Meta HMAC bound to internal verifier; client-controlled route denied'},
 {id:'WA36-KEY-SEPARATION',owner:'META_INFRA',positive:'WA37-P03',negative:'WA37-N03',
  criterion:'Meta App Secret and internal handoff keys isolated and revocable; stolen/rotated key denied'},
 {id:'WA36-SCOPE-BINDING',owner:'S0_S1',positive:'WA37-P04',negative:'WA37-N04',
  criterion:'Durable App/WABA/sender/recipient/shop/case/attempt binding with revision; cross-tenant and stale revision denied'},
 {id:'WA36-MACHINE-ROLE',owner:'S0_S1',positive:'WA37-P05',negative:'WA37-N05',
  criterion:'Dedicated machine permission FORENSIC_APPEND_ONLY; Diretor/Gestor/Consultor not interchangeable'},
 {id:'WA36-NONCE-ATOMICITY',owner:'S0',positive:'WA37-P06',negative:'WA37-N06',
  criterion:'Verify internal MAC, nonce uniqueness and forensic append in authenticated S0 transaction; replay denied'},
 {id:'WA36-LOCK-ORDER',owner:'S0_S1',positive:'WA37-P07',negative:'WA37-N07',
  criterion:'S1/S0/Meta lock order ratified under revocation/assignment races; no deadlock or stale grant'},
 {id:'WA36-RLS-MIN-PRIVILEGE',owner:'S0_S1',positive:'WA37-P08',negative:'WA37-N08',
  criterion:'Tenant-scoped minimum write only; no direct SQL/privileged bypass from webhook, client or AI'},
 {id:'WA36-CALLBACK-DEDUPE',owner:'META_S0',positive:'WA37-P09',negative:'WA37-N09',
  criterion:'Status identity, reordered/late/duplicate/conflicting callbacks specified; synthetic hash not certified unique'},
 {id:'WA36-ACK-RETRY',owner:'META_S0_INFRA',positive:'WA37-P10',negative:'WA37-N10',
  criterion:'Provider HTTP ACK only on durable accepted status; uncertain append must not cause Graph resend'},
 {id:'WA36-RETENTION-LGPD',owner:'S0_LEGAL',positive:'WA37-P11',negative:'WA37-N11',
  criterion:'Forensic minimization, access audit and retention formally approved; raw PII and secret leak denied'},
 {id:'WA36-REVOCATION',owner:'S0_S1_META',positive:'WA37-P12',negative:'WA37-N12',
  criterion:'Late technical evidence can be archived after revoke but consent/claim/send authority never reopens'},
] as const).map(x=>Object.freeze(x)));
export type Wa37CheckId=(typeof WA37_CHECKS)[number]['id'];
export type Wa37PacketRow=Readonly<{
 id:Wa37CheckId;
 requested_owner:string;
 positive_probe:string;
 negative_probe:string;
 evidence_state:'NOT_PROVIDED'|'LAB_FIXTURE_ONLY'|'OTHER_FRONT_DRAFT';
 ratification:'AWAITING_OWNER_DECISION';
}>;
export type Wa37ReviewPacket=Readonly<{
 contract:'wa37.crossfront.acceptance.offline.v1';
 purpose:'HANDOFF_REVIEW_ONLY';
 entries:readonly Wa37PacketRow[];
}>;
export type Wa37ReviewResult=Readonly<{
 outcome:'LAB_REVIEW_BLOCKED'|'INVALID_REVIEW_PACKET';
 required_owner_decisions:12;
 matched_criteria:number;
 service_authenticated:false;
 s0_write_authorized:false;
 production_authorized:false;
 ack_allowed:false;
 send_authorized:false;
 retry_external:false;
 case_transition_authorized:false;
 delivery_confirmed:false;
}>;
const fields=['id','requested_owner','positive_probe','negative_probe',
 'evidence_state','ratification'] as const;
function ownPlain(x:unknown,keys:readonly string[]):Record<string,unknown>|null{
 try{
  if(!x||typeof x!=='object'||Array.isArray(x))return null;
  const proto=Object.getPrototypeOf(x);
  if(proto!==Object.prototype&&proto!==null)return null;
  const desc=Object.getOwnPropertyDescriptors(x);
  if(Reflect.ownKeys(x).length!==keys.length||
     !keys.every(k=>Object.hasOwn(desc,k)&&Object.hasOwn(desc[k],'value')))
    return null;
  return Object.fromEntries(keys.map(k=>[k,desc[k].value]));
 }catch{return null;}
}
const result=(outcome:Wa37ReviewResult['outcome'],matched:number):Wa37ReviewResult=>
 Object.freeze({outcome,required_owner_decisions:12,matched_criteria:matched,
  service_authenticated:false,s0_write_authorized:false,
  production_authorized:false,ack_allowed:false,send_authorized:false,
  retry_external:false,case_transition_authorized:false,
  delivery_confirmed:false});
/**
 * A structurally complete checklist remains BLOCKED by design.
 * Never interpret all LAB_FIXTURE_ONLY evidence as an external sign-off.
 */
export function evaluateWa37ReviewPacket(raw:unknown):Wa37ReviewResult{
 try{
  const top=ownPlain(raw,['contract','purpose','entries']);
  if(!top||top.contract!=='wa37.crossfront.acceptance.offline.v1'||
      top.purpose!=='HANDOFF_REVIEW_ONLY'||
      !Array.isArray(top.entries)||top.entries.length!==WA37_CHECKS.length)
   return result('INVALID_REVIEW_PACKET',0);
  const seen=new Set<string>();
  let matched=0;
  for(const rawRow of top.entries){
   const row=ownPlain(rawRow,fields);
   if(!row||typeof row.id!=='string'||seen.has(row.id))
    return result('INVALID_REVIEW_PACKET',0);
   const expected=WA37_CHECKS.find(x=>x.id===row.id);
   if(!expected||row.requested_owner!==expected.owner||
      row.positive_probe!==expected.positive||
      row.negative_probe!==expected.negative||
      typeof row.evidence_state!=='string'||
      !['NOT_PROVIDED','LAB_FIXTURE_ONLY','OTHER_FRONT_DRAFT']
        .includes(row.evidence_state)||
      row.ratification!=='AWAITING_OWNER_DECISION')
    return result('INVALID_REVIEW_PACKET',0);
   seen.add(row.id);
   matched++;
  }
  if(matched!==WA36_REQUIREMENTS.length||WA37_CHECKS.some(
    x=>!WA36_REQUIREMENTS.some(y=>x.id===y.id&&x.owner===y.owner)))
   return result('INVALID_REVIEW_PACKET',0);
  return result('LAB_REVIEW_BLOCKED',matched);
 }catch{return result('INVALID_REVIEW_PACKET',0);}
}
export function createWa37PendingReviewPacket():Wa37ReviewPacket{
 return Object.freeze({
  contract:'wa37.crossfront.acceptance.offline.v1',
  purpose:'HANDOFF_REVIEW_ONLY',
  entries:Object.freeze(WA37_CHECKS.map(x=>Object.freeze({
   id:x.id,requested_owner:x.owner,
   positive_probe:x.positive,negative_probe:x.negative,
   evidence_state:'NOT_PROVIDED' as const,
   ratification:'AWAITING_OWNER_DECISION' as const,
  }))),
 });
}
