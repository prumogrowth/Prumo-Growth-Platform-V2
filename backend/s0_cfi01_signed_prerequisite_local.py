"""LOCAL ONLY: CFI-01 signed prerequisite over restricted PostgreSQL login.

The GoTrue verifier MUST already have authenticated the Principal. This is a
second factor against a public SQL caller spoofing actor/session/case, not a
standalone authorization or a substitute for the S0 capture/recheck transaction.
No document/form write, messages or receipt contents are returned.

The proof is bound to action + authenticated actor + session + case + cycle
version + optional event + issue time + unique nonce. DB checks authorization
again from trusted S0/S1 tables and consumes the nonce once. No credential is
shared with the model. TEST credential/secret only, no production DSN.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
import urllib.parse
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from backend.identity_boundary import Principal

_LOCAL_TEST_DB="prumo_s0_test_cfi01"
_LOCAL_USER="prumo_cfi01_pgtest_login"
_QUERY="""select prumo_private.cfi01_signed_prerequisite_local(
%s::text,%s::uuid,%s::uuid,%s::uuid,%s::bigint,%s::uuid,
%s::uuid,%s::bigint,%s::uuid,%s::text)"""


class SignedState(str, Enum):
    DENIED="DENIED"
    UNAVAILABLE="UNAVAILABLE"
    SIGNED_PREREQUISITES_ONLY_LOCAL="SIGNED_PREREQUISITES_ONLY_LOCAL"


@dataclass(frozen=True)
class SignedResult:
    state: SignedState
    # Deliberately NO grant token or permission to process model data.


class S0CFI01RestrictedSignedPrerequisiteLocal:
    """Separate DB login; no direct table rights; only one signed SQL function."""
    def __init__(self, dsn: str, *, key_id: uuid.UUID, signing_key: bytes):
        u=urllib.parse.urlsplit(dsn)
        if (u.scheme not in ("postgres","postgresql")
                or u.hostname not in ("127.0.0.1","localhost","::1")
                or u.username != _LOCAL_USER or u.query or u.fragment
                or not ((u.port == 5432 and u.path == "/"+_LOCAL_TEST_DB)
                        or (os.environ.get("PRUMO_CFI01_SUPABASE_LOCAL_AUTH_TEST") == "1"
                            and u.port == 54322 and u.path == "/postgres"))):
            raise ValueError("SIGNED_GATE_DISPOSABLE_PG_ONLY")
        if any(os.environ.get(k) for k in (
            "PGHOSTADDR","PGHOST","PGPORT","PGDATABASE","PGUSER",
            "PGSERVICE","PGSERVICEFILE","PGOPTIONS","PGSSLMODE",
            "PGSSLCERT","PGSSLKEY","PGSSLROOTCERT")):
            raise ValueError("LIBPQ_ENVIRONMENT_REDIRECT_DENIED")
        if type(key_id) is not uuid.UUID or type(signing_key) is not bytes or len(signing_key)<32:
            raise ValueError("GATEWAY_KEY_INVALID")
        self._dsn=dsn
        self._key_id=key_id
        self._secret=signing_key

    @staticmethod
    def _material(operation: str, principal: Principal, case: uuid.UUID,
                  version: int, event: uuid.UUID | None,
                  issued: int, nonce: uuid.UUID) -> bytes:
        return "|".join([
            "cfi01-local-v1",operation,str(principal.actor_id),
            str(principal.session_id),str(case),str(version),
            str(event) if event is not None else "-",
            str(issued),str(nonce)
        ]).encode("utf-8")

    def prove(self, operation: str, principal: Principal,
              case: uuid.UUID, version: int,
              *, event: uuid.UUID | None = None) -> SignedResult:
        if (operation not in ("capture_human_closure","recheck_human_closure")
                or type(principal) is not Principal
                or type(principal.actor_id) is not uuid.UUID
                or type(principal.session_id) is not uuid.UUID
                or type(case) is not uuid.UUID
                or type(version) is not int or not 1<=version<=9223372036854775807
                or (operation=="capture_human_closure" and event is not None)
                or (operation=="recheck_human_closure" and type(event) is not uuid.UUID)):
            return SignedResult(SignedState.DENIED)
        timestamp=int(time.time())
        nonce=uuid.uuid4()
        signed=hmac.new(
            self._secret,self._material(operation,principal,case,version,
                                        event,timestamp,nonce),hashlib.sha256
        ).hexdigest()
        try:
            import psycopg
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute(_QUERY,(operation,principal.actor_id,
                                       principal.session_id,case,version,event,
                                       self._key_id,timestamp,nonce,signed))
                    row=cur.fetchone()
                    if row is None or row != ("SIGNED_PREREQUISITES_ONLY_LOCAL",):
                        return SignedResult(SignedState.DENIED)
            return SignedResult(SignedState.SIGNED_PREREQUISITES_ONLY_LOCAL)
        except Exception as exc:
            # PostgreSQL denial or unavailable both fail closed. This is a
            # local test port: do not reveal database diagnostics to caller.
            if getattr(exc,"sqlstate",None) in ("42501","40001"):
                return SignedResult(SignedState.DENIED)
            return SignedResult(SignedState.UNAVAILABLE)
