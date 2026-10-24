"""S0-only human identity disposition for unresolved S0/028 synthetic contact.

A durable audit observation, NOT resolution, claim of identity, or a F03
authorization. Human identity and S1 role are checked inside the S0
transaction using trusted IdentityProvider and live auth.session / S1 data.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
import uuid

from backend.identity_boundary import Principal, Denied, IdentityProvider
from backend.s0_human_closure_event_local import (
    S0LocalClosureStore, S1TransactionAuthority, S1Proof, _SESSION, _CASE,
    _GRANT, _uuid,
)

class HumanReviewDecision(str, Enum):
    ESCALATE_REVIEW = "ESCALATE_REVIEW"
    CANDIDATE_POSSIBLY_RELATED = "CANDIDATE_POSSIBLY_RELATED"
    CANDIDATE_NOT_RELATED = "CANDIDATE_NOT_RELATED"

class HumanReviewState(str, Enum):
    RECORDED_REVIEW_ONLY = "RECORDED_REVIEW_ONLY"
    ALREADY_RECORDED_REVIEW_ONLY = "ALREADY_RECORDED_REVIEW_ONLY"
    DENIED = "DENIED"
    BLOCKED_S1 = "BLOCKED_S1"
    STALE_REVIEW_REQUIRED = "STALE_REVIEW_REQUIRED"
    NOT_RELATED_REVIEW_REQUIRED = "NOT_RELATED_REVIEW_REQUIRED"
    CONFLICT_REVIEW_REQUIRED = "CONFLICT_REVIEW_REQUIRED"
    UNAVAILABLE = "UNAVAILABLE"

@dataclass(frozen=True)
class HumanReviewRequest:
    case_ref: str
    pending_ref: str
    expected_cycle_version: int
    expected_identity_version: int
    decision: HumanReviewDecision
    evidence_sha256: str
    idempotency_key: str

@dataclass(frozen=True)
class HumanReviewResult:
    state: HumanReviewState
    # No token, phone, text, identity, customer, evidence or receipt identifier.

_LEAD_VERSION = """select v.versao_identidade,h.lead_id
from prumo_private.cfi01_f03_lead_versions_local v
join public.casos_humanos h
 on h.concessionaria_id=v.concessionaria_id and h.lead_id=v.lead_id
where h.concessionaria_id=%s::uuid and h.id=%s::uuid
for update of v"""
_PENDING = """select p.id from prumo_private.pendencias_identidade_s0 p
where p.concessionaria_id=%s::uuid and p.id=%s::uuid for update"""
_CANDIDATE = """select 1
from prumo_private.pendencias_identidade_s0 p
join public.leads_loja l on l.concessionaria_id=p.concessionaria_id
 and l.id=%s::uuid
where p.concessionaria_id=%s::uuid and p.id=%s::uuid
and (
 p.telefone_sintetico=l.telefone_cliente_normalizado
 or (prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
     and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
       =prumo_private.chave_variante_br_s0(l.telefone_cliente_normalizado))
 or exists (
  select 1 from prumo_private.aliases_identidade_s0 a
  where a.concessionaria_id=l.concessionaria_id and a.lead_id=l.id
    and (a.numero_sintetico=p.telefone_sintetico
    or (prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
      and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
        =prumo_private.chave_variante_br_s0(a.numero_sintetico)))
 )
)"""
_EXISTING = """select ator_id,atribuicao_id,versao_ciclo,versao_identidade,
 decisao,evidencia_sha256,chave_idempotencia
from prumo_private.cfi01_f03_identity_human_reviews_local
where concessionaria_id=%s::uuid and pendencia_id=%s::uuid and caso_id=%s::uuid
for update"""
_INSERT = """insert into prumo_private.cfi01_f03_identity_human_reviews_local
(concessionaria_id,pendencia_id,caso_id,lead_candidato_id,atribuicao_id,
 ator_id,sessao_id,versao_ciclo,versao_identidade,decisao,evidencia_sha256,
 chave_idempotencia)
values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,
 %s::bigint,%s::bigint,%s::text,%s::text,%s::text)
