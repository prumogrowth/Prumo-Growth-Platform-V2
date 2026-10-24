/**
 * WA47: STRICT OFFLINE compatibility gate for WA34/35 JSON-HMAC and S0/044
 * 15-field HMAC. It verifies BOTH wire formats independently, never converts
 * one signature into the other. The passed ports are synthetic, NOT a real
 * service principal, DB transaction or Meta provenance authority.
 * Absolutely no network, hosted DB, Graph, ACK, production or S1 permissions.
 */
import {createHash,createHmac,timingSafeEqual} from 'node:crypto';
import {compareWa44FixtureSignature,wa44CanonicalBytes,WA44_AUDIENCE} from './s0_wa_048_meta_handoff_adapter.mjs';

const SCOPE=['app_ref','concessionaria_id','canal_id','waba_id','phone_number_id',
 'provider_message_id','recipient_verified','case_ref','attempt_ref',
 'binding_revision','event_ref','provider_kind','meta_body_sha256'];
const INVAR=['ack_allowed','send_authorized','retry_external','production_authorized',
 'case_transition_authorized','definitive_failure_count_increment'];
const PAYLOAD=['contract','purpose','issuer','audience','nonce_ref',
 'issued_at_ms','expires_at_ms',...SCOPE,...INVAR];
const CONTEXT=['appRef','tenantRef','channelRef','wabaTechnical','phoneTechnical',
 'appTechnical','intentRef','caseRef','attemptRef','correlationRef','bindingRevision',
 'recipient','wamid','providerTimestampSeconds','wa34KeySlot','s0KeyId'];
const PORTS=['getContext','getWa34Key','getS0Key','nowMs'];
const TICKET=['contract','audience','candidate','macSha256',
 'ack_allowed','send_authorized','retry_external','production_authorized','service_authenticated'];
const WA46=['decision','ticket','ack_allowed','send_authorized','retry_external',
 'production_authorized','service_authenticated','meta_provenance_production_proven',
 'delivery_confirmed','case_transition_authorized'];
const ident=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const uuid=x=>typeof x==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(x);
const tech=x=>typeof x==='string'&&/^[0-9]{5,25}$/.test(x);
const wamid=x=>typeof x==='string'&&/^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$/.test(x);
const phone=x=>typeof x==='string'&&/^[0-9]{8,15}$/.test(x);
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const time=x=>Number.isSafeInteger(x)&&x>=0;
const nonce=x=>ident(x);
const deny=decision=>Object.freeze({decision,wire_agreement:false,
 service_authenticated:false,ack_allowed:false,send_authorized:false,
 retry_external:false,production_authorized:false,delivery_confirmed:false,
 case_transition_authorized:false,definitive_failure_count_increment:false,
 s0_write_authorized:false,meta_provenance_production_proven:false});
