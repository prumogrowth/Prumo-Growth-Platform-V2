"""S0-only E04 synthetic media digest/lineage attestation (read-only).

Cryptographically binds a TEST media-bytes digest and TEST transcript digest to
a S0-trusted PG17 message, closure, shop, case, purpose and retention. It never
asserts semantic correctness of a transcript, authentic STT, LGPD consent,
external provider signatures, human approval or any F03 access permission.

The existing F03 literal evidence gate must CONTINUE to reject all media.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
from uuid import UUID

from backend.s0_f03_crossfront_contract_local import (
    S0F03CrossFrontLocalBridge, CrossFrontState,
)
from backend.s0_f03_operational_contracts_local import ProposedField
from backend.s0_f03_version_reservation_local import VersionVector
from backend.s0_f03_crossfront_evidence_local import _uuid

PURPOSE='F03_POST_HUMAN_REVIEW_SYNTHETIC'
_SELECT="""select a.proposito,a.chave_versao,a.anexo_sha256,
a.transcricao_sha256,a.prova_hmac_sha256,a.valido_ate,
t.tipo,t.estado,t.anexo_sha256
from prumo_private.cfi01_f03_media_attestations_local a
join prumo_private.cfi01_f03_message_modalities_local t
 on t.concessionaria_id=a.concessionaria_id and t.mensagem_id=a.mensagem_id
join public.mensagens m on m.concessionaria_id=a.concessionaria_id
 and m.id=a.mensagem_id
join public.conversas v on v.concessionaria_id=m.concessionaria_id
 and v.id=m.conversa_id
join prumo_private.cfi01_human_closure_events_local e
 on e.id=a.evento_fechamento_id
 and e.concessionaria_id=a.concessionaria_id and e.caso_id=a.caso_id
join public.casos_humanos h on h.concessionaria_id=e.concessionaria_id
 and h.id=e.caso_id
where a.concessionaria_id=%s::uuid
 and a.evento_fechamento_id=%s::uuid
 and a.caso_id=%s::uuid
 and a.mensagem_id=%s::uuid
 and v.lead_id=h.lead_id and m.criada_em<=e.registrado_em
