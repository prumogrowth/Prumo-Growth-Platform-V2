"""Offline structural proof-source inventory: source presence is NOT authenticity."""
import ast
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
MAP=ROOT/"docs/contracts/OAI_E04_F02_S0_MAPA_QUATRO_PROVAS_V1.json"
FIELDS={"f03_receipt_sha256","c08_local_witness_sha256",
        "origin_ledger_sha256","human_intent_sha256"}

def read():
    return json.loads(MAP.read_text(encoding="utf-8"))

def method_exists(path, dotted):
    source=ROOT/path
    if not source.is_file(): return False
    parsed=ast.parse(source.read_text(encoding="utf-8"))
    cls,name=dotted.split(".")
    return any(isinstance(n,ast.ClassDef) and n.name==cls and
               any(isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef))
                   and child.name==name for child in n.body)
               for n in parsed.body)

class ProofSources(unittest.TestCase):
    def test_01_four_expected_claimed_fields_only(self):
        d=read()
        self.assertEqual({x["field"] for x in d["fields"]},FIELDS)
        self.assertEqual(len(d["fields"]),4)

    def test_02_producers_exist_with_documented_methods(self):
        for p in read()["fields"]:
            with self.subTest(p=p["field"]):
                self.assertTrue(method_exists(p["producer"],p["symbol"]))

    def test_03_additional_f03_evidence_bridge_exists(self):
        x=read()["fields"][0]
        self.assertEqual(x["field"],"f03_receipt_sha256")
        self.assertTrue(method_exists(x["additional"],x["additional_symbol"]))

    def test_04_f01_cfi_handover_producers_exist(self):
        h=read()["handover"]
        self.assertTrue(method_exists(h["producer"],h["symbol"]))
        self.assertTrue(method_exists(h["transport"],h["transport_symbol"]))
        self.assertIn("NOT_F01_F03_COMPLETE",h["state"])

    def test_05_field_claims_resolve_to_existing_handoff_dataclass(self):
        from backend.f02_reconciled_human_authorization_handoff import ClaimedS0Evidence
        names=set(ClaimedS0Evidence.__dataclass_fields__)
        self.assertTrue(FIELDS<=names)

    def test_06_no_attested_send_or_s1_ratification(self):
        d=read()
        self.assertFalse(d["schema_cannot_authorize_send"] is False)
        self.assertTrue(all(x["operationally_verified"] is False for x in d["fields"]))
        self.assertEqual(d["consumer"]["status"],"UNSIGNED_ALLEGATIONS_NEVER_SOURCE_PROOF")

    def test_07_each_producer_has_missing_identity_metadata(self):
        for x in read()["fields"]:
            self.assertGreaterEqual(len(x["identity_needed"]),6)
            self.assertTrue(x["required_verification"])
            self.assertTrue(x["stage"].endswith(("_ONLY","AUDIT_ONLY")))

    def test_08_audit_reconciliation_preserves_all_seven_gates(self):
        d=read()
        self.assertEqual(d["status_current"],"G03_PARTIAL_G07_PENDING")
        self.assertEqual(d["hard_gates_unchanged"],
            ["G01","G02","G03","G04","G05","G06","G07"])
        self.assertEqual(d["source_audit"]["sha"],
            "7c282df5f6e5942729f15187c199dffb5e872797")

    def test_09_no_product_or_external_meta_claim_by_local_witness(self):
        d=read()
        c=next(x for x in d["fields"] if x["field"]=="c08_local_witness_sha256")
        self.assertIn("LOCAL_CANCELLATION",c["stage"])
        self.assertIn("external Meta outcome remains unknown",
                      c["required_verification"])

    def test_10_synthetic_intent_is_not_approval(self):
        x=next(x for x in read()["fields"] if x["field"]=="human_intent_sha256")
        self.assertIn("SYNTHETIC",x["stage"])
        self.assertIn("not S1 distinct-manager",x["required_verification"])

    def test_11_audit_map_is_only_a_lab_artifact(self):
        d=read()
        self.assertIn("NOT_HOMOLOGATED",d["status"])
        self.assertEqual(d["status"],"PRODUCERS_LOCATED_CANONICAL_BINDING_NOT_HOMOLOGATED")

if __name__=="__main__":
    unittest.main()
