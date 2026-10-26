"""S0-only E04 observed-origin gate. The ledger is NOT a Meta receipt.

Replays the physical signed S0 closure and C08 cancellation witness before
reading the PG17 AFTER-trigger event ledger. Backdated legacy columns cannot
fabricate PRE-HANDOFF creation; incomplete history is fail-closed.

The return status is a private audit review only, NEVER an authorization to
schedule a post-human plan or send via Meta. Fixture-only, no hosted Supabase.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from uuid import UUID
from backend.s0_f02_legacy_cancellation_witness_local import (
    S0F02LocalLegacyCancellationWitness,CancelWitnessState
)
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL
from backend.s0_f03_operational_contracts_local import ProposedField
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_f02_posthuman_intent_local import PostHumanIntentRequest

_QUERY="""select prumo_private.cfi01_f02_check_origin_local(
  %s::uuid,%s::uuid,%s::uuid)"""

class OriginState(str,Enum):
    LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY='LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY'
    LATE_ORIGIN_REVIEW_REQUIRED='LATE_ORIGIN_REVIEW_REQUIRED'
    INCOMPLETE_ORIGIN_REVIEW_REQUIRED='INCOMPLETE_ORIGIN_REVIEW_REQUIRED'
    MUTATED_ORIGIN_REVIEW_REQUIRED='MUTATED_ORIGIN_REVIEW_REQUIRED'
    RESERVED_EXTERNAL_UNKNOWN='RESERVED_EXTERNAL_UNKNOWN'
    S0_REVIEW_REQUIRED='S0_REVIEW_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class OriginResult:
    state:OriginState

_STATUS={
    'LOCAL_ORIGIN_VERIFIED_AUDIT_ONLY':OriginState.LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY,
    'LATE_OBSERVED_SOURCE':OriginState.LATE_ORIGIN_REVIEW_REQUIRED,
    'MUTATED_ORIGIN':OriginState.MUTATED_ORIGIN_REVIEW_REQUIRED,
    'RESERVED_EXTERNAL_UNKNOWN':OriginState.RESERVED_EXTERNAL_UNKNOWN,
    'MISSING_ORIGIN':OriginState.INCOMPLETE_ORIGIN_REVIEW_REQUIRED,
    'INCOMPLETE_ORIGIN':OriginState.INCOMPLETE_ORIGIN_REVIEW_REQUIRED,
    'NO_LEGACY_CHAIN':OriginState.INCOMPLETE_ORIGIN_REVIEW_REQUIRED,
    'ACTIVE_LEGACY_CHAIN':OriginState.INCOMPLETE_ORIGIN_REVIEW_REQUIRED,
    'S0_SCOPE_DENIED':OriginState.S0_REVIEW_REQUIRED,
}
class S0F02LegacyObservedOriginBridge:
    def __init__(self,witness:S0F02LocalLegacyCancellationWitness):
        if type(witness) is not S0F02LocalLegacyCancellationWitness:
            raise TypeError('requires physical S0 C08 witness')
        self._witness=witness
        self._dsn=witness._dsn

    def inspect(self,authorization:str,binding:S0F03BoundReceiptLocal,
                key_version:str,secret:bytes,version:VersionVector,
                request_ref:str,fields:tuple[ProposedField,...],
                f03_output:dict,f03_proposal:dict,s2_f02_result:dict,
                channel_ref:str,request:PostHumanIntentRequest)->OriginResult:
        prior=self._witness.inspect_and_seal(authorization,binding,
             key_version,secret,version,request_ref,fields,f03_output,
             f03_proposal,s2_f02_result,channel_ref,request)
        if prior.state not in (
            CancelWitnessState.LOCAL_CHAIN_ATTESTED_AUDIT_ONLY,
            CancelWitnessState.ALREADY_ATTESTED_AUDIT_ONLY):
            return OriginResult(
                OriginState.UNAVAILABLE if prior.state is CancelWitnessState.UNAVAILABLE
                else OriginState.S0_REVIEW_REQUIRED)
        r=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set transaction isolation level repeatable read read only")
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_CONTEXT_SQL,(r.closure_event_ref,r.store_ref,
                        r.case_ref,r.snapshot_sha256,r.expected_cycle_version,
                        r.message_watermark,r.message_count))
                    context=cur.fetchall()
                    if (len(context)!=1 or type(context[0][0]) is not UUID):
                        return OriginResult(OriginState.S0_REVIEW_REQUIRED)
                    cur.execute(_QUERY,(r.store_ref,context[0][0],r.case_ref))
                    observed=cur.fetchone()
                    if observed is None or len(observed)!=1 or type(observed[0]) is not str:
                        return OriginResult(OriginState.UNAVAILABLE)
                    state=_STATUS.get(observed[0],OriginState.S0_REVIEW_REQUIRED)
            return OriginResult(state)
        except Exception:
            return OriginResult(OriginState.UNAVAILABLE)
