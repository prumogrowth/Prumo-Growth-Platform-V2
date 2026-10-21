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
from dataclasses import dataclass
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
_ATOMIC_INTERNAL_SQL=_ATOMIC_SQL.replace(
    'select state,event_ref',
    'select state,event_ref,store_ref,snapshot_sha256,message_watermark,'
    'assignment_ref,cycle_version,message_count',1)
_OUTCOMES=frozenset({
    "CAPTURED_LOCAL_ONLY","ALREADY_CAPTURED","DUPLICATE_SNAPSHOT",
    "VERIFIED_REVIEW_ONLY_LOCAL","NO_CONVERSATION"
})


@dataclass(frozen=True)
class S0InternalReceiptLocal:
    """Backend S0 metadata, not model content or commercial authorization."""
    store_ref: str
    case_ref: str
    closure_event_ref: str
    expected_cycle_version: int
    assignment_ref: str
    snapshot_sha256: str
    message_watermark: str
    message_count: int


@dataclass(frozen=True)
class S0InternalReceiptResultLocal:
    state: CommandState
    receipt: S0InternalReceiptLocal | None = None


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
        return self._execute(authorization,command,payload,include_receipt=False)

    def capture_internal_receipt(self,authorization: str,payload: object) -> S0InternalReceiptResultLocal:
        result=self._execute(authorization,'capture_human_closure',payload,include_receipt=True)
        return result if type(result) is S0InternalReceiptResultLocal else S0InternalReceiptResultLocal(result.state)

    def recheck_internal_receipt(self,authorization: str,payload: object) -> S0InternalReceiptResultLocal:
        result=self._execute(authorization,'recheck_human_closure',payload,include_receipt=True)
        return result if type(result) is S0InternalReceiptResultLocal else S0InternalReceiptResultLocal(result.state)

    def _execute(self,authorization: str,command: str,payload: object, *,
                 include_receipt: bool) -> CommandResult | S0InternalReceiptResultLocal:
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
                    cur.execute(_ATOMIC_INTERNAL_SQL if include_receipt else _ATOMIC_SQL,(
                        command,principal.actor_id,principal.session_id,
                        case,version,event,key,self._key_id,issued,nonce,proof))
                    rows=cur.fetchall()
            if len(rows)!=1 or type(rows[0][0]) is not str:
                return CommandResult(CommandState.DENIED)
            state,event_ref=rows[0][0:2]
            if state not in _OUTCOMES:
                return CommandResult(CommandState.DENIED)
            if command=="recheck_human_closure" and state!="VERIFIED_REVIEW_ONLY_LOCAL":
                return CommandResult(CommandState.DENIED)
            if command=="capture_human_closure" and state=="VERIFIED_REVIEW_ONLY_LOCAL":
                return CommandResult(CommandState.DENIED)
            if include_receipt:
                if state in ("CAPTURED_LOCAL_ONLY","ALREADY_CAPTURED",
                             "VERIFIED_REVIEW_ONLY_LOCAL"):
                    actual_event=(event if command=="recheck_human_closure" else event_ref)
                    if (type(actual_event) is not uuid.UUID or len(rows[0])!=8
                            or type(rows[0][2]) is not uuid.UUID
                            or type(rows[0][3]) is not str
                            or len(rows[0][3])!=64
                            or any(c not in '0123456789abcdef' for c in rows[0][3])
                            or type(rows[0][4]) is not uuid.UUID
                            or type(rows[0][5]) is not uuid.UUID
                            or type(rows[0][6]) is not int or rows[0][6]!=version
                            or type(rows[0][7]) is not int
                            or not 1<=rows[0][7]<=2500):
                        return CommandResult(CommandState.DENIED)
                    return S0InternalReceiptResultLocal(CommandState[state],
                        S0InternalReceiptLocal(
                            str(rows[0][2]),str(case),str(actual_event),version,
                            str(rows[0][5]),rows[0][3],str(rows[0][4]),rows[0][7]))
                return S0InternalReceiptResultLocal(CommandState[state])
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
