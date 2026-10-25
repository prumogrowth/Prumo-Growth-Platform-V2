/**
 * WA56: OFFLINE-only trusted-to-PG17 S0/055 bridge. It is NOT a webhook, IAM
 * authenticator, production Meta verifier, Graph/ACK handler or S1 operation.
 * WA46 must verify raw X-Hub-Signature-256 before a WA45 ticket exists.
 * The bridge independently checks the raw body/event and S0 ticket MAC.
 */
import {createHash,createHmac,timingSafeEqual} from 'node:crypto';
import {WA44_AUDIENCE,wa44CanonicalBytes} from './s0_wa_048_meta_handoff_adapter.mjs';

const PORTS=['rawGate','getInternalKey','appendWa55','nowSeconds'];
const hex64=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const digits=x=>typeof x==='string'&&/^[0-9]{5,25}$/.test(x);
const uuid=x=>typeof x==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(x);
const bad=decision=>Object.freeze({decision,receipt:null,lab_only:true,
 service_authenticated:false,meta_provenance_production_proven:false,
 ack_allowed:false,send_authorized:false,retry_external:false,
 production_authorized:false,delivery_confirmed:false,case_transition_authorized:false});
function obj(x,fields){
 try {
  if(!x||typeof x!=='object'||Array.isArray(x))return null;
  const p=Object.getPrototypeOf(x);
  if(p!==Object.prototype&&p!==null)return null;
  const d=Object.getOwnPropertyDescriptors(x),keys=Reflect.ownKeys(x);
  if(keys.length!==fields.length||!fields.every(k=>Object.hasOwn(d,k)&&
    Object.hasOwn(d[k],'value')))return null;
  return Object.freeze(Object.fromEntries(fields.map(k=>[k,d[k].value])));
 }catch{return null;}
}
function immutableTuple(candidate){
 try {
  if(!Array.isArray(candidate)||candidate.length!==15)return null;
  const descriptors=Object.getOwnPropertyDescriptors(candidate);
  if(Reflect.ownKeys(candidate).length!==16)return null; // 15 indices + length
  const fields=[];
  for(let i=0;i<15;i++){
   const d=descriptors[String(i)];
   if(!d||!Object.hasOwn(d,'value')||typeof d.value!=='string')return null;
   fields.push(d.value);
  }
  return Object.freeze(fields);
 }catch{return null;}
}
function rawEvent(bytes){
 try {
  const root=obj(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)),['object','entry']);
  if(!root||root.object!=='whatsapp_business_account'||
     !Array.isArray(root.entry)||root.entry.length!==1)return null;
  const entry=obj(root.entry[0],['id','changes']);
  if(!entry||!digits(entry.id)||!Array.isArray(entry.changes)||entry.changes.length!==1)return null;
  const change=obj(entry.changes[0],['field','value']);
  if(!change||change.field!=='messages')return null;
  const value=obj(change.value,['metadata','statuses']);
  const metadata=value&&obj(value.metadata,['phone_number_id']);
  if(!value||!metadata||!digits(metadata.phone_number_id)||
    !Array.isArray(value.statuses)||value.statuses.length!==1)return null;
  const status=obj(value.statuses[0],['id','status','recipient_id','timestamp']);
  if(!status||typeof status.id!=='string'||
    !/^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$/.test(status.id)||
    !['sent','delivered','read','failed'].includes(status.status)||
    typeof status.recipient_id!=='string'||!/^[0-9]{8,15}$/.test(status.recipient_id)||
    typeof status.timestamp!=='string'||!/^[1-9][0-9]{0,11}$/.test(status.timestamp))return null;
  const tuple=JSON.stringify([entry.id,metadata.phone_number_id,status.id,
   status.recipient_id,status.status,status.timestamp]);
  return Object.freeze({waba:entry.id,phone:metadata.phone_number_id,
   wamid:status.id,recipient:status.recipient_id,kind:status.status,
   eventRef:'WA46_'+createHash('sha256').update(tuple).digest('hex'),
   bodySha256:createHash('sha256').update(bytes).digest('hex')});
 }catch{return null;}
}
/**
 * Only a current synthetic WA46 gate and separate private S0 key port can
 * create an accepted handoff. No event-supplied scope, nonce, MAC or tenant.
 * The append port represents an isolated PG17 writer, not a live service.
 */
