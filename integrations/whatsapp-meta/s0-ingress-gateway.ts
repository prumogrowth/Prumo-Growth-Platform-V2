/**
 * WA-05D: OFFLINE/FAKE S0 privileged ingress boundary; never an HTTP endpoint.
 * The real S0 must authenticate its service identity and implement atomic SQL.
 * An apparent successful lab admission NEVER proves a durable commit or ACK.
 */
import type { S0HandoffCandidate, S0HandoffOccurrence } from './s0-handoff-contract.ts';
import { selectMetaCredential, resolveSignedMetaChannel, type TrustedMetaRegistry } from './credential-routing.ts';
import { FakeProtectedPayloads } from './transactional-ingress.ts';

export type FakePrivilegedCaller = Readonly<{
  service_ref: string;
  active: boolean;
  allowed_route_refs: readonly string[];
}>;
export type FakeS0IngressPorts = Readonly<{
  /** In future: authenticated S0 service identity, NEVER supplied by the request. */
  trustedCaller(): FakePrivilegedCaller;
  /** In future: locked/serializable S0 mapping at the SAME commit boundary. */
  trustedRegistry(): TrustedMetaRegistry;
  nowMs(): number;
  /** This is a memory fixture, not protected durable storage. */
  payloads: FakeProtectedPayloads;
}>;
export type FakeS0IngressResult = Readonly<{
  decision: 'LAB_ACCEPTED' | 'LAB_REPLAY' | 'DENIED' | 'LAB_CONFLICT';
  reason: 'FAKE_COMMIT' | 'SAME_BATCH' | 'MALFORMED' | 'UNTRUSTED_CALLER' |
    'BODY_NOT_PRESERVED' | 'SCOPE_OR_REVISION_INVALID' | 'SCOPE_DIGEST_MISMATCH' |
    'BATCH_REF_COLLISION' | 'FAKE_WRITE_FAILED';
  simulated_occurrences: number;
  ack_allowed: false;
  production_authorized: false;
}>;
const deny = (reason: FakeS0IngressResult['reason'], decision: FakeS0IngressResult['decision']='DENIED'): FakeS0IngressResult =>
  ({decision,reason,simulated_occurrences:0,ack_allowed:false,production_authorized:false});
const identifier = (v:unknown):v is string => typeof v==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(v);
const hash = (v:unknown):v is string => typeof v==='string' && /^[a-f0-9]{64}$/.test(v);
const positive = (v:unknown):v is number => Number.isSafeInteger(v) && (v as number)>0;
const nonnegative = (v:unknown):v is number => Number.isSafeInteger(v) && (v as number)>=0;
const onlyDataFields = (v:unknown, names:readonly string[]):boolean => {
  try {
    if(!v || typeof v!=='object' || Array.isArray(v)) return false;
    const proto=Object.getPrototypeOf(v);
    if(proto!==Object.prototype && proto!==null) return false;
    const fields=Object.getOwnPropertyDescriptors(v);
    return Object.keys(fields).length===names.length &&
      Object.values(fields).every(d=>Object.prototype.hasOwnProperty.call(d,'value')) &&
      names.every(n=>Object.prototype.hasOwnProperty.call(fields,n));
  }catch{return false;}
};
const candidateFields=['contract_version','batch_ref','route_ref','route_revision','app_ref',
  'protected_payload_ref','payload_sha256','scope_sha256','event_count','occurrences',
  'ack_allowed','production_authorized'];
const occurrenceFields=['position','event_kind','app_ref','concessionaria_id','canal_id',
  'waba_id','phone_number_id','provider_message_id','provider_timestamp','provider_kind'];
const positionFields=['entry_index','change_index','array_kind','item_index'];
function checkedSnapshot(v:unknown):S0HandoffCandidate|undefined {
  try{
    if(!onlyDataFields(v,candidateFields))return;
    const c=v as S0HandoffCandidate;
    if(!Array.isArray(c.occurrences) || c.occurrences.length===0 || c.occurrences.length>100 ||
      !c.occurrences.every(x=>onlyDataFields(x,occurrenceFields) && onlyDataFields(x.position,positionFields)))return;
    const copy=structuredClone(c);
    if(copy.contract_version!=='meta-s0-handoff.v0.1-proposed' ||
      !identifier(copy.batch_ref) || !identifier(copy.route_ref) ||
      !positive(copy.route_revision) || !identifier(copy.app_ref) ||
      !identifier(copy.protected_payload_ref) || !hash(copy.payload_sha256) ||
      !hash(copy.scope_sha256) || !positive(copy.event_count) ||
      copy.event_count!==copy.occurrences.length || copy.ack_allowed!==false ||
      copy.production_authorized!==false) return;
    const seen=new Set<string>();
    for(const e of copy.occurrences){
      const p=e.position;
      if(![p.entry_index,p.change_index,p.item_index].every(nonnegative) ||
        !['messages','statuses'].includes(p.array_kind) ||
        !['inbound_message','status_callback'].includes(e.event_kind) ||
        (p.array_kind==='messages')!==(e.event_kind==='inbound_message') ||
        ![e.app_ref,e.concessionaria_id,e.canal_id,e.waba_id,e.phone_number_id,
          e.provider_kind].every(identifier) ||
        typeof e.provider_message_id!=='string' ||
        !/^wamid\.[A-Za-z0-9+\/_=:.-]{1,1024}$/.test(e.provider_message_id) ||
        typeof e.provider_timestamp!=='string' ||
        !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(e.provider_timestamp))return;
      const k=JSON.stringify([p.entry_index,p.change_index,p.array_kind,p.item_index]);
      if(seen.has(k))return;
      seen.add(k);
    }
    return copy;
  }catch{return;}
}
const bytesToHex=(bytes:Uint8Array)=>Array.from(bytes,x=>x.toString(16).padStart(2,'0')).join('');
const digest=async(bytes:Uint8Array)=>bytesToHex(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)));
/** Exact WA-05C canonical scope digest; S0's real implementation must version this protocol. */
function scopeData(c:S0HandoffCandidate):string {
  return JSON.stringify([c.batch_ref,c.route_ref,c.route_revision,c.app_ref,
    c.occurrences.map((e:S0HandoffOccurrence)=>[
      e.position.entry_index,e.position.change_index,e.position.array_kind,e.position.item_index,
      e.app_ref,e.concessionaria_id,e.canal_id,e.waba_id,e.phone_number_id,
      e.event_kind,e.provider_message_id,e.provider_timestamp,e.provider_kind])]);
}
const sameScope=(a:S0HandoffOccurrence,b:ReturnType<typeof resolveSignedMetaChannel>):boolean =>
  b.ok && b.scope.app_ref===a.app_ref && b.scope.concessionaria_id===a.concessionaria_id &&
  b.scope.canal_id===a.canal_id && b.scope.waba_id===a.waba_id &&
  b.scope.phone_number_id===a.phone_number_id;
