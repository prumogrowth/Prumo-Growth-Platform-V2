"""E04 S0-only independent legacy reconciliation REVIEW, no posthuman plan.

Requires complete real PG17 chain: S0/F03 closure & synthetic evidence,
authenticated scoped S1 manager and manager-intent record, physical C08 local
cancel witness, and observed pre-handoff plan + attempt event ledger.

A positive result is an AUDIT-ONLY diagnostic for further independent human
approval. Never relaxes C04 old scheduler or the S0 new-draft gate; never
proves Meta cancellation or provides permission for a real commercial send.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from backend.s0_f02_legacy_observed_origin_local import (
    S0F02LegacyObservedOriginBridge,OriginState
)
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL
from backend.s0_f02_posthuman_intent_local import PostHumanIntentRequest
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_f03_operational_contracts_local import ProposedField
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal

# An independent DB-only check that the historical local-chain witness still
# belongs to the SAME S0 closure and lead and has NO executable replacement.
# This is a private review only; no row is generated in draft or queue tables.
_LOCAL="""select 1 from prumo_private.cfi01_f02_posthuman_intents_local i
join prumo_private.cfi01_f02_legacy_cancel_witness_local w
 on w.concessionaria_id=i.concessionaria_id
 and w.evento_fechamento_id=i.evento_fechamento_id
join public.casos_humanos h
 on h.id=i.caso_id and h.concessionaria_id=i.concessionaria_id
 and h.lead_id=i.lead_id
where i.concessionaria_id=%s::uuid
 and i.evento_fechamento_id=%s::uuid and i.caso_id=%s::uuid
 and i.lead_id=%s::uuid and i.estado='AUDIT_ONLY_C04_BLOCKED'
 and w.tipo='C08_LOCAL_CANCELED_AUDIT_ONLY'
 and w.planos_cancelados>0 and w.tentativas_canceladas>0
 and exists (
   select 1 from public.planos_recontato_sinteticos p
   where p.concessionaria_id=i.concessionaria_id and p.lead_id=i.lead_id
    and p.ciclo_id=h.ciclo_id and p.estado='cancelado'
 )
 and not exists (
   select 1 from public.planos_recontato_sinteticos p
   where p.concessionaria_id=i.concessionaria_id and p.lead_id=i.lead_id
    and p.estado<>'cancelado'
 )
 and not exists (
   select 1 from prumo_private.cfi01_f02_posthuman_draft_local draft
   where draft.concessionaria_id=i.concessionaria_id
    and draft.evento_fechamento_id=i.evento_fechamento_id
 )
 and not exists (
   select 1 from public.supressoes_contato_sinteticas o
   where o.concessionaria_id=i.concessionaria_id and o.lead_id=i.lead_id
    and o.canal_id=i.canal_id
    and o.finalidade='recontato_comercial_sintetico'
 )"""

class LegacyReviewState(str,Enum):
    LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY='LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY'
    LATE_ORIGIN_REVIEW_REQUIRED='LATE_ORIGIN_REVIEW_REQUIRED'
    MISSING_ORIGIN_REVIEW_REQUIRED='MISSING_ORIGIN_REVIEW_REQUIRED'
    MUTATED_ORIGIN_REVIEW_REQUIRED='MUTATED_ORIGIN_REVIEW_REQUIRED'
    EXTERNAL_DISPATCH_UNKNOWN='EXTERNAL_DISPATCH_UNKNOWN'
    RECHECK_S0_REQUIRED='RECHECK_S0_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class LegacyReviewResult:
    state:LegacyReviewState

_MAP={
    OriginState.LATE_ORIGIN_REVIEW_REQUIRED:
      LegacyReviewState.LATE_ORIGIN_REVIEW_REQUIRED,
    OriginState.INCOMPLETE_ORIGIN_REVIEW_REQUIRED:
      LegacyReviewState.MISSING_ORIGIN_REVIEW_REQUIRED,
    OriginState.MUTATED_ORIGIN_REVIEW_REQUIRED:
      LegacyReviewState.MUTATED_ORIGIN_REVIEW_REQUIRED,
    OriginState.RESERVED_EXTERNAL_UNKNOWN:
      LegacyReviewState.EXTERNAL_DISPATCH_UNKNOWN,
    OriginState.S0_REVIEW_REQUIRED:
      LegacyReviewState.RECHECK_S0_REQUIRED,
    OriginState.UNAVAILABLE:
      LegacyReviewState.UNAVAILABLE,
}

class S0F02LegacyReconciliationReview:
    def __init__(self,origin:S0F02LegacyObservedOriginBridge):
        if type(origin) is not S0F02LegacyObservedOriginBridge:
            raise TypeError('requires physical S0 C08 observed-origin bridge')
        self._origin=origin
        self._dsn=origin._dsn

    def inspect(self,authorization:str,binding:S0F03BoundReceiptLocal,
                key_version:str,secret:bytes,version:VersionVector,
                request_ref:str,fields:tuple[ProposedField,...],
                f03_output:dict,f03_proposal:dict,s2_f02_result:dict,
                channel_ref:str,request:PostHumanIntentRequest)->LegacyReviewResult:
        verified=self._origin.inspect(
            authorization,binding,key_version,secret,version,request_ref,
            fields,f03_output,f03_proposal,s2_f02_result,channel_ref,request)
        if verified.state is not OriginState.LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY:
            return LegacyReviewResult(
                _MAP.get(verified.state,LegacyReviewState.RECHECK_S0_REQUIRED))
        r=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute('set transaction isolation level repeatable read read only')
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_CONTEXT_SQL,(r.closure_event_ref,r.store_ref,
                        r.case_ref,r.snapshot_sha256,r.expected_cycle_version,
                        r.message_watermark,r.message_count))
                    rows=cur.fetchall()
                    if len(rows)!=1 or type(rows[0][0]) is not UUID:
                        return LegacyReviewResult(LegacyReviewState.RECHECK_S0_REQUIRED)
                    lead=rows[0][0]
                    cur.execute(_LOCAL,(r.store_ref,r.closure_event_ref,
                                        r.case_ref,lead))
                    if cur.fetchone() is None:
                        return LegacyReviewResult(LegacyReviewState.RECHECK_S0_REQUIRED)
            # NO authority hand-off: explicit S0/S1 operational approval and
            # separate real Meta cancellation evidence still absent.
            return LegacyReviewResult(LegacyReviewState.LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY)
        except Exception:
            return LegacyReviewResult(LegacyReviewState.UNAVAILABLE)