on conflict (concessionaria_id,pendencia_id,caso_id) do nothing returning id"""

def _valid(req: object) -> bool:
    return (type(req) is HumanReviewRequest and _uuid(req.case_ref) is not None
            and _uuid(req.pending_ref) is not None
            and type(req.expected_cycle_version) is int
            and 1<=req.expected_cycle_version<9223372036854775807
            and type(req.expected_identity_version) is int
            and 1<=req.expected_identity_version<9223372036854775807
            and type(req.decision) is HumanReviewDecision
            and type(req.evidence_sha256) is str
            and re.fullmatch(r"[0-9a-f]{64}",req.evidence_sha256) is not None
            and type(req.idempotency_key) is str
            and re.fullmatch(r"[A-Za-z0-9._:-]{8,128}",
                             req.idempotency_key) is not None)

class S0F03LocalHumanReviewStore:
    """Physical S0 auth, team and candidate-bound append-only audit, PG17 only."""
    def __init__(self, dsn: str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def capture(self, principal: Principal, req: HumanReviewRequest,
                s1: S1TransactionAuthority | None) -> HumanReviewResult:
        if s1 is None:
            return HumanReviewResult(HumanReviewState.BLOCKED_S1)
        import psycopg
        with psycopg.connect(self._dsn,connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute("set local lock_timeout = '3s'")
                cur.execute(_SESSION,(principal.session_id,principal.actor_id))
                if cur.fetchone() is None:
                    return HumanReviewResult(HumanReviewState.DENIED)
                if s1.lock_team(cur,principal) is not S1Proof.ALLOW:
                    return HumanReviewResult(HumanReviewState.BLOCKED_S1)
                cur.execute(_CASE,(principal.actor_id,_uuid(req.case_ref)))
                case=cur.fetchone()
                if case is None:
                    return HumanReviewResult(HumanReviewState.DENIED)
                store,cycle_version,status,assignment=case
                cur.execute(_GRANT,(principal.actor_id,store))
                if cur.fetchone() is None:
                    return HumanReviewResult(HumanReviewState.DENIED)
                if cycle_version!=req.expected_cycle_version:
                    return HumanReviewResult(HumanReviewState.STALE_REVIEW_REQUIRED)
                if status not in ('em atendimento pelo operador',
                                  'cadastro enviado ao operador'):
                    return HumanReviewResult(HumanReviewState.DENIED)
                if s1.check(cur,principal,store,_uuid(req.case_ref),
                            assignment) is not S1Proof.ALLOW:
                    return HumanReviewResult(HumanReviewState.BLOCKED_S1)
                cur.execute(_LEAD_VERSION,(store,_uuid(req.case_ref)))
                found=cur.fetchone()
                if found is None:
                    return HumanReviewResult(HumanReviewState.STALE_REVIEW_REQUIRED)
                identity_version,lead=found
                if identity_version!=req.expected_identity_version:
                    return HumanReviewResult(HumanReviewState.STALE_REVIEW_REQUIRED)
                cur.execute(_PENDING,(store,_uuid(req.pending_ref)))
                if cur.fetchone() is None:
                    return HumanReviewResult(HumanReviewState.DENIED)
                cur.execute(_CANDIDATE,(lead,store,_uuid(req.pending_ref)))
                if cur.fetchone() is None:
                    return HumanReviewResult(HumanReviewState.NOT_RELATED_REVIEW_REQUIRED)
                cur.execute(_EXISTING,(store,_uuid(req.pending_ref),
                                       _uuid(req.case_ref)))
                row=cur.fetchone()
                expected=(principal.actor_id,assignment,req.expected_cycle_version,
                          req.expected_identity_version,req.decision.value,
                          req.evidence_sha256,req.idempotency_key)
                if row is not None:
                    state=(HumanReviewState.ALREADY_RECORDED_REVIEW_ONLY
                           if row==expected else HumanReviewState.CONFLICT_REVIEW_REQUIRED)
                    return HumanReviewResult(state)
                cur.execute(_INSERT,(store,_uuid(req.pending_ref),
                                     _uuid(req.case_ref),lead,assignment,
                                     principal.actor_id,principal.session_id,
                                     req.expected_cycle_version,
                                     req.expected_identity_version,
                                     req.decision.value,req.evidence_sha256,
                                     req.idempotency_key))
                if cur.fetchone() is None:
                    return HumanReviewResult(HumanReviewState.CONFLICT_REVIEW_REQUIRED)
                return HumanReviewResult(HumanReviewState.RECORDED_REVIEW_ONLY)

def record_human_identity_review_local(
    authorization: str, request: HumanReviewRequest, *,
    identity: IdentityProvider, store: S0F03LocalHumanReviewStore,
    s1: S1TransactionAuthority | None = None,
) -> HumanReviewResult:
    """S0 trusted only: bearer verified by IdentityProvider, never supplied UUID."""
    if not _valid(request) or type(store) is not S0F03LocalHumanReviewStore:
        return HumanReviewResult(HumanReviewState.DENIED)
    try:
        principal=identity.verify(authorization)
        if (type(principal) is not Principal or
            type(principal.actor_id) is not uuid.UUID or
            type(principal.session_id) is not uuid.UUID):
            return HumanReviewResult(HumanReviewState.DENIED)
        return store.capture(principal,request,s1)
    except Denied:
        return HumanReviewResult(HumanReviewState.DENIED)
    except Exception:
        return HumanReviewResult(HumanReviewState.UNAVAILABLE)
