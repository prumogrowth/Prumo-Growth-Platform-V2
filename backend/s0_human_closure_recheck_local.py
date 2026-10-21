"""CFI-01 S0-side recheck of a recorded human closure, LOCAL PostgreSQL only.

This is NOT a production authorization, public endpoint, signed grant, or
permission to give fields to F03. It uses the S0-owned closure fixture and
locks the session, S1 team, case, assignment, conversations and message rows
before comparing the original receipt to current trusted database state.
All information passed into the F03 model is outside this module.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

from backend.identity_boundary import Denied, IdentityProvider, Principal
from backend.s0_human_closure_event_local import (
    S0LocalClosureStore, S1TransactionAuthority, S1Proof, _uuid, _SESSION,
    _CASE, _GRANT, _LOCK_CONVERSATIONS, _MESSAGES, _fingerprint,
)


class RecheckState(str, Enum):
    DENIED = "DENIED"
    STALE = "STALE"
    BLOCKED_S1 = "BLOCKED_S1"
    UNAVAILABLE = "UNAVAILABLE"
    VERIFIED_REVIEW_ONLY_LOCAL = "VERIFIED_REVIEW_ONLY_LOCAL"


@dataclass(frozen=True)
class RecheckRequest:
    case_ref: str
    closure_event_ref: str
    expected_cycle_version: int
    idempotency_key: str
    # Trusted S0 server must bind these to the ORIGINAL closure receipt.
    # Never accept these directly from a model as authority.


@dataclass(frozen=True)
class RecheckResult:
    state: RecheckState
    # No actor/store/grant/snapshot/content nor APPLIED status.


_RECEIPT = """select ator_id,sessao_id,atribuicao_id,versao_ciclo,
 chave_idempotencia,snapshot_sha256,ultima_mensagem_id,quantidade_mensagens
from prumo_private.cfi01_human_closure_events_local
where id=%s::uuid and concessionaria_id=%s::uuid and caso_id=%s::uuid
for share"""


def _valid_request(request: object) -> bool:
    return (
        type(request) is RecheckRequest
        and _uuid(request.case_ref) is not None
        and _uuid(request.closure_event_ref) is not None
        and type(request.expected_cycle_version) is int
        and 1 <= request.expected_cycle_version <= 9223372036854775807
        and type(request.idempotency_key) is str
        and 8 <= len(request.idempotency_key) <= 128
        and request.idempotency_key.strip() == request.idempotency_key
    )


class S0LocalClosureRecheck(S0LocalClosureStore):
    """Reuse the parent local-only DSN and libpq redirect restrictions."""

    def recheck(self, principal: Principal, request: RecheckRequest,
                s1: S1TransactionAuthority | None) -> RecheckResult:
        if s1 is None:
            return RecheckResult(RecheckState.BLOCKED_S1)
        import psycopg
        with psycopg.connect(self._dsn, connect_timeout=5) as con:
            with con.cursor() as cur:
                cur.execute(_SESSION, (principal.session_id, principal.actor_id))
                if cur.fetchone() is None:
                    return RecheckResult(RecheckState.DENIED)
                # Match the S1-first lock order of human closure capture.
                if s1.lock_team(cur, principal) is not S1Proof.ALLOW:
                    return RecheckResult(RecheckState.BLOCKED_S1)
                case_id = _uuid(request.case_ref)
                cur.execute(_CASE, (principal.actor_id, case_id))
                found = cur.fetchone()
                if found is None:
                    return RecheckResult(RecheckState.DENIED)
                shop, version, status, assignment = found
                cur.execute(_GRANT, (principal.actor_id, shop))
                if cur.fetchone() is None:
                    return RecheckResult(RecheckState.DENIED)
                if version != request.expected_cycle_version:
                    return RecheckResult(RecheckState.STALE)
                if status not in (
                        "em atendimento pelo operador",
                        "cadastro enviado ao operador"):
                    return RecheckResult(RecheckState.DENIED)
                if s1.check(cur, principal, shop, case_id, assignment) is not S1Proof.ALLOW:
                    return RecheckResult(RecheckState.BLOCKED_S1)

                cur.execute(_LOCK_CONVERSATIONS, (shop, case_id))
                if not cur.fetchall():
                    return RecheckResult(RecheckState.STALE)
                cur.execute(_MESSAGES, (shop, case_id))
                messages = cur.fetchall()
                if not 1 <= len(messages) <= 2500:
                    return RecheckResult(RecheckState.STALE)

                # Never look up by event ID alone; the store/case are derived
                # from the CURRENT S0 authorization, not the supplied receipt.
                cur.execute(_RECEIPT,
                            (_uuid(request.closure_event_ref), shop, case_id))
                receipt = cur.fetchone()
                if receipt is None:
                    return RecheckResult(RecheckState.DENIED)

                actor, session, saved_assignment, saved_version, saved_key, saved_hash, saved_watermark, saved_count = receipt
                if (actor != principal.actor_id
                        or session != principal.session_id
                        or saved_assignment != assignment
                        or saved_key != request.idempotency_key):
                    return RecheckResult(RecheckState.DENIED)
                if (saved_version != version
                        or saved_count != len(messages)
                        or saved_watermark != messages[-1][0]
                        or saved_hash != _fingerprint(messages)):
                    return RecheckResult(RecheckState.STALE)
                return RecheckResult(RecheckState.VERIFIED_REVIEW_ONLY_LOCAL)


def recheck_human_closure_local(
    authorization: str, request: RecheckRequest, *,
    identity: IdentityProvider, store: S0LocalClosureRecheck,
    s1: S1TransactionAuthority | None = None,
) -> RecheckResult:
    """Only the verified identity and database receipt can confer local recheck."""
    if not _valid_request(request):
        return RecheckResult(RecheckState.DENIED)
    if s1 is None:
        return RecheckResult(RecheckState.BLOCKED_S1)
    try:
        principal = identity.verify(authorization)
        if (type(principal) is not Principal
                or type(principal.actor_id) is not uuid.UUID
                or type(principal.session_id) is not uuid.UUID):
            return RecheckResult(RecheckState.DENIED)
        return store.recheck(principal, request, s1)
    except Denied:
        return RecheckResult(RecheckState.DENIED)
    except Exception:
        return RecheckResult(RecheckState.UNAVAILABLE)
