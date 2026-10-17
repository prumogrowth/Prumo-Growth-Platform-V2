"""Synthetic S0 identity-boundary tests; do not use real user credentials."""
import base64
import json
import sys
import types
import unittest
import uuid
from unittest.mock import patch

from backend.identity_boundary import (
    AuthenticatedCommands, Denied, IdentityUnavailable, InvalidCommand,
    Principal, PsycopgTrustedDatabase, SupabaseGoTrueVerifier,
)

A = "a1000000-0000-4000-8000-000000000001"
B = "a1000000-0000-4000-8000-000000000002"
SESSION = "b1000000-0000-4000-8000-000000000001"
SHOP_A = "c1000000-0000-4000-8000-000000000001"
PLAN_A = "d1000000-0000-4000-8000-000000000001"
PENDING = "e1000000-0000-4000-8000-000000000001"


def fake_token(sub=A, session=SESSION, **extra):
    claims = {"sub": sub, "session_id": session, "role": "authenticated", **extra}
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return "e30." + body + ".fake-signature"


class _Reply:
    status = 200
    def __init__(self, response): self.response = response
    def __enter__(self): return self
    def __exit__(self, *_): return None
    def read(self, size): return json.dumps(self.response).encode()


class _Opener:
    def __init__(self, user_id=A):
        self.user_id = user_id
        self.calls = []
    def open(self, req, timeout):
        self.calls.append((req.full_url, req.get_header("Authorization"), timeout))
        return _Reply({"id": self.user_id, "role": "authenticated"})


class _Identity:
    def __init__(self, actor=A):
        self.actor = uuid.UUID(actor)
        self.calls = []
    def verify(self, token):
        self.calls.append(token)
        return Principal(self.actor, uuid.UUID(SESSION))


class _DB:
    def __init__(self): self.calls = []
    def invoke(self, principal, command, values):
        self.calls.append((principal, command, values))
        return {"outcome": "APPLIED", "transmissao_externa": "DESABILITADA"}


def cancel_payload(**kwargs):
    return {"loja_id": SHOP_A, "plano_id": PLAN_A, "expected_version": 1, **kwargs}


def reconcile_payload(**kwargs):
    return {"loja_id": SHOP_A, "pendencia_id": PENDING, "expected_version": 1,
            "decisao": "ENCERRAR_SEM_PROVA", "justificativa": "Registro ficticio revisado",
            "envio_id": None, **kwargs}


