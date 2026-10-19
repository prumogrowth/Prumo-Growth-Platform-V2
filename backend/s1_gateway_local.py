"""S1-002/I19: gateway demonstrativo SOMENTE LOCAL, nunca deploy.

Confere Bearer via GoTrue confiável e define claims no PostgreSQL numa
transação sob login SQL restrito, que só pode assumir role authenticated.
A segurança contra COMPROMETIMENTO do login SQL exige segunda prova
independente (como S0/025); I19 NÃO satisfaz esse gate de produção.
"""
from __future__ import annotations

import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from backend.identity_boundary import (
    Denied, IdentityUnavailable, InvalidCommand, SupabaseGoTrueVerifier,
)

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SQL = {
    "mover": (
        "select prumo_s1_interface.s1_mover_atendimento_sessao("
        "%s::uuid,%s::uuid,%s::uuid,%s::uuid)",
        ("loja_id", "caso_id", "atribuicao_esperada_id", "destino_id"),
    ),
    "pausar": (
        "select prumo_s1_interface.s1_pausar_operador_sessao(%s::uuid,%s::text)",
        ("operador_id", "motivo_codigo"),
    ),
    "reativar": (
        "select prumo_s1_interface.s1_reativar_operador_sessao(%s::uuid)",
        ("operador_id",),
    ),
}
_REASON = frozenset(("AUSENCIA_TEMPORARIA", "INDISPONIBILIDADE_OPERACIONAL"))


def _uuid(value):
    if not isinstance(value, str) or not _UUID.fullmatch(value):
        raise InvalidCommand("ID_INVALIDO")
    return uuid.UUID(value)


def _fields(command, data):
    if command not in _SQL or type(data) is not dict:
        raise InvalidCommand("COMANDO_NAO_PERMITIDO")
    fields = _SQL[command][1]
    if set(data) != set(fields):
        raise InvalidCommand("CAMPOS_NAO_PERMITIDOS")
    output = []
    for field in fields:
        value = data[field]
        if field == "motivo_codigo":
            if type(value) is not str or value not in _REASON:
                raise InvalidCommand("MOTIVO_INVALIDO")
            output.append(value)
        else:
            output.append(_uuid(value))
    return tuple(output)


class LocalTeamGateway:
    def __init__(self, dsn, gotrue):
        parsed = urlsplit(dsn)
        if (parsed.scheme not in ("postgres", "postgresql")
            or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
            or parsed.username != "prumo_s1_gateway_ci"
            or parsed.path != "/postgres" or parsed.query or parsed.fragment):
            raise ValueError("DSN_LOCAL_E_ROLE_RESTRITOS_OBRIGATORIOS")
        self.dsn = dsn
        self.gotrue = gotrue

    def invoke(self, authorization, command, payload):
        import psycopg
        values = _fields(command, payload)
        principal = self.gotrue.verify(authorization)
        # Tokens NÃO são passados ao banco nem gravados; claims são derivados
        # exclusivamente do retorno confiável de GoTrue, nunca do JSON enviado.
        claims = json.dumps({
            "sub": str(principal.actor_id),
            "session_id": str(principal.session_id),
            "role": "authenticated",
        }, separators=(",", ":"))
        with psycopg.connect(self.dsn, connect_timeout=5) as connection:
            with connection.cursor() as cur:
                cur.execute("SET LOCAL ROLE authenticated")
                cur.execute(
                    "select set_config('request.jwt.claims', %s, true), "
                    "set_config('request.jwt.claim.sub', %s, true), "
                    "set_config('request.jwt.claim.role', 'authenticated', true)",
                    (claims, str(principal.actor_id)),
                )
                try:
                    cur.execute(_SQL[command][0], values)
                except psycopg.Error as exc:
                    if exc.sqlstate in ("42501", "23514", "22023"):
                        raise Denied("GESTAO_NAO_AUTORIZADA") from None
                    # Falha fechada, sem SQL/DSN/segredo na resposta HTTP.
                    raise IdentityUnavailable("DB_INDISPONIVEL") from None
                row = cur.fetchone()
                if row is None or type(row[0]) is not dict:
                    raise IdentityUnavailable("RESPOSTA_INVALIDA")
                return row[0]


def serve_local(gateway):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            command = self.path.removeprefix("/s1/")
            if self.path != "/s1/" + command or command not in _SQL:
                return self.respond(404, {"error": "NOT_FOUND"})
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self.respond(415, {"error": "CONTENT_TYPE"})
            size_text = self.headers.get("Content-Length", "")
            if not size_text.isascii() or not size_text.isdigit():
                return self.respond(400, {"error": "INVALID_SIZE"})
            size = int(size_text)
            if not 2 <= size <= 1024:
                return self.respond(413, {"error": "INVALID_SIZE"})
            try:
                data = json.loads(self.rfile.read(size))
                result = gateway.invoke(self.headers.get("Authorization", ""), command, data)
            except InvalidCommand:
                return self.respond(400, {"error": "INVALID_COMMAND"})
            except Denied:
                return self.respond(403, {"error": "DENIED"})
            except IdentityUnavailable:
                return self.respond(503, {"error": "IDENTITY_UNAVAILABLE"})
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
                return self.respond(400, {"error": "INVALID_JSON"})
            return self.respond(200, result)

        def respond(self, status, body):
            raw = json.dumps(body, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, _format, *_args):
            # Não registrar JWT, payload, headers ou stack trace.
            pass

    # Nunca bind remoto; testes HTTP exercitam somente loopback.
    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)
