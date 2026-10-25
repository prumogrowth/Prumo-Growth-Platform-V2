"""S1-002/I23 - fronteira HTTP defensiva APENAS para testes locais.

Nao e servidor de producao: http.server nao oferece TLS, proxy confiavel,
controles distribuidos de taxa ou resiliencia contra Slowloris em escala.
Recebe requests exclusivamente no loopback, sem cookies, sem CORS/browser.
O adapter assinado I22 segue responsavel por GoTrue/HMAC/SQL/RBAC.
"""
from __future__ import annotations

import ipaddress
import json
import re
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from backend.identity_boundary import Denied, IdentityUnavailable, InvalidCommand
from backend.s1_command_validation_local import LEGACY_COMMANDS

_BEARER = re.compile(r"Bearer [A-Za-z0-9_.-]{20,8192}\Z")
_LENGTH = re.compile(r"[0-9]{1,5}\Z")
_MAX_BODY = 1024
_FORBIDDEN = (
    "Transfer-Encoding", "Cookie", "Forwarded", "X-Forwarded-For",
    "X-Forwarded-Host", "X-Forwarded-Proto", "X-Real-IP",
    "Proxy-Authorization", "Proxy-Connection",
)


class _RateLimit:
    """Deterministic per-peer fixed-window brake (local, NOT distributed)."""

    def __init__(self, maximum: int, seconds: float, clock=None):
        if type(maximum) is not int or not 1 <= maximum <= 10000:
            raise ValueError("RATE_LIMIT_INVALIDO")
        if not isinstance(seconds, (int, float)) or seconds <= 0:
            raise ValueError("WINDOW_INVALIDA")
        self.maximum = maximum
        self.seconds = float(seconds)
        self.clock = clock or time.monotonic
        self._lock = threading.Lock()
        self._hits: dict[str, tuple[float, int]] = {}

    def allow(self, peer: str) -> bool:
        now = self.clock()
        with self._lock:
            start, count = self._hits.get(peer, (now, 0))
            if now - start >= self.seconds:
                start, count = now, 0
            # Bounded in practice by loopback-only binding. Not production scale.
            self._hits[peer] = (start, count + 1)
            return count < self.maximum


def _reject_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_constant(_value):
    raise ValueError("NON_FINITE_JSON")


def _parse_body(raw: bytes):
    # Explicit UTF-8, duplicate object fields, NaN/Infinity, top-level arrays
    # or scalar values all fail closed before GoTrue/DB calls.
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_pairs,
                      parse_constant=_reject_constant)
    if type(data) is not dict:
        raise ValueError("OBJECT_REQUIRED")
    return data