class IdentityBoundaryTests(unittest.TestCase):
    def test_01_authenticated_subject_from_gotrue_not_user_metadata(self):
        opener = _Opener()
        api = SupabaseGoTrueVerifier("http://127.0.0.1:54321", "local-key", opener=opener)
        principal = api.verify("Bearer " + fake_token(user_metadata={"actor_id": B}))
        self.assertEqual(str(principal.actor_id), A)
        self.assertEqual(str(principal.session_id), SESSION)
        self.assertEqual(opener.calls[0][0], "http://127.0.0.1:54321/auth/v1/user")

    def test_02_token_subject_must_match_verified_user(self):
        with self.assertRaises(Denied):
            SupabaseGoTrueVerifier("http://localhost:54321", "local-key", opener=_Opener()).verify("Bearer " + fake_token(sub=B))

    def test_03_missing_session_denied(self):
        with self.assertRaises(Denied):
            SupabaseGoTrueVerifier("http://localhost:54321", "local-key", opener=_Opener()).verify("Bearer " + fake_token(session="bad"))

    def test_04_auth_origin_cannot_be_untrusted_http_or_path(self):
        for url in ("http://example.com", "https://example.com/evil", "https://user:pass@example.com", "https://example.com?foo=1"):
            with self.assertRaises(ValueError, msg=url):
                SupabaseGoTrueVerifier(url, "key")

    def test_05_invalid_bearer_fails_closed(self):
        for head in ("", "Basic bad", "Bearer", "bearer " + fake_token(), "Bearer token with space"):
            with self.assertRaises(Denied):
                SupabaseGoTrueVerifier("http://localhost:54321", "local-key", opener=_Opener()).verify(head)

    def test_06_allowlist_rejects_arbitrary_actor_and_sql(self):
        identity, db = _Identity(), _DB()
        server = AuthenticatedCommands(identity, db)
        for command, body in (
            ("delete_database", cancel_payload()),
            ("cancelar_plano", cancel_payload(actor_id=B)),
            ("cancelar_plano", cancel_payload(principal=B)),
            ("conciliar_c07", reconcile_payload(actor_id=B)),
        ):
            with self.assertRaises(InvalidCommand):
                server.execute("Bearer synthetic", command, body)
        self.assertEqual(identity.calls, [])
        self.assertEqual(db.calls, [])

    def test_07_only_verified_actor_reaches_database(self):
        identity, db = _Identity(A), _DB()
        server = AuthenticatedCommands(identity, db)
        self.assertEqual(server.execute("Bearer test", "cancelar_plano", cancel_payload())["outcome"], "APPLIED")
        principal, command, values = db.calls[0]
        self.assertEqual(str(principal.actor_id), A)
        self.assertEqual(command, "cancelar_plano")
        self.assertEqual(values, (uuid.UUID(SHOP_A), uuid.UUID(PLAN_A), 1))

    def test_08_reconciliation_exact_validation(self):
        server = AuthenticatedCommands(_Identity(), _DB())
        for body in (
            reconcile_payload(decisao="RETRY_AUTOMATICO"),
            reconcile_payload(justificativa="curto"),
            reconcile_payload(envio_id=PLAN_A),
            reconcile_payload(expected_version=True),
            reconcile_payload(loja_id="1;drop table auth.sessions"),
        ):
            with self.assertRaises(InvalidCommand):
                server.execute("Bearer x", "conciliar_c07", body)
        self.assertEqual(server.execute("Bearer x", "conciliar_c07",
            reconcile_payload(decisao="VINCULAR_SINTETICAMENTE", envio_id=PLAN_A))["outcome"], "APPLIED")

    def test_09_privileged_database_cannot_point_remote(self):
        for dsn in ("postgresql://postgres:x@db.example.com:5432/postgres",
                    "postgresql://postgres:x@localhost:5432/producao",
                    "sqlite:///tmp/test.db"):
            with self.assertRaises(ValueError):
                PsycopgTrustedDatabase(dsn)

    def test_10_active_session_checked_and_sql_is_parameterized(self):
        executed = []
        class Cursor:
            def __init__(self): self.rows = [(1,), ({"outcome": "APPLIED"},)]
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def execute(self, sql, args): executed.append((sql, args))
            def fetchone(self): return self.rows.pop(0)
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def cursor(self): return Cursor()
        with patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(connect=lambda *a, **k: Connection())}):
            db = PsycopgTrustedDatabase("postgresql://postgres:x@localhost:5432/postgres")
            resp = db.invoke(Principal(uuid.UUID(A), uuid.UUID(SESSION)),
                "cancelar_plano", (uuid.UUID(SHOP_A), uuid.UUID(PLAN_A), 1))
        self.assertEqual(resp["outcome"], "APPLIED")
        self.assertIn("auth.sessions", executed[0][0])
        self.assertIn("FOR KEY SHARE", executed[0][0].upper())
        self.assertEqual(executed[1][1][0], uuid.UUID(A))
        self.assertEqual(len(executed[1][1]), 4)
        self.assertIn("%s", executed[1][0])

    def test_11_revoked_session_prevents_write(self):
        executed = []
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def execute(self, sql, args): executed.append(sql)
            def fetchone(self): return None
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def cursor(self): return Cursor()
        with patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(connect=lambda *a, **k: Connection())}):
            db = PsycopgTrustedDatabase("postgresql://postgres:x@localhost:5432/postgres")
            with self.assertRaises(Denied):
                db.invoke(Principal(uuid.UUID(A), uuid.UUID(SESSION)),
                          "cancelar_plano", (uuid.UUID(SHOP_A), uuid.UUID(PLAN_A), 1))
        self.assertEqual(len(executed), 1)

    def test_12_auth_outage_cannot_write_to_database(self):
        class Failing:
            def verify(self, token): raise IdentityUnavailable("AUTH_INDISPONIVEL")
        db = _DB()
        with self.assertRaises(IdentityUnavailable):
            AuthenticatedCommands(Failing(), db).execute("Bearer x", "cancelar_plano", cancel_payload())
        self.assertEqual(db.calls, [])


if __name__ == "__main__":
    unittest.main()
