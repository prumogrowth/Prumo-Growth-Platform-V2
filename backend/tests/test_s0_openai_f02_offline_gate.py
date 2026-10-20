"""Tests for tentative F02 offline template-only proposals, no Meta/DB/LLM."""
from dataclasses import replace
import unittest

from backend.s0_openai_bridge.f02_offline_gate import (
    F02Attempt, F02Capture, F02Current, F02Proposal, F02Review,
    F02Status, review_f02_offline,
)


def scenario():
    cap = F02Capture('store-A', 'case-1', 'cycle-1', 'plan-1', 9, 'msg-7', 'cat-v1',
                     'post_human',
                     (('t-1', 'v1'), ('t-2', 'v1'), ('t-final', 'v1'), ('t-3', 'v1'),
                      ('t-4', 'v1'), ('t-5', 'v1')),
                     ('msg-1', 'msg-7'), 2, 5,
                     '2026-11-03T08:00:00-03:00', '2026-11-10T18:00:00-03:00')
    current = F02Current('store-A', 'case-1', 'cycle-1', 9, 'msg-7', 'cat-v1',
                         'post_human', True, True, True, True, False, False,
                         False, False, True, 'human')
    proposal = F02Proposal('plan-1', 'recontact_plan', (
        F02Attempt('t-1', 'v1', '2026-11-04T12:00:00-03:00', ('msg-1',), 'interest'),
        F02Attempt('t-2', 'v1', '2026-11-05T12:00:00-03:00', ('msg-7',), 'follow_up'),
    ), F02Attempt('t-final', 'v1', '2026-11-06T12:00:00-03:00', ('msg-7',), 'final'))
    return cap, current, proposal


