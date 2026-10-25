"""E04 offline S2 F02 lifecycle candidate vs physical S0 C04 compatibility.

NO scheduling/send, no model authority, no consent or human authorization
fabricated from JS booleans. The *current* C04 PG17 implementation expressly
forbids a human case on the cycle; S2's post-human candidate is therefore a
CONTRACT GAP even when synthetic C04 contact eligibility is demonstrated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
from uuid import UUID

from backend.s0_f03_crossfront_evidence_local import (
    S0F03LocalEvidenceReviewBridge,EvidenceState,
)
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_f03_operational_contracts_local import ProposedField
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_human_closure_event_local import S0LocalClosureStore

_C04 = """select prumo_private.verificar_contato_sintetico(
 %s::uuid,%s::uuid,%s::uuid,'recontato_comercial_sintetico')"""
_CHANNEL = """select m.canal_id from public.mensagens m
join public.conversas v
 on v.id=m.conversa_id and v.concessionaria_id=m.concessionaria_id
where m.id=%s::uuid and m.concessionaria_id=%s::uuid
 and m.caso_id=%s::uuid and v.lead_id=%s::uuid
 and m.canal_id=%s::uuid"""
_HUMAN = """select 1 from public.casos_humanos h
join public.ciclos_comerciais c on c.id=h.ciclo_id
 and c.concessionaria_id=h.concessionaria_id and c.lead_id=h.lead_id
where h.id=%s::uuid and h.concessionaria_id=%s::uuid
 and h.lead_id=%s::uuid and c.versao_registro=%s::bigint"""
_OLD_PLAN = """select 1 from public.planos_recontato_sinteticos p
join public.casos_humanos h on h.ciclo_id=p.ciclo_id
 and h.concessionaria_id=p.concessionaria_id and h.lead_id=p.lead_id
where h.id=%s::uuid and p.concessionaria_id=%s::uuid
 and p.lead_id=%s::uuid and p.estado='ativo' limit 1"""

class F02RecheckState(str,Enum):
    DENIED='DENIED'
    STALE_REVIEW_REQUIRED='STALE_REVIEW_REQUIRED'
    C04_OPTOUT_BLOCK='C04_OPTOUT_BLOCK'
    C04_EVIDENCE_MISSING='C04_EVIDENCE_MISSING'
    OLD_AI_PLAN_ACTIVE='OLD_AI_PLAN_ACTIVE'
    LEGACY_C04_HUMAN_CASE_INCOMPATIBLE='LEGACY_C04_HUMAN_CASE_INCOMPATIBLE'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class F02RecheckResult:
    state:F02RecheckState
    # No template, customer ID, commercial status or send authorization.

def _candidate(js:object)->bool:
    if type(js) is not dict or set(js)!={
        'status','attemptId','templateId','templateVersion','category'}:
        return False
    if js['status']!='READY_FOR_S0_RECHECK':
        return False
    if any(type(js[k]) is not str or re.fullmatch(
        r'[A-Za-z0-9_.:-]{1,100}',js[k]) is None
        for k in ('attemptId','templateId','templateVersion')):
        return False
    return js['category'] in ('MARKETING','UTILITY','AUTHENTICATION')

class S0F02LocalPostHumanCompatibilityBridge:
    """Review-only barrier: receipt, evidence and actual C04 PG17 checked."""
    def __init__(self,f03:S0F03LocalEvidenceReviewBridge,dsn:str):
        if type(f03) is not S0F03LocalEvidenceReviewBridge:
            raise TypeError('physical S0 F03 evidence validator required')
        local=S0LocalClosureStore(dsn)._dsn
        if f03._base._contract._store._dsn!=local:
            raise TypeError('physical S0 F03 DB mismatch')
        self._f03=f03
        self._dsn=local

    def inspect(self,authorization:str,binding:S0F03BoundReceiptLocal,
                key_version:str,secret:bytes,version:VersionVector,
                request_ref:str,fields:tuple[ProposedField,...],
                f03_output:dict,f03_proposal:dict,
                s2_f02_result:dict,channel_ref:str)->F02RecheckResult:
        if (not _candidate(s2_f02_result)
            or type(channel_ref) is not str or not _uuid(channel_ref)):
            return F02RecheckResult(F02RecheckState.DENIED)
        before=self._f03.inspect(authorization,binding,key_version,secret,
                                  version,request_ref,fields,
                                  f03_output,f03_proposal)
        if before.state is not EvidenceState.S0_EVIDENCE_REVIEW_ONLY:
            if before.state is EvidenceState.UNAVAILABLE:
                return F02RecheckResult(F02RecheckState.UNAVAILABLE)
            if before.state is EvidenceState.DENIED:
                return F02RecheckResult(F02RecheckState.DENIED)
            return F02RecheckResult(F02RecheckState.STALE_REVIEW_REQUIRED)
        r=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set transaction isolation level repeatable read read only")
                    cur.execute(_CONTEXT_SQL,(r.closure_event_ref,r.store_ref,
                        r.case_ref,r.snapshot_sha256,r.expected_cycle_version,
                        r.message_watermark,r.message_count))
                    ctx=cur.fetchall()
                    if len(ctx)!=1 or not isinstance(ctx[0][0],UUID):
                        return F02RecheckResult(F02RecheckState.STALE_REVIEW_REQUIRED)
                    lead,_cutoff=ctx[0]
                    cur.execute(_CHANNEL,(r.message_watermark,r.store_ref,
                                          r.case_ref,lead,channel_ref))
                    if len(cur.fetchall())!=1:
                        return F02RecheckResult(F02RecheckState.DENIED)
                    cur.execute(_HUMAN,(r.case_ref,r.store_ref,lead,
                                        r.expected_cycle_version))
                    if cur.fetchone() is None:
                        return F02RecheckResult(F02RecheckState.STALE_REVIEW_REQUIRED)
                    cur.execute(_C04,(r.store_ref,lead,channel_ref))
                    response=cur.fetchone()
                    if response is None or type(response[0]) is not dict:
                        return F02RecheckResult(F02RecheckState.UNAVAILABLE)
                    decision=response[0]
                    if decision.get('decisao')=='INELEGIVEL':
                        return F02RecheckResult(F02RecheckState.C04_OPTOUT_BLOCK)
                    if decision.get('decisao')!='ELEGIVEL_SOMENTE_SIMULACAO':
                        return F02RecheckResult(F02RecheckState.C04_EVIDENCE_MISSING)
                    cur.execute(_OLD_PLAN,(r.case_ref,r.store_ref,lead))
                    if cur.fetchone() is not None:
                        return F02RecheckResult(F02RecheckState.OLD_AI_PLAN_ACTIVE)
            # Previous C04 agendar_recontatos_sinteticos explicitly refuses
            # ANY human case on same cycle. The proposed F02 post-human
            # capability MUST NOT be promoted by a simple boolean in S2.
            after=self._f03.inspect(authorization,binding,key_version,secret,
                                    version,request_ref,fields,
                                    f03_output,f03_proposal)
            if after.state is not EvidenceState.S0_EVIDENCE_REVIEW_ONLY:
                return F02RecheckResult(F02RecheckState.STALE_REVIEW_REQUIRED)
            return F02RecheckResult(
                F02RecheckState.LEGACY_C04_HUMAN_CASE_INCOMPATIBLE)
        except Exception:
            return F02RecheckResult(F02RecheckState.UNAVAILABLE)

def _uuid(value:object)->bool:
    if type(value) is not str:return False
    try:return str(UUID(value))==value
    except (TypeError,AttributeError,ValueError):return False
