"""Trusted S0 backend boundary: verified user, live session, allowlisted writes.

No HTTP server is exposed by this module. The browser may submit an access token,
shop/object identifiers and expected version, never actor_id or arbitrary SQL.
GoTrue verifies the token; PostgreSQL checks the live session and existing private
domain functions enforce store membership atomically.

This prototype uses a privileged PostgreSQL connection for S0 LOCAL tests only.
NEVER deploy a postgres DSN to a public process, client or browser.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import time
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class Denied(Exception):
    """No valid identity or session, or no permission to perform the command."""


class InvalidCommand(Exception):
    """Unsupported operation or malformed public request."""


class IdentityUnavailable(Exception):
    """Identity authority unavailable: fail closed without touching database."""


@dataclass(frozen=True)
class Principal:
    actor_id: uuid.UUID
    session_id: uuid.UUID


class IdentityProvider(Protocol):
    def verify(self, authorization: str) -> Principal: ...


class CommandDatabase(Protocol):
    def invoke(self, principal: Principal, command: str, values: tuple[Any, ...]) -> dict[str, Any]: ...


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: Any, msg: Any, hdrs: Any, newurl: Any) -> None:
        return None


def _uuid(value: Any) -> uuid.UUID:
    if not isinstance(value, str):
        raise InvalidCommand("ID_INVALIDO")
    try:
        result = uuid.UUID(value)
    except (ValueError, AttributeError):
        raise InvalidCommand("ID_INVALIDO") from None
    if str(result) != value.lower():
        raise InvalidCommand("ID_INVALIDO")
    return result


def _version(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 9223372036854775807:
        raise InvalidCommand("VERSAO_INVALIDA")
    return value


def _claims_verified_only(token: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Decode ONLY after server GoTrue verification. Does NOT verify JWT signature."""
    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        raise Denied("TOKEN_INVALIDO")
    try:
        payload_bytes = base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
        claims = json.loads(payload_bytes)
        if not isinstance(claims, dict) or claims.get("role") != "authenticated":
            raise ValueError("invalid role")
        return uuid.UUID(str(claims["sub"])), uuid.UUID(str(claims["session_id"]))
    except (ValueError, TypeError, KeyError, OverflowError, UnicodeDecodeError, binascii.Error):
        raise Denied("TOKEN_SESSAO_INVALIDO") from None


class SupabaseGoTrueVerifier:
    """Calls configured trusted GET /auth/v1/user; authentication never trusts body identity."""

    def __init__(self, api_url: str, publishable_key: str, opener: Any = None):
        u = urllib.parse.urlsplit(api_url)
        local = u.hostname in ("localhost", "127.0.0.1", "::1")
        if (u.scheme != "https" and not (u.scheme == "http" and local)) or not u.hostname or u.username or u.password or u.query or u.fragment or u.path.rstrip("/") not in ("",):
            raise ValueError("TRUSTED_AUTH_URL_REQUIRED")
        if not publishable_key or not publishable_key.isascii() or "\r" in publishable_key or "\n" in publishable_key:
            raise ValueError("API_KEY_INVALID")
        self._url = api_url.rstrip("/") + "/auth/v1/user"
        self._key = publishable_key
        self._opener = opener if opener is not None else urllib.request.build_opener(_NoRedirect())

    def verify(self, authorization: str) -> Principal:
        if not isinstance(authorization, str) or not re.fullmatch(r"Bearer [A-Za-z0-9_.-]{20,8192}", authorization):
            raise Denied("BEARER_REQUIRED")
        token = authorization[7:]
        request = urllib.request.Request(self._url, headers={
            "Authorization": authorization, "apikey": self._key, "Accept": "application/json"
        }, method="GET")
        try:
            with self._opener.open(request, timeout=5) as res:
                if res.status != 200:
                    raise Denied("AUTH_REJEITADA")
                body = res.read(65537)
                if len(body) > 65536:
                    raise Denied("AUTH_RESPONSE_INVALID")
                user = json.loads(body)
        except urllib.error.HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308, 401, 403, 404):
                raise Denied("AUTH_REJEITADA") from None
            raise IdentityUnavailable("AUTH_INDISPONIVEL") from None
        except (OSError, TimeoutError, urllib.error.URLError):
            raise IdentityUnavailable("AUTH_INDISPONIVEL") from None
        except (ValueError, UnicodeDecodeError):
            raise Denied("AUTH_RESPONSE_INVALID") from None
        if not isinstance(user, dict) or user.get("role") != "authenticated":
            raise Denied("AUTH_REJEITADA")
        try:
            uid = uuid.UUID(str(user["id"]))
        except (KeyError, ValueError, TypeError):
            raise Denied("AUTH_RESPONSE_INVALID") from None
        # GoTrue verified token first; claims are used ONLY to bind session to user.
        sub, session_id = _claims_verified_only(token)
        if sub != uid:
            raise Denied("IDENTIDADE_DIVERGENTE")
        return Principal(uid, session_id)


