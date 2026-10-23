"""S0-owned F03 multi-case HISTORY METADATA preflight, disposable PG only.

Additive bridge for the existing CFI-01 S0 receipt. Never returns content to F03,
asserts a frozen multi-case snapshot, writes a form, or bypasses S0/S1. The
currently available closure receipt freezes one case only; cross-case closure
integrity and per-field versions still require a separate physical S0 contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any
from uuid import UUID

from backend.s0_cfi01_f03_receipt_bridge_local import (
    S0CFI01F03ReceiptBridgeLocal, S0F03BoundReceiptLocal, S0F03BridgeState,
)
from backend.s0_human_closure_event_local import S0LocalClosureStore

# Query only S0-owned records, never a client/model-provided identity or cutoff.
# Both queries run in a disposable PostgreSQL snapshot read transaction.
_CONTEXT_SQL = """select h.lead_id,e.registrado_em
from prumo_private.cfi01_human_closure_events_local e
join public.casos_humanos h on h.id=e.caso_id
 and h.concessionaria_id=e.concessionaria_id
where e.id=%s::uuid and e.concessionaria_id=%s::uuid
 and e.caso_id=%s::uuid and e.snapshot_sha256=%s::text
 and e.versao_ciclo=%s::bigint and e.ultima_mensagem_id=%s::uuid
 and e.quantidade_mensagens=%s::integer"""
_HISTORY_SQL = """select m.id,v.caso_id,v.id,m.criada_em,m.direcao,m.origem,m.enviada_por
from public.mensagens m
join public.conversas v on v.id=m.conversa_id
 and v.concessionaria_id=m.concessionaria_id
where m.concessionaria_id=%s::uuid and v.lead_id=%s::uuid
 and m.criada_em<=%s::timestamptz
