"""E04 S0 only: verify synthetic field values against physical text sources.

S2 supplies UNTRUSTED source IDs and values. Each must match a strictly
structured S0 fixture message (field=value) on the same lead/shop by cutoff.
Not semantic NLP, audio evidence, permission, customer access, or any write.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hmac
import uuid
from backend.s0_f03_crossfront_contract_local import S0F03CrossFrontLocalBridge,CrossFrontState
from backend.s0_f03_operational_contracts_local import ProposedField,proposal_digest
from backend.s0_f03_bound_content_seal_local import _valid,_LOCK_LEAD,_LOCK_CONVERSATIONS
from backend.s0_f03_content_integrity_local import _CONTENT_SQL,_derive
from backend.s0_f03_history_manifest_local import _CONTEXT_SQL,MAX_HISTORY_RECORDS
from backend.s0_f03_field_application_local import _SAVED_HMAC
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_cfi01_f03_receipt_bridge_local import S0F03BoundReceiptLocal

_MODALITIES = """select mensagem_id,tipo,estado
from prumo_private.cfi01_f03_message_modalities_local
where concessionaria_id=%s::uuid and mensagem_id=any(%s::uuid[])
order by mensagem_id for share"""

class EvidenceState(str,Enum):
    S0_EVIDENCE_REVIEW_ONLY='S0_EVIDENCE_REVIEW_ONLY'
    DENIED='DENIED'
    SOURCE_REVIEW_REQUIRED='SOURCE_REVIEW_REQUIRED'
    MEDIA_REVIEW_REQUIRED='MEDIA_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED='CONFLICT_REVIEW_REQUIRED'
    STALE_REVIEW_REQUIRED='STALE_REVIEW_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class EvidenceResult:
    state:EvidenceState

def _uuid(value:object)->uuid.UUID|None:
    if type(value) is not str:return None
    try:
        out=uuid.UUID(value)
        return out if str(out)==value else None
    except (TypeError,ValueError,AttributeError):
        return None

def _untrusted_sources(proposal:object,fields:object)->dict[str,uuid.UUID]|None:
    if type(fields) is not tuple or proposal_digest(fields) is None:return None
    if (type(proposal) is not dict
        or set(proposal)!={'proposalRef','fields','conflicts','advisory'}
        or type(proposal['proposalRef']) is not str
        or not 1<=len(proposal['proposalRef'])<=120
        or type(proposal['fields']) is not list
        or len(proposal['fields'])!=len(fields)
        or proposal['conflicts']!=[] or proposal['advisory'] is not None):
        return None
    expected={f.field_key:f for f in fields}
    sources={}
    for item in proposal['fields']:
        if (type(item) is not dict or set(item)!={'code','value','sourceId'}
            or type(item['code']) is not str
            or item['code'] not in expected or item['code'] in sources
            or type(item['value']) is not str
            or item['value']!=expected[item['code']].value
            or _uuid(item['sourceId']) is None):
            return None
        sources[item['code']]=_uuid(item['sourceId'])
    return sources if set(sources)==set(expected) else None

def _synthetic_claim(content:object,code:str)->str|None:
    """Exact field=value synthetic fixture, never free-form NLP extraction."""
    if type(content) is not str or type(code) is not str:return None
    prefix=code+'='
    if not content.startswith(prefix):return None
    value=content[len(prefix):]
    if (not 1<=len(value)<=128 or value!=value.strip()
        or any(ord(c)<32 for c in value)):
        return None
    return value

class S0F03LocalEvidenceReviewBridge:
    """Read-only physical provenance after full authenticated S0 review gate."""
    def __init__(self,base:S0F03CrossFrontLocalBridge):
        if type(base) is not S0F03CrossFrontLocalBridge:
            raise TypeError('requires physical S0 crossfront validator')
        self._base=base

    def inspect(self,authorization:str,binding:S0F03BoundReceiptLocal,
                key_version:str,secret:bytes,version:VersionVector,
                request_ref:str,fields:tuple[ProposedField,...],
                s2_output:dict,s2_proposal:dict)->EvidenceResult:
        sources=_untrusted_sources(s2_proposal,fields)
        if sources is None or not _valid(binding,key_version,secret):
            return EvidenceResult(EvidenceState.DENIED)
        prior=self._base.inspect(authorization,binding,key_version,secret,
                                 version,request_ref,fields,s2_output)
        if prior.state is not CrossFrontState.REVIEW_ONLY:
            if prior.state is CrossFrontState.UNAVAILABLE:
                return EvidenceResult(EvidenceState.UNAVAILABLE)
            if prior.state is CrossFrontState.CONFLICT_REVIEW_REQUIRED:
                return EvidenceResult(EvidenceState.CONFLICT_REVIEW_REQUIRED)
            if prior.state is CrossFrontState.DENIED:
                return EvidenceResult(EvidenceState.DENIED)
            return EvidenceResult(EvidenceState.STALE_REVIEW_REQUIRED)
        r=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._base._contract._store._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_CONTEXT_SQL,(
                        r.closure_event_ref,r.store_ref,r.case_ref,
                        r.snapshot_sha256,r.expected_cycle_version,
                        r.message_watermark,r.message_count))
                    ctx=cur.fetchall()
                    if len(ctx)!=1 or type(ctx[0][0]) is not uuid.UUID:
                        return EvidenceResult(EvidenceState.STALE_REVIEW_REQUIRED)
                    lead,cutoff=ctx[0]
                    cur.execute(_LOCK_LEAD,(r.store_ref,lead))
                    if len(cur.fetchall())!=1:
                        return EvidenceResult(EvidenceState.STALE_REVIEW_REQUIRED)
                    cur.execute(_LOCK_CONVERSATIONS,(r.store_ref,lead))
                    if not cur.fetchall():
                        return EvidenceResult(EvidenceState.STALE_REVIEW_REQUIRED)
                    cur.execute(_CONTENT_SQL+' for share of m',(r.store_ref,lead,cutoff))
                    rows=cur.fetchmany(MAX_HISTORY_RECORDS+1)
                    proof=_derive(rows,r,str(lead),cutoff,secret)
                    if proof is None:
                        return EvidenceResult(EvidenceState.STALE_REVIEW_REQUIRED)
                    cur.execute(_SAVED_HMAC,(r.store_ref,r.closure_event_ref,r.case_ref))
                    saved=cur.fetchone()
                    if (saved is None or len(saved)!=5
                        or saved[0]!=key_version or saved[1]!=proof.metadata_sha256
                        or saved[3]!=proof.count or saved[4]!=proof.case_count
                        or not hmac.compare_digest(saved[2],proof.content_mac_sha256)):
                        return EvidenceResult(EvidenceState.STALE_REVIEW_REQUIRED)
                    # Classifications are immutable S0-only PG17 fixtures,
                    # NEVER model declared. Missing/multimodal media anywhere
                    # in this history may hide conflicting evidence, so fail
                    # closed even if the chosen source looks like normal text.
                    ids=[row[0] for row in rows]
                    cur.execute(_MODALITIES,(r.store_ref,ids))
                    classified=cur.fetchall()
                    if (len(classified)!=len(ids)
                        or {m[0] for m in classified}!=set(ids)):
                        return EvidenceResult(EvidenceState.MEDIA_REVIEW_REQUIRED)
                    if any(m[1]!='TEXT' or m[2]!='NATIVE_TEXT_FIXTURE'
                           for m in classified):
                        return EvidenceResult(EvidenceState.MEDIA_REVIEW_REQUIRED)
                    for field in fields:
                        found={}
                        for row in rows:
                            value=_synthetic_claim(row[7],field.field_key)
                            if value is not None:found[row[0]]=value
                        if (sources[field.field_key] not in found
                            or found[sources[field.field_key]]!=field.value):
                            return EvidenceResult(EvidenceState.SOURCE_REVIEW_REQUIRED)
                        if len(set(found.values()))!=1:
                            return EvidenceResult(EvidenceState.CONFLICT_REVIEW_REQUIRED)
            final=self._base.inspect(authorization,binding,key_version,secret,
                                     version,request_ref,fields,s2_output)
            if final.state is not CrossFrontState.REVIEW_ONLY:
                return EvidenceResult(EvidenceState.STALE_REVIEW_REQUIRED)
            return EvidenceResult(EvidenceState.S0_EVIDENCE_REVIEW_ONLY)
        except Exception:
            return EvidenceResult(EvidenceState.UNAVAILABLE)
