"""E04/S0 operational contract CHECK ONLY for synthetic form + catalogue.

Consumes an existing S0-bound, HMAC-reviewed F03 CAS reservation.
No real operational schema, no field updates, no customer data in results,
no AI permission or removal of identity HOLD.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from uuid import UUID

from backend.s0_f03_version_reservation_local import (
    VersionVector, _validated, _CATALOG, _LEAD, _CASE, _PENDING_IDENTITY, _PROOF,
)
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL
from backend.s0_f03_bound_content_seal_local import (
    S0F03LocalBoundContentBridge, BoundContentState, _valid,
)
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_human_closure_event_local import S0LocalClosureStore

class FieldKind(str, Enum):
    TEXT_ONLY = 'TEXT_ONLY'
    CATALOG_CODE = 'CATALOG_CODE'

@dataclass(frozen=True)
class ProposedField:
    field_key: str
    kind: FieldKind
    value: str

class OperationalState(str, Enum):
    CONTRACT_REVIEW_ONLY = 'CONTRACT_REVIEW_ONLY'
    FIELD_REVIEW_REQUIRED = 'FIELD_REVIEW_REQUIRED'
    CATALOG_REVIEW_REQUIRED = 'CATALOG_REVIEW_REQUIRED'
    STALE_REVIEW_REQUIRED = 'STALE_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED = 'CONFLICT_REVIEW_REQUIRED'
    DENIED = 'DENIED'
    UNAVAILABLE = 'UNAVAILABLE'

@dataclass(frozen=True)
class OperationalResult:
    state: OperationalState
    # Never returns proposed values, identity, evidence, key, or a F03 grant.

_RESERVATION = """select referencia_requisicao,proposta_sha256,chave_versao,
 versao_ficha,versao_catalogo,versao_caso,versao_atribuicao,versao_identidade
 from prumo_private.cfi01_f03_reservations_local
 where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid
 and caso_id=%s::uuid and lead_id=%s::uuid for share"""
_FIELD = """select tipo_sintetico,max_chars,ativo_sintetico
 from prumo_private.cfi01_f03_operational_field_contracts_local
 where concessionaria_id=%s::uuid and campo_sintetico=%s::text for share"""
_PRODUCT = """select ativo_sintetico
 from prumo_private.cfi01_f03_catalog_entries_local
 where concessionaria_id=%s::uuid and codigo_sintetico=%s::text for share"""
_SHOP_LOCK = "select prumo_private.s0_f03_lock_shop_local(%s::uuid)"

def proposal_digest(fields: object) -> str | None:
    """Stable digest bound to a reserved proposal, no raw values persisted."""
    if type(fields) is not tuple or not 1 <= len(fields) <= 12:
        return None
    seen=set()
    serial=[]
    for f in fields:
        if (type(f) is not ProposedField or type(f.kind) is not FieldKind
            or type(f.field_key) is not str
            or re.fullmatch(r'[a-z_]{2,48}', f.field_key) is None
            or type(f.value) is not str or not 1 <= len(f.value) <= 128
            or f.value!=f.value.strip() or any(ord(c)<32 for c in f.value)
            or f.field_key in seen):
            return None
        seen.add(f.field_key)
        serial.append([f.field_key,f.kind.value,f.value])
    encoded=json.dumps(sorted(serial),separators=(',',':'),
                       ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()

class S0F03LocalOperationalContractsStore:
    """Read-only physical validation in S0 PG transaction (not public API)."""
    def __init__(self,dsn:str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def check(self,binding:S0F03BoundReceiptLocal,version:VersionVector,
              request:str,proposal_sha:str,key_id:str,
              fields:tuple[ProposedField,...])->OperationalState:
        digest=proposal_digest(fields)
        if (digest is None or not _validated(binding,version,request,
                                              proposal_sha,key_id)):
            return OperationalState.DENIED
        if digest!=proposal_sha:
            return OperationalState.CONFLICT_REVIEW_REQUIRED
        r=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout='3s'")
                    # Cooperative same-shop S0 candidate source writers cannot
                    # create a phantom pending during this decision.
                    cur.execute(_SHOP_LOCK,(r.store_ref,))
                    cur.execute(_CONTEXT_SQL,(
                        r.closure_event_ref,r.store_ref,r.case_ref,
                        r.snapshot_sha256,r.expected_cycle_version,
                        r.message_watermark,r.message_count))
                    context=cur.fetchall()
                    if len(context)!=1 or not isinstance(context[0][0],UUID):
                        return OperationalState.STALE_REVIEW_REQUIRED
                    lead,_=context[0]
                    # Established lock order: catalog, person, case.
                    cur.execute(_CATALOG,(r.store_ref,))
                    cat=cur.fetchone()
                    cur.execute(_LEAD,(r.store_ref,lead))
                    person=cur.fetchone()
                    cur.execute(_CASE,(r.assignment_ref,r.store_ref,r.case_ref,
                                       lead,r.expected_cycle_version))
                    case=cur.fetchone()
                    if cat is None or person is None or case is None:
                        return OperationalState.STALE_REVIEW_REQUIRED
                    expected=(version.form,version.catalog,version.case,
                              version.assignment,version.identity)
                    if (person[0],cat[0],case[0],case[1],person[1])!=expected:
                        return OperationalState.STALE_REVIEW_REQUIRED
                    cur.execute(_PENDING_IDENTITY,(lead,r.store_ref))
                    if cur.fetchone() is not None:
                        return OperationalState.CONFLICT_REVIEW_REQUIRED
                    cur.execute(_PROOF,(r.store_ref,r.closure_event_ref,
                                       r.case_ref,lead,r.expected_cycle_version,
                                       r.snapshot_sha256,r.message_watermark))
                    if cur.fetchone()!=(key_id,):
                        return OperationalState.STALE_REVIEW_REQUIRED
                    cur.execute(_RESERVATION,(r.store_ref,r.closure_event_ref,
                                              r.case_ref,lead))
                    if cur.fetchone()!=(request,proposal_sha,key_id,*expected):
                        return OperationalState.CONFLICT_REVIEW_REQUIRED
                    for proposal in fields:
                        cur.execute(_FIELD,(r.store_ref,proposal.field_key))
                        specification=cur.fetchone()
                        if specification is None or not specification[2]:
                            return OperationalState.FIELD_REVIEW_REQUIRED
                        kind,max_chars,_active=specification
                        if (kind!=proposal.kind.value or
                            len(proposal.value)>max_chars):
                            return OperationalState.FIELD_REVIEW_REQUIRED
                        if proposal.kind is FieldKind.CATALOG_CODE:
                            if re.fullmatch(r'[A-Z0-9_-]{2,48}',proposal.value) is None:
                                return OperationalState.CATALOG_REVIEW_REQUIRED
                            cur.execute(_PRODUCT,(r.store_ref,proposal.value))
                            item=cur.fetchone()
                            if item is None or item[0] is not True:
                                return OperationalState.CATALOG_REVIEW_REQUIRED
                    return OperationalState.CONTRACT_REVIEW_ONLY
        except Exception:
            return OperationalState.UNAVAILABLE

class S0F03LocalOperationalContractsBridge:
    """Two S0-authenticated HMAC reads around the contract snapshot."""
    def __init__(self,content:S0F03LocalBoundContentBridge,
                 store:S0F03LocalOperationalContractsStore):
        if (type(content) is not S0F03LocalBoundContentBridge
            or type(store) is not S0F03LocalOperationalContractsStore
            or content._store._dsn!=store._dsn):
            raise TypeError('requires matching S0 local content proof and DB')
        self._content=content
        self._store=store

    def validate(self,authorization:str,binding:S0F03BoundReceiptLocal,
                 key_id:str,secret:bytes,version:VersionVector,
                 request:str,proposal_sha:str,
                 fields:tuple[ProposedField,...])->OperationalResult:
        if (not _valid(binding,key_id,secret)
            or proposal_digest(fields) is None
            or not _validated(binding,version,request,proposal_sha,key_id)):
            return OperationalResult(OperationalState.DENIED)
        try:
            before=self._content.verify(authorization,binding,key_id,secret)
            if before.state is not BoundContentState.MATCHES_REVIEW_ONLY:
                return OperationalResult(OperationalState.STALE_REVIEW_REQUIRED)
            state=self._store.check(binding,version,request,proposal_sha,
                                    key_id,fields)
            if state is not OperationalState.CONTRACT_REVIEW_ONLY:
                return OperationalResult(state)
            after=self._content.verify(authorization,binding,key_id,secret)
            if after.state is not BoundContentState.MATCHES_REVIEW_ONLY:
                return OperationalResult(OperationalState.STALE_REVIEW_REQUIRED)
            return OperationalResult(state)
        except Exception:
            return OperationalResult(OperationalState.UNAVAILABLE)
