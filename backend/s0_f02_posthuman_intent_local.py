"""E04 S0 post-human F02 manager INTENT audit (not a schedule or send).

Requires all existing F03/compatibility/preview checks plus fresh S0/S1 manager
session, physical C04 fictional eligibility and opt-out, current immutable
template policy, same lead/case/closure and no active old plan. Serializes
per-lead; replay checks the live state before returning audit-only.

A manager's evidence SHA is a S0-typed explicit-intent *fixture*, NOT the
content of human approval or real consent. The resulting record cannot be
executed by C04. No Meta transport, commercial status or F03 write.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
import uuid

from backend.identity_boundary import Principal,Denied
from backend.s0_f02_posthuman_preview_local import (
    S0F02LocalPostHumanPreview,PostHumanPreviewRequest,PreviewState,
    _MANAGER,_TEMPLATE
)
from backend.s0_f02_posthuman_compatibility_local import _CHANNEL,_HUMAN,_OLD_PLAN,_C04
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_f03_operational_contracts_local import ProposedField
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal

class IntentState(str,Enum):
    RECORDED_AUDIT_ONLY='RECORDED_AUDIT_ONLY'
    ALREADY_RECORDED_AUDIT_ONLY='ALREADY_RECORDED_AUDIT_ONLY'
    DENIED='DENIED'
    S0_REVIEW_REQUIRED='S0_REVIEW_REQUIRED'
    MANAGER_S1_REQUIRED='MANAGER_S1_REQUIRED'
    STALE_REVIEW_REQUIRED='STALE_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED='CONFLICT_REVIEW_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class IntentResult:
    state:IntentState

@dataclass(frozen=True)
class PostHumanIntentRequest:
    preview:PostHumanPreviewRequest
    decision:str
    manager_evidence_sha256:str
    idempotency_key:str

_DECISION='EXPLICIT_REVIEW_SYNTHETIC_ONLY'
_EXIST="""select gestor_id,sessao_id,canal_id,template_id,tentativa_s2,
versao_template,categoria,versao_politica,decisao,evidencia_gestor_sha256,
proposta_sha256,chave_idempotencia,caso_id,lead_id
from prumo_private.cfi01_f02_posthuman_intents_local
where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid
for update"""
_DUP_KEY="""select 1 from prumo_private.cfi01_f02_posthuman_intents_local
where concessionaria_id=%s::uuid and chave_idempotencia=%s::text
for update"""
_LEAD="""select id from public.leads_loja
 where concessionaria_id=%s::uuid and id=%s::uuid for update"""
_INSERT="""insert into prumo_private.cfi01_f02_posthuman_intents_local
(concessionaria_id,evento_fechamento_id,caso_id,lead_id,canal_id,
template_id,gestor_id,sessao_id,tentativa_s2,versao_template,categoria,
versao_politica,decisao,evidencia_gestor_sha256,proposta_sha256,
chave_idempotencia)
values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,
%s::uuid,%s::uuid,%s::uuid,%s::text,%s::text,%s::text,
%s::text,%s::text,%s::text,%s::text,%s::text)
on conflict do nothing returning id"""

def _valid(req:object)->bool:
    return (type(req) is PostHumanIntentRequest
       and type(req.preview) is PostHumanPreviewRequest
       and type(req.decision) is str and req.decision==_DECISION
       and type(req.manager_evidence_sha256) is str and
           re.fullmatch(r'[0-9a-f]{64}',req.manager_evidence_sha256) is not None
       and type(req.idempotency_key) is str and
           re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',req.idempotency_key) is not None)

def _proposal_hash(s2:dict,req:PostHumanIntentRequest,receipt,
                   channel_ref:str)->str:
    payload=[receipt.store_ref,receipt.case_ref,receipt.closure_event_ref,
             channel_ref,req.preview.template_ref,req.preview.policy_version,
             s2['attemptId'],s2['templateId'],s2['templateVersion'],
             s2['category'],_DECISION,req.manager_evidence_sha256]
    return hashlib.sha256(json.dumps(payload,separators=(',',':')).encode()).hexdigest()

class S0F02LocalPostHumanIntentStore:
    def __init__(self,preview:S0F02LocalPostHumanPreview):
        if type(preview) is not S0F02LocalPostHumanPreview:
            raise TypeError('physical S0 F02 preview required')
        self._preview=preview
        self._dsn=preview._dsn

    def record(self,authorization:str,binding:S0F03BoundReceiptLocal,
               key_version:str,secret:bytes,version:VersionVector,
               request_ref:str,fields:tuple[ProposedField,...],
               f03_output:dict,f03_proposal:dict,
               s2_f02_result:dict,channel_ref:str,
               request:PostHumanIntentRequest)->IntentResult:
        from backend.s0_f02_posthuman_compatibility_local import _candidate
        if (not _valid(request) or not _candidate(s2_f02_result)
            or type(channel_ref) is not str):
            return IntentResult(IntentState.DENIED)
        try:
            principal=self._preview._identity.verify(authorization)
            if type(principal) is not Principal:
                return IntentResult(IntentState.DENIED)
        except Denied:
            return IntentResult(IntentState.DENIED)
        except Exception:
            return IntentResult(IntentState.UNAVAILABLE)
        prior=self._preview.inspect(authorization,binding,key_version,secret,
             version,request_ref,fields,f03_output,f03_proposal,
             s2_f02_result,channel_ref,request.preview)
        if prior.state is not PreviewState.PREVIEW_ONLY_LEGACY_C04_BLOCKED:
            if prior.state is PreviewState.MANAGER_S1_REQUIRED:
                return IntentResult(IntentState.MANAGER_S1_REQUIRED)
            if prior.state is PreviewState.UNAVAILABLE:
                return IntentResult(IntentState.UNAVAILABLE)
            return IntentResult(IntentState.S0_REVIEW_REQUIRED)
        r=binding.receipt
        digest=_proposal_hash(s2_f02_result,request,r,channel_ref)
        import psycopg
        try:
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout='3s'")
                    # First establish lead from S0 closure, never from model.
                    cur.execute(_CONTEXT_SQL,(r.closure_event_ref,
                        r.store_ref,r.case_ref,r.snapshot_sha256,
                        r.expected_cycle_version,r.message_watermark,
                        r.message_count))
                    ctx=cur.fetchall()
                    if len(ctx)!=1 or type(ctx[0][0]) is not uuid.UUID:
                        return IntentResult(IntentState.STALE_REVIEW_REQUIRED)
                    lead,_=ctx[0]
                    cur.execute(_LEAD,(r.store_ref,lead))
                    if cur.fetchone() is None:
                        return IntentResult(IntentState.STALE_REVIEW_REQUIRED)
                    # The C04 opt-out/cancellation path takes the same lead
                    # lock. Reconfirm eligibility under that lock.
                    cur.execute(_MANAGER,(r.store_ref,principal.session_id,principal.actor_id))
                    if cur.fetchone() is None:
                        return IntentResult(IntentState.MANAGER_S1_REQUIRED)
                    cur.execute(_CHANNEL,(r.message_watermark,r.store_ref,
                        r.case_ref,lead,channel_ref))
                    if cur.fetchone() is None:
                        return IntentResult(IntentState.DENIED)
                    cur.execute(_HUMAN,(r.case_ref,r.store_ref,lead,
                                        r.expected_cycle_version))
                    if cur.fetchone() is None:
                        return IntentResult(IntentState.STALE_REVIEW_REQUIRED)
                    cur.execute(_C04,(r.store_ref,lead,channel_ref))
                    decision=cur.fetchone()
                    if (decision is None or type(decision[0]) is not dict or
                        decision[0].get('decisao')!='ELEGIVEL_SOMENTE_SIMULACAO'):
                        return IntentResult(IntentState.S0_REVIEW_REQUIRED)
                    cur.execute(_OLD_PLAN,(r.case_ref,r.store_ref,lead))
                    if cur.fetchone() is not None:
                        return IntentResult(IntentState.S0_REVIEW_REQUIRED)
                    cur.execute(_TEMPLATE,(r.store_ref,request.preview.template_ref))
                    t=cur.fetchone()
                    if (t is None or t[2] is not True or t[3]!='post_human'
                       or t[0]!=s2_f02_result['templateId']
                       or f'v{t[1]}'!=s2_f02_result['templateVersion']
                       or t[4]!=s2_f02_result['category']
                       or t[5]!=request.preview.policy_version):
                        return IntentResult(IntentState.STALE_REVIEW_REQUIRED)
                    cur.execute(_EXIST,(r.store_ref,r.closure_event_ref))
                    existing=cur.fetchone()
                    matching=(str(principal.actor_id),str(principal.session_id),
                         channel_ref,request.preview.template_ref,
                         s2_f02_result['attemptId'],s2_f02_result['templateVersion'],
                         s2_f02_result['category'],request.preview.policy_version,
                         _DECISION,request.manager_evidence_sha256,digest,
                         request.idempotency_key,r.case_ref,str(lead))
                    if existing is not None:
                        return IntentResult(IntentState.ALREADY_RECORDED_AUDIT_ONLY
                            if tuple(str(v) for v in existing)==matching
                            else IntentState.CONFLICT_REVIEW_REQUIRED)
                    cur.execute(_DUP_KEY,(r.store_ref,request.idempotency_key))
                    if cur.fetchone() is not None:
                        return IntentResult(IntentState.CONFLICT_REVIEW_REQUIRED)
                    cur.execute(_INSERT,(r.store_ref,r.closure_event_ref,
                        r.case_ref,lead,channel_ref,request.preview.template_ref,
                        principal.actor_id,principal.session_id,
                        s2_f02_result['attemptId'],s2_f02_result['templateVersion'],
                        s2_f02_result['category'],request.preview.policy_version,
                        _DECISION,request.manager_evidence_sha256,digest,
                        request.idempotency_key))
                    if cur.fetchone() is None:
                        return IntentResult(IntentState.CONFLICT_REVIEW_REQUIRED)
            return IntentResult(IntentState.RECORDED_AUDIT_ONLY)
        except Exception:
            return IntentResult(IntentState.UNAVAILABLE)