export function createWa56OfflineArchiveBridge(rawPorts){
 const p=obj(rawPorts,PORTS);
 if(!p||!p.rawGate||typeof p.rawGate.receive!=='function'||
  typeof p.getInternalKey!=='function'||typeof p.appendWa55!=='function'||
  typeof p.nowSeconds!=='function')return null;
 return Object.freeze({async receive(rawBytes,signatureHeader){
  if(!Buffer.isBuffer(rawBytes)||rawBytes.length<1||rawBytes.length>262144||
   typeof signatureHeader!=='string'||!/^sha256=[0-9a-f]{64}$/.test(signatureHeader))
   return bad('LAB_DENIED');
  const raw=Buffer.from(rawBytes); // snapshot BEFORE async gate/ports
  try {
   const start=p.nowSeconds();
   if(!Number.isSafeInteger(start)||start<0)return bad('LAB_UNAVAILABLE');
   const parsed=rawEvent(raw);
   if(!parsed)return bad('LAB_SCOPE_DENIED');
   const gateResult=obj(await p.rawGate.receive(Buffer.from(raw),signatureHeader),
    ['decision','ticket','ack_allowed','send_authorized','retry_external',
     'production_authorized','service_authenticated',
     'meta_provenance_production_proven','delivery_confirmed','case_transition_authorized']);
   if(!gateResult||gateResult.decision!=='LAB_META_HMAC_AND_S0_CANDIDATE_ONLY'||
    ['ack_allowed','send_authorized','retry_external','production_authorized',
    'service_authenticated','meta_provenance_production_proven','delivery_confirmed',
    'case_transition_authorized'].some(k=>gateResult[k]!==false))
    return bad('LAB_META_GATE_DENIED');
   const t=obj(gateResult.ticket,['contract','audience','candidate','macSha256',
    'ack_allowed','send_authorized','retry_external','production_authorized',
    'service_authenticated']);
   if(!t||t.contract!=='WA40_PG17_LAB_ONLY'||t.audience!==WA44_AUDIENCE||
    ['ack_allowed','send_authorized','retry_external','production_authorized',
     'service_authenticated'].some(k=>t[k]!==false)||!hex64(t.macSha256))
    return bad('LAB_TICKET_DENIED');
   const tuple=immutableTuple(t.candidate);
   if(!tuple||!wa44CanonicalBytes(tuple)||!uuid(tuple[0])||!id(tuple[6])||
      !id(tuple[7])||!digits(tuple[1])||tuple[2]!==parsed.waba||
      tuple[3]!==parsed.phone||tuple[8]!==parsed.recipient||
      tuple[9]!==parsed.wamid||tuple[10]!==parsed.eventRef||
      tuple[11]!==parsed.kind||tuple[12]!==parsed.bodySha256)
    return bad('LAB_WIRE_MISMATCH');
   const key=await p.getInternalKey(tuple[0]); // NEVER from the event
   if(!Buffer.isBuffer(key)||key.length<32||key.length>128)
    return bad('LAB_KEY_UNAVAILABLE');
   const secret=Buffer.from(key);
   const material=wa44CanonicalBytes(tuple);
   const expected=createHmac('sha256',secret).update(material).digest();
   if(!timingSafeEqual(expected,Buffer.from(t.macSha256,'hex')))
    return bad('LAB_TICKET_MAC_DENIED');
   const beforeWrite=p.nowSeconds();
   if(!Number.isSafeInteger(beforeWrite)||beforeWrite<start||
     beforeWrite-start>20||Number(tuple[13])>beforeWrite+5||
     Number(tuple[13])<beforeWrite-30)return bad('LAB_STALE');
   // No mutable ticket or separately-supplied event fields can cross.
   const safe=Object.freeze({candidate:tuple,macSha256:t.macSha256});
   const receipt=obj(await p.appendWa55(safe),
    ['outcome','lab_only','authoritative_lab_forensic_appended',
    'original_wa39_owner_preserved','service_authenticated',
    'production_authorized','ack_allowed','send_authorized','retry_external',
    'delivery_confirmed','case_transition_authorized',
    'definitive_failure_count_increment','entrypoint',
    'legacy_paths_directly_executable','runtime_principal_authenticated']);
   if(!receipt||!['LAB_OBSERVED_UNVERIFIED','LAB_LATE_UNVERIFIED',
     'LAB_EXACT_BODY_REPLAY','LAB_BODY_VARIANT_QUARANTINED',
     'LAB_KIND_CONFLICT_QUARANTINED'].includes(receipt.outcome)||
     receipt.lab_only!==true||
     receipt.authoritative_lab_forensic_appended!==true||
     receipt.original_wa39_owner_preserved!==true||
     receipt.entrypoint!=='WA55_PG17_SINGLE_LAB_ONLY'||
     receipt.legacy_paths_directly_executable!==false||
     receipt.runtime_principal_authenticated!==false||
     ['service_authenticated','production_authorized','ack_allowed',
      'send_authorized','retry_external','delivery_confirmed',
      'case_transition_authorized','definitive_failure_count_increment']
      .some(k=>receipt[k]!==false))
    return bad('LAB_RECEIPT_UNTRUSTED');
   return Object.freeze({decision:'LAB_META_RAW_TO_WA55_FORENSIC_ONLY',
    receipt,lab_only:true,service_authenticated:false,
    meta_provenance_production_proven:false,
    ack_allowed:false,send_authorized:false,retry_external:false,
    production_authorized:false,delivery_confirmed:false,
    case_transition_authorized:false});
  }catch{return bad('LAB_UNAVAILABLE');}
 }});
}
