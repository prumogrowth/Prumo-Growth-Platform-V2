/**
 * M09-07 — signed origin + fresh recheck verifier, LABORATORY ONLY.
 *
 * A pinned externally supplied Ed25519 public key checks two separate signed
 * observations over an isolated, strict canonical JSON envelope. Neither
 * signature is proof of real S0 custody or Meta ownership. No secret names
 * are returned and no transport, vault, Graph, ACK or send can be authorized.
 */
import {createPublicKey,verify as verifyEd25519} from 'node:crypto';

type O = Record<string,unknown>;
const VERSION='prumo.s0.meta.origin-recheck/0.1-lab';
const DOMAIN=Buffer.from('PRUMO.S0.M09.ATTEST.RECHECK/0.1\0','utf8');
const SPKI_PREFIX=Buffer.from('302a300506032b6570032100','hex');
const PURPOSES=['GET_VERIFY_TOKEN','POST_APP_SECRET','GRAPH_ACCESS_TOKEN'] as const;
const SCOPE=['concessionaria_id','app_ref','route_ref','canal_id','waba_id','phone_number_id'] as const;
const REVS=['route','app','binding','grant','principal'] as const;
const PAYLOAD=['contract_version','kind','issuer_ref','audience','purpose',
  'scope','revisions','source_snapshot_ref','slot_ref','issued_ms',
  'expires_ms','nonce','parent_nonce'] as const;
const EXPECTED=['purpose','scope','revisions','source_snapshot_ref'] as const;
const FLAGS={
  production_authorized:false as const,
  send_authorized:false as const,
  graph_authorized:false as const,
  ack_allowed:false as const,
  s0_write_authorized:false as const,
  provider_ownership_verified:false as const,
  delegation_verified:false as const,
  m2m_operationally_verified:false as const,
  credential_resolution_authorized:false as const,
  recheck_atomic_with_dispatch:false as const,
};
export type OriginAudit=Readonly<{
  contract_version:'prumo.s0.meta.origin-audit/0.1-lab';
  decision:'LAB_SIGNED_RECHECK_MATCHED_UNVERIFIED'|'DENIED';
  reason:'SIGNED_TWO_OBSERVATIONS'|'INVALID_INPUT'|'INVALID_ATTESTATION'|
    'INVALID_SIGNATURE'|'UNTRUSTED_KEY'|'STALE_RECHECK'|
    'SCOPE_CHANGED'|'RECHECK_REQUIRED';
  signature_integrity_lab_verified:boolean;
  purpose:string|null;
} & typeof FLAGS>;
const ID=/^[A-Za-z0-9_.:-]{1,128}$/;
const SLOT=/^[A-Z][A-Z0-9_]{2,127}$/;
const HASH=/^[a-f0-9]{64}$/;
const NONCE=/^[A-Za-z0-9_-]{16,128}$/;
const isID=(x:unknown):x is string=>typeof x==='string'&&ID.test(x);
const isRevision=(x:unknown):x is number=>typeof x==='number'&&Number.isSafeInteger(x)&&x>0;
const isClock=(x:unknown):x is number=>typeof x==='number'&&Number.isSafeInteger(x)&&x>=0;
function exact(v:unknown,keys:readonly string[]):O|null {
  try{
    if(!v||typeof v!=='object'||Array.isArray(v))return null;
    const proto=Object.getPrototypeOf(v);
    if(proto!==Object.prototype&&proto!==null)return null;
    const d=Object.getOwnPropertyDescriptors(v);
    const own=Reflect.ownKeys(v);
    if(own.length!==keys.length||
       own.some(k=>typeof k!=='string'||!keys.includes(k)))return null;
    const out:O=Object.create(null);
    for(const k of keys){
      if(!d[k]||!Object.hasOwn(d[k],'value'))return null;
      out[k]=d[k].value;
    }
    return out;
  }catch{return null;}
}
function canonical(v:unknown):string{
  if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
  if(v&&typeof v==='object'){
    const o=v as O;
    return '{'+Object.keys(o).sort().map(k=>JSON.stringify(k)+':'+canonical(o[k])).join(',')+'}';
  }
  return JSON.stringify(v);
}
function deny(reason:OriginAudit['reason']):OriginAudit{
  return Object.freeze({contract_version:'prumo.s0.meta.origin-audit/0.1-lab',
    decision:'DENIED' as const,reason,signature_integrity_lab_verified:false,
    purpose:null,...FLAGS});
}
function parsePayload(raw:unknown,kind:'ORIGIN'|'RECHECK'):O|null {
  const p=exact(raw,PAYLOAD);
  if(!p||p.contract_version!==VERSION||p.kind!==kind||
     p.issuer_ref!=='M09_S0_LAB'||p.audience!=='LAB_META_CONSUMER'||
     !PURPOSES.includes(p.purpose as typeof PURPOSES[number])||
     typeof p.nonce!=='string'||!NONCE.test(p.nonce)||
     !isClock(p.issued_ms)||!isClock(p.expires_ms)||
     (p.expires_ms as number)-(p.issued_ms as number)>30000||
     (p.expires_ms as number)<=(p.issued_ms as number)||
     !(kind==='ORIGIN'?p.parent_nonce===null:
        typeof p.parent_nonce==='string'&&NONCE.test(p.parent_nonce))||
     typeof p.slot_ref!=='string'||!SLOT.test(p.slot_ref)||
     p.slot_ref.startsWith('SUPABASE_')||
     typeof p.source_snapshot_ref!=='string'||!HASH.test(p.source_snapshot_ref))
    return null;
  const s=exact(p.scope,SCOPE),r=exact(p.revisions,REVS);
  if(!s||!r||SCOPE.slice(0,5).some(k=>!isID(s[k]))||
    typeof s.phone_number_id!=='string'||!/^\d{5,25}$/.test(s.phone_number_id)||
    REVS.some(k=>!isRevision(r[k])))return null;
  p.scope=s;p.revisions=r;
  return p;
}
function checkedSignature(entry:unknown,kind:'ORIGIN'|'RECHECK',key:ReturnType<typeof createPublicKey>):
  {payload:O}|null {
  const e=exact(entry,['payload','signature']);
  if(!e||typeof e.signature!=='string'||!(/^[A-Za-z0-9_-]{86}$/).test(e.signature))
    return null;
  const p=parsePayload(e.payload,kind);
  if(!p)return null;
  const sig=Buffer.from(e.signature,'base64url');
  if(sig.length!==64||sig.toString('base64url')!==e.signature)return null;
  if(!verifyEd25519(null,Buffer.concat([DOMAIN,Buffer.from(canonical(p),'utf8')]),key,sig))
    return null;
  return {payload:p};
}
/**
 * expected is supplied independently of BOTH signed inputs. Recheck must be
 * a fresh, separately signed PG17 observation with its own nonce.
 *
 * Positive status only validates laboratory integrity and equality. An old
 * signed recheck may remain valid briefly after a real change; no actual
 * dispatch or vault use may depend on it.
 */
