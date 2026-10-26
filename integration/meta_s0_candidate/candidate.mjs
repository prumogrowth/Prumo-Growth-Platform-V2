/**
 * Isolated executable MODEL of four candidate contracts.
 * Caller supplies ONLY laboratory keys/stores. No operational adapter exists.
 * Transaction/lock behavior is a serialized model, NOT PostgreSQL/S1 evidence.
 */
import {randomUUID} from 'node:crypto';
import {classifyCloudWireObservation} from '../../integrations/whatsapp-meta/cloud-wire-observation.ts';
import {inspectCloudWebhookForHandoff} from '../../integrations/whatsapp-meta/cloud-webhook-handoff.ts';
import {FLAGS,sha,ident,revision,exact,decodeBase64,parseEnvelope,
  verifyMac,response,InputRejected} from './protocol.mjs';

const OPS=new Set(['reserve','begin','observe','read','review','append_batch']);
const owns=(k,a)=>k.tenant_ref===a.tenant_ref && k.channel_ref===a.channel_ref
  && k.route_ref===a.route_ref;
const eligible=a=>!a.cancelled && !a.opted_out
  && ['s0','s1','assignment','consent','window','template','catalog','purpose','destination']
    .every(g=>a.gates[g]===true);
const binding=(s,k,a)=>owns(k,a) && s.routes[a.route_ref]?.active===true
  && k.route_revision===s.routes[a.route_ref].revision
  && a.route_revision===k.route_revision;
const tuple=(...parts)=>JSON.stringify(parts);
const fail=()=>{throw new InputRejected('INPUT_REJECTED');};

