"""S0 CFI-01: LOCAL-ONLY durable human-conversation closure receipt prototype.

The database table lives ONLY in a disposable S0 PostgreSQL test fixture.
This isn't the final S0 authorization or an OpenAI invocation. S1 authorization
must be checked in the same transaction by a trusted server-side port.
"""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Any

from backend.identity_boundary import Principal, Denied, IdentityUnavailable, IdentityProvider


class ClosureState(str, Enum):
    DENIED = "DENIED"
    STALE = "STALE"
    BLOCKED_S1 = "BLOCKED_S1"
    UNAVAILABLE = "UNAVAILABLE"
    NO_CONVERSATION = "NO_CONVERSATION"
    ALREADY_CAPTURED = "ALREADY_CAPTURED"
    DUPLICATE_SNAPSHOT = "DUPLICATE_SNAPSHOT"
    CAPTURED_LOCAL_ONLY = "CAPTURED_LOCAL_ONLY"


class S1Proof(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True)
class ClosureRequest:
    case_ref: str
    expected_cycle_version: int
    idempotency_key: str


@dataclass(frozen=True)
class ClosureResult:
    state: ClosureState
    closure_event_ref: str | None = None
    # No bank status, business status, raw messages, customer or S0 grant.


class S1TransactionAuthority(Protocol):
    """S1 authorization must lock TEAM before CASE using the SAME cursor."""
    def lock_team(self, cursor: Any, principal: Principal) -> S1Proof: ...
    def check(self, cursor: Any, principal: Principal, store: uuid.UUID,
              case: uuid.UUID, assignment: uuid.UUID) -> S1Proof: ...


_SESSION = """select 1 from auth.sessions where id=%s::uuid and user_id=%s::uuid for key share"""
_CASE = """select h.concessionaria_id, c.versao_registro, c.status_comercial, a.id
from public.casos_humanos h
join public.ciclos_comerciais c on c.concessionaria_id=h.concessionaria_id and c.id=h.ciclo_id
join public.concessionarias l on l.id=h.concessionaria_id and l.ativo=true
join public.atribuicoes_humanas a on a.concessionaria_id=h.concessionaria_id
 and a.caso_id=h.id and a.encerrada_em is null and a.operador_id=%s::uuid
where h.id=%s::uuid for update of h,c,l,a"""
_GRANT = """select 1 from public.vinculos_papel_escopo v
where v.ator_id=%s::uuid and v.concessionaria_id=%s::uuid
and v.papel in ('operador','gestor') and v.valido_desde<=statement_timestamp()
and (v.valido_ate is null or v.valido_ate>statement_timestamp()) for share"""
_LOCK_CONVERSATIONS = """select id from public.conversas
where concessionaria_id=%s::uuid and caso_id=%s::uuid order by id for update"""
_MESSAGES = """select m.id, m.criada_em, m.direcao, m.origem, m.conteudo_sintetico, m.enviada_por
from public.mensagens m join public.conversas v
on v.id=m.conversa_id and v.concessionaria_id=m.concessionaria_id
where v.concessionaria_id=%s::uuid and v.caso_id=%s::uuid
order by m.criada_em,m.id"""
_EXISTING = """select id, ator_id, atribuicao_id, versao_ciclo, snapshot_sha256
from prumo_private.cfi01_human_closure_events_local
where concessionaria_id=%s::uuid and caso_id=%s::uuid and chave_idempotencia=%s::text
for update"""
_INSERT = """insert into prumo_private.cfi01_human_closure_events_local
(concessionaria_id,caso_id,ator_id,sessao_id,atribuicao_id,versao_ciclo,
 chave_idempotencia,snapshot_sha256,ultima_mensagem_id,quantidade_mensagens)
values (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::bigint,
 %s::text,%s::text,%s::uuid,%s::integer)
on conflict do nothing returning id"""


def _uuid(value: object) -> uuid.UUID | None:
    if type(value) is not str:
        return None
    try:
        v = uuid.UUID(value)
        return v if value == str(v) else None
    except (ValueError, AttributeError):
        return None


def _valid(request: object) -> bool:
    return (type(request) is ClosureRequest and _uuid(request.case_ref) is not None
            and type(request.expected_cycle_version) is int
            and 1 <= request.expected_cycle_version <= 9223372036854775807
            and type(request.idempotency_key) is str
            and 8 <= len(request.idempotency_key) <= 128
            and request.idempotency_key.strip() == request.idempotency_key)


def _fingerprint(rows: list[tuple]) -> str:
    # SHA256 fingerprint for staleness, NOT a signature/authorization credential.
    payload = [[str(v) if v is not None else None for v in row] for row in rows]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