class F02CandidateReviewTests(unittest.TestCase):
    def check(self, expected, cap=None, current=None, proposal=None):
        a,b,c=scenario()
        v=review_f02_offline(a if cap is None else cap,
                             b if current is None else current,
                             c if proposal is None else proposal)
        self.assertEqual(v.status, expected, repr(v))
        if expected != F02Status.REVIEW_ONLY:
            self.assertEqual(v.regular_template_refs, ())
            self.assertIsNone(v.final_template_ref)
        return v

    def test_01_review_only_never_schedule(self):
        r=self.check(F02Status.REVIEW_ONLY)
        self.assertEqual(r.regular_template_refs, (('t-1', 'v1'), ('t-2', 'v1')))
        self.assertEqual(r.final_template_ref, ('t-final', 'v1'))
        self.assertNotIn('scheduled_at', F02Review.__dataclass_fields__)
        self.assertNotIn('sent', F02Review.__dataclass_fields__)
    def test_02_revoked_session(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,session_authorized=False))
    def test_03_revoked_store(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,store_authorized=False))
    def test_04_optout(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,opted_out=True))
    def test_05_bank_submitted(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,bank_submitted=True))
    def test_06_sold_historical(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,sold_or_historical_sale=True))
    def test_07_support_return(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,post_sale_support=True))
    def test_08_not_eligible(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,case_eligible=False))
    def test_09_no_plan_permission(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,plan_authorized=False))
    def test_10_lost_handoff_for_post_human(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,has_handoff_history=False))
    def test_11_post_human_routes_to_human_only(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,owner_route='seller_ai'))
    def test_12_new_inbound_invalidates_plan(self):
        _,s,_=scenario(); self.check(F02Status.STALE,current=replace(s,message_watermark='msg-8'))
    def test_13_case_edit_invalidates_plan(self):
        _,s,_=scenario(); self.check(F02Status.STALE,current=replace(s,case_version=10))
    def test_14_catalogue_change_invalidates_plan(self):
        _,s,_=scenario(); self.check(F02Status.STALE,current=replace(s,template_catalogue_version='cat-v2'))
    def test_15_cross_store_denied(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,store='store-B'))
    def test_16_cross_case_denied(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,case='case-2'))
    def test_17_cross_cycle_denied(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,cycle='cycle-2'))
    def test_18_revocation_outranks_stale(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,store_authorized=False,case_version=10))
    def test_19_wrong_request_id(self):
        _,_,p=scenario(); self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,request_id='other'))
    def test_20_wrong_operation(self):
        _,_,p=scenario(); self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,operation_kind='sales_reply'))
    def test_21_template_not_approved(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[0],template_id='invented')
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(a,p.proposed_attempts[1])))
    def test_22_template_version_not_approved(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[0],template_version='v2')
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(a,p.proposed_attempts[1])))
    def test_23_final_separate_required(self):
        _,_,p=scenario(); self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,final_template_candidate=p.proposed_attempts[0]))
    def test_24_duplicate_regular_template(self):
        _,_,p=scenario(); self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(p.proposed_attempts[0],p.proposed_attempts[0])))
    def test_25_too_few_regular_attempts(self):
        _,_,p=scenario(); self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=p.proposed_attempts[:1]))
    def test_26_over_limit_regular_attempts(self):
        _,_,p=scenario(); self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=p.proposed_attempts*3))
    def test_27_outside_time_window(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[0],scheduled_at='2026-11-01T12:00:00-03:00')
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(a,p.proposed_attempts[1])))
    def test_28_out_of_order_schedule(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[1],scheduled_at='2026-11-04T11:00:00-03:00')
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(p.proposed_attempts[0],a)))
    def test_29_naive_time_without_zone(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[0],scheduled_at='2026-11-04T12:00:00')
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(a,p.proposed_attempts[1])))
    def test_30_unknown_evidence_ref(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[0],evidence_refs=('msg-other',))
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(a,p.proposed_attempts[1])))
    def test_31_duplicate_evidence_ref(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[0],evidence_refs=('msg-1','msg-1'))
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(a,p.proposed_attempts[1])))
    def test_32_malformed_source_ref_no_exception(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[0],evidence_refs=([1],))
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(a,p.proposed_attempts[1])))
    def test_33_malformed_bool_authority(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,opted_out='false'))
    def test_34_malformed_bool_version(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,case_version=True))
    def test_35_wrong_mode_purpose(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,purpose='unknown'))
    def test_36_wrong_model_type(self):
        self.check(F02Status.INVALID_PROPOSAL,proposal={'text':'send'})
    def test_37_ai_owned_can_review_before_handoff(self):
        c,s,p=scenario(); c=replace(c,purpose='ai_owned',regular_min=1)
        s=replace(s,purpose='ai_owned',has_handoff_history=False,owner_route='seller_ai')
        self.check(F02Status.REVIEW_ONLY,cap=c,current=s,proposal=p)
    def test_38_ai_owned_never_reopens_after_handoff(self):
        c,s,p=scenario(); c=replace(c,purpose='ai_owned',regular_min=1)
        s=replace(s,purpose='ai_owned',has_handoff_history=True,owner_route='seller_ai')
        self.check(F02Status.DENIED,cap=c,current=s,proposal=p)
    def test_39_permission_change_outranks_bad_proposal(self):
        _,s,_=scenario(); self.check(F02Status.DENIED,current=replace(s,plan_authorized=False),proposal={})
    def test_40_time_offset_equivalence_does_not_create_backwards_steps(self):
        _,_,p=scenario(); a=replace(p.proposed_attempts[1],scheduled_at='2026-11-04T15:00:00+00:00')
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,proposed_attempts=(p.proposed_attempts[0],a)))


    def test_41_operator_requested_human_route_can_review(self):
        c,s,p=scenario()
        self.check(F02Status.REVIEW_ONLY, cap=replace(c,purpose='operator_requested'),
                   current=replace(s,purpose='operator_requested'), proposal=p)
    def test_42_operator_requested_cannot_route_to_ai(self):
        c,s,p=scenario()
        self.check(F02Status.DENIED, cap=replace(c,purpose='operator_requested'),
                   current=replace(s,purpose='operator_requested', owner_route='seller_ai'),
                   proposal=p)
    def test_43_malformed_catalogue_is_denied(self):
        c,_,_=scenario()
        self.check(F02Status.DENIED,cap=replace(c,allowed_template_versions=((['t-1'], 'v1'),)))
    def test_44_final_in_past_of_last_attempt_rejected(self):
        _,_,p=scenario()
        fin=replace(p.final_template_candidate,scheduled_at='2026-11-05T11:00:00-03:00')
        self.check(F02Status.INVALID_PROPOSAL,proposal=replace(p,final_template_candidate=fin))


if __name__ == '__main__':
    unittest.main()
