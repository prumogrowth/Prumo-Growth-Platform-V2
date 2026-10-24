"""E04 S0-only, local PG17: read-only live validity of identity CLOSE receipt.

'CURRENT_HOLD_ONLY' certifies only a serialized transaction point; it
never grants future permanence, identity resolution, or a right for F03 to
read messages, apply fields, remove a hold or contact a customer.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hmac
import re
import uuid

from backend.identity_boundary import Principal, Denied, IdentityProvider
from backend.s0_human_closure_event_local import (
    S0LocalClosureStore, S1TransactionAuthority, S1Proof, _SESSION, _uuid,
)
from backend.s0_f03_identity_ratification_local import _MANAGER_SCOPE
from backend.s0_f03_identity_human_review_local import _CANDIDATE
from backend.s0_f03_identity_resolution_local import (
    ResolutionRequest, _source_hmac, _PENDING,
)

class ValidityState(str, Enum):
    CURRENT_HOLD_ONLY = 'CURRENT_HOLD_ONLY'
    STALE_REVIEW_REQUIRED = 'STALE_REVIEW_REQUIRED'
    CONFLICT_REVIEW_REQUIRED = 'CONFLICT_REVIEW_REQUIRED'
    DENIED = 'DENIED'
    BLOCKED_S1 = 'BLOCKED_S1'
    UNAVAILABLE = 'UNAVAILABLE'

@dataclass(frozen=True)
class ValidityRequest:
    resolution_ref: str
    pending_ref: str
    case_ref: str
    key_version: str

@dataclass(frozen=True)
class ValidityResult:
    state: ValidityState
    # No HMAC, evidence, source text, lead identity, or F03 entitlement.

_CURRENT = """select
 d.concessionaria_id,d.pendencia_id,d.caso_id,d.revisao_id,
 d.ratificacao_id,d.lead_candidato_id,d.gestor_resolvedor_id,
 d.sessao_id,d.versao_ciclo,d.versao_identidade,d.chave_hmac_versao,
 d.pendencia_mac_sha256,d.evidencia_sha256,d.chave_idempotencia,d.resultado,
 r.ator_id,t.ratificador_id,r.decisao,t.decisao,
 r.versao_ciclo,r.versao_identidade,t.versao_ciclo,t.versao_identidade,
 c.versao_registro,v.versao_identidade,a.encerrada_em
from prumo_private.cfi01_f03_identity_resolution_local d
join prumo_private.cfi01_f03_identity_ratifications_local t
 on t.id=d.ratificacao_id and t.concessionaria_id=d.concessionaria_id
 and t.pendencia_id=d.pendencia_id and t.caso_id=d.caso_id
 and t.revisao_id=d.revisao_id and t.lead_candidato_id=d.lead_candidato_id
join prumo_private.cfi01_f03_identity_human_reviews_local r
 on r.id=d.revisao_id and r.concessionaria_id=d.concessionaria_id
 and r.pendencia_id=d.pendencia_id and r.caso_id=d.caso_id
 and r.lead_candidato_id=d.lead_candidato_id
join public.casos_humanos h
 on h.concessionaria_id=d.concessionaria_id and h.id=d.caso_id
 and h.lead_id=d.lead_candidato_id
join public.ciclos_comerciais c
 on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
 and c.lead_id=h.lead_id
join prumo_private.cfi01_f03_lead_versions_local v
 on v.concessionaria_id=h.concessionaria_id and v.lead_id=h.lead_id
join public.atribuicoes_humanas a
 on a.concessionaria_id=r.concessionaria_id
 and a.id=r.atribuicao_id and a.caso_id=r.caso_id
 and a.operador_id=r.ator_id
where d.id=%s::uuid and d.pendencia_id=%s::uuid and d.caso_id=%s::uuid
for share of d,t,r,h,c,a for update of v"""

_OTHER_PENDING = """select p.id
from prumo_private.pendencias_identidade_s0 p
join public.leads_loja l
 on l.concessionaria_id=p.concessionaria_id and l.id=%s::uuid
