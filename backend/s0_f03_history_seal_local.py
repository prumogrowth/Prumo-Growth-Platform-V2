"""Append-only S0 F03 historical metadata manifest, disposable PostgreSQL only.

Composes the existing authenticated CFI01 history bridge, never mints authority.
Immutable *membership metadata* is retained, not message content; this does NOT
prove full multi-case semantic completeness or authorize OpenAI/form writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from uuid import UUID
import hashlib
import json

from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal
from backend.s0_f03_history_manifest_local import (
    S0F03LocalHistoryManifestBridge, S0F03LocalPostgresHistoryReader,
    HistoricalRead, HistoricalMessageRef, HistoryState, _uuid,
)
from backend.s0_human_closure_event_local import S0LocalClosureStore

_INSERT = """insert into prumo_private.cfi01_f03_history_seals_local
(concessionaria_id,evento_fechamento_id,caso_id,lead_id,versao_ciclo,
 snapshot_caso_sha256,ultima_mensagem_id,corte_em,quantidade_mensagens,
 quantidade_casos,metadados_sha256,metadados_json)
values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::bigint,
 %s::text,%s::uuid,%s::timestamptz,%s::integer,
 %s::integer,%s::text,%s::jsonb)
on conflict (concessionaria_id,evento_fechamento_id) do nothing"""
_SELECT = """select lead_id,versao_ciclo,snapshot_caso_sha256,ultima_mensagem_id,
 corte_em,quantidade_mensagens,quantidade_casos,metadados_sha256,metadados_json
