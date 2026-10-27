"""Guard the owner-approved destination architecture, without deploying it."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs/contracts/OAI_ARQUITETURA_BACKEND_SUPABASE_OPENAI_V1.json"

class BackendArchitectureDecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_01_supabase_is_primary_backend_host(self):
        d=self.data
        self.assertEqual(d["backend"]["primary_host"],"SUPABASE")
        self.assertEqual(d["backend"]["runtime"],"SUPABASE_EDGE_FUNCTIONS_PRIMARY_CANDIDATE")
        self.assertFalse(d["backend"]["external_host_default"])

    def test_02_direct_server_side_openai_api(self):
        d=self.data
        self.assertEqual(d["ai"]["provider"],"OPENAI_API")
        self.assertEqual(d["ai"]["integration"],"SERVER_SIDE_DIRECT_HTTPS_FROM_SUPABASE_BACKEND")
        self.assertFalse(d["ai"]["client_exposes_openai_credentials"])

    def test_03_n8n_is_truly_optional(self):
        d=self.data
        self.assertFalse(d["automation"]["n8n_required"])
        self.assertFalse(d["automation"]["n8n_default_in_realtime_path"])
        self.assertTrue(d["automation"]["n8n_cannot_authorize_commercial_actions"])

    def test_04_product_approved_not_running(self):
        d=self.data
        self.assertEqual(d["status"],"APPROVED_BY_PRODUCT_OWNER_FOR_TARGET_ARCHITECTURE")
        self.assertEqual(d["implementation_status"],"DESIGN_ONLY_NO_PRODUCTION_DEPLOYMENT")
        self.assertTrue(all(value is False for value in d["operational_scope"].values()))

    def test_05_domain_authority_stays_s0_not_model(self):
        d=self.data
        self.assertEqual(d["ownership"]["server_authority"],"S0_WITH_APPROVED_DOMAIN_CONTRACTS")
        self.assertTrue(d["ownership"]["commercial_dispatch_requires_independent_guards"])
        self.assertEqual(d["ownership"]["data_truth"],"SUPABASE_POSTGRESQL")

    def test_06_markdown_and_registry_reference_same_decision(self):
        d=self.data
        src=(ROOT/d["documentation"]).read_text(encoding="utf-8")
        reg=(ROOT/"docs/DECISOES_E_GATES.md").read_text(encoding="utf-8")
        self.assertIn(d["decision_id"],src)
        self.assertIn(d["decision_id"],reg)
        self.assertIn("n8n",src)
        self.assertIn("sem n8n",src.lower())

    def test_07_exception_requires_explicit_decision(self):
        d=self.data
        self.assertIn("explicit architecture amendment",d["exceptions"])
        self.assertFalse(d["operational_scope"]["hosted_supabase_migrations_approved"])

if __name__=="__main__":
    unittest.main()
