"""E04 S0-only third-person resolution CLOSE receipt for synthetic identities.

Immutable HOLD_ONLY resolution evidence after independent review and manager
ratification. It never clears S0/028 pending, never grants F03 model access,
and never changes customer fields. HMAC key must be supplied by trusted S0.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import hashlib
import hmac
import json
import re
import uuid

from backend.identity_boundary import Principal, Denied, IdentityProvider
from backend.s0_human_closure_event_local import (
    S0LocalClosureStore, S1TransactionAuthority, S1Proof, _SESSION, _uuid,
)
from backend.s0_f03_identity_ratification_local import _MANAGER_SCOPE
from backend.s0_f03_identity_human_review_local import _CANDIDATE

class ResolutionState(str, Enum):
    CLOSED_HOLD_ONLY = 'CLOSED_HOLD_ONLY'
    ALREADY_CLOSED_HOLD_ONLY = 'ALREADY_CLOSED_HOLD_ONLY'
    DENIED = 'DENIED'
    BLOCKED_S1 = 'BLOCKED_S1'
    STALE_REVIEW_REQUIRED = 'STALE_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED = 'CONFLICT_REVIEW_REQUIRED'
    UNAVAILABLE = 'UNAVAILABLE'

@dataclass(frozen=True)
class ResolutionRequest:
    review_ref: str
    ratification_ref: str
    pending_ref: str
    case_ref: str
    expected_cycle_version: int
    expected_identity_version: int
    key_version: str
    evidence_sha256: str
    idempotency_key: str

@dataclass(frozen=True)
class ResolutionResult:
    state: ResolutionState
    # Intentionally no PII, source text, MAC, secret or grant.

_CONTEXT = """select t.concessionaria_id,t.lead_candidato_id,
 t.ratificador_id,r.ator_id,r.decisao,t.decisao,
 t.versao_ciclo,t.versao_identidade,r.versao_ciclo,r.versao_identidade,
 c.versao_registro,v.versao_identidade,a.encerrada_em
from prumo_private.cfi01_f03_identity_ratifications_local t
join prumo_private.cfi01_f03_identity_human_reviews_local r
 on r.id=t.revisao_id and r.concessionaria_id=t.concessionaria_id
 and r.pendencia_id=t.pendencia_id and r.caso_id=t.caso_id
join public.casos_humanos h on
 h.concessionaria_id=t.concessionaria_id and h.id=t.caso_id
 and h.lead_id=t.lead_candidato_id
join public.ciclos_comerciais c on
 c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
 and c.lead_id=h.lead_id
join prumo_private.cfi01_f03_lead_versions_local v
 on v.concessionaria_id=t.concessionaria_id and v.lead_id=t.lead_candidato_id
join public.atribuicoes_humanas a on
 a.concessionaria_id=r.concessionaria_id and a.id=r.atribuicao_id
 and a.caso_id=r.caso_id and a.operador_id=r.ator_id
where t.id=%s::uuid and t.revisao_id=%s::uuid
 and t.pendencia_id=%s::uuid and t.caso_id=%s::uuid
for share of t,r,h,c,a for update of v"""
_PENDING = """select id,concessionaria_id,canal_id,id_externo,
 telefone_sintetico,texto_sintetico,motivo,registrado_em
from prumo_private.pendencias_identidade_s0
where concessionaria_id=%s::uuid and id=%s::uuid for update"""
_EXISTING = """select revisao_id,ratificacao_id,gestor_resolvedor_id,sessao_id,
 versao_ciclo,versao_identidade,chave_hmac_versao,pendencia_mac_sha256,
 evidencia_sha256,chave_idempotencia,resultado
from prumo_private.cfi01_f03_identity_resolution_local
where concessionaria_id=%s::uuid and pendencia_id=%s::uuid and caso_id=%s::uuid
for update"""
_INSERT = """insert into prumo_private.cfi01_f03_identity_resolution_local
(concessionaria_id,pendencia_id,caso_id,revisao_id,ratificacao_id,
 lead_candidato_id,gestor_resolvedor_id,sessao_id,versao_ciclo,
 versao_identidade,chave_hmac_versao,pendencia_mac_sha256,
 evidencia_sha256,chave_idempotencia,resultado)
values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,
 %s::uuid,%s::uuid,%s::bigint,%s::bigint,%s::text,%s::text,
 %s::text,%s::text,%s::text)
