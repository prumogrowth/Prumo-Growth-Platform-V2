"""CFI-01 atomic S0 capture/recheck under restricted database principal.

LAB-ONLY: authenticates with existing GoTrue verifier and performs one
transactional signed HMAC/nonce command; no postgres DSN or second privileged
connection. SQL function owner is a dedicated NOLOGIN/NOSUPERUSER role,
granted narrow read/row-lock/receipt-insert rights on disposable fixtures.
This is NOT a production route, F03 reader or fields writer.
"""
from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from typing import Any

from backend.identity_boundary import (
    Denied, IdentityUnavailable, Principal, SupabaseGoTrueVerifier
)
from backend.s0_cfi01_authenticated_commands_local import (
    CommandResult, CommandState, _CAPTURE_FIELDS, _RECHECK_FIELDS
)
from backend.s0_cfi01_signed_prerequisite_local import (
    S0CFI01RestrictedSignedPrerequisiteLocal
)
from backend.s0_human_closure_event_local import _uuid


_ATOMIC_SQL="""select state,event_ref
 from prumo_private.cfi01_atomic_signed_closure_local(
 %s::text,%s::uuid,%s::uuid,%s::uuid,%s::bigint,%s::uuid,
 %s::text,%s::uuid,%s::bigint,%s::uuid,%s::text)"""
_OUTCOMES=frozenset({
    "CAPTURED_LOCAL_ONLY","ALREADY_CAPTURED","DUPLICATE_SNAPSHOT",
    "VERIFIED_REVIEW_ONLY_LOCAL","NO_CONVERSATION"
})


class S0CFI01AtomicCommandsLocal:
    """A single signed PG transaction after each genuine GoTrue user check."""
    def __init__(self, api_url: str, publishable_key: str,
                 restricted_test_dsn: str, *,
                 key_id: uuid.UUID, signing_key: bytes, opener: Any = None):
        self._identity=SupabaseGoTrueVerifier(
            api_url,publishable_key,opener=opener)
        # Reuse STRICT nonremote test DSN + libpq env + test key validation.
        gate=S0CFI01RestrictedSignedPrerequisiteLocal(
            restricted_test_dsn,key_id=key_id,signing_key=signing_key)
        self._dsn=gate._dsn
        self._key_id=key_id
        self._secret=signing_key

    @staticmethod
    def _material(operation: str,principal: Principal,case: uuid.UUID,
                  version: int,event: uuid.UUID | None,key: str,
                  key_id: uuid.UUID,issued: int,nonce: uuid.UUID) -> bytes:
        return "|".join([
            "cfi01-atomic-local-v1",operation,str(principal.actor_id),
            str(principal.session_id),str(case),str(version),
            str(event) if event is not None else "-",key,str(key_id),
            str(issued),str(nonce)
        ]).encode("utf-8")

    def execute(self,authorization: str,command: str,payload: object) -> CommandResult:
        if type(command) is not str or command not in (
            "capture_human_closure","recheck_human_closure"):
            return CommandResult(CommandState.UNSUPPORTED_COMMAND)
        if type(payload) is not dict or set(payload) != (
            _CAPTURE_FIELDS if command=="capture_human_closure" else _RECHECK_FIELDS
        ):
            return CommandResult(CommandState.INPUT_REJECTED)
        case=_uuid(payload["case_ref"])
        event=(None if command=="capture_human_closure"
               else _uuid(payload["closure_event_ref"]))
        version=payload["expected_cycle_version"]
        key=payload["idempotency_key"]
        if (case is None or type(version) is not int
                or not 1<=version<=9223372036854775807
                or type(key) is not str or not 8<=len(key)<=128
                or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-"
                       for c in key)
                or (command=="recheck_human_closure" and event is None)):
            return CommandResult(CommandState.INPUT_REJECTED)
        try:
            principal=self._identity.verify(authorization)
        except Denied:
            return CommandResult(CommandState.DENIED)
        except (IdentityUnavailable,Exception):
            return CommandResult(CommandState.UNAVAILABLE)
        if (type(principal) is not Principal
                or type(principal.actor_id) is not uuid.UUID
                or type(principal.session_id) is not uuid.UUID):
            return CommandResult(CommandState.DENIED)
        issued=int(time.time())
        nonce=uuid.uuid4()
        proof=hmac.new(self._secret,self._material(
            command,principal,case,version,event,key,self._key_id,issued,nonce
        ),hashlib.sha256).hexdigest()
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute(_ATOMIC_SQL,(
                        command,principal.actor_id,principal.session_id,
                        case,version,event,key,self._key_id,issued,nonce,proof))
                    rows=cur.fetchall()
            if len(rows)!=1 or type(rows[0][0]) is not str:
                return CommandResult(CommandState.DENIED)
            state,event_ref=rows[0]
            if state not in _OUTCOMES:
                return CommandResult(CommandState.DENIED)
            if command=="recheck_human_closure" and state!="VERIFIED_REVIEW_ONLY_LOCAL":
                return CommandResult(CommandState.DENIED)
            if command=="capture_human_closure" and state=="VERIFIED_REVIEW_ONLY_LOCAL":
                return CommandResult(CommandState.DENIED)
            if state in ("CAPTURED_LOCAL_ONLY","ALREADY_CAPTURED"):
                if type(event_ref) is not uuid.UUID:
                    return CommandResult(CommandState.DENIED)
                return CommandResult(CommandState[state],str(event_ref))
            if event_ref is not None:
                return CommandResult(CommandState.DENIED)
            return CommandResult(CommandState[state])
        except Exception as exc:
            # Database denial and stale versions always fail closed;
            # never surface backend SQL, tenant, or authentication details.
            code=getattr(exc,"sqlstate",None)
            if code=="40001":
                return CommandResult(CommandState.STALE)
            if code=="42501":
                return CommandResult(CommandState.DENIED)
            return CommandResult(CommandState.UNAVAILABLE)
