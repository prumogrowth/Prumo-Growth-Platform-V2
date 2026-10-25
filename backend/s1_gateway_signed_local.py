"""S1-002/I20 - adapter SQL assinado, APENAS para CI descartável.

Gateway S1 de teste: GoTrue valida o Bearer, HMAC independente comprova
ator/sessão/operação/argumentos/epoch/nonce dentro do PostgreSQL.
Sem SET ROLE authenticated, sem GUC escrita pelo login SQL e sem public RPC.
A infraestrutura web de produção, secrets e ownership continuam fora do escopo.
"""
from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from urllib.parse import urlsplit

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand, Principal
from backend.s1_command_validation_local import _fields

_COMMAND = {"mover": "MOVER", "pausar": "PAUSAR", "reativar": "REATIVAR"}
_SQL_SIGNED = (
    "select prumo_s1_signed_i20.invocar("
    "%s::text,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::uuid,"
    "%s::uuid,%s::text,%s::uuid,%s::bigint,%s::uuid,%s::text)"
)


def _action_args(command: str, values: tuple):
    if command == "mover":
        shop, case, expected, target = values
        return (shop, case, expected, target, None, None)
    if command == "pausar":
        operator, reason = values
        return (None, None, None, None, operator, reason)
    if command == "reativar":
        (operator,) = values
        return (None, None, None, None, operator, None)
    raise InvalidCommand("COMANDO_NAO_PERMITIDO")


def _proof_material(op, actor, session, args, issued, nonce) -> bytes:
    # Campos opcionais têm marcador '-', UUID canônico e enum restrito.
    fields = (
        "prumo-s1-i20-v1", op, str(actor), str(session),
        *(str(x) if x is not None else "-" for x in args),
        str(issued), str(nonce),
    )
    return "|".join(fields).encode("utf-8")


class LocalSignedTeamGateway:
    def __init__(self, dsn: str, gotrue, *, key_id: uuid.UUID, signing_key: bytes):
        u = urlsplit(dsn)
        if (u.scheme not in ("postgres", "postgresql")
            or u.hostname not in ("127.0.0.1", "localhost", "::1")
            or u.username != "prumo_s1_signed_login_ci"
            or u.path != "/postgres" or u.query or u.fragment):
            raise ValueError("DSN_ASSINADO_APENAS_CI_LOCAL")
        if not isinstance(key_id, uuid.UUID) or not isinstance(signing_key, bytes) or len(signing_key) < 32:
            raise ValueError("ASSINATURA_INDEPENDENTE_OBRIGATORIA")
        self.dsn = dsn
        self.gotrue = gotrue
        self.key_id = key_id
        self.signing_key = signing_key

    def proof(self, principal: Principal, command: str, values: tuple,
              *, issued: int | None = None, nonce: uuid.UUID | None = None):
        op = _COMMAND.get(command)
        if op is None:
            raise InvalidCommand("COMANDO_NAO_PERMITIDO")
        args = _action_args(command, values)
        timestamp = int(time.time()) if issued is None else issued
        unique = uuid.uuid4() if nonce is None else nonce
        material = _proof_material(op, principal.actor_id, principal.session_id, args,
                                   timestamp, unique)
        signature = hmac.new(self.signing_key, material, hashlib.sha256).hexdigest()
        return (op, principal.actor_id, principal.session_id, *args, self.key_id,
                timestamp, unique, signature)

    def invoke(self, authorization: str, command: str, payload: dict):
        import psycopg
        values = _fields(command, payload)
        principal = self.gotrue.verify(authorization)
        signed_args = self.proof(principal, command, values)
        with psycopg.connect(self.dsn, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(_SQL_SIGNED, signed_args)
                except psycopg.Error as exc:
                    if exc.sqlstate in ("42501", "22023", "23514", "23505"):
                        raise Denied("OPERACAO_S1_NAO_AUTORIZADA") from None
                    raise IdentityUnavailable("BANCO_INDISPONIVEL") from None
                record = cursor.fetchone()
                if record is None or not isinstance(record[0], dict):
                    raise IdentityUnavailable("RETORNO_S1_INVALIDO")
                return record[0]
