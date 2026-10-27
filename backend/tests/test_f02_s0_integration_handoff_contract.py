"""Offline, machine-verifiable contract handoff from F02 to S0; no I/O/S0."""
import hashlib
import json
from pathlib import Path
import unittest

from backend.f02_s0_joint_homologation_candidate import (
    JointGate, ALL_UNRESOLVED, JointStatus,
)
from backend.f02_s0_review_projection_candidate import (
    SCHEMA, EVIDENCE_SCOPE, HUMAN_RATIFICATION, _PERSISTED, _NEGATIVE,
)

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "docs/contracts/OAI_E04_F02_S0_INTEGRATION_HANDOFF_V1.json"
MATRIX = ROOT / "docs/contracts/OAI_E04_F02_ACCEPTANCE_MATRIX_V1.json"


def load():
    return json.loads(PACK.read_text(encoding="utf-8"))


class IntegrationHandoffTests(unittest.TestCase):
    def test_01_exact_s0_git_blob_pinned(self):
        p = load()
        source = ROOT / p["pinned_schema_file"]
        original = source.read_bytes()
        blob = hashlib.sha1(
            b"blob " + str(len(original)).encode() + b"\\0" + original
        ).hexdigest()
        self.assertEqual(blob, p["source_checkpoints"]["s0"]["candidate_schema_blob_sha"])
        self.assertEqual(blob, "61598ba702dc03f9f715673118c88f9359e64113")

    def test_02_schema_keys_exactly_match_runtime_adapter(self):
        p = load()
        schema = json.loads((ROOT / p["pinned_schema_file"]).read_text())
        expected = {
            "schema", "state", "review_ref", "revision", "observed_at",
            "request_sha256", "expires_at", "evidence_scope", "human_ratification",
            "send_authorized", "scheduling_authorized",
            "commercial_transition_authorized",
        }
        self.assertEqual(set(schema["required"]), expected)
        self.assertEqual(set(schema["properties"]), expected)
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["$id"], SCHEMA)

    def test_03_all_s0_candidate_states_match_runtime(self):
        p = load()
        schema = json.loads((ROOT / p["pinned_schema_file"]).read_text())
        self.assertEqual(set(schema["properties"]["state"]["enum"]),
                         set(_PERSISTED) | set(_NEGATIVE))
        self.assertEqual(len(schema["properties"]["state"]["enum"]), 13)

    def test_04_schema_forbids_all_operational_flags(self):
        p = load()
        s = json.loads((ROOT / p["pinned_schema_file"]).read_text())
        for key in ("send_authorized", "scheduling_authorized",
                    "commercial_transition_authorized"):
            self.assertIs(s["properties"][key]["const"], False)
        self.assertEqual(s["properties"]["evidence_scope"]["const"], EVIDENCE_SCOPE)
        self.assertEqual(s["properties"]["human_ratification"]["const"],
                         HUMAN_RATIFICATION)

    def test_05_schema_revision_and_hash_domains_preserved(self):
        p = load()
        s = json.loads((ROOT / p["pinned_schema_file"]).read_text())
        self.assertEqual(s["properties"]["revision"]["anyOf"][1]["pattern"],
                         "^[1-9][0-9]{0,9}$")
        self.assertEqual(s["properties"]["request_sha256"]["anyOf"][1]["pattern"],
                         "^[0-9a-f]{64}$")

    def test_06_all_hard_gates_have_exactly_one_owner_request_and_proof(self):
        p = load()
        h = p["handoff_requests"]
        self.assertEqual([x["gate_id"] for x in h],
                         [x.value for x in ALL_UNRESOLVED])
        self.assertEqual(len(h), 7)
        self.assertEqual(len(set(x["gate_id"] for x in h)), 7)
        for item in h:
            self.assertEqual(item["status"], "INTEGRATION_PENDING")
            for key in ("owner", "source_requirement", "question", "expected_evidence"):
                self.assertGreater(len(item[key]), 25 if key != "owner" else 1)

    def test_07_joint_gates_manifest_agrees_without_hidden_clearance(self):
        p = load()
        gates = json.loads((ROOT / p["joint_gates_manifest"]).read_text())
        self.assertEqual(set(JointGate), set(ALL_UNRESOLVED))
        self.assertEqual([x["gate_id"] for x in p["handoff_requests"]],
                         [x["id"] for x in gates["gates"]])
        self.assertTrue(all(x["owner"] == y["owner"] and
                            x["source_requirement"] == y["needed"]
                            for x,y in zip(p["handoff_requests"],gates["gates"])))
        self.assertFalse(gates["real_s0_e2e_homologated"])

    def test_08_integration_pending_criteria_unchanged(self):
        p = load()
        mat = json.loads((ROOT / p["f02_acceptance_matrix"]).read_text())
        states = {x["id"]:x["status"] for x in mat["requirements"]}
        self.assertEqual(p["integration_pending_criteria"],
                         ["F02-A16","F02-A17","F02-A18"])
        self.assertTrue(all(states[id]=="INTEGRATION_PENDING"
                            for id in p["integration_pending_criteria"]))

    def test_09_lab_verified_does_not_become_approved(self):
        p = load()
        m = json.loads((ROOT / p["f02_acceptance_matrix"]).read_text())
        requirements = {x["id"]: x for x in m["requirements"]}
        for id in p["lab_evidence"]["f02_criteria"]:
            self.assertEqual(requirements[id]["status"],"LAB_VERIFIED")
            self.assertTrue(requirements[id]["tests"])
        self.assertFalse(p["lab_evidence"]["fully_authorized"])
        self.assertFalse(m["approved_operational_authorization"])
        self.assertFalse(m["production_tests_executed"])

    def test_10_source_checkpoints_are_pinned_not_live_authority(self):
        p = load()
        self.assertEqual(p["source_checkpoints"]["f02"]["sha"],
                         "84d76c1340f5ab831e10a6e9c3c76fa1ee01d72e")
        self.assertEqual(p["source_checkpoints"]["s0"]["sha"],
                         "88af4aea3aeb2c403bab4c078fdc04d560f2cba0")
        self.assertEqual(p["source_checkpoints"]["f02"]["ci_run_id"],40475244137)
        self.assertEqual(p["source_checkpoints"]["s0"]["ci_run_id"],40414847271)
        self.assertIs(p["source_checkpoints"]["f02"]["pr_draft"],True)

    def test_11_candidate_contract_never_ratifies_itself(self):
        p = load()
        self.assertEqual(p["mode"],"READ_ONLY_COORDINATION_NOT_AUTHORIZATION")
        for key in ("schema_ratified","s0_transport_authenticated_for_f02",
                    "s1_operational_ratification",
                    "meta_external_disposition_verified","production_homologation"):
            self.assertIs(p[key],False)
        self.assertEqual(p["lab_evidence"]["s0_verified_scope"],
                         "CFI_CONTEXT_ONLY_F02_EVIDENCE_PENDING")

    def test_12_handoff_has_no_actions_or_live_secrets(self):
        p = load()
        self.assertEqual(set(p["forbidden_actions"]),{
            "MERGE","DEPLOY","SEND","SCHEDULE","PRODUCTION_MIGRATION",
            "S0_SOURCE_PATCH_FROM_F02",
        })
        text=json.dumps(p).lower()
        for bad in ("bearer eyj","sk-proj-","service_role_key","access_token"):
            self.assertNotIn(bad,text)

    def test_13_all_joint_assessment_states_remain_non_homologated(self):
        self.assertEqual(len(JointStatus),3)
        self.assertTrue(all(x.value.endswith("_NOT_HOMOLOGATED")
                            for x in JointStatus))

    def test_14_lab_runner_includes_gate_and_handoff_regression(self):
        script=(ROOT/"scripts/run-s0-f03-pg17-local.sh").read_text()
        self.assertIn("backend.tests.test_f02_s0_joint_homologation_candidate",script)
        self.assertIn("backend.tests.test_f02_s0_integration_handoff_contract",script)

    def test_15_packet_requires_exact_s0_context_not_48h_policy(self):
        p=load()
        self.assertEqual(p["source_checkpoints"]["s0"]["branch"],
                         "exp/s0-f02-revisao-autoritativa-20261026")
        self.assertEqual(p["source_checkpoints"]["s0"]["verified_executable_commit"],
                         "4a3d248d46fad5c195398324b3ee98ae6236365f")
        self.assertTrue(any("TTL" in g["source_requirement"]
                            for g in p["handoff_requests"]))


if __name__=="__main__":
    unittest.main()
