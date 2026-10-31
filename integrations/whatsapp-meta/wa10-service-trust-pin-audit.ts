/**
 * WA10/M10: offline, fail-closed *candidate* trust-pin and service-context audit.
 * This code does not authenticate the M2M principal. The privileged host MUST
 * independently authenticate it and obtain the trust registry from Infra/S0,
 * never from a signed receipt, HTTP request, provider payload or AI.
 *
 * Matching a lab receipt, Ed25519 signature, pinned key and synthetic service
 * metadata is NOT proof of production custody, rotation, M2M or HTTP authority.
 * No vault, Graph, S0/SQL, network, retry, ACK or production effects.
 */
import {inspectPinnedS0LabReceipt,
 type TrustedExpectedS0LabReceipt} from './cloud-s0-ed25519-receipt-interop.ts';

export type Wa10ReceiptPin=Readonly<{
 app_ref:string;instance_ref:string;key_id:string;key_revision:string;
 public_key_base64:string;status:'ACTIVE'|'STAGED'|'REVOKED';
 not_before_ms:number;not_after_ms:number;
}>;
export type Wa10ServiceMetadata=Readonly<{
 principal_ref:string;app_ref:string;issuer_ref:string;
 m2m_key_id:string;m2m_key_revision:string;
 audience:'PRUMO_S0_META_INGRESS_LAB';
 status:'ACTIVE'|'STAGED'|'REVOKED';
 not_before_ms:number;not_after_ms:number;
}>;
export type Wa10FixtureRegistry=Readonly<{
 contract_version:'wa10-meta-service-trust.lab.v0.1-candidate';
 registry_revision:number;
 receipt_pins:readonly Wa10ReceiptPin[];
 service_principals:readonly Wa10ServiceMetadata[];
}>;
/** These values MUST come from a trusted caller, not from the receipt. */
export type Wa10HostContext=Readonly<{
 principal_ref:string;app_ref:string;issuer_ref:string;
 m2m_key_id:string;m2m_key_revision:string;
 audience:'PRUMO_S0_META_INGRESS_LAB';
 expected_registry_revision:number;at_ms:number;
}>;
export type Wa10AuditResult=Readonly<{
 decision:'LAB_PIN_AND_RECEIPT_MATCHED_UNRATIFIED'|'DENIED';
 reason:null|'INVALID_INPUT'|'INVALID_TRUST_REGISTRY'|
  'STALE_TRUST_REVISION'|'SERVICE_CONTEXT_DENIED'|
  'PIN_NOT_CURRENT'|'PIN_REVOKED'|'RECEIPT_DENIED';
 /** The receipt's Ed25519 signature was verified only in a lab profile. */
 receipt_signature_matched:boolean;
 m2m_authenticated:false;key_custody_verified:false;
 pin_authority_ratified:false;rotation_authorized:false;
 ack_allowed:false;http_ack_allowed:false;send_authorized:false;
 production_authorized:false;s0_write_authorized:false;
 retry_external:false;commercial_transition_authorized:false;
}>;
const RIGHTS=Object.freeze({
 m2m_authenticated:false,key_custody_verified:false,
 pin_authority_ratified:false,rotation_authorized:false,
 ack_allowed:false,http_ack_allowed:false,send_authorized:false,
 production_authorized:false,s0_write_authorized:false,
 retry_external:false,commercial_transition_authorized:false,
} as const);
const denied=(reason:Exclude<Wa10AuditResult['reason'],null>):Wa10AuditResult=>
 Object.freeze({decision:'DENIED',reason,receipt_signature_matched:false,...RIGHTS});
const matched=():Wa10AuditResult=>Object.freeze({
 decision:'LAB_PIN_AND_RECEIPT_MATCHED_UNRATIFIED',reason:null,
 receipt_signature_matched:true,...RIGHTS,
});
const ID=/^[A-Za-z0-9_.:-]{1,128}$/;
const REV=/^[1-9][0-9]{0,17}$/;
const id=(x:unknown):x is string=>typeof x==='string'&&ID.test(x);
const rev=(x:unknown):x is string=>typeof x==='string'&&REV.test(x);
const pos=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>0;
const time=(x:unknown):x is number=>typeof x==='number'&&
 Number.isSafeInteger(x)&&x>=0;