on conflict (concessionaria_id,pendencia_id,caso_id) do nothing returning id"""
_FINAL = 'NOT_RELATED_HOLD_ONLY'

def _valid(req: object, key: object) -> bool:
    return (type(req) is ResolutionRequest
        and all(_uuid(v) is not None for v in (
            req.review_ref,req.ratification_ref,req.pending_ref,req.case_ref))
        and type(req.expected_cycle_version) is int
        and 1 <= req.expected_cycle_version < 9223372036854775807
        and type(req.expected_identity_version) is int
        and 1 <= req.expected_identity_version < 9223372036854775807
        and type(req.key_version) is str
        and re.fullmatch(r'[A-Za-z0-9._:-]{8,80}',req.key_version) is not None
        and type(req.evidence_sha256) is str
        and re.fullmatch(r'[0-9a-f]{64}',req.evidence_sha256) is not None
        and type(req.idempotency_key) is str
        and re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',req.idempotency_key) is not None
        and type(key) is bytes and len(key)>=32)

def _source_hmac(row: object,shop: uuid.UUID,lead: uuid.UUID,
                 req: ResolutionRequest,key: bytes) -> str | None:
    if not isinstance(row,(tuple,list)) or len(row)!=8:
        return None
    rid,rshop,channel,external,phone,body,reason,created=row
    if (not all(type(x) is uuid.UUID for x in (rid,rshop,channel))
        or rid!=_uuid(req.pending_ref) or rshop!=shop
        or type(created) is not datetime or created.tzinfo is None
        or any(type(x) is not str or len(x)>20000 or len(x)==0
               for x in (external,phone,body,reason))):
        return None
    scope=[str(shop),str(lead),req.case_ref,req.pending_ref,
           req.review_ref,req.ratification_ref,req.expected_cycle_version,
           req.expected_identity_version,str(channel),external,phone,body,
           reason,created.isoformat()]
    message=json.dumps(scope,separators=(',',':'),ensure_ascii=False).encode()
    return hmac.new(key,message,hashlib.sha256).hexdigest()

class S0F03LocalResolutionStore:
    """S0 local PG only; triple-person distinction, pending snapshot HMAC."""
    def __init__(self,dsn:str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def capture(self,principal:Principal,req:ResolutionRequest,
                s1:S1TransactionAuthority | None,key:bytes)->ResolutionResult:
        if s1 is None:
            return ResolutionResult(ResolutionState.BLOCKED_S1)
        import psycopg
        with psycopg.connect(self._dsn,connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute("set local lock_timeout = '3s'")
                cur.execute(_SESSION,(principal.session_id,principal.actor_id))
                if cur.fetchone() is None:
                    return ResolutionResult(ResolutionState.DENIED)
                if s1.lock_team(cur,principal) is not S1Proof.ALLOW:
                    return ResolutionResult(ResolutionState.BLOCKED_S1)
                cur.execute(_CONTEXT,(
                    _uuid(req.ratification_ref),_uuid(req.review_ref),
                    _uuid(req.pending_ref),_uuid(req.case_ref)))
                ctx=cur.fetchone()
                if ctx is None:
                    return ResolutionResult(ResolutionState.DENIED)
                (shop,lead,ratifier,reviewer,first_decision,second_decision,
                 rat_cycle,rat_identity,rev_cycle,rev_identity,
                 current_cycle,current_identity,closed)=ctx
                if (principal.actor_id in (ratifier,reviewer)
                    or ratifier==reviewer
                    or first_decision!='CANDIDATE_NOT_RELATED'
                    or second_decision!='RATIFY_CANDIDATE_NOT_RELATED'):
                    return ResolutionResult(ResolutionState.DENIED)
                if (closed is not None
                    or any(v!=req.expected_cycle_version for v in
                           (rat_cycle,rev_cycle,current_cycle))
                    or any(v!=req.expected_identity_version for v in
                           (rat_identity,rev_identity,current_identity))):
                    return ResolutionResult(ResolutionState.STALE_REVIEW_REQUIRED)
                cur.execute(_MANAGER_SCOPE,(principal.actor_id,shop))
                if cur.fetchone() is None:
                    return ResolutionResult(ResolutionState.DENIED)
                cur.execute(_PENDING,(shop,_uuid(req.pending_ref)))
                pending=cur.fetchone()
                if pending is None:
                    return ResolutionResult(ResolutionState.DENIED)
                cur.execute(_CANDIDATE,(lead,shop,_uuid(req.pending_ref)))
                if cur.fetchone() is None:
                    return ResolutionResult(ResolutionState.STALE_REVIEW_REQUIRED)
                proof=_source_hmac(pending,shop,lead,req,key)
                if proof is None:
                    return ResolutionResult(ResolutionState.DENIED)
                cur.execute(_EXISTING,(shop,_uuid(req.pending_ref),
                                       _uuid(req.case_ref)))
                row=cur.fetchone()
                signature=(_uuid(req.review_ref),_uuid(req.ratification_ref),
                           principal.actor_id,principal.session_id,
                           req.expected_cycle_version,req.expected_identity_version,
                           req.key_version,proof,req.evidence_sha256,
                           req.idempotency_key,_FINAL)
                if row is not None:
                    return ResolutionResult(
                        ResolutionState.ALREADY_CLOSED_HOLD_ONLY if row==signature
                        else ResolutionState.CONFLICT_REVIEW_REQUIRED)
                cur.execute(_INSERT,(shop,_uuid(req.pending_ref),
                    _uuid(req.case_ref),_uuid(req.review_ref),
                    _uuid(req.ratification_ref),lead,principal.actor_id,
                    principal.session_id,req.expected_cycle_version,
                    req.expected_identity_version,req.key_version,proof,
                    req.evidence_sha256,req.idempotency_key,_FINAL))
                if cur.fetchone() is None:
                    return ResolutionResult(ResolutionState.CONFLICT_REVIEW_REQUIRED)
                return ResolutionResult(ResolutionState.CLOSED_HOLD_ONLY)

def close_human_identity_resolution_local(
    authorization:str,request:ResolutionRequest,*,
    identity:IdentityProvider,store:S0F03LocalResolutionStore,
    s1:S1TransactionAuthority | None,key:bytes)->ResolutionResult:
    if not _valid(request,key) or type(store) is not S0F03LocalResolutionStore:
        return ResolutionResult(ResolutionState.DENIED)
    try:
        principal=identity.verify(authorization)
        if (type(principal) is not Principal
            or type(principal.actor_id) is not uuid.UUID
            or type(principal.session_id) is not uuid.UUID):
            return ResolutionResult(ResolutionState.DENIED)
        return store.capture(principal,request,s1,key)
    except Denied:
        return ResolutionResult(ResolutionState.DENIED)
    except Exception:
        return ResolutionResult(ResolutionState.UNAVAILABLE)
