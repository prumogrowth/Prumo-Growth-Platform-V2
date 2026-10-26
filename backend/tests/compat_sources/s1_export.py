"""I73 local-only export gateway: verified GoTrue identity, least-privilege SQL.

No public HTTP listener. No arbitrary actor identity or SQL accepted from caller.
The login is isolated from public authenticated; a separate signed authority is
still required before production to defend a compromised gateway login.
"""
from __future__ import annotations

import re
import uuid
from typing import Any
from urllib.parse import urlsplit

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand

_UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
_KINDS = frozenset(("lotes", "canais"))
_SQL = ("select public.s1_71_exportar_resumo("
        "%s::text,%s::uuid,%s::uuid,%s::integer)")


def _id(value: Any, *, optional: bool = False) -> uuid.UUID | None:
    if optional and value is None:
        return None
    if type(value) is not str or _UUID.fullmatch(value) is None:
        raise InvalidCommand("I73_UUID_INVALIDO")
    return uuid.UUID(value)


def export_fields(payload: Any) -> tuple[str, uuid.UUID, uuid.UUID | None, int]:
    if type(payload) is not dict or set(payload) != {"tipo", "loja_id", "apos", "limite"}:
        raise InvalidCommand("I73_CAMPOS_INVALIDOS")
    kind = payload["tipo"]
    if type(kind) is not str or kind not in _KINDS:
        raise InvalidCommand("I73_TIPO_INVALIDO")
    shop = _id(payload["loja_id"])
    cursor = _id(payload["apos"], optional=True)
    limit = payload["limite"]
    if type(limit) is not int or not 1 <= limit <= 20:
        raise InvalidCommand("I73_LIMITE_INVALIDO")
    return kind, shop, cursor, limit


def _safe_reply(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {"estado", "linhas"}:
        raise IdentityUnavailable("I73_RESPOSTA_INESPERADA")
    if value["estado"] not in ("OK", "VAZIO", "LIMITE_ATINGIDO"):
        raise IdentityUnavailable("I73_ESTADO_INESPERADO")
    rows = value["linhas"]
    if type(rows) is not list or len(rows) > 20:
        raise IdentityUnavailable("I73_PAGINA_INESPERADA")
    if value["estado"] != "OK" and rows:
        raise IdentityUnavailable("I73_NEGATIVA_COM_DADOS")
    allowed = ({"concessionaria_id", "lote_ref", "itens_autorizados"},
               {"concessionaria_id", "canal_ref", "conversas_autorizadas"})
    if any(type(row) is not dict or set(row) not in allowed for row in rows):
        raise IdentityUnavailable("I73_COLUNAS_INESPERADAS")
    return value


class LocalExportGateway:
    """GoTrue + live DB session + executor-only invoker, disposable CI.

    Compromise of the executor's own SQL login remains an open threat:
    a real separate signer / replay guard is required for production.
    """

    def __init__(self, dsn: str, gotrue: Any):
        u = urlsplit(dsn)
        if (u.scheme not in ("postgres", "postgresql")
            or u.hostname not in ("127.0.0.1", "localhost", "::1")
            or u.username != "prumo_s1_export_login_ci"
            or u.path != "/postgres" or u.query or u.fragment or not u.password):
            raise ValueError("I73_APENAS_LOGIN_LOCAL_RESTRITO")
        if gotrue is None or not callable(getattr(gotrue, "verify", None)):
            raise ValueError("I73_GOTRUE_OBRIGATORIO")
        self._dsn = dsn
        self._gotrue = gotrue

    def export(self, authorization: str, payload: Any) -> dict[str, Any]:
        import psycopg
        fields = export_fields(payload)
        # Token verification is GoTrue /auth/v1/user, never JWT decoding alone.
        principal = self._gotrue.verify(authorization)
        if not isinstance(principal.actor_id, uuid.UUID) or not isinstance(principal.session_id, uuid.UUID):
            raise Denied("I73_IDENTIDADE_INVALIDA")
        try:
            with psycopg.connect(self._dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL ROLE prumo_s1_export_executor")
                    cur.execute(
                        "select prumo_export_auth.sessao_ativa(%s::uuid,%s::uuid)",
                        (principal.actor_id, principal.session_id))
                    row = cur.fetchone()
                    if row is None or row[0] is not True:
                        raise Denied("I73_SESSAO_INATIVA")
                    # Server-derived claims, never client-supplied actor IDs.
                    cur.execute(
                        "select pg_catalog.set_config('request.jwt.claim.sub',%s,true)",
                        (str(principal.actor_id),))
                    cur.execute(_SQL, fields)
                    result = cur.fetchone()
                    if result is None:
                        raise IdentityUnavailable("I73_SEM_RESPOSTA")
                    return _safe_reply(result[0])
        except psycopg.Error as exc:
            if exc.sqlstate == "42501":
                raise Denied("I73_OPERACAO_NEGADA") from None
            raise IdentityUnavailable("I73_BANCO_INDISPONIVEL") from None