for share of a,t,m,v,e,h"""

class MediaAttestationState(str,Enum):
    MEDIA_DIGEST_REVIEW_ONLY='MEDIA_DIGEST_REVIEW_ONLY'
    DENIED='DENIED'
    MISSING_ATTESTATION='MISSING_ATTESTATION'
    EXPIRED_REVIEW_REQUIRED='EXPIRED_REVIEW_REQUIRED'
    INTEGRITY_REVIEW_REQUIRED='INTEGRITY_REVIEW_REQUIRED'
    STALE_REVIEW_REQUIRED='STALE_REVIEW_REQUIRED'
    UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class MediaAttestationResult:
    state:MediaAttestationState
    # Absolutely no media, transcript, hash, signed key or identity leaves S0.

def _digest(media:object,transcript:object)->tuple[str,str]|None:
    # Tiny fixed local synthetic assets; no production media ingest capability.
    if (type(media) is not bytes or not 1<=len(media)<=2097152
        or type(transcript) is not str or not 1<=len(transcript)<=20000
        or transcript!=transcript.strip() or '\x00' in transcript):
        return None
    return (hashlib.sha256(media).hexdigest(),
            hashlib.sha256(transcript.encode('utf-8')).hexdigest())

def _proof_hmac(secret:object,shop:object,closure:object,case:object,
                message:object,key_version:object,media_sha:object,
                transcript_sha:object,valid_until:object)->str|None:
    if (type(secret) is not bytes or len(secret)<32
        or any(_uuid(v) is None for v in (shop,closure,case,message))
        or type(key_version) is not str or not 8<=len(key_version)<=80
        or not isinstance(valid_until,datetime) or valid_until.tzinfo is None):
        return None
    if not all(isinstance(v,str) and len(v)==64
               and all(c in '0123456789abcdef' for c in v)
               for v in (media_sha,transcript_sha)):
        return None
    body=[shop,closure,case,message,PURPOSE,key_version,media_sha,
          transcript_sha,valid_until.isoformat()]
    return hmac.new(secret,json.dumps(body,ensure_ascii=False,separators=(',',':')
                    ).encode('utf-8'),hashlib.sha256).hexdigest()

class S0F03LocalMediaAttestationBridge:
    def __init__(self,base:S0F03CrossFrontLocalBridge):
        if type(base) is not S0F03CrossFrontLocalBridge:
            raise TypeError('requires S0 physical reviewer, not S2 model')
        self._base=base

    def inspect(self,authorization:str,binding:object,key_version:str,
                secret:bytes,version:VersionVector,request_ref:str,
                fields:tuple[ProposedField,...],s2_output:dict,
                message_id:str,synthetic_media_bytes:bytes,
                synthetic_transcript:str)->MediaAttestationResult:
        # Authenticity first; raw media is explicitly a S0-owned TEST input.
        hashes=_digest(synthetic_media_bytes,synthetic_transcript)
        if (_uuid(message_id) is None or hashes is None):
            return MediaAttestationResult(MediaAttestationState.DENIED)
        initial=self._base.inspect(authorization,binding,key_version,secret,
                                   version,request_ref,fields,s2_output)
        if initial.state is not CrossFrontState.REVIEW_ONLY:
            return MediaAttestationResult(
                MediaAttestationState.UNAVAILABLE if initial.state is CrossFrontState.UNAVAILABLE
                else MediaAttestationState.DENIED if initial.state is CrossFrontState.DENIED
                else MediaAttestationState.STALE_REVIEW_REQUIRED)
        r=binding.receipt
        try:
            import psycopg
            with psycopg.connect(self._base._contract._store._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute("set local lock_timeout='3s'")
                    cur.execute(_SELECT,(r.store_ref,r.closure_event_ref,
                                         r.case_ref,message_id))
                    row=cur.fetchone()
                    if row is None or len(row)!=9:
                        return MediaAttestationResult(
                            MediaAttestationState.MISSING_ATTESTATION)
                    (purpose,key,media_sha,transcript_sha,mac,expiry,
                     kind,classification,source_sha)=row
                    if purpose!=PURPOSE or key!=key_version:
                        return MediaAttestationResult(
                            MediaAttestationState.INTEGRITY_REVIEW_REQUIRED)
                    if (type(expiry) is not datetime or expiry.tzinfo is None
                        or expiry<=datetime.now(timezone.utc)):
                        return MediaAttestationResult(
                            MediaAttestationState.EXPIRED_REVIEW_REQUIRED)
                    if (kind not in ('AUDIO','DOCUMENT')
                        or classification!='MEDIA_UNVERIFIED'
                        or source_sha!=media_sha
                        or not hmac.compare_digest(media_sha,hashes[0])
                        or not hmac.compare_digest(transcript_sha,hashes[1])):
                        return MediaAttestationResult(
                            MediaAttestationState.INTEGRITY_REVIEW_REQUIRED)
                    expected=_proof_hmac(secret,r.store_ref,r.closure_event_ref,
                        r.case_ref,message_id,key_version,media_sha,
                        transcript_sha,expiry)
                    if (expected is None or not hmac.compare_digest(expected,mac)):
                        return MediaAttestationResult(
                            MediaAttestationState.INTEGRITY_REVIEW_REQUIRED)
            final=self._base.inspect(authorization,binding,key_version,secret,
                                     version,request_ref,fields,s2_output)
            if final.state is not CrossFrontState.REVIEW_ONLY:
                return MediaAttestationResult(
                    MediaAttestationState.STALE_REVIEW_REQUIRED)
            # REVIEW ONLY. Existing textual F03 evidence remains blocked.
            return MediaAttestationResult(
                MediaAttestationState.MEDIA_DIGEST_REVIEW_ONLY)
        except Exception:
            return MediaAttestationResult(MediaAttestationState.UNAVAILABLE)
