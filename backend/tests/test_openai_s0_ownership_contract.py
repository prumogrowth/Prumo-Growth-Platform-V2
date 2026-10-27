"""Project owner F01/F02/F03 versus S0 scope and audit contract guards."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[2]
GOV=ROOT/"docs/decisoes/ADR_20261027_GOVERNANCA_FRENTES_OPENAI_S0.md"
AUD=ROOT/"docs/OAI_E04_F01_F02_F03_S0_AUDITORIA_CONTRATOS_20261027.md"
M=ROOT/"docs/contracts/OAI_E04_F02_ACCEPTANCE_MATRIX_V1.json"

class OwnershipScopeTests(unittest.TestCase):
    def test_01_owned_fronts_named(self):
        s=GOV.read_text(encoding="utf-8")
        for name in ("F01","F02","F03","S2","OpenAI"):self.assertIn(name,s)
    def test_02_S0_remains_read_only(self):
        s=GOV.read_text(encoding="utf-8")
        self.assertIn("somente leitura",s) if "somente leitura" in s else self.assertIn("ler, investigar, comparar e auditar",s)
        self.assertIn("não podem ser alterados",s)
    def test_03_audited_pinned_sources_and_gap(self):
        s=AUD.read_text(encoding="utf-8")
        for word in ("88af4aea3aeb2c403bab4c078fdc04d560f2cba0",
                     "ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c",
                     "ReviewWindow","prepare_document","G02/G03/G04/G07"):
            self.assertIn(word,s)
    def test_04_operational_blocks_still_present(self):
        d=json.loads(M.read_text(encoding="utf-8"))
        # Ownership A28 must remain, without freezing future F02 additions.
        ids = {entry["id"] for entry in d["requirements"]}
        self.assertIn("F02-A28", ids)
        self.assertGreaterEqual(len(ids), 28)
        self.assertEqual(len(ids), len(d["requirements"]))
        self.assertFalse(d["approved_operational_authorization"])
        self.assertFalse(d["production_tests_executed"])
        self.assertFalse(d["ownership_audit_f01_f02_f03_s0"]["s0_changes_made"])
    def test_05_central_index_links_ADR(self):
        self.assertIn(GOV.name,(ROOT/"docs/DECISOES_E_GATES.md").read_text(encoding="utf-8"))
    def test_06_candidate_window_has_no_authority(self):
        from backend.f02_s0_proof_binding_candidate import (
            SCHEMA, AUTHORITY_STATE, ProofBindingGate)
        self.assertIn("0.1-lab",SCHEMA)
        self.assertEqual(AUTHORITY_STATE,"NO_S0_SOURCE_ATTESTATION")
        self.assertTrue(all("APPROVED" not in x.value and "SEND" not in x.value
                            for x in ProofBindingGate))