function trustedAtCommit(c:S0HandoffCandidate,service:FakePrivilegedCaller,registry:TrustedMetaRegistry,now:number):boolean {
  if(!service || !identifier(service.service_ref) || service.active!==true ||
    !Array.isArray(service.allowed_route_refs) || !service.allowed_route_refs.includes(c.route_ref))return false;
  const selected=selectMetaCredential(registry,{purpose:'POST_APP_SECRET',trusted_route_ref:c.route_ref,
    expected_revision:c.route_revision,at_ms:now});
  if(!selected.ok || selected.app_ref!==c.app_ref) return false;
  return c.occurrences.every(e=>sameScope(e,resolveSignedMetaChannel(registry,{
    trusted_route_ref:c.route_ref,authenticated_app_ref:c.app_ref,
    waba_id:e.waba_id,phone_number_id:e.phone_number_id,
    expected_revision:c.route_revision,at_ms:now
  })));
}
/** Simulation of internal S0 admission after a *separately* HMAC-validated handoff. */
export class FakePrivilegedS0Ingress {
  private readonly batches=new Map<string,{fingerprint:string,count:number}>();
  private count=0;
  get batchCount():number{return this.batches.size;}
  get occurrenceCount():number{return this.count;}

  async admit(input:{candidate:S0HandoffCandidate;raw_body:Uint8Array},ports:FakeS0IngressPorts,
    options:{beforeCommit?:()=>void;failWrite?:boolean}={}):Promise<FakeS0IngressResult> {
    try {
      const candidate=checkedSnapshot(input?.candidate);
      if(!candidate || !(input?.raw_body instanceof Uint8Array) ||
         input.raw_body.length===0 || input.raw_body.length>256*1024 ||
         !ports || typeof ports.trustedCaller!=='function' ||
         typeof ports.trustedRegistry!=='function' || typeof ports.nowMs!=='function' ||
         !ports.payloads || typeof ports.payloads.matchesFixture!=='function')return deny('MALFORMED');
      // Capture bytes and metadata before any await. No claim from candidate is
      // treated as a service credential or proof of persistence.
      const raw=Uint8Array.from(input.raw_body);
      if(!trustedAtCommit(candidate,ports.trustedCaller(),ports.trustedRegistry(),ports.nowMs()))
        return deny('UNTRUSTED_CALLER');
      if(!ports.payloads.matchesFixture(candidate.protected_payload_ref,raw))
        return deny('BODY_NOT_PRESERVED');
      const bodyHash=await digest(raw);
      if(bodyHash!==candidate.payload_sha256)return deny('BODY_NOT_PRESERVED');
      if(await digest(new TextEncoder().encode(scopeData(candidate)))!==candidate.scope_sha256)
        return deny('SCOPE_DIGEST_MISMATCH');
      const fingerprint=JSON.stringify([candidate.route_ref,candidate.route_revision,candidate.app_ref,
        candidate.protected_payload_ref,candidate.payload_sha256,candidate.scope_sha256]);
      // Offline fault injection: simulate a configuration change before commit.
      options.beforeCommit?.();
      // Sync final check + fake insertion, not atomic persistence across services.
      if(!trustedAtCommit(candidate,ports.trustedCaller(),ports.trustedRegistry(),ports.nowMs()))
        return deny('SCOPE_OR_REVISION_INVALID');
      if(!ports.payloads.matchesFixture(candidate.protected_payload_ref,raw))
        return deny('BODY_NOT_PRESERVED');
      const existing=this.batches.get(candidate.batch_ref);
      if(existing){
        if(existing.fingerprint!==fingerprint)return deny('BATCH_REF_COLLISION','LAB_CONFLICT');
        return {decision:'LAB_REPLAY',reason:'SAME_BATCH',simulated_occurrences:existing.count,
          ack_allowed:false,production_authorized:false};
      }
      if(this.batches.size>=100 || this.count+candidate.event_count>1000)
        return deny('MALFORMED');
      if(options.failWrite)return deny('FAKE_WRITE_FAILED');
      this.batches.set(candidate.batch_ref,{fingerprint,count:candidate.event_count});
      this.count+=candidate.event_count;
      return {decision:'LAB_ACCEPTED',reason:'FAKE_COMMIT',simulated_occurrences:candidate.event_count,
        ack_allowed:false,production_authorized:false};
    }catch{return deny('MALFORMED');}
  }
}