class S0LocalClosureStore:
    """LOCAL PostgreSQL transaction; identity/S1 cannot be derived from a model."""
    def __init__(self, dsn: str):
        u=urllib.parse.urlsplit(dsn)
        if (u.scheme not in ('postgres','postgresql') or
            u.hostname not in ('localhost','127.0.0.1','::1') or
            u.username != 'postgres' or u.query or u.fragment or
            not u.path.strip('/').startswith('prumo_s0_test_')):
            raise ValueError('DISPOSABLE_LOCAL_PG_ONLY')
        self._dsn=dsn

    def capture(self, principal: Principal, request: ClosureRequest,
                s1: S1TransactionAuthority | None) -> ClosureResult:
        if s1 is None:
            return ClosureResult(ClosureState.BLOCKED_S1)
        import psycopg  # imported only in isolated local PG adapter
        with psycopg.connect(self._dsn, connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute(_SESSION,(principal.session_id,principal.actor_id))
                if cur.fetchone() is None:
                    return ClosureResult(ClosureState.DENIED)
                # Match S1 I13 lock order: TEAM BEFORE case and assignment.
                # If S1 table/adapter is absent or rejects, fail closed.
                if s1.lock_team(cur,principal) is not S1Proof.ALLOW:
                    return ClosureResult(ClosureState.BLOCKED_S1)
                case_id=_uuid(request.case_ref)
                cur.execute(_CASE,(principal.actor_id,case_id))
                case=cur.fetchone()
                if case is None:
                    return ClosureResult(ClosureState.DENIED)
                store, version, status, assignment=case
                cur.execute(_GRANT,(principal.actor_id,store))
                if cur.fetchone() is None:
                    return ClosureResult(ClosureState.DENIED)
                if version != request.expected_cycle_version:
                    return ClosureResult(ClosureState.STALE)
                if status not in ('em atendimento pelo operador','cadastro enviado ao operador'):
                    return ClosureResult(ClosureState.DENIED)
                # S1 was locked first; recheck exact scope after the
                # current case/assignment/store grant locks. Adapter is only
                # local until S0+S1 physical contract is ratified.
                if s1.check(cur,principal,store,case_id,assignment) is not S1Proof.ALLOW:
                    return ClosureResult(ClosureState.BLOCKED_S1)
                # FOR UPDATE of parent conversations serializes inserts that
                # reference them via S0's FK while capturing this snapshot.
                cur.execute(_LOCK_CONVERSATIONS,(store,case_id))
                conversations=cur.fetchall()
                if not conversations:
                    return ClosureResult(ClosureState.NO_CONVERSATION)
                cur.execute(_MESSAGES,(store,case_id))
                messages=cur.fetchall()
                if not messages:
                    return ClosureResult(ClosureState.NO_CONVERSATION)
                if len(messages)>2500:
                    return ClosureResult(ClosureState.DENIED)
                sha=_fingerprint(messages)
                cur.execute(_EXISTING,(store,case_id,request.idempotency_key))
                prior=cur.fetchone()
                if prior is not None:
                    eid,actor,assign,ver,prior_sha=prior
                    if (actor != principal.actor_id or assign != assignment or
                            ver != version):
                        return ClosureResult(ClosureState.DENIED)
                    if prior_sha != sha:
                        return ClosureResult(ClosureState.STALE)
                    return ClosureResult(ClosureState.ALREADY_CAPTURED,str(eid))
                watermark=messages[-1][0]
                cur.execute(_INSERT,(store,case_id,principal.actor_id,principal.session_id,
                                     assignment,version,request.idempotency_key,
                                     sha,watermark,len(messages)))
                inserted=cur.fetchone()
                if inserted is None:
                    # Unique fingerprint or concurrent request: refuse to
                    # create a second event, never infer authorization.
                    return ClosureResult(ClosureState.DUPLICATE_SNAPSHOT)
                return ClosureResult(ClosureState.CAPTURED_LOCAL_ONLY,str(inserted[0]))


def capture_human_closure_local(
    authorization: str, request: ClosureRequest, *, identity: IdentityProvider,
    store: S0LocalClosureStore, s1: S1TransactionAuthority | None = None,
) -> ClosureResult:
    """Fail closed: no closure event absent S0 and S1 inputs."""
    if not _valid(request):
        return ClosureResult(ClosureState.DENIED)
    try:
        principal=identity.verify(authorization)
        if (type(principal) is not Principal or
                type(principal.actor_id) is not uuid.UUID or
                type(principal.session_id) is not uuid.UUID):
            return ClosureResult(ClosureState.DENIED)
        return store.capture(principal,request,s1)
    except Denied:
        return ClosureResult(ClosureState.DENIED)
    except Exception:  # Local database, S1 and transport must all fail closed.
        return ClosureResult(ClosureState.UNAVAILABLE)
