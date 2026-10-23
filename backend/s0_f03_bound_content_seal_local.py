"""Local-only S0 F03 atomic content proof bound to sealed multi-case metadata.

Trust boundary: authenticated S0 history-seal bridge must approve before/after;
message text and runtime HMAC key stay in S0. No OpenAI data path or form writes.
Transaction locks lead and conversations before reading the synthetic history;
other writer paths and media completeness are NOT ratified by this lab.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID
import hmac

from backend.s0_cfi01_atomic_commands_local import S0InternalReceiptLocal
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_f03_history_seal_local import (
    S0F03LocalHistorySealingBridge, SealState,
)
from backend.s0_f03_content_integrity_local import (
    _CONTENT_SQL, _derive, ContentProof, _equal_proof, ContentState,
)
from backend.s0_f03_history_manifest_local import (
    _CONTEXT_SQL, _uuid, MAX_HISTORY_RECORDS,
)
from backend.s0_human_closure_event_local import S0LocalClosureStore

_LOCK_LEAD = """select id from public.leads_loja
where concessionaria_id=%s::uuid and id=%s::uuid for update"""
_LOCK_CONVERSATIONS = """select id from public.conversas
where concessionaria_id=%s::uuid and lead_id=%s::uuid
order by id for update"""
_PROOF_INSERT = """insert into prumo_private.cfi01_f03_content_proofs_local
(concessionaria_id,evento_fechamento_id,caso_id,chave_versao,
 metadados_sha256,mac_sha256,quantidade_mensagens,quantidade_casos)
select %s::uuid,%s::uuid,%s::uuid,%s::text,%s::text,%s::text,%s::integer,%s::integer
from prumo_private.cfi01_f03_history_seals_local s
where s.concessionaria_id=%s::uuid and s.evento_fechamento_id=%s::uuid
 and s.caso_id=%s::uuid and s.lead_id=%s::uuid
 and s.versao_ciclo=%s::bigint and s.corte_em=%s::timestamptz
 and s.snapshot_caso_sha256=%s::text and s.ultima_mensagem_id=%s::uuid
 and s.metadados_sha256=%s::text and s.quantidade_mensagens=%s::integer
 and s.quantidade_casos=%s::integer
on conflict (concessionaria_id,evento_fechamento_id) do nothing"""
_PROOF_SELECT = """select p.chave_versao,p.metadados_sha256,p.mac_sha256,
 p.quantidade_mensagens,p.quantidade_casos
from prumo_private.cfi01_f03_content_proofs_local p
join prumo_private.cfi01_f03_history_seals_local s
 on s.concessionaria_id=p.concessionaria_id
 and s.evento_fechamento_id=p.evento_fechamento_id
