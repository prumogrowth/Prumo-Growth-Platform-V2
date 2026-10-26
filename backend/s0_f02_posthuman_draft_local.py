"""S0-only F02 POST-HUMAN REVIEW DRAFT. No queue, send or real consent.

Requires an existing separately recorded synthetic S0 manager intent, S0/F03
physical preflight, S1 manager session and S0 catalog. The draft is written
ONLY to a separate private PG17 local table. It cannot feed C04 or Meta.

For this E04 slice, legacy chains (active OR canceled) strictly require a
future independent reconciliation path and are never promoted to a draft.
No chain is not claimed as positive evidence of historical cancellation.
The synthetic 24h..7d window is a fixture, NOT an approved business policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID
import hashlib
import json
import re

from backend.identity_boundary import Principal,Denied
from backend.s0_f02_posthuman_preview_local import (
    S0F02LocalPostHumanPreview,PreviewState,_MANAGER,_TEMPLATE
)
from backend.s0_f02_posthuman_intent_local import (
    PostHumanIntentRequest,_valid as _valid_intent,_proposal_hash
)
from backend.s0_f02_posthuman_compatibility_local import (
    _candidate,_C04,_CHANNEL,_HUMAN
)
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL
from backend.s0_f03_operational_contracts_local import ProposedField
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal

class DraftState(str,Enum):
    DRAFT_RECORDED_REVIEW_ONLY='DRAFT_RECORDED_REVIEW_ONLY'
    DRAFT_REPLAY_REVIEW_ONLY='DRAFT_REPLAY_REVIEW_ONLY'
    LEGACY_RECONCILIATION_REQUIRED='LEGACY_RECONCILIATION_REQUIRED'
    S0_REVIEW_REQUIRED='S0_REVIEW_REQUIRED'
    MANAGER_S1_REQUIRED='MANAGER_S1_REQUIRED'
    POLICY_TIME_REVIEW_REQUIRED='POLICY_TIME_REVIEW_REQUIRED'
    TEMPLATE_STALE_REVIEW_REQUIRED='TEMPLATE_STALE_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED='CONFLICT_REVIEW_REQUIRED'
    DENIED='DENIED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class DraftResult:
    state:DraftState

@dataclass(frozen=True)
class PostHumanDraftRequest:
    intent:PostHumanIntentRequest
    proposed_at:datetime
    draft_key:str

_LEAD="""select id from public.leads_loja where concessionaria_id=%s::uuid
 and id=%s::uuid for update"""
_INTENT="""select caso_id,lead_id,canal_id,template_id,gestor_id,sessao_id,
 tentativa_s2,versao_template,categoria,versao_politica,
 evidencia_gestor_sha256,proposta_sha256,chave_idempotencia
 from prumo_private.cfi01_f02_posthuman_intents_local
 where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid
 for share"""
_LEGACY="""select 1 from public.planos_recontato_sinteticos p
 where p.concessionaria_id=%s::uuid and p.lead_id=%s::uuid
 union all
 select 1 from prumo_private.cfi01_f02_c04_origin_ledger_local o
 where o.concessionaria_id=%s::uuid and o.lead_id=%s::uuid
  and o.tipo='PLAN' limit 1"""
_NOW="""select statement_timestamp()"""
_EXIST="""select caso_id,lead_id,canal_id,template_id,gestor_id,sessao_id,
 tentativa_s2,versao_template,categoria,versao_politica,
 horario_proposto,proposta_sha256,chave_idempotencia
 from prumo_private.cfi01_f02_posthuman_draft_local
 where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid
 for update"""
_DUP="""select 1 from prumo_private.cfi01_f02_posthuman_draft_local
 where concessionaria_id=%s::uuid and chave_idempotencia=%s::text
 for update"""
_INSERT="""insert into prumo_private.cfi01_f02_posthuman_draft_local
(concessionaria_id,evento_fechamento_id,caso_id,lead_id,canal_id,
template_id,gestor_id,sessao_id,tentativa_s2,versao_template,
categoria,versao_politica,horario_proposto,proposta_sha256,chave_idempotencia)
values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,
%s::uuid,%s::uuid,%s::uuid,%s::text,%s::text,
%s::text,%s::text,%s::timestamptz,%s::text,%s::text)
on conflict do nothing returning id"""

def _valid_request(value:object)->bool:
    return (type(value) is PostHumanDraftRequest and
        _valid_intent(value.intent) and
        type(value.proposed_at) is datetime and
        value.proposed_at.tzinfo is not None and
        value.proposed_at.utcoffset() is not None and
        type(value.draft_key) is str and
        re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',value.draft_key) is not None)

def _hash(req:PostHumanDraftRequest,receipt,js:dict,channel_ref:str)->str:
    body=[receipt.store_ref,receipt.closure_event_ref,receipt.case_ref,
          channel_ref,req.intent.preview.template_ref,req.intent.preview.policy_version,
          req.intent.idempotency_key,req.intent.manager_evidence_sha256,
          js['attemptId'],js['templateId'],js['templateVersion'],js['category'],
          req.proposed_at.isoformat(),req.draft_key]
    return hashlib.sha256(json.dumps(body,separators=(',',':')).encode()).hexdigest()

class S0F02PostHumanDraftLocal:
    def __init__(self,preview:S0F02LocalPostHumanPreview):
        if type(preview) is not S0F02LocalPostHumanPreview:
            raise TypeError('S0 physical post-human preview required')
        self._preview=preview
        self._dsn=preview._dsn

    def record(self,authorization:str,binding:S0F03BoundReceiptLocal,
               key_version:str,secret:bytes,version:VersionVector,
               request_ref:str,fields:tuple[ProposedField,...],
               f03_output:dict,f03_proposal:dict,
               s2_f02_result:dict,channel_ref:str,
               request:PostHumanDraftRequest)->DraftResult:
        if (not _valid_request(request) or not _candidate(s2_f02_result)
            or type(channel_ref) is not str):
            return DraftResult(DraftState.DENIED)
        try:
            actor=self._preview._identity.verify(authorization)
            if type(actor) is not Principal:
                return DraftResult(DraftState.DENIED)
        except Denied:
            return DraftResult(DraftState.DENIED)
        except Exception:
            return DraftResult(DraftState.UNAVAILABLE)
        initial=self._preview.inspect(authorization,binding,key_version,
              secret,version,request_ref,fields,f03_output,f03_proposal,
              s2_f02_result,channel_ref,request.intent.preview)
        if initial.state is not PreviewState.PREVIEW_ONLY_LEGACY_C04_BLOCKED:
            if initial.state is PreviewState.UNAVAILABLE:
                return DraftResult(DraftState.UNAVAILABLE)
            if initial.state is PreviewState.MANAGER_S1_REQUIRED:
                return DraftResult(DraftState.MANAGER_S1_REQUIRED)
            return DraftResult(DraftState.S0_REVIEW_REQUIRED)
        r=binding.receipt
        digest=_hash(request,r,s2_f02_result,channel_ref)
        expected_intent_hash=_proposal_hash(s2_f02_result,request.intent,r,channel_ref)
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_CONTEXT_SQL,(r.closure_event_ref,r.store_ref,
                      r.case_ref,r.snapshot_sha256,r.expected_cycle_version,
                      r.message_watermark,r.message_count))
                    ctx=cur.fetchall()
                    if len(ctx)!=1 or type(ctx[0][0]) is not UUID:
                        return DraftResult(DraftState.S0_REVIEW_REQUIRED)
                    lead,_=ctx[0]
                    cur.execute(_LEAD,(r.store_ref,lead))
                    if cur.fetchone() is None:
                        return DraftResult(DraftState.S0_REVIEW_REQUIRED)
                    cur.execute(_MANAGER,(r.store_ref,actor.session_id,actor.actor_id))
                    if cur.fetchone() is None:
                        return DraftResult(DraftState.MANAGER_S1_REQUIRED)
                    cur.execute(_CHANNEL,(r.message_watermark,r.store_ref,
                                          r.case_ref,lead,channel_ref))
                    if cur.fetchone() is None:
                        return DraftResult(DraftState.S0_REVIEW_REQUIRED)
                    cur.execute(_HUMAN,(r.case_ref,r.store_ref,lead,
                                        r.expected_cycle_version))
                    if cur.fetchone() is None:
                        return DraftResult(DraftState.S0_REVIEW_REQUIRED)
                    cur.execute(_C04,(r.store_ref,lead,channel_ref))
                    eligibility=cur.fetchone()
                    if (eligibility is None or type(eligibility[0]) is not dict
                        or eligibility[0].get('decisao')!='ELEGIVEL_SOMENTE_SIMULACAO'):
                        return DraftResult(DraftState.S0_REVIEW_REQUIRED)
                    cur.execute(_LEGACY,(r.store_ref,lead,r.store_ref,lead))
                    if cur.fetchone() is not None:
                        return DraftResult(DraftState.LEGACY_RECONCILIATION_REQUIRED)
                    cur.execute(_INTENT,(r.store_ref,r.closure_event_ref))
                    stored=cur.fetchone()
                    exact=(r.case_ref,str(lead),channel_ref,
                       request.intent.preview.template_ref,str(actor.actor_id),
                       str(actor.session_id),s2_f02_result['attemptId'],
                       s2_f02_result['templateVersion'],s2_f02_result['category'],
                       request.intent.preview.policy_version,
                       request.intent.manager_evidence_sha256,
                       expected_intent_hash,request.intent.idempotency_key)
                    if stored is None or tuple(str(v) for v in stored)!=exact:
                        return DraftResult(DraftState.S0_REVIEW_REQUIRED)
                    cur.execute(_TEMPLATE,(r.store_ref,request.intent.preview.template_ref))
                    cat=cur.fetchone()
                    if (cat is None or cat[2] is not True or cat[3]!='post_human'
                        or cat[0]!=s2_f02_result['templateId']
                        or f'v{cat[1]}'!=s2_f02_result['templateVersion']
                        or cat[4]!=s2_f02_result['category']
                        or cat[5]!=request.intent.preview.policy_version):
                        return DraftResult(DraftState.TEMPLATE_STALE_REVIEW_REQUIRED)
                    cur.execute(_NOW);now=cur.fetchone()[0]
                    delta=(request.proposed_at-now).total_seconds()
                    if not (86400<=delta<=604800):
                        return DraftResult(DraftState.POLICY_TIME_REVIEW_REQUIRED)
                    cur.execute(_EXIST,(r.store_ref,r.closure_event_ref))
                    previous=cur.fetchone()
                    exact_draft=(r.case_ref,str(lead),channel_ref,
                      request.intent.preview.template_ref,str(actor.actor_id),
                      str(actor.session_id),s2_f02_result['attemptId'],
                      s2_f02_result['templateVersion'],s2_f02_result['category'],
                      request.intent.preview.policy_version,
                      request.proposed_at,digest,request.draft_key)
                    if previous is not None:
                        return DraftResult(DraftState.DRAFT_REPLAY_REVIEW_ONLY
                           if tuple(str(v) for v in previous)==tuple(str(v) for v in exact_draft)
                           else DraftState.CONFLICT_REVIEW_REQUIRED)
                    cur.execute(_DUP,(r.store_ref,request.draft_key))
                    if cur.fetchone() is not None:
                        return DraftResult(DraftState.CONFLICT_REVIEW_REQUIRED)
                    cur.execute(_INSERT,(r.store_ref,r.closure_event_ref,r.case_ref,
                      lead,channel_ref,request.intent.preview.template_ref,
                      actor.actor_id,actor.session_id,s2_f02_result['attemptId'],
                      s2_f02_result['templateVersion'],s2_f02_result['category'],
                      request.intent.preview.policy_version,request.proposed_at,
                      digest,request.draft_key))
                    if cur.fetchone() is None:
                        return DraftResult(DraftState.CONFLICT_REVIEW_REQUIRED)
            return DraftResult(DraftState.DRAFT_RECORDED_REVIEW_ONLY)
        except Exception:
            return DraftResult(DraftState.UNAVAILABLE)
