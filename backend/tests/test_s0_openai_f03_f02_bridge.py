"""Synthetic F03->F02 gate regression; no provider, database, Meta, S0 APIs."""
from dataclasses import replace
import unittest

from backend.s0_openai_bridge.f03_f02_offline_bridge import (
    BridgeStatus, F03Receipt, F03ReviewState, FollowupNeed,
    S0PlanningAuthorization, BridgeReview, review_f03_to_f02_offline,
)
from backend.tests.test_s0_openai_f02_offline_gate import scenario


def fixture():
    capture, current, plan = scenario()
    receipt = F03Receipt('store-A', 'case-1', 'close-1', 'hash-1',
                         9, 2, 'msg-7', F03ReviewState.REVIEW_ONLY,
                         FollowupNeed.YES, ('msg-7',))
    grant = S0PlanningAuthorization('store-A', 'case-1', 'cycle-1', 'close-1',
                                    'hash-1', 9, 2, 'msg-7', 'plan-1',
                                    ('msg-1', 'msg-7'), True, True, True, False)
    return receipt, grant, capture, current, plan


class F03F02BridgeTests(unittest.TestCase):
    def check(self, expected, *, receipt=None, grant=None, capture=None,
              current=None, plan=None):
        f, g, c, n, p = fixture()
        value = review_f03_to_f02_offline(f if receipt is None else receipt,
                                           g if grant is None else grant,
                                           c if capture is None else capture,
                                           n if current is None else current,
                                           p if plan is None else plan)
        self.assertEqual(value.status, expected, repr(value))
        if value.status is not BridgeStatus.REVIEW_ONLY:
            self.assertEqual(value.regular_template_refs, ())
            self.assertIsNone(value.final_template_ref)
        return value

    def test_01_s0_explicitly_requested_followup_review_only(self):
        r = self.check(BridgeStatus.REVIEW_ONLY)
        self.assertEqual(r.regular_template_refs, (('t-1', 'v1'), ('t-2', 'v1')))
        self.assertEqual(r.final_template_ref, ('t-final', 'v1'))
        self.assertNotIn('scheduled_at', BridgeReview.__dataclass_fields__)
        self.assertNotIn('send', BridgeReview.__dataclass_fields__)
    def test_02_no_s0_planning_request(self):
        _, g, *_ = fixture(); self.check(BridgeStatus.DENIED, grant=replace(g, explicit_planning_request=False))
    def test_03_no_s0_authorization(self):
        _, g, *_ = fixture(); self.check(BridgeStatus.DENIED, grant=replace(g, authorized_for_post_human=False))
    def test_04_no_proven_human_closure(self):
        _, g, *_ = fixture(); self.check(BridgeStatus.DENIED, grant=replace(g, valid_human_closure=False))
    def test_05_compliance_hold(self):
        _, g, *_ = fixture(); self.check(BridgeStatus.DENIED, grant=replace(g, unresolved_compliance_hold=True))
    def test_06_f03_denied_never_requests_f02(self):
        f, *_ = fixture(); self.check(BridgeStatus.DENIED, receipt=replace(f, review_state=F03ReviewState.DENIED))
    def test_07_f03_stale_never_requests_f02(self):
        f, *_ = fixture(); self.check(BridgeStatus.STALE, receipt=replace(f, review_state=F03ReviewState.STALE))
    def test_08_f03_needs_review_requires_human(self):
        f, *_ = fixture(); self.check(BridgeStatus.HUMAN_REVIEW, receipt=replace(f, review_state=F03ReviewState.REVIEW_REQUIRED))
    def test_09_f03_not_ready_requires_human(self):
        f, *_ = fixture(); self.check(BridgeStatus.HUMAN_REVIEW, receipt=replace(f, review_state=F03ReviewState.NOT_READY))
    def test_10_f03_says_no_followup_even_with_grant(self):
        f, *_ = fixture(); self.check(BridgeStatus.NOT_ELIGIBLE, receipt=replace(f, followup_need=FollowupNeed.NO))
    def test_11_f03_ambiguous_followup_not_auto_proposed(self):
        f, *_ = fixture(); self.check(BridgeStatus.HUMAN_REVIEW, receipt=replace(f, followup_need=FollowupNeed.UNCERTAIN))
    def test_12_f03_yes_requires_cited_evidence(self):
        f, *_ = fixture(); self.check(BridgeStatus.HUMAN_REVIEW, receipt=replace(f, followup_evidence_refs=()))
    def test_13_f03_unknown_source_not_trusted(self):
        f, *_ = fixture(); self.check(BridgeStatus.HUMAN_REVIEW, receipt=replace(f, followup_evidence_refs=('other-msg',)))
    def test_14_duplicate_source_rejected(self):
        f, *_ = fixture(); self.check(BridgeStatus.DENIED, receipt=replace(f, followup_evidence_refs=('msg-7','msg-7')))
    def test_15_no_store_leak(self):
        f, *_ = fixture(); self.check(BridgeStatus.DENIED, receipt=replace(f, store='store-B'))
    def test_16_no_case_leak(self):
        f, *_ = fixture(); self.check(BridgeStatus.DENIED, receipt=replace(f, case='other'))
    def test_17_new_closure_invalidates_advisory(self):
        f, *_ = fixture(); self.check(BridgeStatus.STALE, receipt=replace(f, closure_event_id='close-old'))
    def test_18_changed_snapshot_invalidates_advisory(self):
        f, *_ = fixture(); self.check(BridgeStatus.STALE, receipt=replace(f, snapshot_hash='hash-old'))
    def test_19_form_changed_invalidates_advisory(self):
        f, *_ = fixture(); self.check(BridgeStatus.STALE, receipt=replace(f, form_version=1))
    def test_20_case_changed_invalidates_advisory(self):
        f, *_ = fixture(); self.check(BridgeStatus.STALE, receipt=replace(f, case_version=8))
    def test_21_new_inbound_invalidates_advisory(self):
        f, *_ = fixture(); self.check(BridgeStatus.STALE, receipt=replace(f, message_watermark='msg-6'))
    def test_22_mismatched_planning_request_cannot_replay(self):
        _, g, *_ = fixture(); self.check(BridgeStatus.DENIED, grant=replace(g, planning_request_id='other'))
    def test_23_catalogue_change_invalidates_plan(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.STALE, current=replace(n, template_catalogue_version='catalogue-new'))
    def test_24_revoked_session_wins_over_f03_ambiguity(self):
        f, _, _, n, _ = fixture()
        self.check(BridgeStatus.DENIED, receipt=replace(f, followup_need=FollowupNeed.UNCERTAIN), current=replace(n, session_authorized=False))
    def test_25_revoked_store_wins_over_f03_conflict(self):
        f, _, _, n, _ = fixture()
        self.check(BridgeStatus.DENIED, receipt=replace(f, review_state=F03ReviewState.REVIEW_REQUIRED), current=replace(n, store_authorized=False))
    def test_26_opt_out_wins_over_f03_proposal(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.DENIED, current=replace(n, opted_out=True))
    def test_27_bank_submitted_no_commercial_chain(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.DENIED, current=replace(n, bank_submitted=True))
    def test_28_historical_sold_not_replanned(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.DENIED, current=replace(n, sold_or_historical_sale=True))
    def test_29_post_sale_support_not_commercial_chain(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.DENIED, current=replace(n, post_sale_support=True))
    def test_30_no_seller_ai_route_after_handoff(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.DENIED, current=replace(n, owner_route='seller_ai'))
    def test_31_no_implicit_f03_plan_for_ai_owned(self):
        _, _, c, _, _ = fixture(); self.check(BridgeStatus.DENIED, capture=replace(c, purpose='ai_owned'))
    def test_32_template_not_in_allowlist_rejected(self):
        _, _, _, _, p = fixture(); a=replace(p.proposed_attempts[0], template_id='invented')
        self.check(BridgeStatus.INVALID_PROPOSAL, plan=replace(p,proposed_attempts=(a,p.proposed_attempts[1])))
    def test_33_model_cannot_change_request(self):
        _, _, _, _, p = fixture(); self.check(BridgeStatus.INVALID_PROPOSAL, plan=replace(p,request_id='arbitrary'))
    def test_34_model_cannot_emit_free_text(self):
        self.check(BridgeStatus.INVALID_PROPOSAL, plan={'send_text':'test'})
    def test_35_s0_grant_does_not_override_f02_denial(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.DENIED, current=replace(n,plan_authorized=False))
    def test_36_malformed_grant_flags_fail_closed(self):
        _, g, *_ = fixture(); self.check(BridgeStatus.DENIED, grant=replace(g, authorized_for_post_human='true'))
    def test_37_malformed_f03_verdict_fail_closed(self):
        f, *_ = fixture(); self.check(BridgeStatus.DENIED, receipt=replace(f,review_state='REVIEW_ONLY'))
    def test_38_bad_evidence_allowlist_is_denied(self):
        _, g, *_ = fixture(); self.check(BridgeStatus.DENIED, grant=replace(g, allowed_evidence_refs=('msg-1', ['oops'])))
    def test_39_grant_expanded_sources_cannot_override_f02(self):
        _, g, *_ = fixture(); self.check(BridgeStatus.DENIED, grant=replace(g,allowed_evidence_refs=('msg-1', 'msg-7','msg-8')))
    def test_40_a_second_store_with_own_consistent_grant_isolated(self):
        f,g,c,n,p=fixture()
        self.check(BridgeStatus.REVIEW_ONLY, receipt=replace(f,store='store-B'),
                   grant=replace(g,store='store-B'),capture=replace(c,store='store-B'),current=replace(n,store='store-B'),plan=p)
    def test_41_f03_cannot_invent_authority(self):
        f,g,*_=fixture()
        self.check(BridgeStatus.DENIED, receipt=replace(f, followup_need=FollowupNeed.YES),grant=replace(g, explicit_planning_request=False))
    def test_42_current_case_version_change_is_stale(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.STALE, current=replace(n, case_version=11))
    def test_43_current_inbound_change_is_stale(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.STALE, current=replace(n, message_watermark='msg-8'))
    def test_44_malformed_current_flag_fail_closed(self):
        _, _, _, n, _ = fixture(); self.check(BridgeStatus.DENIED, current=replace(n, has_handoff_history='false'))


if __name__ == '__main__':
    unittest.main()
