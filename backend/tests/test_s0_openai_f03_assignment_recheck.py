"""F03 late-apply synthetic tests, no database or API."""
import unittest
from dataclasses import replace

from backend.s0_openai_bridge.f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority, ReviewDecision, recheck_before_apply,
)


def baseline():
    start = ClosingSnapshot("A", "CASE1", "CLOSE1", "OP1", "ASG1", 4, 5, "M9", "H9", "CAT1")
    now = CurrentAuthority("A", "CASE1", "CLOSE1", "OP1", "ASG1", 4, 5, "M9", "H9", "CAT1",
                           True, True, True, True, "human_bank_collection", False, True)
    return start, now


class LateApplyTests(unittest.TestCase):
    def check(self, expected, **updates):
        initial, current = baseline()
        self.assertEqual(recheck_before_apply(initial, replace(current, **updates)), expected)

    def test_01_no_write_even_in_ideal_fiction(self):
        self.check(ReviewDecision.REVIEW_ONLY)

    def test_02_store_mismatch_denied(self):
        self.check(ReviewDecision.DENY, store="B")

    def test_03_case_mismatch_denied(self):
        self.check(ReviewDecision.DENY, case="CASE2")

    def test_04_closure_event_mismatch_denied(self):
        self.check(ReviewDecision.DENY, closure_event="FORGED")

    def test_05_session_unverified_denied(self):
        self.check(ReviewDecision.DENY, authenticated_session=False)

    def test_06_operator_globally_paused_denied(self):
        self.check(ReviewDecision.DENY, operator_active=False)

    def test_07_store_grant_removed_denied(self):
        self.check(ReviewDecision.DENY, store_grant=False)

    def test_08_manager_team_is_not_customer_authority(self):
        self.check(ReviewDecision.DENY, store_grant=False, operator="MANAGER")

    def test_09_not_human_case_denied(self):
        self.check(ReviewDecision.DENY, case_human=False)

    def test_10_post_sale_support_not_auto_apply(self):
        self.check(ReviewDecision.DENY, purpose="post_sale_support")

    def test_11_optout_denied(self):
        self.check(ReviewDecision.DENY, opted_out=True)

    def test_12_operator_transfer_invalidates_result(self):
        self.check(ReviewDecision.STALE, operator="OP2", assignment="ASG2")

    def test_13_same_operator_reassigned_invalidates_old_assignment(self):
        self.check(ReviewDecision.STALE, assignment="ASG2")

    def test_14_case_version_changed_invalidates_result(self):
        self.check(ReviewDecision.STALE, case_version=5)

    def test_15_form_changed_invalidates_result(self):
        self.check(ReviewDecision.STALE, form_version=6)

    def test_16_customer_inbound_invalidates_result(self):
        self.check(ReviewDecision.STALE, watermark="M10")

    def test_17_snapshot_changed_invalidates_result(self):
        self.check(ReviewDecision.STALE, snapshot_hash="H10")

    def test_18_catalogue_changed_invalidates_result(self):
        self.check(ReviewDecision.STALE, catalogue_version="CAT2")

    def test_19_no_validated_fields_not_ready(self):
        self.check(ReviewDecision.NOT_READY, result_has_validated_fields=False)

    def test_20_invalid_case_version_denied(self):
        self.check(ReviewDecision.DENY, case_version=True)

    def test_21_missing_assignment_denied(self):
        self.check(ReviewDecision.DENY, assignment="")


if __name__ == "__main__":
    unittest.main()
