"""E04 S0-only sealed witness of LOCAL canceled C08 attempts, NOT external.

A preexisting synthetic manager intent does not create or cancel plans. This
gate reads independently the physical S0/C04 plan, attempted reservations and
the corresponding local cancellation events, and anchors a canonical HMAC
snapshot to the S0 closure and authenticated manager.

Even positive result is a forensic audit: it is NOT a real Meta revoke,
not a proof that no external message was sent, and never an authorization for
new post-human planning or delivery. Zero plans is not canceled evidence.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import json
import re
import uuid

from backend.identity_boundary import Principal, Denied
from backend.s0_f02_posthuman_intent_local import (
  S0F02LocalPostHumanIntentStore,PostHumanIntentRequest,_valid as _valid_intent,
  _proposal_hash
)
from backend.s0_f02_posthuman_preview_local import _MANAGER,PreviewState
from backend.s0_f02_posthuman_compatibility_local import _C04, _CHANNEL, _HUMAN
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL
from backend.s0_f03_operational_contracts_local import ProposedField
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal

_LEAD="""select 1 from public.leads_loja where concessionaria_id=%s::uuid
 and id=%s::uuid for update"""
_INTENT="""select caso_id,lead_id,canal_id,gestor_id,sessao_id,
 template_id,versao_politica,tentativa_s2,versao_template,categoria,
 decisao,evidencia_gestor_sha256,proposta_sha256,chave_idempotencia
 from prumo_private.cfi01_f02_posthuman_intents_local
 where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid
 for share"""
_PLANS="""select p.id,p.ciclo_id,p.estado,p.versao,p.motivo_cancelamento,
 p.cancelado_em from public.planos_recontato_sinteticos p
 where p.concessionaria_id=%s::uuid and p.lead_id=%s::uuid
 order by p.id for update"""
_ATTEMPTS="""select e.id,e.plano_id,e.estado,e.reservado_em,e.cancelado_em
 from public.envios_template_sinteticos e
 join public.planos_recontato_sinteticos p
  on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
 where e.concessionaria_id=%s::uuid and p.lead_id=%s::uuid
 order by e.id for update of e"""
_EVENTS="""select ev.id,ev.envio_id,ev.estado_anterior,ev.estado_posterior,
 ev.motivo,ev.criado_em
 from public.eventos_envio_template_sinteticos ev
 join public.envios_template_sinteticos e on e.id=ev.envio_id
  and e.concessionaria_id=ev.concessionaria_id
 join public.planos_recontato_sinteticos p on p.id=e.plano_id
  and p.concessionaria_id=e.concessionaria_id
 where ev.concessionaria_id=%s::uuid and p.lead_id=%s::uuid
 order by ev.envio_id,ev.criado_em,ev.id"""
_EXIST="""select gestor_id,sessao_id,chave_versao,cadeia_sha256,
 prova_hmac_sha256,planos_cancelados,tentativas_canceladas
 from prumo_private.cfi01_f02_legacy_cancel_witness_local
 where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid
 for update"""
_INSERT="""insert into prumo_private.cfi01_f02_legacy_cancel_witness_local
 (concessionaria_id,evento_fechamento_id,gestor_id,sessao_id,chave_versao,
 cadeia_sha256,prova_hmac_sha256,planos_cancelados,tentativas_canceladas)
 values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::text,
 %s::text,%s::text,%s::integer,%s::integer)
 on conflict do nothing returning concessionaria_id"""

class CancelWitnessState(str,Enum):
    LOCAL_CHAIN_ATTESTED_AUDIT_ONLY='LOCAL_CHAIN_ATTESTED_AUDIT_ONLY'
    ALREADY_ATTESTED_AUDIT_ONLY='ALREADY_ATTESTED_AUDIT_ONLY'
    NO_LEGACY_CHAIN='NO_LEGACY_CHAIN'
    ACTIVE_LEGACY_CHAIN='ACTIVE_LEGACY_CHAIN'
    INCOMPLETE_LOCAL_CANCELLATION='INCOMPLETE_LOCAL_CANCELLATION'
    RESERVED_PREVIOUSLY_EXTERNAL_UNKNOWN='RESERVED_PREVIOUSLY_EXTERNAL_UNKNOWN'
    STALE_WITNESS_REVIEW_REQUIRED='STALE_WITNESS_REVIEW_REQUIRED'
    S0_REVIEW_REQUIRED='S0_REVIEW_REQUIRED'
    DENIED='DENIED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class CancelWitnessResult:
    state:CancelWitnessState

def _canonical(plan_rows,attempt_rows,event_rows):
    def convert(rows):
        return [[v.isoformat() if hasattr(v,'isoformat') else str(v)
                 if isinstance(v,uuid.UUID) else v.isoformat()
                 if hasattr(v,'isoformat') else v
                 for v in row] for row in rows]
    return json.dumps([convert(plan_rows),convert(attempt_rows),
                       convert(event_rows)],separators=(',',':'),
                      ensure_ascii=False).encode('utf-8')

def _seal(secret,shop,closure,actor,session,key,chain_sha):
    if type(secret) is not bytes or len(secret)<32 or type(key) is not str or not re.fullmatch(
        r'[A-Za-z0-9_.:-]{8,80}',key):
        return None
    raw=json.dumps([shop,closure,str(actor),str(session),key,chain_sha],
                   separators=(',',':')).encode()
    return hmac.new(secret,raw,hashlib.sha256).hexdigest()

def _verify_chain(plan_rows,attempt_rows,event_rows):
    if not plan_rows:return CancelWitnessState.NO_LEGACY_CHAIN
    if len(plan_rows)>100 or len(attempt_rows)>500 or len(event_rows)>1000:
        return CancelWitnessState.INCOMPLETE_LOCAL_CANCELLATION
    if any(p[2]=='ativo' for p in plan_rows):
        return CancelWitnessState.ACTIVE_LEGACY_CHAIN
    if any(p[2]!='cancelado' or p[3]<2 or
           p[4] not in ('resposta_cliente','handoff','opt_out_simulado',
                        'desfecho','cancelamento_gestor') or p[5] is None
           for p in plan_rows):
        return CancelWitnessState.INCOMPLETE_LOCAL_CANCELLATION
    if not attempt_rows:return CancelWitnessState.INCOMPLETE_LOCAL_CANCELLATION
    plan_ids={p[0] for p in plan_rows}
    reasons={p[0]:p[4] for p in plan_rows}
    events={}
    for ev in event_rows:
        events.setdefault(ev[1],[]).append(ev)
    for a in attempt_rows:
        if a[1] not in plan_ids or a[2]!='cancelado' or a[4] is None:
            return CancelWitnessState.INCOMPLETE_LOCAL_CANCELLATION
        proof=[e for e in events.get(a[0],[])
               if e[3]=='cancelado' and e[4]==reasons[a[1]]
               and e[2] in ('programado','reservado')]
        if len(proof)!=1 or a[4]<proof[0][5]:
            return CancelWitnessState.INCOMPLETE_LOCAL_CANCELLATION
        if proof[0][2]=='reservado' or a[3] is not None:
            return CancelWitnessState.RESERVED_PREVIOUSLY_EXTERNAL_UNKNOWN
    return CancelWitnessState.LOCAL_CHAIN_ATTESTED_AUDIT_ONLY

class S0F02LocalLegacyCancellationWitness:
    def __init__(self,intent:S0F02LocalPostHumanIntentStore):
        if type(intent) is not S0F02LocalPostHumanIntentStore:
            raise TypeError('requires the physical S0 post-human intent store')
        self._intent=intent
        self._dsn=intent._dsn

    def inspect_and_seal(self,authorization:str,binding:S0F03BoundReceiptLocal,
      key_version:str,secret:bytes,version:VersionVector,
      request_ref:str,fields:tuple[ProposedField,...],
      f03_output:dict,f03_proposal:dict,s2_f02_result:dict,
      channel_ref:str,request:PostHumanIntentRequest)->CancelWitnessResult:
        from backend.s0_f02_posthuman_compatibility_local import _candidate
        if (not _valid_intent(request) or not _candidate(s2_f02_result)
            or type(channel_ref) is not str or _seal(secret,'s','c','a','b',
                                                     key_version,'a'*64) is None):
            return CancelWitnessResult(CancelWitnessState.DENIED)
        preview=self._intent._preview
        try:
            principal=preview._identity.verify(authorization)
            if type(principal) is not Principal:
                return CancelWitnessResult(CancelWitnessState.DENIED)
        except Denied:
            return CancelWitnessResult(CancelWitnessState.DENIED)
        except Exception:
            return CancelWitnessResult(CancelWitnessState.UNAVAILABLE)
        p=preview.inspect(authorization,binding,key_version,secret,
                          version,request_ref,fields,f03_output,f03_proposal,
                          s2_f02_result,channel_ref,request.preview)
        if p.state is not PreviewState.PREVIEW_ONLY_LEGACY_C04_BLOCKED:
            return CancelWitnessResult(
                CancelWitnessState.UNAVAILABLE if p.state is PreviewState.UNAVAILABLE
                else CancelWitnessState.S0_REVIEW_REQUIRED)
        r=binding.receipt
        digest=_proposal_hash(s2_f02_result,request,r,channel_ref)
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_CONTEXT_SQL,(r.closure_event_ref,r.store_ref,
                        r.case_ref,r.snapshot_sha256,r.expected_cycle_version,
                        r.message_watermark,r.message_count))
                    ctx=cur.fetchall()
                    if len(ctx)!=1 or type(ctx[0][0]) is not uuid.UUID:
                        return CancelWitnessResult(CancelWitnessState.S0_REVIEW_REQUIRED)
                    lead,_cutoff=ctx[0]
                    cur.execute(_LEAD,(r.store_ref,lead))
                    if cur.fetchone() is None:
                        return CancelWitnessResult(CancelWitnessState.S0_REVIEW_REQUIRED)
                    cur.execute(_MANAGER,(r.store_ref,principal.session_id,
                                          principal.actor_id))
                    if cur.fetchone() is None:
                        return CancelWitnessResult(CancelWitnessState.S0_REVIEW_REQUIRED)
                    cur.execute(_CHANNEL,(r.message_watermark,r.store_ref,
                         r.case_ref,lead,channel_ref))
                    if cur.fetchone() is None:
                        return CancelWitnessResult(CancelWitnessState.S0_REVIEW_REQUIRED)
                    cur.execute(_HUMAN,(r.case_ref,r.store_ref,lead,
                                         r.expected_cycle_version))
                    if cur.fetchone() is None:
                        return CancelWitnessResult(CancelWitnessState.S0_REVIEW_REQUIRED)
                    cur.execute(_C04,(r.store_ref,lead,channel_ref))
                    contact=cur.fetchone()
                    if (contact is None or type(contact[0]) is not dict or
                        contact[0].get('decisao')!='ELEGIVEL_SOMENTE_SIMULACAO'):
                        return CancelWitnessResult(CancelWitnessState.S0_REVIEW_REQUIRED)
                    cur.execute(_INTENT,(r.store_ref,r.closure_event_ref))
                    signed=cur.fetchone()
                    expected=(r.case_ref,str(lead),channel_ref,
                              str(principal.actor_id),str(principal.session_id),
                              request.preview.template_ref,
                              request.preview.policy_version,s2_f02_result['attemptId'],
                              s2_f02_result['templateVersion'],s2_f02_result['category'],
                              request.decision,request.manager_evidence_sha256,
                              digest,request.idempotency_key)
                    if signed is None or tuple(str(v) for v in signed)!=expected:
                        return CancelWitnessResult(CancelWitnessState.S0_REVIEW_REQUIRED)
                    cur.execute(_PLANS,(r.store_ref,lead));plans=cur.fetchall()
                    cur.execute(_ATTEMPTS,(r.store_ref,lead));attempts=cur.fetchall()
                    cur.execute(_EVENTS,(r.store_ref,lead));events=cur.fetchall()
                    state=_verify_chain(plans,attempts,events)
                    if state is not CancelWitnessState.LOCAL_CHAIN_ATTESTED_AUDIT_ONLY:
                        return CancelWitnessResult(state)
                    canonical=_canonical(plans,attempts,events)
                    chain_sha=hashlib.sha256(canonical).hexdigest()
                    mac=_seal(secret,r.store_ref,r.closure_event_ref,
                              principal.actor_id,principal.session_id,
                              key_version,chain_sha)
                    cur.execute(_EXIST,(r.store_ref,r.closure_event_ref))
                    previous=cur.fetchone()
                    exact=(str(principal.actor_id),str(principal.session_id),
                            key_version,chain_sha,mac,len(plans),len(attempts))
                    if previous is not None:
                        return CancelWitnessResult(
                            CancelWitnessState.ALREADY_ATTESTED_AUDIT_ONLY
                            if tuple(str(v) for v in previous)==tuple(str(v) for v in exact)
                            else CancelWitnessState.STALE_WITNESS_REVIEW_REQUIRED)
                    cur.execute(_INSERT,(r.store_ref,r.closure_event_ref,
                             principal.actor_id,principal.session_id,key_version,
                             chain_sha,mac,len(plans),len(attempts)))
                    if cur.fetchone() is None:
                        return CancelWitnessResult(
                            CancelWitnessState.STALE_WITNESS_REVIEW_REQUIRED)
            return CancelWitnessResult(CancelWitnessState.LOCAL_CHAIN_ATTESTED_AUDIT_ONLY)
        except Exception:
            return CancelWitnessResult(CancelWitnessState.UNAVAILABLE)
