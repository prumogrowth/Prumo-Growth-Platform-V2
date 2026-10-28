import unittest
from integration.i86.manual.policy import ACTIONS, policy


class ManualPolicyTests(unittest.TestCase):
    def test_manual_only_does_not_enable_application_or_agents(self):
        for action in ACTIONS | {"SUBSTITUTE"}:
            p = policy(action)
            self.assertEqual(p["state"], "MANUAL_PRIVILEGED_ONLY")
            self.assertFalse(p["ordinary_application_enabled"])
            self.assertFalse(p["mcp_or_agent_enabled"])
            self.assertTrue(p["manual_act_evidence_required"])

    def test_no_invented_quorum_or_numeric_director_limit(self):
        p = policy("APPOINT")
        self.assertIsNone(p["numeric_director_limit"])
        self.assertNotIn("quorum", p)
        self.assertNotIn("approval_expiry", p)

    def test_substitution_is_not_an_automatic_transition(self):
        self.assertTrue(policy("SUBSTITUTE")["continuity_details_pending"])
        self.assertNotIn("SUBSTITUTE", ACTIONS)

    def test_unknown_action_has_no_approval_default(self):
        for action in ("AUTO_APPROVE", "MCP_APPOINT", True, {}, None):
            with self.assertRaises(ValueError):
                policy(action)


if __name__ == "__main__":
    unittest.main(verbosity=2)
