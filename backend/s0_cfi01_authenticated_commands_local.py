"""S0 CFI-01 candidate authenticated command entrypoint, LOCAL-ONLY.

The *real* existing SupabaseGoTrueVerifier code validates a bearer via trusted
GET /auth/v1/user, then resolves its JWT session ID. The PostgreSQL capture
and recheck independently lock the current auth.sessions, S1 team, case,
assignment and conversation records. No claimed actor, shop, grant or model
response is accepted from the caller.

No public HTTP route, HMAC/nonce, least-privileged DB login or production
GoTrue service is provisioned here. Only disposable local S0 PostgreSQL.
The command never sends data to F03 and never applies extracted fields.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from backend.identity_boundary import SupabaseGoTrueVerifier
from backend.s0_human_closure_event_local import (
    ClosureRequest, ClosureResult, ClosureState, S0LocalClosureStore,
    capture_human_closure_local,
)
from backend.s0_human_closure_recheck_local import (
    RecheckRequest, RecheckResult, RecheckState, S0LocalClosureRecheck,
    recheck_human_closure_local,
)
from backend.s0_s1_closure_authority_local import S0S1LocalTeamAuthority


class CommandState(str, Enum):
    INPUT_REJECTED = "INPUT_REJECTED"
    UNSUPPORTED_COMMAND = "UNSUPPORTED_COMMAND"
    DENIED = "DENIED"
    STALE = "STALE"
    BLOCKED_S1 = "BLOCKED_S1"
    UNAVAILABLE = "UNAVAILABLE"
    NO_CONVERSATION = "NO_CONVERSATION"
    ALREADY_CAPTURED = "ALREADY_CAPTURED"
    DUPLICATE_SNAPSHOT = "DUPLICATE_SNAPSHOT"
    CAPTURED_LOCAL_ONLY = "CAPTURED_LOCAL_ONLY"
    VERIFIED_REVIEW_ONLY_LOCAL = "VERIFIED_REVIEW_ONLY_LOCAL"


@dataclass(frozen=True)
class CommandResult:
    state: CommandState
    closure_event_ref: str | None = None
    # No store, actor, assignment, snapshot, conversation, extracted data.


_CAPTURE_FIELDS = frozenset(("case_ref", "expected_cycle_version", "idempotency_key"))
_RECHECK_FIELDS = _CAPTURE_FIELDS | {"closure_event_ref"}
_STATE_FROM_CAPTURE = {name: CommandState[name] for name in ClosureState.__members__}
_STATE_FROM_RECHECK = {name: CommandState[name] for name in RecheckState.__members__}


class S0CFI01AuthenticatedCommandsLocal:
    """S0-owned allowlist around GoTrue and physical S0/S1 case authority.

    The default concrete adapter cannot be swapped with browser-supplied
    auth, permissions or JSON. Runtime is still local-only and DB-privileged;
    do NOT route public HTTP to it or treat this as a production executor.
    """

    def __init__(self, api_url: str, publishable_key: str, database_url: str,
                 *, opener: Any = None):
        self._identity = SupabaseGoTrueVerifier(
            api_url, publishable_key, opener=opener)
        self._capture_store = S0LocalClosureStore(database_url)
        self._recheck_store = S0LocalClosureRecheck(database_url)
        self._s1 = S0S1LocalTeamAuthority()

    def execute(self, authorization: str, command: str,
                payload: Mapping[str, Any]) -> CommandResult:
        if type(command) is not str or command not in (
                "capture_human_closure", "recheck_human_closure"):
            return CommandResult(CommandState.UNSUPPORTED_COMMAND)
        if type(payload) is not dict:
            return CommandResult(CommandState.INPUT_REJECTED)
        if command == "capture_human_closure":
            if set(payload) != _CAPTURE_FIELDS:
                return CommandResult(CommandState.INPUT_REJECTED)
            request = ClosureRequest(
                payload["case_ref"], payload["expected_cycle_version"],
                payload["idempotency_key"])
            outcome: ClosureResult = capture_human_closure_local(
                authorization, request, identity=self._identity,
                store=self._capture_store, s1=self._s1)
            # Only a recorded, scoped receipt exposes its opaque reference.
            return CommandResult(
                _STATE_FROM_CAPTURE[outcome.state.name],
                outcome.closure_event_ref if outcome.state in (
                    ClosureState.CAPTURED_LOCAL_ONLY,
                    ClosureState.ALREADY_CAPTURED) else None,
            )
        if set(payload) != _RECHECK_FIELDS:
            return CommandResult(CommandState.INPUT_REJECTED)
        request = RecheckRequest(
            payload["case_ref"], payload["closure_event_ref"],
            payload["expected_cycle_version"], payload["idempotency_key"])
        outcome: RecheckResult = recheck_human_closure_local(
            authorization, request, identity=self._identity,
            store=self._recheck_store, s1=self._s1)
        return CommandResult(_STATE_FROM_RECHECK[outcome.state.name])