where p.concessionaria_id=%s::uuid and p.id<>%s::uuid
 and (
  p.telefone_sintetico=l.telefone_cliente_normalizado
  or (
    prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
    and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
       =prumo_private.chave_variante_br_s0(l.telefone_cliente_normalizado)
  )
  or exists(
   select 1 from prumo_private.aliases_identidade_s0 al
   where al.concessionaria_id=l.concessionaria_id and al.lead_id=l.id
     and (
      al.numero_sintetico=p.telefone_sintetico
      or (
       prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
       and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
         =prumo_private.chave_variante_br_s0(al.numero_sintetico)
      )
     )
  )
 )
order by p.id limit 1 for share of p"""


# Resolve shop through the immutable receipt, never from client input.
_SCOPE = """select concessionaria_id
from prumo_private.cfi01_f03_identity_resolution_local
where id=%s::uuid and pendencia_id=%s::uuid and caso_id=%s::uuid"""
_LOCK_SCOPE = "select prumo_private.s0_f03_lock_shop_local(%s::uuid)"
# Distinct actual S0 leads: a phone comparison is a candidate, not identity.
# Consistent with existing _CANDIDATE matching, including BR variant.
_CANDIDATE_COUNT = """select count(distinct lead_id) from (
 select l.id as lead_id
 from public.leads_loja l
 join prumo_private.pendencias_identidade_s0 p
  on p.concessionaria_id=l.concessionaria_id
 where p.concessionaria_id=%s::uuid and p.id=%s::uuid
 and (p.telefone_sintetico=l.telefone_cliente_normalizado
  or (prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
   and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
      =prumo_private.chave_variante_br_s0(l.telefone_cliente_normalizado)))
 union all
 select a.lead_id
 from prumo_private.aliases_identidade_s0 a
 join prumo_private.pendencias_identidade_s0 p
  on p.concessionaria_id=a.concessionaria_id
 where p.concessionaria_id=%s::uuid and p.id=%s::uuid
 and (p.telefone_sintetico=a.numero_sintetico
  or (prumo_private.chave_variante_br_s0(p.telefone_sintetico) is not null
   and prumo_private.chave_variante_br_s0(p.telefone_sintetico)
      =prumo_private.chave_variante_br_s0(a.numero_sintetico)))
) candidates"""

def _valid(request: object, key: object) -> bool:
    return (type(request) is ValidityRequest
            and all(_uuid(v) is not None for v in
                    (request.resolution_ref,request.pending_ref,request.case_ref))
            and type(request.key_version) is str
            and re.fullmatch(r'[A-Za-z0-9._:-]{8,80}',request.key_version) is not None
            and type(key) is bytes and len(key)>=32)

class S0F03LocalResolutionValidityStore:
    """Rechecks live source and current caller at every invocation."""
    def __init__(self, dsn: str):
        self._dsn=S0LocalClosureStore(dsn)._dsn

    def check(self, principal: Principal, request: ValidityRequest,
              s1: S1TransactionAuthority | None, key: bytes) -> ValidityResult:
        if s1 is None:
            return ValidityResult(ValidityState.BLOCKED_S1)
        import psycopg
        with psycopg.connect(self._dsn,connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute("set local lock_timeout = '3s'")
                cur.execute(_SESSION,(principal.session_id,principal.actor_id))
                if cur.fetchone() is None:
                    return ValidityResult(ValidityState.DENIED)
                if s1.lock_team(cur,principal) is not S1Proof.ALLOW:
                    return ValidityResult(ValidityState.BLOCKED_S1)
                # Linearize the read with ALL synthetic identity writers
                # in this tenant BEFORE any candidate or receipt row lock.
                cur.execute(_SCOPE,(
                    _uuid(request.resolution_ref),_uuid(request.pending_ref),
                    _uuid(request.case_ref)))
                scope=cur.fetchone()
                if scope is None or len(scope)!=1:
                    return ValidityResult(ValidityState.DENIED)
                cur.execute(_LOCK_SCOPE,(scope[0],))
                cur.execute(_CURRENT,(
                    _uuid(request.resolution_ref),_uuid(request.pending_ref),
                    _uuid(request.case_ref)))
                row=cur.fetchone()
                if row is None or len(row)!=26:
                    return ValidityResult(ValidityState.DENIED)
                (shop,pending_id,case_id,review_id,rat_id,lead,closer,
                 _original_session,close_cycle,close_identity,keyid,
                 saved_mac,evidence_sha,idem,result,reviewer,ratifier,
                 review_decision,rat_decision,rev_cycle,rev_identity,
                 rat_cycle,rat_identity,current_cycle,current_identity,
                 assignment_closed)=row
                if (shop!=scope[0] or closer!=principal.actor_id
                    or len({closer,reviewer,ratifier})!=3
                    or result!='NOT_RELATED_HOLD_ONLY'
                    or review_decision!='CANDIDATE_NOT_RELATED'
                    or rat_decision!='RATIFY_CANDIDATE_NOT_RELATED'):
                    return ValidityResult(ValidityState.DENIED)
                cur.execute(_MANAGER_SCOPE,(principal.actor_id,shop))
                if cur.fetchone() is None:
                    return ValidityResult(ValidityState.DENIED)
                if (assignment_closed is not None or
                    close_cycle!=rev_cycle or close_cycle!=rat_cycle
                    or close_cycle!=current_cycle or
                    close_identity!=rev_identity
                    or close_identity!=rat_identity
                    or close_identity!=current_identity):
                    return ValidityResult(ValidityState.STALE_REVIEW_REQUIRED)
                if keyid!=request.key_version:
                    return ValidityResult(ValidityState.STALE_REVIEW_REQUIRED)
                if (type(saved_mac) is not str or
                    re.fullmatch(r'[0-9a-f]{64}',saved_mac) is None):
                    return ValidityResult(ValidityState.DENIED)
                cur.execute(_PENDING,(shop,pending_id))
                pending=cur.fetchone()
                if pending is None:
                    return ValidityResult(ValidityState.STALE_REVIEW_REQUIRED)
                cur.execute(_CANDIDATE,(lead,shop,pending_id))
                if cur.fetchone() is None:
                    return ValidityResult(ValidityState.STALE_REVIEW_REQUIRED)
                # Canonical lower-case UUID strings identical to the original
                # authenticated receipt. All original versions are persisted.
                snap=ResolutionRequest(
                    str(review_id),str(rat_id),str(pending_id),str(case_id),
                    close_cycle,close_identity,keyid,evidence_sha,idem)
                computed=_source_hmac(pending,shop,lead,snap,key)
                if computed is None or not hmac.compare_digest(saved_mac,computed):
                    return ValidityResult(ValidityState.STALE_REVIEW_REQUIRED)
                # Count all competing leads without claiming an identity.
                # The shared shop lock prevents concurrent insertion phantoms
                # until the read-only transaction completes.
                cur.execute(_CANDIDATE_COUNT,
                            (shop,pending_id,shop,pending_id))
                candidate_count=cur.fetchone()
                if (candidate_count is None or len(candidate_count)!=1
                    or type(candidate_count[0]) is not int
                    or candidate_count[0]!=1):
                    return ValidityResult(ValidityState.CONFLICT_REVIEW_REQUIRED)
                # A subsequently created pending match is NOT covered by this
                # single receipt. Reject instead of claiming full identity.
                cur.execute(_OTHER_PENDING,(lead,shop,pending_id))
                if cur.fetchone() is not None:
                    return ValidityResult(ValidityState.CONFLICT_REVIEW_REQUIRED)
                return ValidityResult(ValidityState.CURRENT_HOLD_ONLY)

def verify_human_identity_resolution_local(
    authorization: str,request: ValidityRequest, *,
    identity: IdentityProvider,store: S0F03LocalResolutionValidityStore,
    s1: S1TransactionAuthority | None,key:bytes,
) -> ValidityResult:
    if not _valid(request,key) or type(store) is not S0F03LocalResolutionValidityStore:
        return ValidityResult(ValidityState.DENIED)
    try:
        principal=identity.verify(authorization)
        if (type(principal) is not Principal
            or type(principal.actor_id) is not uuid.UUID
            or type(principal.session_id) is not uuid.UUID):
            return ValidityResult(ValidityState.DENIED)
        return store.check(principal,request,s1,key)
    except Denied:
        return ValidityResult(ValidityState.DENIED)
    except Exception:
        return ValidityResult(ValidityState.UNAVAILABLE)
