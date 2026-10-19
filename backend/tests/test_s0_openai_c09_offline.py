"""Offline safety regression: synthetic evidence, no network or database."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from backend.s0_openai_bridge.c09_offline_gate import Decision, Observation, evaluate_c09

NOW = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


def sample(**changes):
    original = Observation(
        case_store="LOJA_A", case_id="CASO_1",
        commercial_status="em atendimento pelo operador", human_handoff=True,
        plan_active=True, opt_out=False, final_template_is_separate=True,
        final_event_store="LOJA_A", final_event_case="CASO_1",
        final_event_kind="sent", final_event_authenticated=True,
        final_sent_at=NOW - timedelta(hours=25),
        latest_customer_inbound_at=NOW - timedelta(hours=50),
        observed_at=NOW,
    )
    return replace(original, **changes)


class ConservativeC09Tests(unittest.TestCase):
    def check(self, expected, **kwargs):
        self.assertEqual(evaluate_c09(sample(**kwargs)), expected)

    def test_01_human_phase_never_approved(self):
        self.check(Decision.POLICY_PENDING)

    def test_02_prebank_operator_submission_pending(self):
        self.check(Decision.POLICY_PENDING, commercial_status="cadastro enviado ao operador")

    def test_03_bank_submitted_deny(self):
        self.check(Decision.DENY, commercial_status="cadastro enviado ao banco")

    def test_04_sold_deny(self):
        self.check(Decision.DENY, commercial_status="vendido")

    def test_05_lost_deny(self):
        self.check(Decision.DENY, commercial_status="perdido")

    def test_06_optout_deny(self):
        self.check(Decision.DENY, opt_out=True)

    def test_07_queued_does_not_start_clock(self):
        self.check(Decision.NOT_READY, final_event_kind="queued")

    def test_08_accepted_does_not_start_clock(self):
        self.check(Decision.NOT_READY, final_event_kind="accepted")

    def test_09_uncertain_does_not_start_clock(self):
        self.check(Decision.NOT_READY, final_event_kind="uncertain")

    def test_10_failed_does_not_start_clock(self):
        self.check(Decision.NOT_READY, final_event_kind="failed")

    def test_11_untrusted_event(self):
        self.check(Decision.NOT_READY, final_event_authenticated=False)

    def test_12_wrong_store(self):
        self.check(Decision.NOT_READY, final_event_store="LOJA_B")

    def test_13_wrong_case(self):
        self.check(Decision.NOT_READY, final_event_case="CASO_2")

    def test_14_inbound_after_final(self):
        self.check(Decision.NOT_READY, latest_customer_inbound_at=NOW - timedelta(hours=4))

    def test_15_inbound_at_sent(self):
        self.check(Decision.NOT_READY, latest_customer_inbound_at=NOW - timedelta(hours=25))

    def test_16_before_full_24h(self):
        self.check(Decision.NOT_READY, final_sent_at=NOW - timedelta(hours=23, minutes=59))

    def test_17_exactly_24h_remains_pending_policy(self):
        self.check(Decision.POLICY_PENDING, final_sent_at=NOW - timedelta(hours=24))

    def test_18_future_sent_event(self):
        self.check(Decision.NOT_READY, final_sent_at=NOW + timedelta(seconds=10))

    def test_19_missing_sent_timestamp(self):
        self.check(Decision.NOT_READY, final_sent_at=None)

    def test_20_missing_timezone(self):
        self.check(Decision.NOT_READY, observed_at=datetime(2026, 10, 19, 12, 0))

    def test_21_expired_plan(self):
        self.check(Decision.NOT_READY, plan_active=False)

    def test_22_missing_separate_final(self):
        self.check(Decision.NOT_READY, final_template_is_separate=False)

    def test_23_ia_without_handoff_not_automatically_approved(self):
        self.check(Decision.POLICY_PENDING, human_handoff=False, commercial_status="em atendimento pela IA")

    def test_24_missing_identifiers(self):
        self.check(Decision.DENY, case_id="")

    def test_25_unknown_status_never_approved(self):
        self.check(Decision.DENY, commercial_status="desconhecido")

    def test_26_inbound_in_future(self):
        self.check(Decision.NOT_READY, latest_customer_inbound_at=NOW + timedelta(minutes=1))

    def test_27_missing_inbound_but_verified_final_no_allow(self):
        self.check(Decision.POLICY_PENDING, latest_customer_inbound_at=None)


if __name__ == "__main__":
    unittest.main()