where p.concessionaria_id=%s::uuid and p.evento_fechamento_id=%s::uuid
 and p.caso_id=%s::uuid and s.caso_id=p.caso_id"""

class BoundContentState(str, Enum):
    SEALED_REVIEW_ONLY = 'SEALED_REVIEW_ONLY'
    ALREADY_SEALED_REVIEW_ONLY = 'ALREADY_SEALED_REVIEW_ONLY'
    MATCHES_REVIEW_ONLY = 'MATCHES_REVIEW_ONLY'
    STALE_REVIEW_REQUIRED = 'STALE_REVIEW_REQUIRED'
    MISSING_REVIEW_REQUIRED = 'MISSING_REVIEW_REQUIRED'
    DENIED = 'DENIED'
    UNAVAILABLE = 'UNAVAILABLE'

@dataclass(frozen=True)
class BoundContentResult:
    state: BoundContentState
    # Never disclose MAC, key, scoped identity, row or source text.

def _valid(binding: object, key_id: object, secret: object) -> bool:
    if type(binding) is not S0F03BoundReceiptLocal:
        return False
    r=binding.receipt
    return (type(r) is S0InternalReceiptLocal
            and all(_uuid(x) for x in (r.store_ref,r.case_ref,r.closure_event_ref,
                                        r.message_watermark))
            and type(r.expected_cycle_version) is int
            and 1<=r.expected_cycle_version<=9223372036854775807
            and type(r.snapshot_sha256) is str and len(r.snapshot_sha256)==64
            and all(c in '0123456789abcdef' for c in r.snapshot_sha256)
            and type(key_id) is str and 8<=len(key_id)<=80
            and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-'
                    for c in key_id)
            and type(secret) is bytes and len(secret)>=32)

class S0F03LocalBoundContentStore:
    """Disposable local PG only. Captures content MAC in one lock-held transaction."""
    def __init__(self, dsn: str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def check(self, binding: S0F03BoundReceiptLocal, key_id: str,
              secret: bytes, *, create: bool) -> BoundContentState:
        if not _valid(binding,key_id,secret) or type(create) is not bool:
            return BoundContentState.DENIED
        receipt=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout = '3s'")
                    # Lock S0 scope before reading; FK readers must wait on lead
                    # or conversations. Non-cooperating writers are still a gap.
                    cur.execute(_CONTEXT_SQL,(
                        receipt.closure_event_ref,receipt.store_ref,receipt.case_ref,
                        receipt.snapshot_sha256,receipt.expected_cycle_version,
                        receipt.message_watermark,receipt.message_count))
                    context=cur.fetchall()
                    if len(context)!=1:
                        return BoundContentState.MISSING_REVIEW_REQUIRED
                    lead,cutoff=context[0]
                    if not isinstance(lead,UUID) or not _uuid(str(lead)) or not hasattr(cutoff,'tzinfo') or cutoff.tzinfo is None:
                        return BoundContentState.DENIED
                    cur.execute(_LOCK_LEAD,(receipt.store_ref,lead))
                    if len(cur.fetchall())!=1:
                        return BoundContentState.STALE_REVIEW_REQUIRED
                    cur.execute(_LOCK_CONVERSATIONS,(receipt.store_ref,lead))
                    if not cur.fetchall():
                        return BoundContentState.MISSING_REVIEW_REQUIRED
                    cur.execute(_CONTENT_SQL + ' for share of m',(receipt.store_ref,lead,cutoff))
                    rows=cur.fetchmany(MAX_HISTORY_RECORDS+1)
                    if len(rows)>MAX_HISTORY_RECORDS:
                        return BoundContentState.MISSING_REVIEW_REQUIRED
                    proof=_derive(rows,receipt,str(lead),cutoff,secret)
                    if type(proof) is not ContentProof:
                        return BoundContentState.STALE_REVIEW_REQUIRED
                    inserted=False
                    if create:
                        cur.execute(_PROOF_INSERT,(
                            receipt.store_ref,receipt.closure_event_ref,
                            receipt.case_ref,key_id,proof.metadata_sha256,
                            proof.content_mac_sha256,proof.count,proof.case_count,
                            receipt.store_ref,receipt.closure_event_ref,
                            receipt.case_ref,str(lead),receipt.expected_cycle_version,
                            cutoff,receipt.snapshot_sha256,receipt.message_watermark,
                            proof.metadata_sha256,proof.count,proof.case_count,
                        ))
                        inserted=cur.rowcount==1
                    cur.execute(_PROOF_SELECT,(
                        receipt.store_ref,receipt.closure_event_ref,receipt.case_ref))
                    saved=cur.fetchone()
                    if saved is None or len(saved)!=5:
                        return BoundContentState.MISSING_REVIEW_REQUIRED
                    saved_key,saved_meta,saved_mac,count,cases=saved
                    if (saved_key!=key_id or saved_meta!=proof.metadata_sha256
                        or type(count) is not int or count!=proof.count
                        or type(cases) is not int or cases!=proof.case_count
                        or type(saved_mac) is not str
                        or not hmac.compare_digest(saved_mac,proof.content_mac_sha256)):
                        return BoundContentState.STALE_REVIEW_REQUIRED
                    if not create:
                        return BoundContentState.MATCHES_REVIEW_ONLY
                    if inserted:
                        return BoundContentState.SEALED_REVIEW_ONLY
                    return BoundContentState.ALREADY_SEALED_REVIEW_ONLY
        except Exception:
            return BoundContentState.UNAVAILABLE

class S0F03LocalBoundContentBridge:
    """S0 review guard composed with real history sealing, no public F03 grant."""
    def __init__(self, history: S0F03LocalHistorySealingBridge,
                 store: S0F03LocalBoundContentStore):
        if type(history) is not S0F03LocalHistorySealingBridge or type(store) is not S0F03LocalBoundContentStore:
            raise TypeError('requires local S0 history seal bridge and content store')
        if history._reader._dsn!=store._dsn or history._store._dsn!=store._dsn:
            raise TypeError('history and content must be in same local database')
        self._history=history
        self._store=store

    def _run(self, authorization: str, binding: S0F03BoundReceiptLocal,
             key_id: str, secret: bytes, *, create: bool) -> BoundContentResult:
        if not _valid(binding,key_id,secret):
            return BoundContentResult(BoundContentState.DENIED)
        try:
            before=self._history.verify(authorization,binding)
            if before.state is not SealState.MATCHES_LIVE_REVIEW_ONLY:
                return BoundContentResult(BoundContentState.STALE_REVIEW_REQUIRED)
            state=self._store.check(binding,key_id,secret,create=create)
            if state not in (BoundContentState.SEALED_REVIEW_ONLY,
                             BoundContentState.ALREADY_SEALED_REVIEW_ONLY,
                             BoundContentState.MATCHES_REVIEW_ONLY):
                return BoundContentResult(state)
            after=self._history.verify(authorization,binding)
            if after.state is not SealState.MATCHES_LIVE_REVIEW_ONLY:
                return BoundContentResult(BoundContentState.STALE_REVIEW_REQUIRED)
            # Even positive outcomes are only internal S0 review reports.
            return BoundContentResult(state)
        except Exception:
            return BoundContentResult(BoundContentState.UNAVAILABLE)

    def seal(self, authorization: str, binding: S0F03BoundReceiptLocal,
             key_id: str, secret: bytes) -> BoundContentResult:
        return self._run(authorization,binding,key_id,secret,create=True)

    def verify(self, authorization: str, binding: S0F03BoundReceiptLocal,
               key_id: str, secret: bytes) -> BoundContentResult:
        return self._run(authorization,binding,key_id,secret,create=False)
