"""I75C: contract tests for safe, local, effective G3 catalog verification."""
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
  "i75c_pg17",ROOT/"scripts/test_s1_002_i75c_pg17_effective_catalog.py")
scanner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)

def fixture():
    entries=[]
    for name,required in scanner.EXPECTED.items():
        columns=[{"name":n,"anon_select":False,"authenticated_select":True}
                 for n in required]
        entries.append({"name":name,"exists":True,"rls_enabled":True,
                        "anon_select":False,"authenticated_select":True,
                        "columns":columns,"policies":[]})
    return {"tables":entries,"storage_objects_declared":False,
            "storage_buckets_declared":False}

class I75CContract(unittest.TestCase):
    def test_reject_remote_and_non_ephemeral_databases(self):
        for db in (
          "postgresql://postgres:pw@database.example.com/prumo_s0_test_dev",
          "postgresql://postgres:pw@localhost/production",
          "postgresql://postgres:pw@localhost/prumo_s0_test_dev?sslmode=disable"):
            with self.assertRaisesRegex(ValueError,"I75C_REFUSES"):
                scanner.check_url(db)
        self.assertEqual(scanner.check_url(
            "postgresql://postgres:pw@127.0.0.1:5432/prumo_s0_test_ci"),
            "postgresql://postgres:pw@127.0.0.1:5432/prumo_s0_test_ci")

    def test_accept_baseline_without_promoting_media(self):
        metrics=scanner.validate(fixture())
        self.assertEqual(metrics["tables"],11)
        self.assertEqual(metrics["rls_enabled"],11)
        self.assertFalse(metrics["media_contract_verified"])
        self.assertFalse(metrics["d3_d4_column_contract_verified"])
        self.assertFalse(metrics["runtime_authorization_verified"])

    def test_deny_missing_rls(self):
        f=fixture();f["tables"][0]["rls_enabled"]=False
        with self.assertRaisesRegex(ValueError,"I75C_MISSING_RLS"):
            scanner.validate(f)

    def test_deny_anon_table_read(self):
        f=fixture();f["tables"][0]["anon_select"]=True
        with self.assertRaisesRegex(ValueError,"I75C_ANON_TABLE_READ"):
            scanner.validate(f)

    def test_deny_anon_column_read(self):
        f=fixture();f["tables"][0]["columns"][0]["anon_select"]=True
        with self.assertRaisesRegex(ValueError,"I75C_ANON_COLUMN_LEAK"):
            scanner.validate(f)

    def test_deny_test_only_policy_persisted(self):
        f=fixture();f["tables"][0]["policies"]=[
           {"name":"s1_63_canon_casos_p","command":"r","permissive":True}]
        with self.assertRaisesRegex(ValueError,"I75C_TEST_POLICY_PERSISTED"):
            scanner.validate(f)

    def test_deny_column_drift(self):
        f=fixture()
        table=next(t for t in f["tables"] if t["name"]=="mensagens")
        table["columns"]=[c for c in table["columns"] if c["name"]!="concessionaria_id"]
        with self.assertRaisesRegex(ValueError,"I75C_REQUIRED_COLUMN_DRIFT"):
            scanner.validate(f)

    def test_deny_missing_table(self):
        f=fixture();f["tables"].pop()
        with self.assertRaisesRegex(ValueError,"I75C_UNEXPECTED_RELATION_SET"):
            scanner.validate(f)

if __name__=="__main__":unittest.main()
