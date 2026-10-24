/**
 * WA45: synthetic, server-side handoff boundary ONLY for disposable PG17.
 * Injected ports are offline fixtures, NOT authenticated Meta/S0 services.
 * No network, Graph, ACK, hosted Supabase, production service principal, S1.
 * Unlike WA44 candidate fixture, the event CANNOT supply registry/binding/key.
 */
import {makeWa44CandidateFixture,signWa44Fixture} from './s0_wa_048_meta_handoff_adapter.mjs';

const R=['appTechnical','wabaTechnical','phoneTechnical','appRef','tenantRef','channelRef'];
const B=['appRef','tenantRef','channelRef','intentRef','attemptRef','correlationRef','recipient','wamid','bindingRevision'];
const E=['eventRef','kind','bodySha256','wamid','recipient'];
const P=['getRegistry','lookupBinding','getInternalKey','newNonce','nowSeconds'];
const fail=(reason)=>Object.freeze({decision:reason,ticket:null,ack_allowed:false,
 send_authorized:false,retry_external:false,production_authorized:false,
 service_authenticated:false,delivery_confirmed:false,case_transition_authorized:false});
function plain(v,keys){
 try{
  if(v===null||typeof v!=='object'||Array.isArray(v))return null;
  const proto=Object.getPrototypeOf(v);
  if(proto!==Object.prototype&&proto!==null)return null;
  const ds=Object.getOwnPropertyDescriptors(v);
  const own=Reflect.ownKeys(v);
  if(own.length!==keys.length||own.some(k=>typeof k!=='string')||
     !keys.every(k=>Object.hasOwn(ds,k)&&Object.hasOwn(ds[k],'value')))
   return null;
  return Object.freeze(Object.fromEntries(keys.map(k=>[k,ds[k].value])));
 }catch{return null;}
}
function equal(a,b,keys){return keys.every(k=>a[k]===b[k]);}
const seconds=x=>Number.isSafeInteger(x)&&x>=0;
const uuid=x=>typeof x==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(x);
const hex=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);

/**
 * Constructor must be called only by an independently authenticated FUTURE
 * trusted server. The current test harness injects UNTRUSTED synthetic ports,
 * so success is always LAB_CANDIDATE_ONLY, never identity authentication.
 */
export function createWa45OfflineBoundary(rawPorts, keyId){
 const p=plain(rawPorts,P);
 if(!p||!uuid(keyId)||!P.every(k=>typeof p[k]==='function'))return null;
 return Object.freeze({async issue(rawEvent){
  const e=plain(rawEvent,E);
  if(!e||!hex(e.bodySha256)||typeof e.eventRef!=='string'||
    !/^[A-Za-z0-9_.:-]{1,128}$/.test(e.eventRef)||
    !['sent','delivered','read','failed'].includes(e.kind)||
    typeof e.wamid!=='string'||!/^wamid\.[A-Za-z0-9+/_=:.-]{1,1024}$/.test(e.wamid)||
    typeof e.recipient!=='string'||!/^[0-9]{8,15}$/.test(e.recipient))
   return fail('LAB_DENIED');
  try{
   const start=p.nowSeconds();
   if(!seconds(start))return fail('LAB_UNAVAILABLE');
   const r1=plain(await p.getRegistry(),R);
   const b1=plain(await p.lookupBinding(e.wamid,e.recipient),B);
   if(!r1||!b1||b1.wamid!==e.wamid||b1.recipient!==e.recipient||
    b1.bindingRevision<1||!Number.isSafeInteger(b1.bindingRevision))
    return fail('LAB_SCOPE_DENIED');
   // The only key in the issuing process comes from a separate privileged
   // test fixture port; it is never accepted from the event or S0 binding.
   const key=await p.getInternalKey();
   if(!Buffer.isBuffer(key)||key.length<32||key.length>128)
    return fail('LAB_UNAVAILABLE');
   const nonce=await p.newNonce();
   if(!uuid(nonce))return fail('LAB_UNAVAILABLE');
   const r2=plain(await p.getRegistry(),R);
   const b2=plain(await p.lookupBinding(e.wamid,e.recipient),B);
   const end=p.nowSeconds();
   if(!r2||!b2||!seconds(end)||end<start||end-start>20||
     !equal(r1,r2,R)||!equal(b1,b2,B))
    return fail('LAB_STALE');
   const candidate=makeWa44CandidateFixture({
    registry:r2,binding:b2,event:{eventRef:e.eventRef,kind:e.kind,bodySha256:e.bodySha256},
    keyId,nonce,issuedAtSeconds:end,expectedRevision:b1.bindingRevision
   });
   if(!candidate)return fail('LAB_SCOPE_DENIED');
   const ticket=signWa44Fixture(candidate,key);
   if(!ticket)return fail('LAB_UNAVAILABLE');
   return Object.freeze({decision:'LAB_CANDIDATE_ONLY',ticket,ack_allowed:false,
    send_authorized:false,retry_external:false,production_authorized:false,
    service_authenticated:false,delivery_confirmed:false,case_transition_authorized:false});
  }catch{return fail('LAB_UNAVAILABLE');}
 }});
}