const pinKeys=['app_ref','instance_ref','key_id','key_revision',
 'public_key_base64','status','not_before_ms','not_after_ms'] as const;
const serviceKeys=['principal_ref','app_ref','issuer_ref',
 'm2m_key_id','m2m_key_revision','audience','status',
 'not_before_ms','not_after_ms'] as const;
const registryKeys=['contract_version','registry_revision',
 'receipt_pins','service_principals'] as const;
const contextKeys=['principal_ref','app_ref','issuer_ref','m2m_key_id',
 'm2m_key_revision','audience','expected_registry_revision','at_ms'] as const;
const expectedKeys=['app','route','route_revision','instance',
 'receipt_key_id','receipt_key_revision','m2m_issuer',
 'm2m_key_id','m2m_key_revision','expected_item_count','bindings'] as const;
/** Strict own-data snapshots, no getters, inherited fields or symbols. */
function own(raw:unknown,keys:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const p=Object.getPrototypeOf(raw);
  if(p!==Object.prototype&&p!==null)return null;
  const names=Reflect.ownKeys(raw);
  if(names.length!==keys.length||
   names.some(x=>typeof x!=='string'||!keys.includes(x)))return null;
  const d=Object.getOwnPropertyDescriptors(raw);
  if(keys.some(x=>!Object.hasOwn(d,x)||!Object.hasOwn(d[x],'value')))return null;
  return Object.fromEntries(keys.map(k=>[k,d[k].value]));
 }catch{return null;}
}
function rawKey(base64:unknown):Uint8Array|null{
 if(typeof base64!=='string'||base64.length!==44||
    !/^(?:[A-Za-z0-9+/]{4}){10}[A-Za-z0-9+/]{3}=$/.test(base64))
  return null;
 const bytes=Buffer.from(base64,'base64');
 return bytes.length===32&&bytes.toString('base64')===base64?
  Uint8Array.from(bytes):null;
}
const state=(x:unknown):x is Wa10ReceiptPin['status']=>
 x==='ACTIVE'||x==='STAGED'||x==='REVOKED';
type RegistrySnapshot={revision:number;pins:Wa10ReceiptPin[];services:Wa10ServiceMetadata[]};
function validRegistry(input:unknown):RegistrySnapshot|null{
 const reg=own(input,registryKeys);
 if(!reg||reg.contract_version!=='wa10-meta-service-trust.lab.v0.1-candidate'||
    !pos(reg.registry_revision)||!Array.isArray(reg.receipt_pins)||
    !Array.isArray(reg.service_principals)||
    reg.receipt_pins.length<1||reg.receipt_pins.length>64||
    reg.service_principals.length<1||reg.service_principals.length>64)return null;
 const pinIDs=new Set<string>(),serviceIDs=new Set<string>();
 const keyFingerprints=new Set<string>(),principalOwners=new Map<string,string>();
 const pins:Wa10ReceiptPin[]=[],services:Wa10ServiceMetadata[]=[];
 for(const raw of reg.receipt_pins){
  const p=own(raw,pinKeys);
  if(!p||![p.app_ref,p.instance_ref,p.key_id].every(id)||
     !rev(p.key_revision)||!state(p.status)||
     !time(p.not_before_ms)||!time(p.not_after_ms)||
     p.not_after_ms<=p.not_before_ms)return null;
  const bytes=rawKey(p.public_key_base64);
  if(!bytes)return null;
  const identity=JSON.stringify([p.app_ref,p.instance_ref,p.key_id,p.key_revision]);
  if(pinIDs.has(identity))return null;
  pinIDs.add(identity);
  const fingerprint=Buffer.from(bytes).toString('hex');
  // A new key ID pointing to old bytes is not a cryptographic rotation,
  // even within the same dealership. Pin material may not be reused.
  if(keyFingerprints.has(fingerprint))return null;
  keyFingerprints.add(fingerprint);
  pins.push(p as Wa10ReceiptPin);
 }
 for(const raw of reg.service_principals){
  const s=own(raw,serviceKeys);
  if(!s||![s.principal_ref,s.app_ref,s.issuer_ref,s.m2m_key_id].every(id)||
     !rev(s.m2m_key_revision)||
     s.audience!=='PRUMO_S0_META_INGRESS_LAB'||!state(s.status)||
     !time(s.not_before_ms)||!time(s.not_after_ms)||
     s.not_after_ms<=s.not_before_ms)return null;
  const identity=JSON.stringify([s.app_ref,s.principal_ref,s.issuer_ref,
   s.m2m_key_id,s.m2m_key_revision,s.audience]);
  if(serviceIDs.has(identity))return null;
  serviceIDs.add(identity);
  const previousApp=principalOwners.get(s.principal_ref as string);
  if(previousApp!==undefined&&previousApp!==s.app_ref)return null;
  principalOwners.set(s.principal_ref as string,s.app_ref as string);
  services.push(s as Wa10ServiceMetadata);
 }
 return {revision:reg.registry_revision as number,pins,services};
}
const current=(v:{status:string;not_before_ms:number;not_after_ms:number},
 now:number)=>v.status==='ACTIVE'&&now>=v.not_before_ms&&now<v.not_after_ms;
