"""Synthetic S0 identity-boundary tests; do not use real user credentials."""
import base64
import hashlib
import hmac
import json
import sys
import types
import unittest
import uuid
from unittest.mock import patch

from backend.identity_boundary import (
    AuthenticatedCommands, Denied, IdentityUnavailable, InvalidCommand,
    Principal, PsycopgTrustedDatabase, PsycopgGatewayDatabase, SupabaseGoTrueVerifier,
    _gateway_signature_material,
)

A = "a1000000-0000-4000-8000-000000000001"
B = "a1000000-0000-4000-8000-000000000002"
SESSION = "b1000000-0000-4000-8000-000000000001"
SHOP_A = "c1000000-0000-4000-8000-000000000001"
PLAN_A = "d1000000-0000-4000-8000-000000000001"
PENDING = "e1000000-0000-4000-8000-000000000001"
KEY_ID = uuid.UUID("f1000000-0000-4000-8000-000000000001")
TEST_KEY = bytes.fromhex("a5" * 32)


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

    def test_03b_malformed_base64_after_gotrue_is_denied_not_500(self):
        verifier = SupabaseGoTrueVerifier(
            "http://127.0.0.1:54321", "local-key", opener=_Opener()
        )
        with self.assertRaises(Denied):
            verifier.verify("Bearer e30.a.fake-signature-long")

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
                    "postgresql://postgres:x@localhost:5432/postgresproducao",
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



class LeastPrivilegeGatewayTests(unittest.TestCase):
    def test_13_restricted_gateway_disallows_admin_or_remote_login(self):
        for url in (
            "postgresql://postgres:x@localhost:5432/postgres",
            "postgresql://supabase_admin:x@localhost:5432/postgres",
            "postgresql://gateway:x@db.example.com/postgres",
            "postgresql://gateway:x@localhost:5432/production",
            "postgresql://someone_else:x@localhost:5432/postgres",
            "postgresql://gateway:x@localhost:5432/postgres?options=-crole=postgres",
        ):
            with self.assertRaises(ValueError):
                PsycopgGatewayDatabase(url, key_id=KEY_ID, signing_key=TEST_KEY)

    def test_14_gateway_queries_only_whitelisted_wrappers_with_session(self):
        executed = []
        class Cursor:
            def __init__(self): self.row = ({"outcome": "APPLIED"},)
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def execute(self, query, values=None): executed.append((query, values))
            def fetchone(self): return self.row
        class Conn:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def cursor(self): return Cursor()
        with patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(connect=lambda *a, **k: Conn())}):
            gateway = PsycopgGatewayDatabase("postgresql://prumo_gateway_ci:fake@localhost:5432/postgres", key_id=KEY_ID, signing_key=TEST_KEY)
            result = gateway.invoke(Principal(uuid.UUID(A), uuid.UUID(SESSION)),
                "cancelar_plano", (uuid.UUID(SHOP_A), uuid.UUID(PLAN_A), 1))
            self.assertEqual(result["outcome"], "APPLIED")
            self.assertEqual(executed[0], ("SET LOCAL ROLE prumo_s0_gateway", None))
            self.assertIn("gateway_cancelar_plano_assinado_s0(", executed[1][0])
            args = executed[1][1]
            self.assertEqual(args[:5], (uuid.UUID(A), uuid.UUID(SESSION),
                                              uuid.UUID(SHOP_A), uuid.UUID(PLAN_A), 1))
            self.assertEqual(args[5], KEY_ID)
            self.assertIsInstance(args[6], int)
            self.assertIsInstance(args[7], uuid.UUID)
            material = _gateway_signature_material(
                Principal(uuid.UUID(A), uuid.UUID(SESSION)), "cancelar_plano",
                (uuid.UUID(SHOP_A), uuid.UUID(PLAN_A), 1), args[6], args[7])
            self.assertEqual(args[8], hmac.new(TEST_KEY, material, hashlib.sha256).hexdigest())
            self.assertNotIn("cancelar_plano_gestor_sintetico", executed[1][0])
            with self.assertRaises(InvalidCommand):
                gateway.invoke(Principal(uuid.UUID(A), uuid.UUID(SESSION)),
                               "execute_sql", ())
            self.assertEqual(len(executed), 2)

    def test_14b_requires_second_key_distinct_from_sql_password(self):
        for bad in (b"", b"short", None):
            with self.assertRaises(ValueError):
                PsycopgGatewayDatabase(
                    "postgresql://prumo_gateway_ci:fake@localhost/postgres",
                    key_id=KEY_ID, signing_key=bad)

    def test_14c_exact_signature_binds_decision_text_and_target(self):
        principal = Principal(uuid.UUID(A), uuid.UUID(SESSION))
        nonce = uuid.UUID("d1000000-0000-4000-8000-000000000007")
        values = (uuid.UUID(SHOP_A), uuid.UUID(PENDING), 1,
                  "ENCERRAR_SEM_PROVA", "Motivo ficticio suficiente", None)
        m = _gateway_signature_material(principal, "conciliar_c07", values, 1234567890, nonce)
        different = _gateway_signature_material(
            principal, "conciliar_c07",
            (uuid.UUID(SHOP_A), uuid.UUID(PENDING), 1,
             "ENCERRAR_SEM_PROVA", "Motivo ficticio ALTERADO", None),
            1234567890, nonce)
        self.assertNotEqual(m, different)
        self.assertNotEqual(m, _gateway_signature_material(
            principal, "conciliar_c07", values, 1234567891, nonce))

    def test_15_gateway_fails_if_set_role_is_not_allowed(self):
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def execute(self, query, values=None):
                raise PermissionError("role not granted")
            def fetchone(self): raise AssertionError("must not fetch")
        class Conn:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def cursor(self): return Cursor()
        with patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(connect=lambda *a, **k: Conn())}):
            with self.assertRaises(PermissionError):
                PsycopgGatewayDatabase("postgresql://prumo_gateway_ci:fake@localhost/postgres", key_id=KEY_ID, signing_key=TEST_KEY).invoke(
                    Principal(uuid.UUID(A), uuid.UUID(SESSION)), "cancelar_plano",
                    (uuid.UUID(SHOP_A), uuid.UUID(PLAN_A), 1))


if __name__ == "__main__":
    unittest.main()
