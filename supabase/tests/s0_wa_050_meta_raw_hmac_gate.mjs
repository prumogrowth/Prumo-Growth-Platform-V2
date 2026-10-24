/**
 * WA46 OFFLINE-only: HMAC on raw Meta webhook bytes before WA45's synthetic S0
 * candidate builder. No HTTP endpoint, durable ACK, real service identity,
 * real Meta credential, S1 authorization, Graph call, or hosted Supabase.
 * Ports, route and keys are laboratory fixtures, not authenticated services.
 * WA34/35 JSON tickets are never accepted as the S0/044 wire contract.
 */
import {createHmac,createHash,timingSafeEqual} from 'node:crypto';

const REG=['routeRef','revision','appTechnical','wabaTechnical','phoneTechnical',
 'appRef','tenantRef','channelRef','secretSlot','enabled'];
const PORTS=['getRegistry','getMetaAppSecret','nowSeconds','wa45Boundary'];
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const tech=x=>typeof x==='string'&&/^[0-9]{5,25}$/.test(x);
const uuid=x=>typeof x==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(x);
const sec=x=>Number.isSafeInteger(x)&&x>=0;
const fail=decision=>Object.freeze({decision,ticket:null,ack_allowed:false,
 send_authorized:false,retry_external:false,production_authorized:false,
 service_authenticated:false,meta_provenance_production_proven:false,
 delivery_confirmed:false,case_transition_authorized:false});
function dataOnly(raw,keys){
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
function registry(raw,route){
 const r=dataOnly(raw,REG);
 return r&&r.routeRef===route&&id(r.routeRef)&&
  Number.isSafeInteger(r.revision)&&r.revision>0&&
  tech(r.appTechnical)&&tech(r.wabaTechnical)&&tech(r.phoneTechnical)&&
  id(r.appRef)&&id(r.tenantRef)&&uuid(r.channelRef)&&id(r.secretSlot)&&
  r.enabled===true?r:null;
}
function same(a,b){return REG.every(k=>a[k]===b[k]);}
function parseOneStatus(bytes,r){
 try{
  const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
  const root=dataOnly(JSON.parse(raw),['object','entry']);
  if(!root||root.object!=='whatsapp_business_account'||
   !Array.isArray(root.entry)||root.entry.length!==1)return null;
  const ent=dataOnly(root.entry[0],['id','changes']);
  if(!ent||ent.id!==r.wabaTechnical||
   !Array.isArray(ent.changes)||ent.changes.length!==1)return null;
  const ch=dataOnly(ent.changes[0],['field','value']);
  if(!ch||ch.field!=='messages')return null;
  const v=dataOnly(ch.value,['metadata','statuses']);
  const m=v&&dataOnly(v.metadata,['phone_number_id']);
  if(!v||!m||m.phone_number_id!==r.phoneTechnical||
   !Array.isArray(v.statuses)||v.statuses.length!==1)return null;
  const s=dataOnly(v.statuses[0],['id','status','recipient_id','timestamp']);
  if(!s||typeof s.id!=='string'||
   !/^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$/.test(s.id)||
   !['sent','delivered','read','failed'].includes(s.status)||
   typeof s.recipient_id!=='string'||!/^[0-9]{8,15}$/.test(s.recipient_id)||
   typeof s.timestamp!=='string'||!/^[1-9][0-9]{0,11}$/.test(s.timestamp))
   return null;
  // Deterministic fixture identity, NOT a Meta-provided callback ID.
  const tuple=JSON.stringify([ent.id,m.phone_number_id,s.id,s.recipient_id,
   s.status,s.timestamp]);
  return Object.freeze({wamid:s.id,recipient:s.recipient_id,kind:s.status,
   eventRef:'WA46_'+createHash('sha256').update(tuple).digest('hex'),
   bodySha256:createHash('sha256').update(bytes).digest('hex')});
 }catch{return null;}
}

/**
 * Constructor takes an internally selected route and injected, UNTRUSTED
 * laboratory ports. Its "receive" input cannot specify tenant/App/S0 binding.
 * The WA45 boundary independently re-checks its fixture registry and attempt.
 */
export function createWa46OfflineMetaGate(rawPorts,routeRef){
 const p=dataOnly(rawPorts,PORTS);
 if(!p||!id(routeRef)||typeof p.getRegistry!=='function'||
  typeof p.getMetaAppSecret!=='function'||typeof p.nowSeconds!=='function'||
  !p.wa45Boundary||typeof p.wa45Boundary.issue!=='function')return null;
 return Object.freeze({async receive(rawBytes,signatureHeader){
  if(!Buffer.isBuffer(rawBytes)||rawBytes.length<1||rawBytes.length>262144||
   typeof signatureHeader!=='string'||!/^sha256=[0-9a-f]{64}$/.test(signatureHeader))
   return fail('LAB_DENIED');
  // Copy BEFORE any await; HMAC, parsed event and body digest use same bytes.
  const body=Buffer.from(rawBytes);
  try{
   const start=p.nowSeconds();
   if(!sec(start))return fail('LAB_UNAVAILABLE');
   const r1=registry(await p.getRegistry(),routeRef);
   if(!r1)return fail('LAB_SCOPE_DENIED');
   const secret=await p.getMetaAppSecret(r1.secretSlot);
   if(!Buffer.isBuffer(secret)||secret.length<32||secret.length>128)
    return fail('LAB_UNAVAILABLE');
   const key=Buffer.from(secret);
   const r2=registry(await p.getRegistry(),routeRef);
   const mid=p.nowSeconds();
   if(!r2||!same(r1,r2)||!sec(mid)||mid<start||mid-start>20)
    return fail('LAB_STALE');
   const expected=Buffer.from(signatureHeader.slice(7),'hex');
   const computed=createHmac('sha256',key).update(body).digest();
   if(!timingSafeEqual(computed,expected))
    return fail('LAB_META_SIGNATURE_DENIED');
   const e=parseOneStatus(body,r2);
   if(!e)return fail('LAB_SCOPE_DENIED');
   const out=await p.wa45Boundary.issue(e);
   if(!out||out.decision!=='LAB_CANDIDATE_ONLY'||!out.ticket||
    !Array.isArray(out.ticket.candidate))return fail('LAB_SCOPE_DENIED');
   const c=out.ticket.candidate;
   if(c[1]!==r2.appTechnical||c[2]!==r2.wabaTechnical||
    c[3]!==r2.phoneTechnical||c[4]!==r2.channelRef||
    c[9]!==e.wamid||c[8]!==e.recipient||c[10]!==e.eventRef||
    c[11]!==e.kind||c[12]!==e.bodySha256)
    return fail('LAB_SCOPE_DENIED');
   const r3=registry(await p.getRegistry(),routeRef);
   const end=p.nowSeconds();
   if(!r3||!same(r2,r3)||!sec(end)||end<mid||end-start>20)
    return fail('LAB_STALE');
   return Object.freeze({decision:'LAB_META_HMAC_AND_S0_CANDIDATE_ONLY',
    ticket:out.ticket,ack_allowed:false,send_authorized:false,
    retry_external:false,production_authorized:false,service_authenticated:false,
    meta_provenance_production_proven:false,delivery_confirmed:false,
    case_transition_authorized:false});
  }catch{return fail('LAB_UNAVAILABLE');}
 }});
}