order by m.criada_em,m.id"""

MAX_HISTORY_RECORDS = 10000  # safety bound; overflow blocks, never truncates


class HistoryState(str, Enum):
    REVIEW_ONLY_NOT_FROZEN = 'REVIEW_ONLY_NOT_FROZEN'
    DENIED = 'DENIED'
    INPUT_REJECTED = 'INPUT_REJECTED'
    STALE = 'STALE'
    UNAVAILABLE = 'UNAVAILABLE'
    HISTORY_INCOMPLETE = 'HISTORY_INCOMPLETE'


@dataclass(frozen=True)
class HistoricalMessageRef:
    message_ref: str
    case_ref: str | None
    conversation_ref: str
    created_at: datetime
    direction: str
    origin: str
    author_ref: str | None


@dataclass(frozen=True)
class HistoricalRead:
    lead_ref: str
    closure_at: datetime
    rows: tuple[HistoricalMessageRef, ...]


@dataclass(frozen=True)
class HistoryResult:
    state: HistoryState
    count: int = 0
    case_count: int = 0
    metadata_sha256: str | None = None
    # Deliberately no lead UUID, customer text, field proposals or model grant.


def _uuid(s: object) -> bool:
    if type(s) is not str:
        return False
    try:
        return str(UUID(s)) == s
    except (ValueError, TypeError, AttributeError):
        return False


def _mapped(state: S0F03BridgeState) -> HistoryState:
    return {
        S0F03BridgeState.INPUT_REJECTED: HistoryState.INPUT_REJECTED,
        S0F03BridgeState.STALE: HistoryState.STALE,
        S0F03BridgeState.UNAVAILABLE: HistoryState.UNAVAILABLE,
    }.get(state, HistoryState.DENIED)


class S0F03LocalPostgresHistoryReader:
    """Uses the existing S0 local DSN guard without inheriting write methods."""

    def __init__(self, dsn: str):
        self._dsn = S0LocalClosureStore(dsn)._dsn

    def load(self, receipt: object) -> HistoricalRead | None:
        from backend.s0_cfi01_atomic_commands_local import S0InternalReceiptLocal
        if type(receipt) is not S0InternalReceiptLocal:
            return None
        if not all(_uuid(x) for x in (
            receipt.store_ref, receipt.case_ref, receipt.closure_event_ref,
            receipt.message_watermark,
        )):
            return None
        import psycopg
        with psycopg.connect(self._dsn, connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute('set transaction isolation level repeatable read read only')
                cur.execute(_CONTEXT_SQL, (
                    receipt.closure_event_ref, receipt.store_ref,
                    receipt.case_ref, receipt.snapshot_sha256,
                    receipt.expected_cycle_version, receipt.message_watermark,
                    receipt.message_count,
                ))
                rows = cur.fetchall()
                if len(rows) != 1:
                    return None
                lead_ref, closure_at = rows[0]
                if not isinstance(lead_ref, UUID) or type(closure_at) is not datetime or closure_at.tzinfo is None:
                    return None
                cur.execute(_HISTORY_SQL, (receipt.store_ref, lead_ref, closure_at))
                # Fetch one beyond cap so overflow is visible rather than truncated.
                history_rows = cur.fetchmany(MAX_HISTORY_RECORDS + 1)
                if len(history_rows) > MAX_HISTORY_RECORDS:
                    return None
        converted = []
        for row in history_rows:
            if len(row) != 7:
                return None
            message, case, conversation, timestamp, direction, origin, author = row
            if (not isinstance(message, UUID) or
                (case is not None and not isinstance(case, UUID)) or
                not isinstance(conversation, UUID) or
                type(timestamp) is not datetime or timestamp.tzinfo is None or
                type(direction) is not str or type(origin) is not str or
                (author is not None and not isinstance(author, UUID))):
                return None
            converted.append(HistoricalMessageRef(
                str(message), str(case) if case else None, str(conversation),
                timestamp, direction, origin, str(author) if author else None,
            ))
        return HistoricalRead(str(lead_ref), closure_at, tuple(converted))


class S0F03LocalHistoryManifestBridge:
    """Cross-case S0 read *after and before* authenticated receipt rechecks.

    This is metadata inspection, never a physical authorization for F03. The
    reader must be the concrete local-only S0 reader, not caller-selected data.
    """
    def __init__(self, bridge: S0CFI01F03ReceiptBridgeLocal,
                 reader: S0F03LocalPostgresHistoryReader):
        if type(bridge) is not S0CFI01F03ReceiptBridgeLocal:
            raise TypeError('requires existing S0 F03 authenticated bridge')
        if type(reader) is not S0F03LocalPostgresHistoryReader:
            raise TypeError('requires local-only S0 PostgreSQL history reader')
        self._bridge = bridge
        self._reader = reader

    def inspect(self, authorization: str,
                binding: S0F03BoundReceiptLocal) -> HistoryResult:
        before = self._bridge.recheck(authorization, binding)
        if before.state is not S0F03BridgeState.VERIFIED_CONTRACT_PENDING:
            return HistoryResult(_mapped(before.state))
        if type(before.binding) is not S0F03BoundReceiptLocal or before.binding != binding:
            return HistoryResult(HistoryState.DENIED)
        try:
            data = self._reader.load(binding.receipt)
        except Exception:
            return HistoryResult(HistoryState.UNAVAILABLE)
        if type(data) is not HistoricalRead or not _uuid(data.lead_ref) or not data.rows:
            return HistoryResult(HistoryState.HISTORY_INCOMPLETE)
        if type(data.closure_at) is not datetime or data.closure_at.tzinfo is None:
            return HistoryResult(HistoryState.HISTORY_INCOMPLETE)
        fingerprints: list[list[str | None]] = []
        seen = set()
        prior = None
        cases = set()
        found_closure_watermark = False
        for row in data.rows:
            if (type(row) is not HistoricalMessageRef or
                not _uuid(row.message_ref) or
                (row.case_ref is not None and not _uuid(row.case_ref)) or
                not _uuid(row.conversation_ref) or
                (row.author_ref is not None and not _uuid(row.author_ref)) or
                type(row.created_at) is not datetime or row.created_at.tzinfo is None or
                row.created_at > data.closure_at or
                type(row.direction) is not str or type(row.origin) is not str or
                row.message_ref in seen):
                return HistoryResult(HistoryState.HISTORY_INCOMPLETE)
            sort_key = (row.created_at, row.message_ref)
            if prior is not None and sort_key < prior:
                return HistoryResult(HistoryState.HISTORY_INCOMPLETE)
            prior = sort_key
            seen.add(row.message_ref)
            if row.case_ref:
                cases.add(row.case_ref)
            if row.message_ref == binding.receipt.message_watermark and row.case_ref == binding.receipt.case_ref:
                found_closure_watermark = True
            fingerprints.append([
                row.message_ref,row.case_ref,row.conversation_ref,
                row.created_at.isoformat(),row.direction,row.origin,row.author_ref,
            ])
        if not found_closure_watermark:
            return HistoryResult(HistoryState.HISTORY_INCOMPLETE)
        after = self._bridge.recheck(authorization, binding)
        if after.state is not S0F03BridgeState.VERIFIED_CONTRACT_PENDING:
            return HistoryResult(_mapped(after.state))
        if after.binding != before.binding:
            return HistoryResult(HistoryState.STALE)
        fingerprint = hashlib.sha256(json.dumps(
            fingerprints, separators=(',', ':'), ensure_ascii=False,
        ).encode('utf-8')).hexdigest()
        # Historical metadata can be inspected, but completeness is not sealed
        # by the existing *case-local* receipt: never promote to READY/APPLY.
        return HistoryResult(
            HistoryState.REVIEW_ONLY_NOT_FROZEN,len(fingerprints),len(cases),fingerprint)
