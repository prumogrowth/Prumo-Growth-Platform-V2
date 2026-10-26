"""Regression guard for F02 E04 acceptance-contract traceability, not E2E tests.

Checks that the documented proof points to actual test functions, distinguishes
lab evidence from integration gaps and keeps positive contracts review-only.
Never connects to S0/PG17/hosted services and grants no authorization.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/contracts/OAI_E04_F02_ACCEPTANCE_MATRIX_V1.json"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def load_matrix():
    return json.loads(MATRIX.read_text(encoding="utf-8"))


class TestF02AcceptanceContract(unittest.TestCase):
    def test_schema_identity_and_nonproduction_gates(self):
        m = load_matrix()
        self.assertEqual(m["schema"], "prumo.f02.experimental_acceptance_matrix.v1")
        self.assertIs(m["approved_operational_authorization"], False)
        self.assertIs(m["production_tests_executed"], False)
        self.assertIs(m["legacy_e02_oracles_homologated"], False)
        self.assertEqual(m["baseline"]["ci_conclusion"], "success")
        self.assertTrue(SHA40.fullmatch(m["baseline"]["sha"]))
        self.assertEqual(set(m["classification"]),
                         {"LAB_VERIFIED", "LAB_PARTIAL", "INTEGRATION_PENDING"})

    def test_criteria_are_unique_scoped_and_gate_preserving(self):
        m = load_matrix()
        criteria = m["requirements"]
        ids = [x["id"] for x in criteria]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(ids)
        for x in criteria:
            with self.subTest(criterion=x["id"]):
                self.assertRegex(x["id"], r"^F02-A[0-9]{2,3}$")
                self.assertIn(x["status"], m["classification"])
                self.assertTrue(x["area"] and x["behavior"] and x["gate"])
                self.assertIs(type(x["tests"]), list)
                if x["status"] == "INTEGRATION_PENDING":
                    self.assertEqual(x["tests"], [])
                else:
                    self.assertTrue(x["tests"])

    def test_all_declared_lab_proofs_refer_to_existing_test_methods(self):
        seen = {}
        for criterion in load_matrix()["requirements"]:
            for reference in criterion["tests"]:
                with self.subTest(criterion=criterion["id"], proof=reference):
                    self.assertEqual(reference.count("::"), 1)
                    path, method = reference.split("::")
                    self.assertTrue(path.startswith("backend/tests/test_"))
                    self.assertTrue(path.endswith(".py"))
                    self.assertRegex(method, r"^test_[a-zA-Z0-9_]+$")
                    full_path = ROOT / path
                    self.assertTrue(full_path.is_file(), path)
                    if path not in seen:
                        seen[path] = full_path.read_text(encoding="utf-8")
                    self.assertRegex(seen[path], rf"\bdef {re.escape(method)}\s*\(")

    def test_all_positive_codes_exist_in_declared_enums_and_are_review_only(self):
        m = load_matrix()
        for claim in m["non_authorizing_positive_states"]:
            with self.subTest(claim=claim["status"]):
                module_path = ROOT / claim["module"]
                self.assertTrue(module_path.is_file())
                parsed = ast.parse(module_path.read_text(encoding="utf-8"))
                matching = [n for n in parsed.body
                            if isinstance(n, ast.ClassDef)
                            and n.name == claim["enum"]]
                self.assertEqual(len(matching), 1)
                values = {
                    t.id: ast.literal_eval(n.value)
                    for n in matching[0].body if isinstance(n, ast.Assign)
                    for t in n.targets if isinstance(t, ast.Name)
                }
                self.assertEqual(values.get(claim["status"]), claim["status"])
                self.assertTrue(claim["status"].endswith(("_REVIEW_ONLY", "_RECHECK_ONLY")))
                self.assertNotIn("APPROVED", claim["status"])
                self.assertNotIn("SEND", claim["status"])

    def test_codex_coordination_is_explicit_not_automatic_merge(self):
        m = load_matrix()
        self.assertTrue(m["codex_coordination"])
        for dependency in m["codex_coordination"]:
            with self.subTest(area=dependency["area"]):
                self.assertTrue(dependency["observed_branch"])
                self.assertTrue(SHA40.fullmatch(dependency["observed_sha"]))
                self.assertTrue(dependency["affected_interface"])
                self.assertTrue(dependency["action"])
                self.assertIn("Codex", dependency["action"])


if __name__ == "__main__":
    unittest.main()
