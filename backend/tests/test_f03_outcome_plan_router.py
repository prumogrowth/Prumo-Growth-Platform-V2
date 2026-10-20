"""OAI-07 -> F02 stage router: synthetic fixtures only, no commercial effect."""
from dataclasses import replace
import unittest

from backend.s0_openai_bridge.f03_outcome_offline_gate import (
    ConversationOutcome as O, EvidenceTopic as T, OutcomeStatus, OutcomeEvidence,
)
from backend.s0_openai_bridge.f03_f02_offline_bridge import FollowupNeed, F03ReviewState
from backend.s0_openai_bridge.f03_outcome_plan_router import (
    RouterStatus as S, S0StageDecision, RouterReview, route_f03_outcome_to_f02_offline,
)
from backend.tests.test_f03_outcome_offline_gate import fixture as outcome_fixture
from backend.tests.test_s0_openai_f03_f02_bridge import fixture as bridge_fixture


def setup(outcome=O.NEEDS_CLARIFICATION):
    snap, auth, suggested = outcome_fixture(outcome)
    receipt, grant, capture, current, plan = bridge_fixture()
    # Match both synthetic snapshots: outcome_fixture is intentionally distinct.
    snap = replace(snap, closure_event_id=receipt.closure_event_id,
                   snapshot_hash=receipt.snapshot_hash,
                   message_watermark=receipt.message_watermark,
                   case_version=receipt.case_version,
                   form_version=receipt.form_version)
    auth = replace(auth, closure_event_id=receipt.closure_event_id,
                   snapshot_hash=receipt.snapshot_hash,
                   message_watermark=receipt.message_watermark,
                   case_version=receipt.case_version,
                   form_version=receipt.form_version)
    stage = S0StageDecision('store-A', 'case-1', receipt.closure_event_id,
                            receipt.case_version, receipt.form_version,
                            receipt.snapshot_hash, receipt.message_watermark, True)
    return snap, auth, suggested, receipt, grant, stage, capture, current, plan


def dispatch(values):
    return route_f03_outcome_to_f02_offline(*values)


