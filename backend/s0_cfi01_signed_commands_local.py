"""LOCAL ONLY CFI-01: GoTrue -> signed SQL prerequisite -> S0/S1 transaction.

Stage 2 of dismantling privileged lab access. Signed gate uses a restricted SQL
login and HMAC/nonce, but the capture/recheck implementation STILL uses the
privileged postgres lab adapter. No production route, deploy or F03 writes.
The final S0 command must move ALL state changes into a reviewed owner/ACL
boundary, with recheck and apply inside the same transaction.
"""
from __future__ import annotations

import uuid
from typing import Any, Mapping

from backend.identity_boundary import Denied, IdentityUnavailable, Principal
from backend.s0_cfi01_authenticated_commands_local import (
    S0CFI01AuthenticatedCommandsLocal, CommandResult, CommandState,
    _CAPTURE_FIELDS, _RECHECK_FIELDS,
)
from backend.s0_cfi01_signed_prerequisite_local import (
    S0CFI01RestrictedSignedPrerequisiteLocal, SignedState,
)
from backend.s0_human_closure_event_local import _uuid


class S0CFI01SignedCommandsLocal(S0CFI01AuthenticatedCommandsLocal):
    """Strict two-step auth gate; positive prerequisite is NOT an apply grant."""

    def __init__(self, api_url: str, publishable_key: str,
                 privileged_test_dsn: str, restricted_test_dsn: str,
                 *, key_id: uuid.UUID, signing_key: bytes, opener: Any = None):
        super().__init__(api_url,publishable_key,privileged_test_dsn,opener=opener)
        self._signed = S0CFI01RestrictedSignedPrerequisiteLocal(
            restricted_test_dsn,key_id=key_id,signing_key=signing_key)

    def execute(self, authorization: str, command: str,
                payload: Mapping[str, Any]) -> CommandResult:
        if type(command) is not str or command not in (
                "capture_human_closure","recheck_human_closure"):
            return CommandResult(CommandState.UNSUPPORTED_COMMAND)
        if type(payload) is not dict or set(payload) != (
                _CAPTURE_FIELDS if command=="capture_human_closure"
                else _RECHECK_FIELDS):
            return CommandResult(CommandState.INPUT_REJECTED)
        case=_uuid(payload["case_ref"])
        version=payload["expected_cycle_version"]
        event=(None if command=="capture_human_closure"
               else _uuid(payload["closure_event_ref"]))
        key=payload["idempotency_key"]
        if (case is None or type(version) is not int or not 1<=version<=9223372036854775807
                or type(key) is not str or not 8<=len(key)<=128
                or key != key.strip()
                or (command=="recheck_human_closure" and event is None)):
            return CommandResult(CommandState.INPUT_REJECTED)
        try:
            principal=self._identity.verify(authorization)
        except Denied:
            return CommandResult(CommandState.DENIED)
        except IdentityUnavailable:
            return CommandResult(CommandState.UNAVAILABLE)
        except Exception:
            return CommandResult(CommandState.UNAVAILABLE)
        if type(principal) is not Principal:
            return CommandResult(CommandState.DENIED)
        result=self._signed.prove(
            command,principal,case,version,event=event)
        if result.state is not SignedState.SIGNED_PREREQUISITES_ONLY_LOCAL:
            return CommandResult(CommandState.DENIED if result.state is SignedState.DENIED
                                 else CommandState.UNAVAILABLE)
        # A second GoTrue verification and physical S0/S1 case/snapshot check
        # still executes; races between the 2 transactions FAIL CLOSED.
        # NOT safe for production until the privileged database port is gone.
        return super().execute(authorization,command,payload)