function wireObservation(raw) {
  if (exact(raw,['kind']) && ['transport_error','not_attempted'].includes(raw.kind))
    return {kind:raw.kind};
  if (!exact(raw,['kind','http_status','headers','response_base64'])
    || raw.kind!=='http_response') fail();
  return {kind:raw.kind,http_status:raw.http_status,headers:raw.headers,
    response_bytes:decodeBase64(raw.response_base64,65536)};
}
function attemptFor(s,k,ref) {
  if (!ident(ref)) return null;
  const a=s.attempts[ref], authority=a&&s.authorities[a.intent_ref];
  return a && authority && binding(s,k,authority) ? {a,authority} : null;
}
function evidenceSummary(a) {
  if (a.quarantined) return 'QUARANTINED_REVIEW';
  const kinds=a.evidence.map(e=>e.send_state);
  if (kinds.includes('API_ACCEPTED')) return 'API_ACCEPTED_NOT_DELIVERED';
  if (kinds.includes('PROVIDER_REJECTED')) return 'PROVIDER_REJECTED_NO_RETRY';
  return a.phase==='RESERVED' || a.phase==='CANCELLED'
    ? a.phase : 'EXTERNAL_UNCERTAIN';
}
export function newFixtureState({keys,routes,authorities}) {
  return structuredClone({version:1,keys,routes,authorities,attempts:{},
    intents:{}, idempotency:{}, nonces:{}, conflicts:[], batches:{}, raw_receipts:{}, audit:[]});
}
export class CandidateLab {
  #store; #keys; #appSecrets; #clock;
  constructor({optIn,store,keys,appSecrets,clock=Date.now}) {
    if (optIn!=='DISPOSABLE_META_S0_LAB_ONLY') throw Error('LAB_OPT_IN_REQUIRED');
    this.#store=store;
    this.#keys=new Map(Object.entries(keys).map(([id,k])=>[id,Buffer.from(k)]));
    if ([...this.#keys.values()].some(k=>k.length!==32)) throw Error('LAB_KEY_REQUIRED');
    this.#appSecrets={...appSecrets};
    this.#clock=clock;
  }
  async call(raw,proof) {
    let parsed;
    try {
      parsed=parseEnvelope(raw);
      // Snapshot caller-owned proof too, before any await.
      if (!exact(proof,['kind','key_id','mac_sha256'])) return response('M2M_DENIED');
      proof={...proof};
    } catch { return response('INPUT_REJECTED'); }
    const {payload:p,bytes,digest}=parsed;
    try {
      const result=await this.#store.transact(async s=>{
        const k=s.keys[proof.key_id], secret=this.#keys.get(proof.key_id);
        const now=this.#clock();
        if (!k || k.kind!=='LAB_SERVICE' || !k.active || !secret
          || !verifyMac(secret,proof,bytes) || !OPS.has(p.operation)
          || !k.operations.includes(p.operation)
          || !Number.isSafeInteger(now) || now<p.issued_at_ms || now>=p.expires_at_ms
          || now<k.not_before_ms || now>=k.not_after_ms
          || k.issuer!=='LAB_META_SERVICE' || k.audience!=='LAB_S0_CANDIDATE')
          return response('M2M_DENIED',p);
        const route=s.routes[k.route_ref];
        if (!route?.active || route.revision!==k.route_revision)
          return response('TECHNICAL_BINDING_REVOKED',p);
        const nk=tuple(k.issuer,proof.key_id,p.nonce);
        if (s.nonces[nk]) return response(
          s.nonces[nk]===digest?'NONCE_REPLAY_NO_EXECUTION':'NONCE_CONFLICT',p);
        const outcome=await this.#execute(s,k,p);
        // Result validation occurs BEFORE nonce/audit/persistence/commit.
        if (typeof outcome.code!=='string' || Object.keys(FLAGS).some(x=>outcome[x]!==false))
          throw Error('INVALID_RESULT');
        s.nonces[nk]=digest;
        s.audit.push({request_id:p.request_id,correlation_id:p.correlation_id,
          key_id:proof.key_id,operation:p.operation,code:outcome.code,
          tenant_ref:k.tenant_ref,channel_ref:k.channel_ref,route_ref:k.route_ref,
          route_revision:k.route_revision,envelope_sha256:digest,
          requested_attempt_ref:p.body?.attempt_ref??null,
          requested_intent_ref:p.body?.intent_ref??null,
          receipt_ref:outcome.receipt_ref??null});
        return outcome;
      });
      // The adapter must resolve ONLY after the full durable commit. Even a
      // successful in-memory model must never advertise durable lab ACK.
      if (result.lab_receipt_committed===true && this.#store.durable===true)
        return Object.freeze({...result,lab_ack_ready:true});
      return result;
    } catch (error) {
      if (error instanceof InputRejected) return response('INPUT_REJECTED',p);
      // No rollback/commit claim at this boundary: connection/commit may be lost.
      return response('COMMIT_OR_RESULT_UNKNOWN',p);
    }
  }
  async #execute(s,k,p) {
    const b=p.body, out=(code,x={})=>response(code,p,x);
    if (p.operation==='reserve') {
      if (!exact(b,['intent_ref','idempotency_key','expected_revision'])
        || !ident(b.intent_ref)||!ident(b.idempotency_key)||!revision(b.expected_revision)) fail();
      const a=s.authorities[b.intent_ref];
      if (!a || !binding(s,k,a)) return out('SCOPE_DENIED');
      const ik=tuple(k.tenant_ref,k.channel_ref,b.idempotency_key);
      const fingerprint=sha(JSON.stringify([b.intent_ref,b.expected_revision,
        a.route_ref,a.route_revision,a.recipient_ref,a.purpose_ref,a.content_sha256,
        a.catalog_revision,a.template_revision]));
      const prior=s.idempotency[ik];
      if (prior && prior.fingerprint!==fingerprint) return out('IDEMPOTENCY_CONFLICT');
      // All live gates revalidated even on readback of an old reservation.
      if (!eligible(a)) return out('AUTHORITY_REVOKED');
      if (a.revision!==b.expected_revision) return out('STALE_REVISION');
      if (prior) return out('ALREADY_RESERVED_NO_EXECUTION',{attempt_ref:prior.attempt_ref});
      if (s.intents[b.intent_ref]) return out('INTENT_OCCUPIED_NO_RETRY');
      const attempt_ref=randomUUID();
      s.attempts[attempt_ref]={attempt_ref,intent_ref:b.intent_ref,
        revision:a.revision,correlation_ref:randomUUID(),phase:'RESERVED',cancelled:false,quarantined:false,
        evidence:[],reviews:[]};
      s.intents[b.intent_ref]=attempt_ref;
      s.idempotency[ik]={fingerprint,attempt_ref};
      return out('LAB_RESERVED_NO_SEND_RIGHTS',{attempt_ref});
    }
    if (p.operation==='append_batch') return this.#append(s,k,p);
    if (!b || !ident(b.attempt_ref)) fail();
    const pair=attemptFor(s,k,b.attempt_ref);
    if (!pair) return out('SCOPE_DENIED');
    const {a,authority}=pair;
    if (p.operation==='begin') {
      if (!exact(b,['attempt_ref','expected_revision'])||!revision(b.expected_revision)) fail();
      if (!eligible(authority)||a.cancelled) return out('AUTHORITY_REVOKED');
      if (b.expected_revision!==authority.revision || a.revision!==authority.revision)
        return out('STALE_REVISION');
      if (a.phase!=='RESERVED') return out('BEGIN_ALREADY_CONSUMED_NO_RETRY');
      a.phase='EXTERNAL_POSSIBLE';
      return out('LAB_BEGIN_RECORDED_NO_SEND_RIGHTS',{attempt_ref:a.attempt_ref});
    }
    if (p.operation==='read') {
      if (!exact(b,['attempt_ref'])) fail();
      return out('READ_ONLY_NO_RETRY',{attempt_ref:a.attempt_ref,
        state:evidenceSummary(a),cancelled:a.cancelled,
        evidence_count:a.evidence.length,review_count:a.reviews.length});
    }
    if (p.operation==='review') {
      if (!exact(b,['attempt_ref','decision_ref','evidence_refs'])
        || !ident(b.decision_ref)||!Array.isArray(b.evidence_refs)
        || !b.evidence_refs.length||b.evidence_refs.length>100
        || !b.evidence_refs.every(x=>ident(x)&&a.evidence.some(e=>e.ref===x))) fail();
      const oldReview=a.reviews.find(r=>r.decision_ref===b.decision_ref);
      if (oldReview && JSON.stringify(oldReview.evidence_refs)!==JSON.stringify(b.evidence_refs)) {
        a.quarantined=true;
        return out('REVIEW_CONFLICT_QUARANTINED');
      }
      if (!oldReview)
        a.reviews.push({decision_ref:b.decision_ref,evidence_refs:[...b.evidence_refs]});
      return out('REVIEW_ANNOTATED_NO_RELEASE',{attempt_ref:a.attempt_ref});
    }
    if (p.operation==='observe') {
      if (!exact(b,['attempt_ref','observation_ref','wire'])||!ident(b.observation_ref)) fail();
      // Evidence is allowed after S0/S1 cancellation, under a distinct current
      // TECHNICAL ACL; it never revives the old commercial permission.
      if (!['EXTERNAL_POSSIBLE','EXTERNAL_UNCERTAIN'].includes(a.phase))
        return out('EXTERNAL_BEGIN_REQUIRED');
      const wire=wireObservation(b.wire);
      const d=classifyCloudWireObservation(a.attempt_ref,a.correlation_ref,wire);
      const fingerprint=sha(JSON.stringify(b.wire));
      const existing=a.evidence.find(e=>e.ref===b.observation_ref);
      if (existing) {
        if (existing.fingerprint!==fingerprint) {
          a.quarantined=true;
          s.conflicts.push({kind:'OBSERVATION_REF_CONFLICT',attempt_ref:a.attempt_ref,
            observation_ref:b.observation_ref,expected:existing.fingerprint,received:fingerprint});
        }
        return out(existing.fingerprint===fingerprint
          ? 'OBSERVATION_REPLAY_NO_RETRY':'EVIDENCE_CONFLICT_QUARANTINED');
      }
      // not_attempted after begin cannot prove no bytes reached a provider.
      const kind=d.send_state??'UNCERTAIN_EXTERNAL';
      const accepted=a.evidence.filter(e=>e.send_state==='API_ACCEPTED');
      if ((kind==='API_ACCEPTED' && a.evidence.some(e=>e.send_state==='PROVIDER_REJECTED'))
        || (kind==='PROVIDER_REJECTED' && accepted.length)
        || (kind==='API_ACCEPTED' && accepted.some(e=>e.provider_message_id!==d.provider_message_id)))
        a.quarantined=true;
      a.evidence.push({ref:b.observation_ref,fingerprint,correlation_ref:a.correlation_ref,send_state:kind,
        provider_message_id:d.provider_message_id,http_status:d.http_status,
        meta_error_code:d.meta_error_code,meta_error_subcode:d.meta_error_subcode});
      a.phase='EXTERNAL_UNCERTAIN';
      return out(a.quarantined?'EVIDENCE_CONFLICT_QUARANTINED':'OBSERVED_NO_RETRY',
        {attempt_ref:a.attempt_ref,state:evidenceSummary(a)});
    }
    fail();
  }
  async #append(s,k,p) {
    const b=p.body, out=(code,x={})=>response(code,p,x);
    if (!exact(b,['batch_ref','route_revision','raw_base64','meta_signature'])
      || !ident(b.batch_ref)||!revision(b.route_revision)) fail();
    const route=s.routes[k.route_ref];
    if (b.route_revision!==route.revision) return out('STALE_ROUTE');
    const raw=decodeBase64(b.raw_base64,262144);
    if (typeof b.meta_signature!=='string') fail();
    const inspected=await inspectCloudWebhookForHandoff(raw,b.meta_signature,
      this.#appSecrets[k.route_ref],{
        waba_id:route.waba_id,phone_number_id:route.phone_number_id,
        revision:Number(route.revision)}, {maxBodyBytes:262144,maxEvents:100});
    if (inspected.outcome!=='AUTHENTICATED_NOT_DURABLE') return out('META_BATCH_DENIED');
    const bk=tuple(k.tenant_ref,k.channel_ref,k.route_ref,route.revision,b.batch_ref);
    const rk=tuple(k.tenant_ref,k.channel_ref,k.route_ref,route.revision,inspected.raw_sha256);
    const prior=s.batches[bk];
    if (prior && prior.raw_sha256!==inspected.raw_sha256) {
      s.conflicts.push({kind:'BATCH_REF_CONFLICT',batch_key:bk,
        expected:prior.raw_sha256,received:inspected.raw_sha256});
      return out('BATCH_IDEMPOTENCY_CONFLICT_NO_ACK');
    }
    const priorRaw=s.raw_receipts[rk];
    const receipt=prior??priorRaw??{
      receipt_ref:randomUUID(), raw_sha256:inspected.raw_sha256,
      route_revision:route.revision, observations:inspected.observations.map((x,i)=>({
        index:i, observation:x, state:'ARCHIVED_UNVERIFIED',
      })),
    };
    // All items and the batch receipt, nonce, and audit commit in ONE snapshot.
    s.batches[bk]=receipt;
    s.raw_receipts[rk]=receipt;
    return out(prior||priorRaw
      ? 'BATCH_ALREADY_DURABLE_CANDIDATE':'BATCH_COMMITTED_CANDIDATE',{
      lab_receipt_committed:true,receipt_ref:receipt.receipt_ref,
      raw_sha256:receipt.raw_sha256,route_revision:receipt.route_revision,
      items:receipt.observations.map(x=>({index:x.index,state:x.state})),
    });
  }
  // Internal fixture control, deliberately NOT a body command or public route.
  async revokeFixture(kind,ref) {
    if (!['S0','S1','CANCEL','OPT_OUT','KEY','ROUTE'].includes(kind)) throw Error('INVALID_FIXTURE');
    return this.#store.transact(s=>{
      if (kind==='KEY') {s.keys[ref].active=false; return;}
      if (kind==='ROUTE') {
        s.routes[ref].active=false;
        s.routes[ref].revision=(BigInt(s.routes[ref].revision)+1n).toString();
        return;
      }
      const x=s.authorities[ref];
      x.revision=(BigInt(x.revision)+1n).toString();
      if (kind==='S0') x.gates.s0=false;
      if (kind==='S1') x.gates.s1=false;
      if (kind==='CANCEL') x.cancelled=true;
      if (kind==='OPT_OUT') x.opted_out=true;
      for (const a of Object.values(s.attempts).filter(a=>a.intent_ref===ref)) {
        a.cancelled=true;
        if (a.phase==='RESERVED') a.phase='CANCELLED';
        else a.phase='EXTERNAL_UNCERTAIN';
      }
    });
  }
}