class OutcomePlanRoutingTests(unittest.TestCase):
    def verify(self, expected, values):
        result = dispatch(values)
        self.assertIs(result.status, expected, repr(result))
        if expected is not S.REVIEW_ONLY:
            self.assertEqual(result.regular_template_refs, ())
            self.assertIsNone(result.final_template_ref)
        self.assertNotIn('sent', RouterReview.__dataclass_fields__)
        self.assertNotIn('scheduled_at', RouterReview.__dataclass_fields__)
        self.assertNotIn('bank_status', RouterReview.__dataclass_fields__)
        return result

    def test_01_explicit_s0_clarification_eligible_review_only(self):
        r = self.verify(S.REVIEW_ONLY, setup())
        self.assertEqual(r.regular_template_refs, (('t-1', 'v1'), ('t-2', 'v1')))
        self.assertEqual(r.final_template_ref, ('t-final', 'v1'))

    def test_02_bank_return_mentioned_without_proof_never_recontacts(self):
        self.verify(S.COMMERCIAL_RECONTACT_BLOCKED, setup(O.CONTINUE_TO_BANK_REVIEW))

    def test_03_bank_return_with_proof_never_recontacts(self):
        x = list(setup(O.CONTINUE_TO_BANK_REVIEW))
        x[1] = replace(x[1], bank_submission_proved=True)
        self.verify(S.COMMERCIAL_RECONTACT_BLOCKED, x)

    def test_04_ready_for_bank_handoff_not_a_recontact(self):
        self.verify(S.COMMERCIAL_RECONTACT_BLOCKED,
                    setup(O.NEGOTIATION_READY_FOR_BANK_HANDOFF))

    def test_05_ready_for_bank_already_proved_not_a_recontact(self):
        x = list(setup(O.NEGOTIATION_READY_FOR_BANK_HANDOFF))
        x[1] = replace(x[1], bank_submission_proved=True)
        self.verify(S.COMMERCIAL_RECONTACT_BLOCKED, x)

    def test_06_withdrawal_not_recontact(self):
        self.verify(S.COMMERCIAL_RECONTACT_BLOCKED, setup(O.CUSTOMER_WITHDREW))

    def test_07_no_interest_not_recontact(self):
        self.verify(S.COMMERCIAL_RECONTACT_BLOCKED,
                    setup(O.NO_FURTHER_COMMERCIAL_INTEREST))

    def test_08_ambiguous_outcome_goes_to_human(self):
        self.verify(S.HUMAN_REVIEW, setup(O.INCONCLUSIVE))

    def test_09_clarification_without_independent_s0_stage_approval(self):
        x = list(setup()); x[5] = replace(x[5], clarification_recontact_approved=False)
        self.verify(S.HUMAN_REVIEW, x)

    def test_10_clarification_but_bank_already_proved(self):
        x = list(setup()); x[1] = replace(x[1], bank_submission_proved=True)
        self.verify(S.COMMERCIAL_RECONTACT_BLOCKED, x)

    def test_11_essential_gap_returns_to_human(self):
        x = list(setup()); x[1] = replace(x[1], missing_required_field_codes=('ESSENTIAL',))
        self.verify(S.HUMAN_REVIEW, x)

    def test_12_no_s0_separate_planning_request_denied(self):
        x = list(setup()); x[4] = replace(x[4], explicit_planning_request=False)
        self.verify(S.DENIED, x)

    def test_13_no_valid_human_closure_denied(self):
        x = list(setup()); x[1] = replace(x[1], human_closure_verified=False)
        self.verify(S.DENIED, x)

    def test_14_revoked_store_over_bank_outcome(self):
        x = list(setup(O.CONTINUE_TO_BANK_REVIEW))
        x[1] = replace(x[1], store_grant=False)
        self.verify(S.DENIED, x)

    def test_15_revoked_session_over_stale_inbound(self):
        x = list(setup()); x[1] = replace(x[1], authenticated_session=False)
        x[7] = replace(x[7], message_watermark='new-msg')
        self.verify(S.DENIED, x)

    def test_16_opt_out_over_stale_inbound(self):
        x = list(setup()); x[7] = replace(x[7], opted_out=True, message_watermark='new-msg')
        self.verify(S.DENIED, x)

    def test_17_current_bank_submitted_denied(self):
        x = list(setup()); x[7] = replace(x[7], bank_submitted=True)
        self.verify(S.DENIED, x)

    def test_18_sold_historical_denied(self):
        x = list(setup()); x[7] = replace(x[7], sold_or_historical_sale=True)
        self.verify(S.DENIED, x)

    def test_19_post_sale_support_denied(self):
        x = list(setup()); x[7] = replace(x[7], post_sale_support=True)
        self.verify(S.DENIED, x)

    def test_20_wrong_store_in_outcome_snapshot(self):
        x = list(setup()); x[0] = replace(x[0], store='store-B')
        self.verify(S.DENIED, x)

    def test_21_wrong_store_current(self):
        x = list(setup()); x[7] = replace(x[7], store='store-B')
        self.verify(S.DENIED, x)

    def test_22_closure_event_changed_without_regrant(self):
        x = list(setup()); x[0] = replace(x[0], closure_event_id='new-close')
        self.verify(S.STALE, x)

    def test_23_form_version_edited_after_closure(self):
        x = list(setup()); x[5] = replace(x[5], form_version=10)
        self.verify(S.STALE, x)

    def test_24_new_inbound_during_planning(self):
        x = list(setup()); x[7] = replace(x[7], message_watermark='new-msg')
        self.verify(S.STALE, x)

    def test_25_wrong_model_reason(self):
        x = list(setup()); x[2] = replace(x[2], reason_code='SOLD')
        self.verify(S.INVALID_OUTCOME, x)

    def test_26_model_forged_bank_sale(self):
        x = list(setup()); x[2] = replace(x[2], outcome='SOLD')
        self.verify(S.INVALID_OUTCOME, x)

    def test_27_model_missing_source(self):
        x = list(setup()); x[2] = replace(x[2], evidence_refs=('missing',))
        self.verify(S.HUMAN_REVIEW, x)

    def test_28_operator_claim_not_customer_source(self):
        x = list(setup()); evidence = replace(x[0].evidence[0], speaker='operator')
        x[0] = replace(x[0], evidence=(evidence,))
        self.verify(S.HUMAN_REVIEW, x)

    def test_29_model_outcome_invalid_type(self):
        x = list(setup()); x[2] = {'outcome':'NEEDS_CLARIFICATION'}
        self.verify(S.INVALID_OUTCOME, x)

    def test_30_f03_receipt_says_no_plan(self):
        x = list(setup()); x[3] = replace(x[3], followup_need=FollowupNeed.NO)
        self.verify(S.HUMAN_REVIEW, x)

    def test_31_f03_receipt_uncertain(self):
        x = list(setup()); x[3] = replace(x[3], followup_need=FollowupNeed.UNCERTAIN)
        self.verify(S.HUMAN_REVIEW, x)

    def test_32_f03_receipt_stale(self):
        x = list(setup()); x[3] = replace(x[3], review_state=F03ReviewState.STALE)
        self.verify(S.STALE, x)

    def test_33_f03_receipt_denied(self):
        x = list(setup()); x[3] = replace(x[3], review_state=F03ReviewState.DENIED)
        self.verify(S.DENIED, x)

    def test_34_unapproved_template_cannot_be_forwarded(self):
        x = list(setup()); a = replace(x[8].proposed_attempts[0], template_id='unknown')
        x[8] = replace(x[8], proposed_attempts=(a, x[8].proposed_attempts[1]))
        self.verify(S.INVALID_PLAN, x)

    def test_35_missing_plan_request_cannot_be_overridden_by_model(self):
        x = list(setup()); x[4] = replace(x[4], authorized_for_post_human=False)
        self.verify(S.DENIED, x)

    def test_36_invalid_stage_flag_fail_closed(self):
        x = list(setup()); x[5] = replace(x[5], clarification_recontact_approved='true')
        self.verify(S.DENIED, x)

    def test_37_conversation_and_receipt_different_cases_denied(self):
        x = list(setup()); x[3] = replace(x[3], case='other')
        self.verify(S.DENIED, x)

    def test_38_different_snapshot_hash_stale(self):
        x = list(setup()); x[5] = replace(x[5], snapshot_hash='old')
        self.verify(S.STALE, x)

    def test_39_new_f02_catalogue_stale(self):
        x = list(setup()); x[7] = replace(x[7], template_catalogue_version='other')
        self.verify(S.STALE, x)

    def test_40_current_ai_route_after_handoff_denied(self):
        x = list(setup()); x[7] = replace(x[7], owner_route='seller_ai')
        self.verify(S.DENIED, x)


    def test_41_bank_stage_wrong_owner_denied_before_disclosure(self):
        x = list(setup(O.CONTINUE_TO_BANK_REVIEW))
        x[7] = replace(x[7], owner_route='seller_ai')
        self.verify(S.DENIED, x)

    def test_42_bank_stage_without_handoff_denied_before_disclosure(self):
        x = list(setup(O.CONTINUE_TO_BANK_REVIEW))
        x[7] = replace(x[7], has_handoff_history=False)
        self.verify(S.DENIED, x)

    def test_43_bank_stage_wrong_planning_purpose_denied(self):
        x = list(setup(O.CONTINUE_TO_BANK_REVIEW))
        x[6] = replace(x[6], purpose='ai_owned')
        self.verify(S.DENIED, x)


if __name__ == '__main__':
    unittest.main()
