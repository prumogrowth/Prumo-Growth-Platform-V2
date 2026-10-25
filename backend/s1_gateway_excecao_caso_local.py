"""I62: case-only signed GoTrue exception, local CI only.

No caller-supplied manager ID: signed identity is derived from GoTrue token.
"""
from __future__ import annotations
import re
import time
import uuid
from urllib.parse import urlsplit

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand
from backend.s1_gateway_signed_local import _proof_material

_UUID=re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
_SQL_EXC62=("select prumo_s1_signed_i20.invocar_excecao_i62("
 "%s::uuid,%s::uuid,%s::text,%s::uuid,%s::uuid,%s::uuid,%s::uuid,"
 "%s::uuid,%s::bigint,%s::uuid,%s::text)")

def exception_fields(command,payload):
    if type(payload) is not dict:raise InvalidCommand("I62_OBJECT_REQUIRED")
    if command=="mover_excecao":
        keys={"loja_id","caso_id","atribuicao_esperada_id","destino_id"}
        if set(payload)!=keys:raise InvalidCommand("I62_MOVE_FIELDS")
        fields=[payload[k] for k in ("loja_id","caso_id","atribuicao_esperada_id","destino_id")]
        action="MOVE"
    elif command=="revogar_excecao":
        if set(payload)!={"excecao_id"}:raise InvalidCommand("I62_REVOKE_FIELDS")
        fields=[payload["excecao_id"],None,None,None]
        action="REVOKE"
    else:raise InvalidCommand("I62_COMMAND_DENIED")
    for value in fields:
        if value is not None and (type(value) is not str or
            _UUID.fullmatch(value) is None or str(uuid.UUID(value))!=value):
            raise InvalidCommand("I62_UUID_INVALID")
    return action,tuple(uuid.UUID(x) if x is not None else None for x in fields)

def safe_exception_result(operation,value):
    if type(value) is not dict:raise IdentityUnavailable("I62_BAD_REPLY")
    if operation=="MOVE":
        if set(value)!={"outcome","case_id","assignment_id","exception_id"} or value["outcome"]!="MOVED_CASE_EXCEPTION":
            raise IdentityUnavailable("I62_UNSAFE_REPLY")
        if not all(type(value[k]) is str and _UUID.fullmatch(value[k]) and
                   str(uuid.UUID(value[k]))==value[k] for k in
                   ("case_id","assignment_id","exception_id")):
            raise IdentityUnavailable("I62_UNSAFE_UUID")
        return {k:value[k] for k in ("outcome","case_id","assignment_id","exception_id")}
    if operation=="REVOKE" and value in ({"outcome":"REVOKED_CASE_ACCESS"},{"outcome":"ALREADY_REVOKED"}):
        return value
    raise IdentityUnavailable("I62_BAD_OPERATION")

class LocalSignedCaseExceptionGateway:
    def __init__(self,dsn,gotrue,*,signer,key_id):
        u=urlsplit(dsn)
        if (u.scheme not in ("postgres","postgresql")
          or u.hostname not in ("127.0.0.1","localhost","::1")
          or u.username!="prumo_s1_signed_login_ci" or u.path!="/postgres"
          or u.query or u.fragment):
            raise ValueError("I62_DISPOSABLE_ONLY")
        if not isinstance(key_id,uuid.UUID) or signer is None:
            raise ValueError("I62_SIGNER_REQUIRED")
        self.dsn=dsn;self.gotrue=gotrue;self.signer=signer;self.key_id=key_id

    def proof(self,principal,operation,ids,authorization,*,issued=None,nonce=None):
        if operation not in ("MOVE","REVOKE") or len(ids)!=4:
            raise InvalidCommand("I62_OPERATION")
        issued_at=int(time.time()) if issued is None else issued
        unique=uuid.uuid4() if nonce is None else nonce
        op="EXC62M" if operation=="MOVE" else "EXC62R"
        action=None if operation=="MOVE" else "R"
        material=_proof_material(op,principal.actor_id,principal.session_id,
             (ids[0],ids[1],ids[2],ids[3],None,action),issued_at,unique)
        signature=self.signer.sign(self.key_id,material,authorization)
        return (principal.actor_id,principal.session_id,operation,*ids,
                self.key_id,issued_at,unique,signature)

    def invoke(self,authorization,command,payload):
        import psycopg
        operation,ids=exception_fields(command,payload)
        principal=self.gotrue.verify(authorization)
        proof=self.proof(principal,operation,ids,authorization)
        with psycopg.connect(self.dsn,connect_timeout=5) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(_SQL_EXC62,proof)
                except psycopg.Error as exc:
                    if exc.sqlstate in ("42501","22023","23514","23505"):
                        raise Denied("I62_CASE_EXCEPTION_DENIED") from None
                    raise IdentityUnavailable("I62_DB_UNAVAILABLE") from None
                row=cur.fetchone()
                if row is None:raise IdentityUnavailable("I62_MISSING_REPLY")
                return safe_exception_result(operation,row[0])