from prumo_private.cfi01_f03_history_seals_local
where concessionaria_id=%s::uuid and evento_fechamento_id=%s::uuid
 and caso_id=%s::uuid"""

class SealState(str, Enum):
    SEALED_REVIEW_ONLY = 'SEALED_REVIEW_ONLY'
    ALREADY_SEALED_REVIEW_ONLY = 'ALREADY_SEALED_REVIEW_ONLY'
    MATCHES_LIVE_REVIEW_ONLY = 'MATCHES_LIVE_REVIEW_ONLY'
    DENIED = 'DENIED'
    HISTORY_INCOMPLETE = 'HISTORY_INCOMPLETE'
    STALE = 'STALE'
    UNAVAILABLE = 'UNAVAILABLE'

@dataclass(frozen=True)
class SealResult:
    state: SealState
    # No tenant/person identifiers or raw messages leave this adapter.


def _snapshot(read: object):
    """Canonical ordered metadata only; invalid or unbounded input rejects."""
    if type(read) is not HistoricalRead or not _uuid(read.lead_ref) or not read.rows:
        return None
    if type(read.closure_at) is not datetime or read.closure_at.tzinfo is None:
        return None
    if len(read.rows) > 10000:
        return None
    rows = []
    last = None
    seen = set()
    cases = set()
    for r in read.rows:
        if (type(r) is not HistoricalMessageRef or not _uuid(r.message_ref)
            or (r.case_ref is not None and not _uuid(r.case_ref))
            or not _uuid(r.conversation_ref)
            or (r.author_ref is not None and not _uuid(r.author_ref))
            or type(r.created_at) is not datetime or r.created_at.tzinfo is None
            or r.created_at > read.closure_at or r.message_ref in seen
            or type(r.direction) is not str or type(r.origin) is not str):
            return None
        key=(r.created_at, r.message_ref)
        if last is not None and key < last:
            return None
        last=key
        seen.add(r.message_ref)
        if r.case_ref:cases.add(r.case_ref)
        rows.append([r.message_ref, r.case_ref, r.conversation_ref,
                     r.created_at.isoformat(), r.direction, r.origin, r.author_ref])
    payload=json.dumps(rows,ensure_ascii=False,separators=(',', ':'))
    return (hashlib.sha256(payload.encode('utf-8')).hexdigest(),
            len(rows),len(cases),payload)


class S0F03LocalManifestSealStore:
    """Only sealed metadata in disposable local S0 PG, no source/content writes."""
    def __init__(self, dsn: str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def capture(self, binding: S0F03BoundReceiptLocal,
                data: HistoricalRead, fingerprint: tuple) -> SealState:
        if type(binding) is not S0F03BoundReceiptLocal:
            return SealState.DENIED
        receipt=binding.receipt
        digest,count,cases,payload=fingerprint
        args=(receipt.store_ref,receipt.closure_event_ref,receipt.case_ref,
              data.lead_ref,receipt.expected_cycle_version,receipt.snapshot_sha256,
              receipt.message_watermark,data.closure_at,count,cases,digest,payload)
        import psycopg
        with psycopg.connect(self._dsn,connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute(_INSERT,args)
                inserted=cur.rowcount == 1
                cur.execute(_SELECT,(receipt.store_ref,receipt.closure_event_ref,receipt.case_ref))
                rec=cur.fetchone()
        if rec is None or len(rec)!=9:
            return SealState.DENIED
        (lead,version,case_sha,watermark,cutoff,nmessages,ncases,sha,meta)=rec
        # JSONB order/whitespace may be canonicalized by PostgreSQL; compare
        # the structured list and separately the committed canonical digest.
        if (str(lead)!=data.lead_ref or type(version) is not int
            or version!=receipt.expected_cycle_version or case_sha!=receipt.snapshot_sha256
            or str(watermark)!=receipt.message_watermark or cutoff!=data.closure_at
            or nmessages!=count or ncases!=cases or sha!=digest
            or meta!=json.loads(payload)):
            return SealState.STALE
        return SealState.SEALED_REVIEW_ONLY if inserted else SealState.ALREADY_SEALED_REVIEW_ONLY

    def lookup(self, binding: S0F03BoundReceiptLocal):
        if type(binding) is not S0F03BoundReceiptLocal:return None
        receipt=binding.receipt
        import psycopg
        with psycopg.connect(self._dsn,connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute('set transaction read only')
                cur.execute(_SELECT,(receipt.store_ref,receipt.closure_event_ref,receipt.case_ref))
                return cur.fetchone()


class S0F03LocalHistorySealingBridge:
    """No public F03 grant. Requires the actual S0 local history preflight."""
    def __init__(self, history: S0F03LocalHistoryManifestBridge,
                 reader: S0F03LocalPostgresHistoryReader,
                 store: S0F03LocalManifestSealStore):
        if (type(history) is not S0F03LocalHistoryManifestBridge
            or type(reader) is not S0F03LocalPostgresHistoryReader
            or type(store) is not S0F03LocalManifestSealStore
            or history._reader is not reader or reader._dsn != store._dsn):
            raise TypeError('requires coupled S0 authorized history and local store')
        self._history=history
        self._reader=reader
        self._store=store

    def seal(self, authorization: str, binding: S0F03BoundReceiptLocal) -> SealResult:
        if type(binding) is not S0F03BoundReceiptLocal:
            return SealResult(SealState.DENIED)
        try:
            before=self._history.inspect(authorization,binding)
            if before.state is not HistoryState.REVIEW_ONLY_NOT_FROZEN:
                return SealResult(_map_history(before.state))
            data=self._reader.load(binding.receipt)
            fingerprint=_snapshot(data)
            if fingerprint is None or (fingerprint[:3] != (
                    before.metadata_sha256,before.count,before.case_count)):
                return SealResult(SealState.STALE)
            if not any(r.message_ref == binding.receipt.message_watermark and
                       r.case_ref == binding.receipt.case_ref for r in data.rows):
                return SealResult(SealState.HISTORY_INCOMPLETE)
            # A second independent authenticated inspection detects changed
            # selection before local persistence; its proof is NOT a durable lock.
            second=self._history.inspect(authorization,binding)
            if (second.state is not HistoryState.REVIEW_ONLY_NOT_FROZEN
                or (second.metadata_sha256,second.count,second.case_count)
                != fingerprint[:3]):
                return SealResult(SealState.STALE)
            saved=self._store.capture(binding,data,fingerprint)
            if saved not in (SealState.SEALED_REVIEW_ONLY,
                             SealState.ALREADY_SEALED_REVIEW_ONLY):
                return SealResult(saved)
            # Recheck after commit. Retroactive inserts require future recheck;
            # cannot claim full historical completeness from this cycle.
            final=self._history.inspect(authorization,binding)
            if (final.state is not HistoryState.REVIEW_ONLY_NOT_FROZEN
                or (final.metadata_sha256,final.count,final.case_count)
                != fingerprint[:3]):
                return SealResult(SealState.STALE)
            return SealResult(saved)
        except Exception:
            return SealResult(SealState.UNAVAILABLE)

    def verify(self, authorization: str, binding: S0F03BoundReceiptLocal) -> SealResult:
        if type(binding) is not S0F03BoundReceiptLocal:
            return SealResult(SealState.DENIED)
        try:
            current=self._history.inspect(authorization,binding)
            if current.state is not HistoryState.REVIEW_ONLY_NOT_FROZEN:
                return SealResult(_map_history(current.state))
            live=self._reader.load(binding.receipt)
            fingerprint=_snapshot(live)
            if fingerprint is None or fingerprint[:3] != (
                    current.metadata_sha256,current.count,current.case_count):
                return SealResult(SealState.STALE)
            row=self._store.lookup(binding)
            if not isinstance(row,tuple) or len(row)!=9:
                return SealResult(SealState.HISTORY_INCOMPLETE)
            lead,version,case_sha,watermark,cutoff,count,cases,digest,meta=row
            receipt=binding.receipt
            if (str(lead)!=live.lead_ref or cutoff!=live.closure_at
                or type(version) is not int or version!=receipt.expected_cycle_version
                or case_sha!=receipt.snapshot_sha256
                or str(watermark)!=receipt.message_watermark
                or (digest,count,cases)!=fingerprint[:3]
                or meta!=json.loads(fingerprint[3])):
                return SealResult(SealState.STALE)
            final=self._history.inspect(authorization,binding)
            if (final.state is not HistoryState.REVIEW_ONLY_NOT_FROZEN
                or (final.metadata_sha256,final.count,final.case_count)!=fingerprint[:3]):
                return SealResult(SealState.STALE)
            # Still NOT a signed multi-case authorization or F03 content grant.
            return SealResult(SealState.MATCHES_LIVE_REVIEW_ONLY)
        except Exception:
            return SealResult(SealState.UNAVAILABLE)


def _map_history(state: HistoryState) -> SealState:
    if state is HistoryState.STALE:return SealState.STALE
    if state in (HistoryState.HISTORY_INCOMPLETE,):return SealState.HISTORY_INCOMPLETE
    if state is HistoryState.UNAVAILABLE:return SealState.UNAVAILABLE
    return SealState.DENIED
