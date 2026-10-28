"""Model/DTO tests only. They cannot certify SQL or human governance."""
import unittest
from integration.i86.authority import VERSION, GOVERNANCE, command, governance_gate


class ContractTests(unittest.TestCase):
    def test_valid_observation_dto(self):
        p = {"version": VERSION, "idempotency_key": "i86-synthetic-01",
             "expected_sha256": None}
        self.assertEqual(command(p), p)

    def test_payload_cannot_select_identity_or_approval(self):
        for field in ("actor_id", "session_id", "role", "approved", "service_role"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                command({"version": VERSION, "idempotency_key": "i86-synthetic-01",
                         "expected_sha256": None, field: True})

    def test_strict_version_key_and_cas(self):
        for field, value in (("version", "future"), ("idempotency_key", "x"),
                             ("idempotency_key", "i86-\u202e-confusable"),
                             ("expected_sha256", True), ("expected_sha256", "A"*64)):
            p = {"version": VERSION, "idempotency_key": "i86-synthetic-01",
                 "expected_sha256": None, field: value}
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                command(p)

    def test_every_governance_transition_remains_pending(self):
        for action in GOVERNANCE:
            gate = governance_gate(action)
            self.assertEqual(gate["state"], "PENDING_DECISION")
            self.assertFalse(gate["operationally_enabled"])
            self.assertTrue(gate["missing_decisions"])

    def test_unknown_governance_action_does_not_default_to_approve(self):
        for action in ("APPROVE", "SEND_META", None, {}):
            with self.assertRaises(ValueError):
                governance_gate(action)


if __name__ == "__main__":
    unittest.main(verbosity=2)
