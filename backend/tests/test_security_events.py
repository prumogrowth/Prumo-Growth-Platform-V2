"""Synthetic denial-observability tests. Never use real credentials."""
import io
import logging
import unittest

from backend.identity_boundary import (
    AuthenticatedCommands, Denied, IdentityUnavailable, InvalidCommand,
)
from backend.security_events import SanitizedDenialLogger


class StubDb:
    def invoke(self, principal, command, values):
        return {"outcome": "APPLIED"}


class StubIdentity:
    def __init__(self, exc):
        self.exc = exc
    def verify(self, authorization):
        raise self.exc


class DenialSecurityEventTests(unittest.TestCase):
    def setUp(self):
        self.buf = io.StringIO()
        self.logger = logging.Logger("prumo_test_s0_denials")
        self.logger.setLevel(logging.WARNING)
        h = logging.StreamHandler(self.buf)
        h.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(h)
        self.sink = SanitizedDenialLogger(self.logger)

    def test_01_denied_goes_to_low_sensitivity_record(self):
        token = "Bearer SECRET_JWT_NEVER_LOG"
        server = AuthenticatedCommands(
            StubIdentity(Denied("REAL_TOKEN_SECRET")), StubDb(), self.sink
        )
        body = {
            "loja_id": "c1000000-0000-4000-8000-000000000001",
            "plano_id": "d1000000-0000-4000-8000-000000000001",
            "expected_version": 1,
        }
        with self.assertRaises(Denied):
            server.execute(token, "cancelar_plano", body)
        txt = self.buf.getvalue()
        self.assertIn("category=AUTH_DENIED command=cancelar_plano", txt)
        for secret in ("SECRET_JWT", "REAL_TOKEN_SECRET", body["loja_id"], body["plano_id"]):
            self.assertNotIn(secret, txt)

    def test_02_unknown_operation_never_logged_raw(self):
        server = AuthenticatedCommands(StubIdentity(Denied("ignore")), StubDb(), self.sink)
        with self.assertRaises(InvalidCommand):
            server.execute("Bearer x", "exploit\nAuthorization: Bearer SECRET", {})
        txt = self.buf.getvalue()
        self.assertIn("category=INPUT_REJECTED command=desconhecido", txt)
        self.assertNotIn("exploit", txt)
        self.assertNotIn("SECRET", txt)

    def test_03_auth_outage_classified_without_exception_body(self):
        server = AuthenticatedCommands(
            StubIdentity(IdentityUnavailable("https://sensitive.example/path?token=SECRET")),
            StubDb(), self.sink,
        )
        body = {
            "loja_id": "c1000000-0000-4000-8000-000000000001",
            "plano_id": "d1000000-0000-4000-8000-000000000001",
            "expected_version": 1,
        }
        with self.assertRaises(IdentityUnavailable):
            server.execute("Bearer x", "cancelar_plano", body)
        txt = self.buf.getvalue()
        self.assertIn("category=IDENTITY_UNAVAILABLE command=cancelar_plano", txt)
        self.assertNotIn("SECRET", txt)

    def test_04_event_sink_down_does_not_turn_denial_into_success(self):
        class DeadSink:
            def emit(self, category, command):
                raise RuntimeError("logger offline")
        server = AuthenticatedCommands(
            StubIdentity(Denied("unauthorized")), StubDb(), DeadSink(),
        )
        body = {
            "loja_id": "c1000000-0000-4000-8000-000000000001",
            "plano_id": "d1000000-0000-4000-8000-000000000001",
            "expected_version": 1,
        }
        with self.assertRaises(Denied):
            server.execute("Bearer x", "cancelar_plano", body)

    def test_05_invalid_log_category_rejected(self):
        with self.assertRaises(ValueError):
            self.sink.emit("SENSITIVE_PAYLOAD", "cancelar_plano")

    def test_06_unknown_command_name_is_scrubbed_directly(self):
        self.sink.emit("AUTH_DENIED", "Bearer a-secret")
        self.assertNotIn("a-secret", self.buf.getvalue())


if __name__ == "__main__":
    unittest.main()
