"""I73 pure boundary checks: no client actor, SQL names or unsafe output."""
import unittest
import uuid

from backend.identity_boundary import InvalidCommand, IdentityUnavailable
from backend.s1_gateway_export_local import export_fields, _safe_reply, LocalExportGateway

SHOP = "86320000-0000-4000-8000-000000000001"


class I73ExportBoundaryTest(unittest.TestCase):
    def test_exact_fields(self):
        self.assertEqual(export_fields({"tipo":"lotes", "loja_id":SHOP,
                                       "apos":None,"limite":1})[0], "lotes")
        for extra in ("ator_id", "gestor_id", "sql", "session_id"):
            with self.assertRaises(InvalidCommand):
                export_fields({"tipo":"lotes","loja_id":SHOP,
                               "apos":None,"limite":1,extra:SHOP})

    def test_reject_bad_limits(self):
        for limit in (0,21,True,False,1.0,None,"2"):
            with self.assertRaises(InvalidCommand):
                export_fields({"tipo":"lotes","loja_id":SHOP,
                               "apos":None,"limite":limit})

    def test_reject_unknown_kind_and_cursor(self):
        for kind in ("leads","todas",None,1):
            with self.assertRaises(InvalidCommand):
                export_fields({"tipo":kind,"loja_id":SHOP,"apos":None,"limite":1})
        with self.assertRaises(InvalidCommand):
            export_fields({"tipo":"lotes","loja_id":SHOP,"apos":"0' OR true","limite":1})

    def test_validate_safe_rows_and_denials(self):
        self.assertEqual(_safe_reply({"estado":"VAZIO","linhas":[]})["estado"],"VAZIO")
        self.assertEqual(_safe_reply({"estado":"LIMITE_ATINGIDO","linhas":[]})["estado"],"LIMITE_ATINGIDO")
        with self.assertRaises(IdentityUnavailable):
            _safe_reply({"estado":"OK","linhas":[{"telefone":"555"}]})
        with self.assertRaises(IdentityUnavailable):
            _safe_reply({"estado":"VAZIO","linhas":[{"id":SHOP}]})
        with self.assertRaises(IdentityUnavailable):
            _safe_reply({"estado":"OK","linhas":[{}]*21})

    def test_no_remote_or_generic_sql_login(self):
        for dsn in ("postgresql://postgres:pw@localhost:54322/postgres",
                    "postgresql://prumo_s1_export_login_ci:pw@remote.test/postgres",
                    "postgresql://prumo_s1_export_login_ci:pw@localhost/prod"):
            with self.assertRaises(ValueError):
                LocalExportGateway(dsn, object())


if __name__ == "__main__":
    unittest.main()
