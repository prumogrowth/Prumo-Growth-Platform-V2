"""F03 S0-only keyed integrity check of LOCAL synthetic message text.

This is not an OpenAI payload, authorization grant, or full historic lock.
Key must be delivered by trusted S0 at runtime; never embed production keys.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import hmac
import json
from uuid import UUID

# Independent from the metadata reader for least privilege; local PG guard reused.
from backend.s0_human_closure_event_local import S0LocalClosureStore
from backend.s0_cfi01_atomic_commands_local import S0InternalReceiptLocal
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL, _uuid, MAX_HISTORY_RECORDS

_CONTENT_SQL = """select m.id,v.caso_id,v.id,m.criada_em,m.direcao,m.origem,m.enviada_por,m.conteudo_sintetico
from public.mensagens m
join public.conversas v on v.id=m.conversa_id
 and v.concessionaria_id=m.concessionaria_id
where m.concessionaria_id=%s::uuid and v.lead_id=%s::uuid
 and m.criada_em<=%s::timestamptz
order by m.criada_em,m.id"""

class ContentState(str, Enum):
    MATCHES_REVIEW_ONLY = 'MATCHES_REVIEW_ONLY'
    CHANGED_REVIEW_REQUIRED = 'CHANGED_REVIEW_REQUIRED'
    INPUT_REJECTED = 'INPUT_REJECTED'
    INCOMPLETE = 'INCOMPLETE'
    UNAVAILABLE = 'UNAVAILABLE'

@dataclass(frozen=True)
class ContentProof:
    """Internal S0 only: no content or key; must never be sent to model."""
    metadata_sha256: str
    content_mac_sha256: str
    count: int
    case_count: int
    # A MAC does NOT freeze inserts that occur after this read.


def _derive(rows: object, receipt: S0InternalReceiptLocal, lead: str,
            cutoff: datetime, key: bytes) -> ContentProof | None:
    if (type(receipt) is not S0InternalReceiptLocal or not _uuid(lead)
        or not isinstance(key, bytes) or len(key)<32
        or type(cutoff) is not datetime or cutoff.tzinfo is None
        or not isinstance(rows, (tuple, list)) or not 1<=len(rows)<=MAX_HISTORY_RECORDS):
        return None
    meta=[]; packed=[]; seen=set(); prev=None; cases=set(); watermark=False
    for row in rows:
        if not isinstance(row, (tuple,list)) or len(row)!=8:return None
        mid,case,conv,at,direction,origin,author,content=row
        if (not isinstance(mid, UUID) or (case is not None and not isinstance(case, UUID))
            or not isinstance(conv, UUID) or (author is not None and not isinstance(author, UUID))
            or type(at) is not datetime or at.tzinfo is None or at>cutoff
            or not isinstance(direction,str) or not isinstance(origin,str)
            or not isinstance(content,str) or not content or len(content)>20000
            or str(mid) in seen):return None
        sort=(at,str(mid))
        if prev is not None and sort<prev:return None
        prev=sort;seen.add(str(mid))
        if case:cases.add(str(case))
        if str(mid)==receipt.message_watermark and str(case)==receipt.case_ref:
            watermark=True
        metadata=[str(mid),str(case) if case else None,str(conv),at.isoformat(),
                  direction,origin,str(author) if author else None]
        meta.append(metadata)
        packed.append([*metadata,content])
    if not watermark:return None
    meta_bytes=json.dumps(meta,separators=(',', ':'),ensure_ascii=False).encode('utf-8')
    # Bind MAC to shop, case closure, lead, time, existing case receipt and all text.
    scope=[receipt.store_ref,receipt.case_ref,receipt.closure_event_ref,
           lead,cutoff.isoformat(),receipt.snapshot_sha256,receipt.message_watermark,packed]
    mac=hmac.new(key,json.dumps(scope,separators=(',', ':'),ensure_ascii=False).encode('utf-8'),hashlib.sha256).hexdigest()
    return ContentProof(hashlib.sha256(meta_bytes).hexdigest(),mac,len(meta),len(cases))

class S0F03LocalContentIntegrityReader:
    """Reads S0-scope text privately; returns MAC only, not raw customer text."""
    def __init__(self, dsn: str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def compute(self, receipt: object, key: bytes) -> ContentProof | None:
        if (type(receipt) is not S0InternalReceiptLocal or not isinstance(key,bytes)
            or len(key)<32 or not all(_uuid(x) for x in (
                receipt.store_ref,receipt.case_ref,receipt.closure_event_ref,
                receipt.message_watermark))):return None
        import psycopg
        with psycopg.connect(self._dsn,connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute('set transaction isolation level repeatable read read only')
                cur.execute(_CONTEXT_SQL,(
                    receipt.closure_event_ref,receipt.store_ref,receipt.case_ref,
                    receipt.snapshot_sha256,receipt.expected_cycle_version,
                    receipt.message_watermark,receipt.message_count))
                found=cur.fetchall()
                if len(found)!=1:return None
                lead,cutoff=found[0]
                if not isinstance(lead,UUID):return None
                cur.execute(_CONTENT_SQL,(receipt.store_ref,lead,cutoff))
                rows=cur.fetchmany(MAX_HISTORY_RECORDS+1)
                if len(rows)>MAX_HISTORY_RECORDS:return None
        return _derive(rows,receipt,str(lead),cutoff,key)


def _equal_proof(expected: object, actual: object)->ContentState:
    if type(expected) is not ContentProof or type(actual) is not ContentProof:
        return ContentState.INCOMPLETE
    if (expected.metadata_sha256!=actual.metadata_sha256
        or expected.count!=actual.count or expected.case_count!=actual.case_count
        or not hmac.compare_digest(expected.content_mac_sha256,actual.content_mac_sha256)):
        return ContentState.CHANGED_REVIEW_REQUIRED
    return ContentState.MATCHES_REVIEW_ONLY