def serve_http_policy_local(gateway, *, max_requests=200, window_seconds=60,
                            allowed_origins=(), security_events=None,
                            allowed_commands=None):
    """Return a loopback-only test server; caller must shutdown/server_close."""
    commands = frozenset(LEGACY_COMMANDS) if allowed_commands is None else frozenset(allowed_commands)
    if not commands or not commands.issubset({"mover","pausar","reativar","intake","fila","assumir_fila","mover_excecao","revogar_excecao"}):
        raise ValueError("HTTP_COMMAND_ALLOWLIST_INVALID")
    origins = tuple(allowed_origins)
    for origin in origins:
        if not isinstance(origin, str) or not re.fullmatch(
            r"https?://(?:127\.0\.0\.1|localhost)(?::[0-9]{1,5})?", origin
        ):
            raise ValueError("UNTRUSTED_ORIGIN")
    limiter = _RateLimit(max_requests, window_seconds)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, _format, *_args):
            # Nao imprimir JWT, headers, query, IDs, stack ou corpo do cliente.
            pass

        def _audit(self, category, command):
            if security_events is not None:
                try:
                    security_events.emit(category, command)
                except Exception:
                    pass

        def _respond(self, status, error=None, payload=None, extra=None):
            body = payload if payload is not None else {"error": error or "DENIED"}
            raw = json.dumps(body, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Pragma", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.send_header("Connection", "close")
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.close_connection = True
            try:
                self.wfile.write(raw)
            except (OSError, BrokenPipeError):
                pass

        def handle_expect_100(self):
            self._respond(417, "EXPECT_NOT_SUPPORTED")
            return False

        def do_POST(self):
            command = self.path.removeprefix("/s1/")
            if self.path != "/s1/" + command or command not in commands:
                return self._respond(404, "NOT_FOUND")
            command_name = command  # constant allowlisted code, not raw URL
            try:
                if not ipaddress.ip_address(self.client_address[0]).is_loopback:
                    self._audit("HTTP_AUTH_DENIED", command_name)
                    return self._respond(403, "DENIED")
                expected_host = "127.0.0.1:" + str(self.server.server_address[1])
                headers = self.headers
                if (headers.get_all("Host", []) != [expected_host]
                    or any(headers.get_all(name, []) for name in _FORBIDDEN)
                    or any(len(headers.get_all(name, [])) != 1 for name in
                           ("Authorization", "Content-Type", "Content-Length"))):
                    self._audit("HTTP_INPUT_REJECTED", command_name)
                    return self._respond(400, "INVALID_HEADERS")
                origin = headers.get_all("Origin", [])
                if len(origin) > 1 or (origin and origin[0] not in origins):
                    self._audit("HTTP_AUTH_DENIED", command_name)
                    return self._respond(403, "ORIGIN_DENIED")
                if headers.get_all("Content-Type") != ["application/json"]:
                    self._audit("HTTP_INPUT_REJECTED", command_name)
                    return self._respond(415, "CONTENT_TYPE")
                auth = headers.get("Authorization", "")
                if not _BEARER.fullmatch(auth):
                    self._audit("HTTP_AUTH_DENIED", command_name)
                    return self._respond(403, "DENIED")
                length_value = headers.get("Content-Length", "")
                if not _LENGTH.fullmatch(length_value):
                    self._audit("HTTP_INPUT_REJECTED", command_name)
                    return self._respond(400, "INVALID_SIZE")
                size = int(length_value)
                if not 2 <= size <= _MAX_BODY:
                    self._audit("HTTP_INPUT_REJECTED", command_name)
                    return self._respond(413, "INVALID_SIZE")
                if not limiter.allow(self.client_address[0]):
                    self._audit("HTTP_RATE_LIMITED", command_name)
                    return self._respond(429, "RATE_LIMITED", extra={"Retry-After": "60"})
                try:
                    raw = self.rfile.read(size)
                except (TimeoutError, socket.timeout):
                    self._audit("HTTP_INPUT_REJECTED", command_name)
                    return self._respond(408, "REQUEST_TIMEOUT")
                if len(raw) != size:
                    self._audit("HTTP_INPUT_REJECTED", command_name)
                    return self._respond(400, "INVALID_BODY")
                try:
                    payload = _parse_body(raw)
                except (ValueError, UnicodeError):
                    self._audit("HTTP_INPUT_REJECTED", command_name)
                    return self._respond(400, "INVALID_JSON")
                try:
                    answer = gateway.invoke(auth, command, payload)
                except InvalidCommand:
                    self._audit("HTTP_INPUT_REJECTED", command_name)
                    return self._respond(400, "INVALID_COMMAND")
                except Denied:
                    self._audit("HTTP_AUTH_DENIED", command_name)
                    return self._respond(403, "DENIED")
                except IdentityUnavailable:
                    self._audit("HTTP_UPSTREAM_UNAVAILABLE", command_name)
                    return self._respond(503, "UNAVAILABLE")
                except Exception:
                    # Fail closed: no stack trace or credentials in HTTP output.
                    self._audit("HTTP_UPSTREAM_UNAVAILABLE", command_name)
                    return self._respond(503, "UNAVAILABLE")
                if type(answer) is not dict:
                    self._audit("HTTP_UPSTREAM_UNAVAILABLE", command_name)
                    return self._respond(503, "UNAVAILABLE")
                if command_name in ("intake","assumir_fila") and answer.get("outcome") in ("CONFLICT","ALREADY_HAS_CASE"):
                    return self._respond(409, payload={"outcome": "CONFLICT"})
                return self._respond(200, payload=answer)
            except (ValueError, TypeError):
                self._audit("HTTP_INPUT_REJECTED", command_name)
                return self._respond(400, "INVALID_HEADERS")

        def _method_not_allowed(self):
            return self._respond(405, "METHOD_NOT_ALLOWED", extra={"Allow": "POST"})

        do_GET = _method_not_allowed
        do_HEAD = _method_not_allowed
        do_PUT = _method_not_allowed
        do_PATCH = _method_not_allowed
        do_DELETE = _method_not_allowed
        do_OPTIONS = _method_not_allowed

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    return server