/**
 * Reuse the existing Ed25519 S0 lab interop instead of inventing a new
 * receipt signature format. A receipt-provided key is never used as a pin.
 */
export function inspectWa10PinnedS0LabTrust(
 rawBytes:Uint8Array,receipt:unknown,expected:TrustedExpectedS0LabReceipt,
 hostRaw:unknown,registryRaw:unknown,
):Wa10AuditResult{
 try{
  const host=own(hostRaw,contextKeys);
  const trusted=own(expected,expectedKeys);
  if(!host||!trusted||![host.principal_ref,host.app_ref,
     host.issuer_ref,host.m2m_key_id].every(id)||
     !rev(host.m2m_key_revision)||
     host.audience!=='PRUMO_S0_META_INGRESS_LAB'||
     !pos(host.expected_registry_revision)||!time(host.at_ms)||
     !(rawBytes instanceof Uint8Array)||rawBytes.byteLength<1||
     rawBytes.byteLength>262144)return denied('INVALID_INPUT');
  const registry=validRegistry(registryRaw);
  if(!registry)return denied('INVALID_TRUST_REGISTRY');
  if(registry.revision!==host.expected_registry_revision)
   return denied('STALE_TRUST_REVISION');
  if(trusted.app!==host.app_ref||
     trusted.m2m_issuer!==host.issuer_ref||
     trusted.m2m_key_id!==host.m2m_key_id||
     trusted.m2m_key_revision!==host.m2m_key_revision)
   return denied('SERVICE_CONTEXT_DENIED');
  const identities=registry.services.filter(s=>s.app_ref===host.app_ref&&
   s.principal_ref===host.principal_ref&&s.issuer_ref===host.issuer_ref&&
   s.m2m_key_id===host.m2m_key_id&&
   s.m2m_key_revision===host.m2m_key_revision&&
   s.audience===host.audience);
  if(identities.length!==1||!current(identities[0],host.at_ms))
   return denied('SERVICE_CONTEXT_DENIED');
  const pins=registry.pins.filter(p=>p.app_ref===host.app_ref&&
   p.instance_ref===trusted.instance&&
   p.key_id===trusted.receipt_key_id&&
   p.key_revision===trusted.receipt_key_revision);
  if(pins.length!==1)return denied('PIN_NOT_CURRENT');
  if(pins[0].status==='REVOKED')return denied('PIN_REVOKED');
  if(!current(pins[0],host.at_ms))return denied('PIN_NOT_CURRENT');
  const pin=rawKey(pins[0].public_key_base64);
  if(!pin)return denied('INVALID_TRUST_REGISTRY');
  const validated=inspectPinnedS0LabReceipt(
   Uint8Array.from(rawBytes),receipt,
   expected,Uint8Array.from(pin));
  if(validated.decision!=='S0_LAB_SIGNATURE_AND_CONTEXT_MATCH_UNRATIFIED')
   return denied('RECEIPT_DENIED');
  return matched();
 }catch{return denied('INVALID_INPUT');}
}