function snapshot(raw,keys){
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const proto=Object.getPrototypeOf(raw);
  if(proto!==Object.prototype&&proto!==null)return null;
  const ds=Object.getOwnPropertyDescriptors(raw);
  if(Reflect.ownKeys(raw).length!==keys.length||
    !keys.every(k=>Object.hasOwn(ds,k)&&Object.hasOwn(ds[k],'value')))return null;
  return Object.freeze(Object.fromEntries(keys.map(k=>[k,ds[k].value])));
 }catch{return null;}
}
function same(a,b,keys){return keys.every(k=>a[k]===b[k]);}
function context(raw){
 const v=snapshot(raw,CONTEXT);
 if(!v||!ident(v.appRef)||!ident(v.tenantRef)||!uuid(v.channelRef)||
  !tech(v.appTechnical)||!tech(v.wabaTechnical)||!tech(v.phoneTechnical)||
  !uuid(v.intentRef)||!ident(v.caseRef)||!ident(v.attemptRef)||
  !ident(v.correlationRef)||!Number.isSafeInteger(v.bindingRevision)||
  v.bindingRevision<1||!phone(v.recipient)||!wamid(v.wamid)||
  typeof v.providerTimestampSeconds!=='string'||
  !/^[1-9][0-9]{0,11}$/.test(v.providerTimestampSeconds)||
  !Number.isSafeInteger(Number(v.providerTimestampSeconds))||
  !ident(v.wa34KeySlot)||!uuid(v.s0KeyId))return null;
 const iso=new Date(Number(v.providerTimestampSeconds)*1000);
 return !Number.isNaN(iso.valueOf())?v:null;
}
const digest=s=>createHash('sha256').update(s,'utf8').digest('hex');
function expectedEvents(ctx,kind){
 const iso=new Date(Number(ctx.providerTimestampSeconds)*1000).toISOString();
 return {
  wa34:'EVT_'+digest(JSON.stringify([ctx.appRef,ctx.wabaTechnical,ctx.phoneTechnical,
   ctx.wamid,ctx.recipient,kind,iso])),
  wa46:'WA46_'+digest(JSON.stringify([ctx.wabaTechnical,ctx.phoneTechnical,
   ctx.wamid,ctx.recipient,kind,ctx.providerTimestampSeconds]))
 };
}
function wa34Valid(packet,ctx,now){
 const outer=snapshot(packet,['payload','mac_sha256']);
 const p=outer&&snapshot(outer.payload,PAYLOAD);
 if(!p||!hash(outer.mac_sha256)||
  p.contract!=='wa34-service-forensic-handoff.lab.v1'||
  p.purpose!=='FORENSIC_APPEND_ONLY'||
  p.issuer!=='WA34_SYNTHETIC_META_INGRESS'||
  p.audience!=='WA34_SYNTHETIC_S0_READER'||
  !nonce(p.nonce_ref)||!time(p.issued_at_ms)||!time(p.expires_at_ms)||
  p.expires_at_ms<=p.issued_at_ms||p.expires_at_ms-p.issued_at_ms>120000||
  p.issued_at_ms>now||p.expires_at_ms<=now||
  !INVAR.every(k=>p[k]===false)||
  p.app_ref!==ctx.appRef||p.concessionaria_id!==ctx.tenantRef||
  p.canal_id!==ctx.channelRef||p.waba_id!==ctx.wabaTechnical||
  p.phone_number_id!==ctx.phoneTechnical||p.provider_message_id!==ctx.wamid||
  p.recipient_verified!==ctx.recipient||p.case_ref!==ctx.caseRef||
  p.attempt_ref!==ctx.attemptRef||p.binding_revision!==ctx.bindingRevision||
  !['sent','delivered','read','failed'].includes(p.provider_kind)||
  !hash(p.meta_body_sha256))return null;
 const ids=expectedEvents(ctx,p.provider_kind);
 if(p.event_ref!==ids.wa34)return null;
 return {outer,p,ids};
}
function s0Valid(raw,ctx,wa34,now){
 const v=snapshot(raw,WA46);
 if(!v||v.decision!=='LAB_META_HMAC_AND_S0_CANDIDATE_ONLY'||
  !WA46.slice(2).every(k=>v[k]===false))return null;
 const t=snapshot(v.ticket,TICKET);
 if(!t||t.contract!=='WA40_PG17_LAB_ONLY'||t.audience!==WA44_AUDIENCE||
  !TICKET.slice(4).every(k=>t[k]===false)||!hash(t.macSha256)||
  !Array.isArray(t.candidate)||t.candidate.length!==15)return null;
 // Validation occurs on an immutable local copy, never on a hostile array.
 let candidate;
 try{
  const ds=Object.getOwnPropertyDescriptors(t.candidate);
  if(Reflect.ownKeys(t.candidate).length!==16||
   !Array.from({length:15},(_,i)=>String(i)).every(k=>
    Object.hasOwn(ds,k)&&Object.hasOwn(ds[k],'value'))||
   !Object.hasOwn(ds,'length'))return null;
  candidate=Object.freeze(Array.from({length:15},(_,i)=>ds[String(i)].value));
 }catch{return null;}
 if(!wa44CanonicalBytes(candidate)||candidate[0]!==ctx.s0KeyId||
  candidate[1]!==ctx.appTechnical||candidate[2]!==ctx.wabaTechnical||
  candidate[3]!==ctx.phoneTechnical||candidate[4]!==ctx.channelRef||
  candidate[5]!==ctx.intentRef||candidate[6]!==ctx.attemptRef||
  candidate[7]!==ctx.correlationRef||candidate[8]!==ctx.recipient||
  candidate[9]!==ctx.wamid||candidate[10]!==wa34.ids.wa46||
  candidate[11]!==wa34.p.provider_kind||
  candidate[12]!==wa34.p.meta_body_sha256||
  // WA44 receiver measures seconds from the privileged S0 clock.
  Number(candidate[13])*1000>now||now-Number(candidate[13])*1000>120000||
  candidate[14]===wa34.p.nonce_ref)return null;
 return {candidate,mac:t.macSha256};
}
/** No authority is returned, even if both test HMACs match. */
export function createWa47OfflineWireAgreement(rawPorts){
 const ports=snapshot(rawPorts,PORTS);
 if(!ports||!PORTS.every(k=>typeof ports[k]==='function'))return null;
 return Object.freeze({async compare(rawWa34,rawWa46){
  try{
   const start=ports.nowMs();
   if(!time(start))return deny('LAB_UNAVAILABLE');
   const c1=context(await ports.getContext());
   if(!c1)return deny('LAB_SCOPE_DENIED');
   const p=wa34Valid(rawWa34,c1,start);
   if(!p)return deny('LAB_WA34_DENIED');
   const t=s0Valid(rawWa46,c1,p,start);
   if(!t)return deny('LAB_S0_DENIED');
   const key34=await ports.getWa34Key(c1.wa34KeySlot);
   const keyS0=await ports.getS0Key(c1.s0KeyId);
   if(!Buffer.isBuffer(key34)||key34.length<32||key34.length>128||
    !Buffer.isBuffer(keyS0)||keyS0.length<32||keyS0.length>128)return deny('LAB_UNAVAILABLE');
   const mac34=createHmac('sha256',Buffer.from(key34)).update(
    JSON.stringify(PAYLOAD.map(k=>p.p[k])),'utf8').digest();
   if(!timingSafeEqual(mac34,Buffer.from(p.outer.mac_sha256,'hex')))
    return deny('LAB_WA34_DENIED');
   if(!compareWa44FixtureSignature(t.candidate,Buffer.from(keyS0),t.mac))
    return deny('LAB_S0_DENIED');
   const c2=context(await ports.getContext());
   const end=ports.nowMs();
   if(!c2||!time(end)||end<start||end-start>20000||
    !same(c1,c2,CONTEXT)||!wa34Valid(rawWa34,c2,end)||
    !s0Valid(rawWa46,c2,p,end))return deny('LAB_STALE');
   return Object.freeze({...deny('LAB_DUAL_WIRE_AGREEMENT_ONLY'),wire_agreement:true});
  }catch{return deny('LAB_UNAVAILABLE');}
 }});
}
