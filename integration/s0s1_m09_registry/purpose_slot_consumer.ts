/**
 * M09-06: single-purpose Meta slot NAME matching, offline LAB ONLY.
 * Input witness is UNTRUSTED. No backend, vault, M2M authentication, HTTP,
 * Graph, Meta ownership, privileged authorization or send/ACK is provided.
 */
import {inspectM09ForMetaOffline} from './wa04a_scope_bridge.ts';
export type MetaPurpose = 'GET_VERIFY_TOKEN' | 'POST_APP_SECRET' | 'GRAPH_ACCESS_TOKEN';
export type PurposeSlotResult = Readonly<{
  contract_version: 'prumo.s0.meta.purpose-slot-lab/0.1-candidate';
  decision: 'LAB_SLOT_NAME_MATCHED_UNVERIFIED' | 'DENIED';
  reason: 'PURPOSE_SLOT_SHAPE_MATCHED' | 'INVALID_REQUEST' |
    'REGISTRY_SCOPE_DENIED' | 'INVALID_SLOT_WITNESS' |
    'PURPOSE_MISMATCH' | 'SOURCE_CHANGED';
  purpose: MetaPurpose | null;
  slot_ref: string | null;
  source_snapshot_ref: string | null;
  legacy_wa04a_directly_compatible: false;
  provider_ownership_verified: false;
  delegation_verified: false;
  m2m_operationally_verified: false;
  production_authorized: false;
  send_authorized: false;
  graph_authorized: false;
  ack_allowed: false;
  s0_write_authorized: false;
}>;
type Obj=Record<string,unknown>;
const VERSION='prumo.s0.meta.purpose-slot-lab/0.1-candidate' as const;
const WITNESS_VERSION='prumo.s0.meta.purpose-slot-witness/0.1-lab';
const EXPECTED_KEYS=['purpose','scope','expected_revisions'] as const;
const WITNESS_KEYS=['contract_version','app_ref','purpose','slot_ref',
  'source_snapshot_ref','source_role','production_authorized',
  'send_authorized'] as const;
const SCOPE_KEYS=['concessionaria_id','app_ref','route_ref',
  'canal_id','waba_id','phone_number_id'] as const;
const REV_KEYS=['route','app','binding','grant','principal'] as const;
const NO_AUTH=Object.freeze({
  legacy_wa04a_directly_compatible:false as const,
  provider_ownership_verified:false as const,
  delegation_verified:false as const,
  m2m_operationally_verified:false as const,
  production_authorized:false as const,
  send_authorized:false as const,
  graph_authorized:false as const,
  ack_allowed:false as const,
  s0_write_authorized:false as const,
});
function exact(value:unknown,keys:readonly string[]):Obj|null {
  try {
    if(!value||typeof value!=='object'||Array.isArray(value))return null;
    const proto=Object.getPrototypeOf(value);
    if(proto!==Object.prototype&&proto!==null)return null;
    const own=Reflect.ownKeys(value);
    if(own.length!==keys.length||own.some(
      k=>typeof k!=='string'||!keys.includes(k)))return null;
    const d=Object.getOwnPropertyDescriptors(value);
    const out:Obj=Object.create(null);
    for(const k of keys){
      if(!d[k]||!Object.hasOwn(d[k],'value'))return null;
      out[k]=d[k].value;
    }
    return out;
  }catch{return null;}
}
const id=(x:unknown):x is string=>
  typeof x==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const phone=(x:unknown):x is string=>
  typeof x==='string'&&/^\d{5,25}$/.test(x);
const digest=(x:unknown):x is string=>
  typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const slot=(x:unknown):x is string=>
  typeof x==='string'&&/^[A-Z][A-Z0-9_]{2,127}$/.test(x)&&
  !x.startsWith('SUPABASE_');
const rev=(x:unknown):x is number=>
  typeof x==='number'&&Number.isSafeInteger(x)&&x>0;
const isPurpose=(x:unknown):x is MetaPurpose=>
  x==='GET_VERIFY_TOKEN'||x==='POST_APP_SECRET'||x==='GRAPH_ACCESS_TOKEN';
function deny(reason:PurposeSlotResult['reason']):PurposeSlotResult {
  return Object.freeze({
    contract_version:VERSION,decision:'DENIED' as const,reason,
    purpose:null,slot_ref:null,source_snapshot_ref:null,...NO_AUTH
  });
}
/**
 * A fixture role marker is not an authentication credential. This does not
 * authenticate Ed25519 on the wire and never grants slot redemption rights.
 * One request can return at most ONE named slot (never three).
 */
export function inspectPurposeSlotLab(
  trustedRead:unknown, slotWitness:unknown, request:unknown,
):PurposeSlotResult {
  try {
    const q=exact(request,EXPECTED_KEYS);
    if(!q||!isPurpose(q.purpose))return deny('INVALID_REQUEST');
    const scope=exact(q.scope,SCOPE_KEYS);
    const versions=exact(q.expected_revisions,REV_KEYS);
    if(!scope||!versions||SCOPE_KEYS.slice(0,5).some(k=>!id(scope[k]))||
      !phone(scope.phone_number_id)||REV_KEYS.some(k=>!rev(versions[k])))
      return deny('INVALID_REQUEST');
    const audit=inspectM09ForMetaOffline(trustedRead,scope,versions,'REGISTRY_READ');
    if(audit.decision!=='LAB_SCOPE_MATCHED_UNVERIFIED')
      return deny('REGISTRY_SCOPE_DENIED');
    const w=exact(slotWitness,WITNESS_KEYS);
    if(!w||w.contract_version!==WITNESS_VERSION||
      w.source_role!=='DISPOSABLE_PG17_INSTALLER_UNVERIFIED'||
      w.production_authorized!==false||w.send_authorized!==false||
      !id(w.app_ref)||!isPurpose(w.purpose)||!slot(w.slot_ref)||
      !digest(w.source_snapshot_ref))
      return deny('INVALID_SLOT_WITNESS');
    if(w.purpose!==q.purpose||w.app_ref!==scope.app_ref)
      return deny('PURPOSE_MISMATCH');
    const source=exact(trustedRead,[
      'contract_version','decision','reason','snapshot',
      'production_authorized','send_authorized','external_http_ack',
      'commercial_transition_authorized'
    ]);
    const snapshot=source&&exact(source.snapshot,[
      ...SCOPE_KEYS,'revisions','source_revision','snapshot_ref',
      'ownership_evidence_state','delegation_evidence_state'
    ]);
    if(!snapshot||w.source_snapshot_ref!==snapshot.snapshot_ref)
      return deny('SOURCE_CHANGED');
    return Object.freeze({
      contract_version:VERSION,
      decision:'LAB_SLOT_NAME_MATCHED_UNVERIFIED' as const,
      reason:'PURPOSE_SLOT_SHAPE_MATCHED' as const,
      purpose:q.purpose as MetaPurpose,
      slot_ref:w.slot_ref as string,
      source_snapshot_ref:w.source_snapshot_ref as string,
      ...NO_AUTH
    });
  }catch{return deny('INVALID_REQUEST');}
}
