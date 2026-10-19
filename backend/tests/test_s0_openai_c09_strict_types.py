"""New regression cases for malformed C09 synthetic flags (no provider access)."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from backend.s0_openai_bridge.c09_offline_gate import Decision, Observation, evaluate_c09
NOW = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)

def sample(**kwargs):
    o = Observation("LOJA_A", "CASE1", "em atendimento pelo operador", True, True,
                    False, True, "LOJA_A", "CASE1", "sent", True,
                    NOW-timedelta(hours=25), NOW-timedelta(hours=26), NOW)
    return replace(o, **kwargs)

class C09StrictTypeCases(unittest.TestCase):
    def test_28_false_string_provider_authenticated_denied(self):
        self.assertEqual(evaluate_c09(sample(final_event_authenticated="false")), Decision.DENY)
    def test_29_false_string_plan_active_denied(self):
        self.assertEqual(evaluate_c09(sample(plan_active="false")), Decision.DENY)
    def test_30_false_string_opt_out_denied(self):
        self.assertEqual(evaluate_c09(sample(opt_out="false")), Decision.DENY)
    def test_31_non_boolean_handoff_denied(self):
        self.assertEqual(evaluate_c09(sample(human_handoff=1)), Decision.DENY)
    def test_32_wrong_timestamp_string_not_crash(self):
        self.assertEqual(evaluate_c09(sample(final_sent_at="2026-10-18")), Decision.NOT_READY)
    def test_33_unknown_input_shape_denied(self):
        self.assertEqual(evaluate_c09({}), Decision.DENY)
    def test_34_complete_synthetic_evidence_never_allows(self):
        self.assertEqual(evaluate_c09(sample()), Decision.POLICY_PENDING)
    def test_35_accepted_event_never_starts_c09(self):
        self.assertEqual(evaluate_c09(sample(final_event_kind="accepted")), Decision.NOT_READY)
    def test_36_non_boolean_separate_final_denied(self):
        self.assertEqual(evaluate_c09(sample(final_template_is_separate="true")), Decision.DENY)
    def test_37_non_boolean_store_denied(self):
        self.assertEqual(evaluate_c09(sample(case_store=1, final_event_store=1)), Decision.DENY)
