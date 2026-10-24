"""Second-person S0/S1 identity attestation, LOCAL PG17 E04 only.

An existing human decision CANDIDATE_NOT_RELATED can be independently
ratified by a different active S1 manager. Neither this ratification nor the
first review clears S0/028 pending conflicts or authorizes F03 content/writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import uuid

from backend.identity_boundary import Principal, Denied, IdentityProvider
from backend.s0_human_closure_event_local import (
    S0LocalClosureStore, S1TransactionAuthority, S1Proof, _SESSION, _uuid,
)
from backend.s0_f03_identity_human_review_local import _CANDIDATE

class RatificationState(str, Enum):
    RATIFIED_AUDIT_ONLY = 'RATIFIED_AUDIT_ONLY'
    ALREADY_RATIFIED_AUDIT_ONLY = 'ALREADY_RATIFIED_AUDIT_ONLY'
    DENIED = 'DENIED'
    BLOCKED_S1 = 'BLOCKED_S1'
    STALE_REVIEW_REQUIRED = 'STALE_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED = 'CONFLICT_REVIEW_REQUIRED'
    UNAVAILABLE = 'UNAVAILABLE'

@dataclass(frozen=True)
class RatificationRequest:
    review_ref: str
    case_ref: str
    pending_ref: str
    expected_cycle_version: int
    expected_identity_version: int
    evidence_sha256: str
    idempotency_key: str

@dataclass(frozen=True)
class RatificationResult:
    state: RatificationState
    # Not a merge, identity mapping, pending resolution or F03 authorization.

_CONTEXT = """select r.concessionaria_id,r.lead_candidato_id,r.ator_id,
 r.decisao,r.versao_ciclo,r.versao_identidade,
 c.versao_registro,v.versao_identidade,a.encerrada_em
from prumo_private.cfi01_f03_identity_human_reviews_local r
join public.casos_humanos h on
 h.concessionaria_id=r.concessionaria_id and h.id=r.caso_id
 and h.lead_id=r.lead_candidato_id
join public.ciclos_comerciais c on
 c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
 and c.lead_id=h.lead_id
join public.atribuicoes_humanas a on
 a.concessionaria_id=r.concessionaria_id and a.id=r.atribuicao_id
 and a.caso_id=r.caso_id and a.operador_id=r.ator_id
join prumo_private.cfi01_f03_lead_versions_local v on
 v.concessionaria_id=r.concessionaria_id and v.lead_id=r.lead_candidato_id
where r.id=%s::uuid and r.caso_id=%s::uuid and r.pendencia_id=%s::uuid
for share of r,h,c,a for update of v"""
_MANAGER_SCOPE = """select 1 from public.vinculos_papel_escopo g
where g.ator_id=%s::uuid and g.concessionaria_id=%s::uuid
 and g.papel='gestor'
 and g.valido_desde<=statement_timestamp()
 and (g.valido_ate is null or g.valido_ate>statement_timestamp())
for share of g"""
_PENDING_LOCK = """select 1 from prumo_private.pendencias_identidade_s0
 where concessionaria_id=%s::uuid and id=%s::uuid for update"""
_EXISTING = """select revisao_id,ratificador_id,sessao_id,versao_ciclo,
 versao_identidade,decisao,evidencia_sha256,chave_idempotencia
from prumo_private.cfi01_f03_identity_ratifications_local
where concessionaria_id=%s::uuid and pendencia_id=%s::uuid and caso_id=%s::uuid
for update"""
_INSERT = """insert into prumo_private.cfi01_f03_identity_ratifications_local
(concessionaria_id,pendencia_id,caso_id,revisao_id,lead_candidato_id,
 ratificador_id,sessao_id,versao_ciclo,versao_identidade,decisao,
 evidencia_sha256,chave_idempotencia)
values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,
 %s::uuid,%s::uuid,%s::bigint,%s::bigint,%s::text,%s::text,%s::text)