# Fixed SQL statements ONLY: no operation/table names interpolated from clients.
_STATEMENTS = {
    "cancelar_plano": (
        "select prumo_private.cancelar_plano_gestor_sintetico(%s::uuid,%s::uuid,%s::uuid,%s::bigint)",
        ("loja_id", "plano_id", "expected_version"),
    ),
    "conciliar_c07": (
        "select prumo_private.conciliar_pendencia_c07_sintetica(%s::uuid,%s::uuid,%s::uuid,%s::bigint,%s::text,%s::text,%s::uuid)",
        ("loja_id", "pendencia_id", "expected_version", "decisao", "justificativa", "envio_id"),
    ),
}


class AuthenticatedCommands:
    """Command boundary (not an HTTP route) with only two S0 permitted writes."""

    def __init__(self, identity: IdentityProvider, database: CommandDatabase):
        self._identity = identity
        self._database = database

    def execute(self, authorization: str, command: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if command not in _STATEMENTS or not isinstance(payload, dict):
            raise InvalidCommand("COMANDO_NAO_PERMITIDO")
        expected = set(_STATEMENTS[command][1])
        if set(payload) != expected:
            raise InvalidCommand("CAMPOS_NAO_PERMITIDOS")
        shop = _uuid(payload["loja_id"])
        version = _version(payload["expected_version"])
        if command == "cancelar_plano":
            values: tuple[Any, ...] = (shop, _uuid(payload["plano_id"]), version)
        else:
            decision = payload["decisao"]
            reason = payload["justificativa"]
            if decision not in ("ENCERRAR_SEM_PROVA", "VINCULAR_SINTETICAMENTE") or not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 500:
                raise InvalidCommand("DECISAO_INVALIDA")
            target = payload["envio_id"]
            if (decision == "VINCULAR_SINTETICAMENTE") != (target is not None):
                raise InvalidCommand("ALVO_INVALIDO")
            values = (shop, _uuid(payload["pendencia_id"]), version, decision, reason, _uuid(target) if target is not None else None)
        principal = self._identity.verify(authorization)
        return self._database.invoke(principal, command, values)


class PsycopgTrustedDatabase:
    """Postgres-only LOCAL S0 adapter. NEVER use a client or hosted remote DSN."""

    def __init__(self, dsn: str):
        u = urllib.parse.urlsplit(dsn)
        if u.scheme not in ("postgres", "postgresql") or u.hostname not in ("127.0.0.1", "localhost", "::1") or not (u.path.strip("/") == "postgres" or u.path.strip("/").startswith("prumo_s0_test_")):
            raise ValueError("ONLY_DISPOSABLE_LOCAL_DATABASE")
        self._dsn = dsn

    def invoke(self, principal: Principal, command: str, values: tuple[Any, ...]) -> dict[str, Any]:
        # Optional dependency imported only when LOCAL integration runs.
        import psycopg
        sql, _ = _STATEMENTS[command]
        with psycopg.connect(self._dsn, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select 1 from auth.sessions where id=%s::uuid and user_id=%s::uuid for key share",
                    (principal.session_id, principal.actor_id),
                )
                if cursor.fetchone() is None:
                    raise Denied("SESSAO_INATIVA")
                cursor.execute(sql, (principal.actor_id, *values))
                result = cursor.fetchone()
                if result is None or not isinstance(result[0], dict):
                    raise IdentityUnavailable("DB_RESULTADO_INVALIDO")
                return result[0]


# LOCAL S0 demonstration only. Signing key and DB login must be separately
# provisioned out-of-band; never include either in the repository or browser.
# This is NOT a final production security design or a public HTTP endpoint.
_GATEWAY_STATEMENTS = {
    "cancelar_plano": (
        "select prumo_private.gateway_cancelar_plano_assinado_s0("
        "%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::bigint,"
        "%s::uuid,%s::bigint,%s::uuid,%s::text)"
    ),
    "conciliar_c07": (
        "select prumo_private.gateway_conciliar_c07_assinado_s0("
        "%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s::bigint,%s::text,"
        "%s::text,%s::uuid,%s::uuid,%s::bigint,%s::uuid,%s::text)"
    ),
}


def _gateway_signature_material(
    principal: Principal, command: str, values: tuple[Any, ...],
    issued_at: int, nonce: uuid.UUID,
) -> bytes:
    if command not in _GATEWAY_STATEMENTS:
        raise InvalidCommand("COMANDO_NAO_PERMITIDO")
    if command == "cancelar_plano":
        shop, target, version = values
        decision, reason, related = "-", "", "-"
    else:
        shop, target, version, decision, reason, related_uuid = values
        related = str(related_uuid) if related_uuid is not None else "-"
    reason_hash = hashlib.sha256(reason.encode("utf-8")).hexdigest()
    material = "|".join([
        "prumo-gw-v1", command, str(principal.actor_id),
        str(principal.session_id), str(shop), str(target), str(version),
        decision, reason_hash, related, str(issued_at), str(nonce),
    ])
    return material.encode("utf-8")


class PsycopgGatewayDatabase:
    """LOCAL-only restricted SQL login plus separate HMAC proof. No remote DSN."""

    def __init__(self, dsn: str, *, key_id: uuid.UUID, signing_key: bytes):
        u = urllib.parse.urlsplit(dsn)
        if (
            u.scheme not in ("postgres", "postgresql")
            or u.hostname not in ("127.0.0.1", "localhost", "::1")
            or not u.username or not u.username.startswith("prumo_gateway_")
            or u.query or u.fragment
            or not (u.path.strip("/") == "postgres"
                    or u.path.strip("/").startswith("prumo_s0_test_"))
        ):
            raise ValueError("GATEWAY_LOCAL_LEAST_PRIVILEGE_DSN_REQUIRED")
        if not isinstance(key_id, uuid.UUID) or not isinstance(signing_key, bytes) or len(signing_key) < 32:
            raise ValueError("GATEWAY_SECOND_FACTOR_REQUIRED")
        self._dsn = dsn
        self._key_id = key_id
        self._signing_key = signing_key

    def invoke(self, principal: Principal, command: str, values: tuple[Any, ...]) -> dict[str, Any]:
        import psycopg
        sql = _GATEWAY_STATEMENTS.get(command)
        if sql is None:
            raise InvalidCommand("COMANDO_NAO_PERMITIDO")
        # Only after GoTrue verification in AuthenticatedCommands.
        # A nonce is unique per invocation; a duplicate HTTP request receives
        # a FRESH proof and domain idempotency handles ALREADY_APPLIED.
        issued_at = int(time.time())
        nonce = uuid.uuid4()
        signature = hmac.new(
            self._signing_key,
            _gateway_signature_material(principal, command, values, issued_at, nonce),
            hashlib.sha256,
        ).hexdigest()
        with psycopg.connect(self._dsn, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL ROLE prumo_s0_gateway")
                try:
                    cursor.execute(
                        sql, (principal.actor_id, principal.session_id, *values,
                              self._key_id, issued_at, nonce, signature)
                    )
                except psycopg.errors.InsufficientPrivilege:
                    raise Denied("ACESSO_NEGADO") from None
                row = cursor.fetchone()
                if row is None or not isinstance(row[0], dict):
                    raise IdentityUnavailable("DB_RESULTADO_INVALIDO")
                return row[0]
