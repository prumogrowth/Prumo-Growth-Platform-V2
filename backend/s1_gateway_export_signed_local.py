"""I74 signed, nonce-protected export boundary. Disposable CI only.

Gateway never holds HMAC key. Separate I26 signer verifies GoTrue itself.
SQL login cannot SET ROLE executor or call raw invoker. Not production TLS/KMS.
"""
from __future__ import annotations

import time
import uuid
from urllib.parse import urlsplit

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand
from backend.s1_gateway_export_local import export_fields, _safe_reply
from backend.s1_gateway_signed_local import _proof_material

_SQL_SIGNED_EXPORT = (
 "select prumo_export_auth.exportar_assinado_i74("
 "%s::uuid,%s::uuid,%s::text,%s::uuid,%s::uuid,%s::integer,"
 "%s::uuid,%s::bigint,%s::uuid,%s::text)"
)


class LocalSignedExportGateway:
    def __init__(self,dsn,gotrue,*,signer,key_id):
        u=urlsplit(dsn)
        if (u.scheme not in ("postgres","postgresql")
            or u.hostname not in ("127.0.0.1","localhost","::1")
            or u.username!="prumo_s1_export_signed_login_ci"
            or u.path!="/postgres" or u.query or u.fragment or not u.password):
            raise ValueError("I74_ONLY_DISPOSABLE_SIGNED_LOGIN")
        if gotrue is None or not callable(getattr(gotrue,"verify",None)):
            raise ValueError("I74_GOTRUE_REQUIRED")
        if type(key_id) is not uuid.UUID or signer is None or not callable(getattr(signer,"sign",None)):
            raise ValueError("I74_INDEPENDENT_SIGNER_REQUIRED")
        self._dsn=dsn
        self._gotrue=gotrue
        self._signer=signer
        self._key_id=key_id

    def proof(self,principal,fields,authorization,*,issued=None,nonce=None):
        kind,shop,cursor,limit=fields
        if not isinstance(principal.actor_id,uuid.UUID) or not isinstance(principal.session_id,uuid.UUID):
            raise Denied("I74_INVALID_IDENTITY")
        when=int(time.time()) if issued is None else issued
        token=uuid.uuid4() if nonce is None else nonce
        if type(when) is not int or type(token) is not uuid.UUID:
            raise InvalidCommand("I74_INVALID_PROOF_OPTIONS")
        marker="E:"+("L" if kind=="lotes" else "C")+":"+str(limit)
        material=_proof_material("EXPORT74",principal.actor_id,principal.session_id,
         (shop,cursor,None,None,None,marker),when,token)
        mac=self._signer.sign(self._key_id,material,authorization)
        return (principal.actor_id,principal.session_id,kind,shop,cursor,limit,
                self._key_id,when,token,mac)

    def export(self,authorization,payload):
        import psycopg
        fields=export_fields(payload)
        principal=self._gotrue.verify(authorization)
        proof=self.proof(principal,fields,authorization)
        try:
            with psycopg.connect(self._dsn,connect_timeout=5) as con:
                with con.cursor() as cur:
                    cur.execute(_SQL_SIGNED_EXPORT,proof)
                    value=cur.fetchone()
                    if value is None:
                        raise IdentityUnavailable("I74_DB_NO_RESULT")
                    return _safe_reply(value[0])
        except psycopg.Error as exc:
            if exc.sqlstate in ("42501","22023","23514","23505"):
                raise Denied("I74_EXPORT_DENIED") from None
            raise IdentityUnavailable("I74_DB_UNAVAILABLE") from None