on conflict (concessionaria_id,pendencia_id,caso_id) do nothing returning id"""

_DECISION = 'RATIFY_CANDIDATE_NOT_RELATED'

def _valid(request: object) -> bool:
    return (type(request) is RatificationRequest
            and all(_uuid(v) is not None for v in (
                request.review_ref,request.case_ref,request.pending_ref))
            and type(request.expected_cycle_version) is int
            and 1 <= request.expected_cycle_version < 9223372036854775807
            and type(request.expected_identity_version) is int
            and 1 <= request.expected_identity_version < 9223372036854775807
            and type(request.evidence_sha256) is str
            and re.fullmatch(r'[0-9a-f]{64}',request.evidence_sha256) is not None
            and type(request.idempotency_key) is str
            and re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',
                             request.idempotency_key) is not None)

class S0F03LocalRatificationStore:
    """Strictly server-side, with live S0/S1 case/version/session validation."""
    def __init__(self, dsn: str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def capture(self, principal: Principal, request: RatificationRequest,
                s1: S1TransactionAuthority | None) -> RatificationResult:
        if s1 is None:
            return RatificationResult(RatificationState.BLOCKED_S1)
        import psycopg
        with psycopg.connect(self._dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("set local lock_timeout = '3s'")
                cur.execute(_SESSION,(principal.session_id,principal.actor_id))
                if cur.fetchone() is None:
                    return RatificationResult(RatificationState.DENIED)
                # S1's team lock is obtained before touching any case.
                if s1.lock_team(cur,principal) is not S1Proof.ALLOW:
                    return RatificationResult(RatificationState.BLOCKED_S1)
                cur.execute(_CONTEXT,(
                    _uuid(request.review_ref),_uuid(request.case_ref),
                    _uuid(request.pending_ref)))
                ctx=cur.fetchone()
                if ctx is None:
                    return RatificationResult(RatificationState.DENIED)
                (shop,lead,reviewer,decision,review_cycle,review_identity,
                 cycle,identity_version,assignment_closed)=ctx
                if reviewer==principal.actor_id or decision!='CANDIDATE_NOT_RELATED':
                    return RatificationResult(RatificationState.DENIED)
                if (assignment_closed is not None
                    or review_cycle!=request.expected_cycle_version
                    or cycle!=request.expected_cycle_version
                    or review_identity!=request.expected_identity_version
                    or identity_version!=request.expected_identity_version):
                    return RatificationResult(RatificationState.STALE_REVIEW_REQUIRED)
                cur.execute(_MANAGER_SCOPE,(principal.actor_id,shop))
                if cur.fetchone() is None:
                    return RatificationResult(RatificationState.DENIED)
                cur.execute(_PENDING_LOCK,(shop,_uuid(request.pending_ref)))
                if cur.fetchone() is None:
                    return RatificationResult(RatificationState.DENIED)
                cur.execute(_CANDIDATE,(lead,shop,_uuid(request.pending_ref)))
                if cur.fetchone() is None:
                    return RatificationResult(RatificationState.STALE_REVIEW_REQUIRED)
                cur.execute(_EXISTING,(shop,_uuid(request.pending_ref),
                                       _uuid(request.case_ref)))
                previous=cur.fetchone()
                signature=(_uuid(request.review_ref),principal.actor_id,
                           principal.session_id,request.expected_cycle_version,
                           request.expected_identity_version,_DECISION,
                           request.evidence_sha256,request.idempotency_key)
                if previous is not None:
                    state=(RatificationState.ALREADY_RATIFIED_AUDIT_ONLY
                           if previous==signature
                           else RatificationState.CONFLICT_REVIEW_REQUIRED)
                    return RatificationResult(state)
                cur.execute(_INSERT,(
                    shop,_uuid(request.pending_ref),_uuid(request.case_ref),
                    _uuid(request.review_ref),lead,principal.actor_id,
                    principal.session_id,request.expected_cycle_version,
                    request.expected_identity_version,_DECISION,
                    request.evidence_sha256,request.idempotency_key))
                if cur.fetchone() is None:
                    return RatificationResult(RatificationState.CONFLICT_REVIEW_REQUIRED)
                return RatificationResult(RatificationState.RATIFIED_AUDIT_ONLY)

def ratify_human_identity_review_local(
    authorization: str,request: RatificationRequest, *,
    identity: IdentityProvider,store: S0F03LocalRatificationStore,
    s1: S1TransactionAuthority | None = None,
) -> RatificationResult:
    if not _valid(request) or type(store) is not S0F03LocalRatificationStore:
        return RatificationResult(RatificationState.DENIED)
    try:
        principal=identity.verify(authorization)
        if (type(principal) is not Principal or
            type(principal.actor_id) is not uuid.UUID or
            type(principal.session_id) is not uuid.UUID):
            return RatificationResult(RatificationState.DENIED)
        return store.capture(principal,request,s1)
    except Denied:
        return RatificationResult(RatificationState.DENIED)
    except Exception:
        return RatificationResult(RatificationState.UNAVAILABLE)
