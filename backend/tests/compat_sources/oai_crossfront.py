"""E04: S2 F03 JS output -> S0 PG17 read-only compatibility port.

This is NOT an authorization or a write adapter. The S2 gate returns only
review status, field keys and a claimed snapshot; no values/provenance grant.
The S0 separately proves the physical historical receipt, HMAC, reservation,
tenant, identities, version vector, trusted catalogue and field proposal.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
from backend.s0_f03_operational_contracts_local import (
    ProposedField,proposal_digest,S0F03LocalOperationalContractsBridge,
    OperationalState,
)
from backend.s0_f03_bound_content_seal_local import (
    BoundContentState,_valid,
)
from backend.s0_f03_version_reservation_local import VersionVector,_validated
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal

class CrossFrontState(str,Enum):
    REVIEW_ONLY='REVIEW_ONLY'
    DENIED='DENIED'
    STALE_REVIEW_REQUIRED='STALE_REVIEW_REQUIRED'
    FIELD_REVIEW_REQUIRED='FIELD_REVIEW_REQUIRED'
    CATALOG_REVIEW_REQUIRED='CATALOG_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED='CONFLICT_REVIEW_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class CrossFrontResult:
    state:CrossFrontState

_SNAPSHOT = """select p.metadados_sha256 from
 prumo_private.cfi01_f03_content_proofs_local p
 join prumo_private.cfi01_f03_history_seals_local s on
 s.concessionaria_id=p.concessionaria_id
 and s.evento_fechamento_id=p.evento_fechamento_id
 and s.caso_id=p.caso_id
 where p.concessionaria_id=%s::uuid and p.evento_fechamento_id=%s::uuid
 and p.caso_id=%s::uuid and p.chave_versao=%s::text
 and p.metadados_sha256=s.metadados_sha256
 for share of p,s"""

def _candidate(output:object,fields:object)->str|None:
    if (type(output) is not dict or set(output)!={'status','fieldCodes','snapshotRef'}
        or output['status']!='S0_RECHECK_ONLY'
        or type(fields) is not tuple or proposal_digest(fields) is None):
        return None
    codes=output['fieldCodes']
    if (type(codes) is not list or len(codes)!=len(fields)
        or any(type(c) is not str for c in codes)
        or codes!=sorted(f.field_key for f in fields)):
        return None
    ref=output['snapshotRef']
    if type(ref) is not str or re.fullmatch(r'[0-9a-f]{64}',ref) is None:
        return None
    return ref

class S0F03CrossFrontLocalBridge:
    def __init__(self,contract:S0F03LocalOperationalContractsBridge):
        if type(contract) is not S0F03LocalOperationalContractsBridge:
            raise TypeError('real S0 local contract required')
        self._contract=contract

    def inspect(self,authorization:str,binding:S0F03BoundReceiptLocal,
                key_version:str,secret:bytes,version:VersionVector,
                request_ref:str,fields:tuple[ProposedField,...],
                s2_output:dict)->CrossFrontResult:
        source_ref=_candidate(s2_output,fields)
        digest=proposal_digest(fields)
        if (source_ref is None or digest is None
            or not _validated(binding,version,request_ref,digest,key_version)
            or not _valid(binding,key_version,secret)):
            return CrossFrontResult(CrossFrontState.DENIED)
        verified=self._contract.validate(authorization,binding,key_version,secret,
                                          version,request_ref,digest,fields)
        if verified.state is not OperationalState.CONTRACT_REVIEW_ONLY:
            states={
                OperationalState.STALE_REVIEW_REQUIRED:CrossFrontState.STALE_REVIEW_REQUIRED,
                OperationalState.CONFLICT_REVIEW_REQUIRED:CrossFrontState.CONFLICT_REVIEW_REQUIRED,
                OperationalState.FIELD_REVIEW_REQUIRED:CrossFrontState.FIELD_REVIEW_REQUIRED,
                OperationalState.CATALOG_REVIEW_REQUIRED:CrossFrontState.CATALOG_REVIEW_REQUIRED,
                OperationalState.UNAVAILABLE:CrossFrontState.UNAVAILABLE,
            }
            return CrossFrontResult(states.get(verified.state,CrossFrontState.DENIED))
        r=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._contract._store._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_SNAPSHOT,(r.store_ref,r.closure_event_ref,
                                           r.case_ref,key_version))
                    row=cur.fetchone()
                    if row is None or row!=(source_ref,):
                        return CrossFrontResult(CrossFrontState.STALE_REVIEW_REQUIRED)
            # A final S0 HMAC proof is independent of the model output.
            again=self._contract._content.verify(authorization,binding,
                                                  key_version,secret)
            if again.state is not BoundContentState.MATCHES_REVIEW_ONLY:
                return CrossFrontResult(CrossFrontState.STALE_REVIEW_REQUIRED)
            return CrossFrontResult(CrossFrontState.REVIEW_ONLY)
        except Exception:
            return CrossFrontResult(CrossFrontState.UNAVAILABLE)