export function inspectOriginRecheckLab(
  origin:unknown,fresh:unknown,expected:unknown,publicKeyDer:unknown,
  nowMs:unknown,
):OriginAudit{
  try{
    const e=exact(expected,EXPECTED);
    if(!e||!isClock(nowMs))return deny('INVALID_INPUT');
    const s=exact(e.scope,SCOPE),r=exact(e.revisions,REVS);
    if(!s||!r||SCOPE.slice(0,5).some(k=>!isID(s[k]))||
       typeof s.phone_number_id!=='string'||!/^\d{5,25}$/.test(s.phone_number_id)||
       REVS.some(k=>!isRevision(r[k]))||
       !PURPOSES.includes(e.purpose as typeof PURPOSES[number])||
       typeof e.source_snapshot_ref!=='string'||!HASH.test(e.source_snapshot_ref))
      return deny('INVALID_INPUT');
    if(!(publicKeyDer instanceof Uint8Array)||publicKeyDer.length!==44)
      return deny('UNTRUSTED_KEY');
    const bytes=Buffer.from(publicKeyDer);
    if(!bytes.subarray(0,12).equals(SPKI_PREFIX))return deny('UNTRUSTED_KEY');
    const key=createPublicKey({key:bytes,format:'der',type:'spki'});
    const first=checkedSignature(origin,'ORIGIN',key);
    if(!first)return deny('INVALID_SIGNATURE');
    if(!fresh)return deny('RECHECK_REQUIRED');
    const second=checkedSignature(fresh,'RECHECK',key);
    if(!second)return deny('INVALID_SIGNATURE');
    const a=first.payload,z=second.payload;
    if(z.parent_nonce!==a.nonce||z.nonce===a.nonce||
       (z.issued_ms as number)<(a.issued_ms as number)||
       (z.issued_ms as number)-(a.issued_ms as number)>15000)
      return deny('STALE_RECHECK');
    if((nowMs as number)<(z.issued_ms as number)-1000||
       (nowMs as number)>=(z.expires_ms as number)||
       (nowMs as number)>=(a.expires_ms as number))
      return deny('STALE_RECHECK');
    for(const p of [a,z]){
      if(p.purpose!==e.purpose||p.source_snapshot_ref!==e.source_snapshot_ref||
         SCOPE.some(k=>(p.scope as O)[k]!==s[k])||
         REVS.some(k=>(p.revisions as O)[k]!==r[k]))
        return deny('SCOPE_CHANGED');
    }
    if(a.slot_ref!==z.slot_ref)return deny('SCOPE_CHANGED');
    return Object.freeze({
      contract_version:'prumo.s0.meta.origin-audit/0.1-lab',
      decision:'LAB_SIGNED_RECHECK_MATCHED_UNVERIFIED' as const,
      reason:'SIGNED_TWO_OBSERVATIONS' as const,
      signature_integrity_lab_verified:true,
      purpose:e.purpose as string,
      ...FLAGS
    });
  }catch{return deny('INVALID_ATTESTATION');}
}
