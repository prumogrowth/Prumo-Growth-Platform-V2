"""I55: loopback-only GoTrue/HMAC queue list + transactional manager claim.

Uses REAL S0/S1/054 queue with signed NOLOGIN owner, not I49 mock.
No direct authenticated SQL grant to queue or internal business function.
"""
from __future__ import annotations
import re
import time
import uuid
from urllib.parse import urlsplit

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand
from backend.s1_gateway_signed_local import _proof_material

_UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
_SQL_QUEUE = ("select prumo_s1_signed_i20.invocar_fila_v55("
              "%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::bigint,"
              "%s::uuid,%s::bigint,%s::uuid,%s::text)")

def queue_fields(command, payload):
    if type(payload) is not dict:
        raise InvalidCommand("I55_OBJECT_REQUIRED")
    if command == "fila":
        if set(payload) != {"loja_id"}:
            raise InvalidCommand("I55_LIST_FIELDS")
    elif command == "assumir_fila":
        if set(payload) != {"loja_id","ciclo_id","versao_esperada"}:
            raise InvalidCommand("I55_CLAIM_FIELDS")
    else:
        raise InvalidCommand("I55_OPERATION_DENIED")
    shop=payload["loja_id"]
    if type(shop) is not str or _UUID.fullmatch(shop) is None:
        raise InvalidCommand("I55_INVALID_STORE")
    if command == "fila":
        return uuid.UUID(shop),None,None
    cycle=payload["ciclo_id"]
    version=payload["versao_esperada"]
    if (type(cycle) is not str or _UUID.fullmatch(cycle) is None
        or type(version) is not int
        or not 1 <= version <= 9223372036854775807):
        raise InvalidCommand("I55_INVALID_CLAIM")
    return uuid.UUID(shop),uuid.UUID(cycle),version

class LocalSignedCanonicalQueueGateway:
    def __init__(self, dsn, gotrue, *, signer, key_id):
        u=urlsplit(dsn)
        if (u.scheme not in ("postgres","postgresql")
            or u.hostname not in ("127.0.0.1","localhost","::1")
            or u.username != "prumo_s1_signed_login_ci" or u.path != "/postgres"
            or u.query or u.fragment):
            raise ValueError("I55_DISPOSABLE_DATABASE_ONLY")
        if not isinstance(key_id,uuid.UUID) or signer is None:
            raise ValueError("I55_SIGNER_REQUIRED")
        self.dsn=dsn
        self.gotrue=gotrue
        self.signer=signer
        self.key_id=key_id

    def proof(self, principal, shop, cycle, version, authorization,
              *, issued=None, nonce=None):
        if (cycle is None) != (version is None):
            raise InvalidCommand("I55_OPERATION_MISMATCH")
        issued_at=int(time.time()) if issued is None else issued
        unique=uuid.uuid4() if nonce is None else nonce
        op="FILA55L" if cycle is None else "FILA55C"
        action="L" if cycle is None else "C:"+str(version)
        material=_proof_material(op,principal.actor_id,principal.session_id,
                        (shop,cycle,None,None,None,action),issued_at,unique)
        signature=self.signer.sign(self.key_id,material,authorization)
        return (principal.actor_id,principal.session_id,shop,cycle,version,
                self.key_id,issued_at,unique,signature)

    def invoke(self, authorization, command, payload):
        import psycopg
        shop,cycle,version=queue_fields(command,payload)
        principal=self.gotrue.verify(authorization)
        proof=self.proof(principal,shop,cycle,version,authorization)
        with psycopg.connect(self.dsn,connect_timeout=5) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(_SQL_QUEUE,proof)
                except psycopg.Error as exc:
                    if exc.sqlstate in ("42501","22023","23514","23505","40001"):
                        raise Denied("I55_QUEUE_DENIED") from None
                    raise IdentityUnavailable("I55_DB_UNAVAILABLE") from None
                row=cur.fetchone()
                if row is None or type(row[0]) is not dict:
                    raise IdentityUnavailable("I55_BAD_RESPONSE")
                return row[0]
