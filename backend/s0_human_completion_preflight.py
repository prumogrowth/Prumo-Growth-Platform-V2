"""S0-owned CFI-01 preflight against existing S0 domain, LOCAL-ONLY.

Uses real GoTrue identity contract from backend.identity_boundary and SELECTs
existing case/assignment/grant/session rows in a PostgreSQL transaction.
This does NOT authorize closure or extraction yet: S1/team authorization,
closure event, form schema and transactional apply are not implemented.
No public HTTP route, model credential, writes or production DSN.
"""
from __future__ import annotations

import uuid
import urllib.parse
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from backend.identity_boundary import Denied, IdentityProvider, IdentityUnavailable, Principal


class CheckStatus(str, Enum):
    DENIED = "DENIED"
    STALE = "STALE"
    S0_READ_CHECKS_PASSED_S1_REQUIRED = "S0_READ_CHECKS_PASSED_S1_REQUIRED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class CasePreflightRequest:
    case_ref: str
    expected_cycle_version: int
    # Explicitly *cycle* version: current S0 schema has no case version column.
    # This is a candidate backend contract, NOT yet FV-02's case version.


@dataclass(frozen=True)
class CasePreflightResult:
    status: CheckStatus
    # No store, assignee, case identifiers, context or authorization token.


class CaseInspection(Protocol):
    def check(self, principal: Principal, case_id: uuid.UUID, cycle_version: int) -> CheckStatus: ...


def preflight_human_closure(
    authorization: str,
    request: CasePreflightRequest,
    *,
    identity: IdentityProvider,
    inspection: CaseInspection,
) -> CasePreflightResult:
    """S0 preflight: caller cannot spoof actor or shop; no operational grant.

    A positive *read check* remains unusable to complete a case or supply F03
    data until a ratified S0/S1 closure transaction exists.
    """
    if (type(request) is not CasePreflightRequest
            or type(request.case_ref) is not str
            or type(request.expected_cycle_version) is not int
            or not 1 <= request.expected_cycle_version <= 9223372036854775807):
        return CasePreflightResult(CheckStatus.DENIED)
    try:
        case_id = uuid.UUID(request.case_ref)
        if str(case_id) != request.case_ref.lower():
            return CasePreflightResult(CheckStatus.DENIED)
    except (ValueError, AttributeError):
        return CasePreflightResult(CheckStatus.DENIED)
    try:
        # Must be the actual trusted GoTrue validator, NOT a parsed JWT claim.
        principal = identity.verify(authorization)
        if type(principal) is not Principal or type(principal.actor_id) is not uuid.UUID or type(principal.session_id) is not uuid.UUID:
            return CasePreflightResult(CheckStatus.DENIED)
        result = inspection.check(principal, case_id, request.expected_cycle_version)
    except (Denied,):
        return CasePreflightResult(CheckStatus.DENIED)
    except (IdentityUnavailable, OSError, TimeoutError):
        return CasePreflightResult(CheckStatus.UNAVAILABLE)
    except Exception:
        # Unexpected storage error must never grant or leak scoped context.
        return CasePreflightResult(CheckStatus.UNAVAILABLE)
    if result not in (CheckStatus.DENIED, CheckStatus.STALE,
                      CheckStatus.S0_READ_CHECKS_PASSED_S1_REQUIRED):
        return CasePreflightResult(CheckStatus.DENIED)
    return CasePreflightResult(result)


class PsycopgLocalCaseInspection:
    """Query ACTUAL S0 schema, locked to a disposable localhost PG instance.

    This temporary LOCAL implementation requires `postgres` access,
    matching the existing S0 local test boundary. It is not a service design:
    must be replaced with audited, least-privileged signed S0 operation.
    """
    _CASE = """select h.concessionaria_id, c.versao_registro, c.status_comercial
from public.casos_humanos h
join public.ciclos_comerciais c
  on c.id=h.ciclo_id and c.concessionaria_id=h.concessionaria_id
join public.concessionarias l
  on l.id=h.concessionaria_id and l.ativo=true
join public.atribuicoes_humanas a
  on a.caso_id=h.id and a.concessionaria_id=h.concessionaria_id
  and a.encerrada_em is null and a.operador_id=%s::uuid
where h.id=%s::uuid
for share of h, c, l, a"""
    _GRANT = """select 1 from public.vinculos_papel_escopo v
where v.ator_id=%s::uuid and v.concessionaria_id=%s::uuid
and v.papel in ('operador','gestor')
and v.valido_desde <= statement_timestamp()
and (v.valido_ate is null or v.valido_ate > statement_timestamp())
for share"""
    _SESSION = """select 1 from auth.sessions
where id=%s::uuid and user_id=%s::uuid for key share"""

    def __init__(self, dsn: str):
        u=urllib.parse.urlsplit(dsn)
        if (u.scheme not in ('postgres','postgresql') or
            u.hostname not in ('localhost','127.0.0.1','::1') or
            u.username != 'postgres' or u.query or u.fragment or
            not (u.path.strip('/') == 'postgres' or
                 u.path.strip('/').startswith('prumo_s0_test_'))):
            raise ValueError('S0_DISPOSABLE_POSTGRES_ONLY')
        self._dsn=dsn

    def check(self, principal: Principal, case_id: uuid.UUID, cycle_version: int) -> CheckStatus:
        # Optional dependency: imported only if the local PG adapter is used.
        import psycopg
        with psycopg.connect(self._dsn,connect_timeout=5) as con:
            with con.cursor() as cur:
                # Session and assignment are locked in one DB transaction.
                cur.execute(self._SESSION,(principal.session_id,principal.actor_id))
                if cur.fetchone() is None:
                    return CheckStatus.DENIED
                cur.execute(self._CASE,(principal.actor_id,case_id))
                case=cur.fetchone()
                if case is None:
                    return CheckStatus.DENIED
                store, version, status=case
                cur.execute(self._GRANT,(principal.actor_id,store))
                if cur.fetchone() is None:
                    return CheckStatus.DENIED
                if version != cycle_version:
                    return CheckStatus.STALE
                if status not in ('em atendimento pelo operador','cadastro enviado ao operador'):
                    # Conservative PRELIMINARY scope. Does not define S0 final policy.
                    return CheckStatus.DENIED
                # Authorization from S1/team & closure operation are still absent.
                return CheckStatus.S0_READ_CHECKS_PASSED_S1_REQUIRED
