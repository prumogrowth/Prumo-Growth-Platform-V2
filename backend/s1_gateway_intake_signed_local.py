"""S1-002/I37: intake-only gateway, local disposable GoTrue + signer + PG.

Never use against hosted Supabase or production. HMAC custody stays with
I22; signer independently checks GoTrue, the database checks auth.sessions,
nonce uniqueness, CAS and manager team/permissions. No reason field.
"""
from __future__ import annotations

import re
import time
import uuid
from urllib.parse import urlsplit

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand
from backend.s1_gateway_signed_local import _proof_material

_UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
_SQL_INTAKE = (
    "select prumo_s1_signed_i20.invocar_intake_v37("
    "%s::uuid,%s::uuid,%s::uuid,%s::boolean,%s::bigint,"
    "%s::uuid,%s::bigint,%s::uuid,%s::text)"
)


def intake_fields(command, payload):
    if command != "intake" or type(payload) is not dict or set(payload) != {
        "operador_id", "pausar", "versao_esperada",
    }:
        raise InvalidCommand("I37_FIELDS_DENIED")
    ident = payload["operador_id"]
    paused = payload["pausar"]
    version = payload["versao_esperada"]
    if (type(ident) is not str or _UUID.fullmatch(ident) is None or
        type(paused) is not bool or type(version) is not int or
        not 1 <= version <= 9223372036854775807):
        raise InvalidCommand("I37_INVALID_FIELDS")
    return uuid.UUID(ident), paused, version


class LocalSignedIntakeOnlyGateway:
    def __init__(self, dsn, gotrue, *, signer, key_id):
        u = urlsplit(dsn)
        if (u.scheme not in ("postgres", "postgresql") or
            u.hostname not in ("127.0.0.1","localhost","::1") or
            u.username != "prumo_s1_signed_login_ci" or
            u.path != "/postgres" or u.query or u.fragment):
            raise ValueError("I37_DISPOSABLE_DB_ONLY")
        if not isinstance(key_id,uuid.UUID) or signer is None:
            raise ValueError("I37_SIGNER_REQUIRED")
        self.dsn=dsn
        self.gotrue=gotrue
        self.signer=signer
        self.key_id=key_id

    def proof(self,principal,operator,paused,version,authorization,*,issued=None,nonce=None):
        issued_at=int(time.time()) if issued is None else issued
        unique=uuid.uuid4() if nonce is None else nonce
        state=("P:" if paused else "R:")+str(version)
        material=_proof_material("INTAKE",principal.actor_id,principal.session_id,
             (None,None,None,None,operator,state),issued_at,unique)
        signature=self.signer.sign(self.key_id,material,authorization)
        return (principal.actor_id,principal.session_id,operator,paused,version,
                self.key_id,issued_at,unique,signature)

    def invoke(self,authorization,command,payload):
        import psycopg
        operator,paused,version=intake_fields(command,payload)
        principal=self.gotrue.verify(authorization)
        proof=self.proof(principal,operator,paused,version,authorization)
        with psycopg.connect(self.dsn,connect_timeout=5) as connection:
            with connection.cursor() as cur:
                try:
                    cur.execute(_SQL_INTAKE,proof)
                except psycopg.Error as exc:
                    if exc.sqlstate in ("42501","22023","23514","23505","40001"):
                        raise Denied("I37_NOT_AUTHORIZED") from None
                    raise IdentityUnavailable("I37_DATABASE_UNAVAILABLE") from None
                row=cur.fetchone()
                if not row or type(row[0]) is not dict:
                    raise IdentityUnavailable("I37_BAD_DATABASE_RESPONSE")
                return row[0]
