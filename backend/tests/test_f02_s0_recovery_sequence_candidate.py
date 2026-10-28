"""A38 untrusted S0 candidate-result recovery — no authenticated session."""
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import unittest

from backend.f02_s0_recovery_sequence_candidate import (
    ClaimedContext, RecoveryGate as Gate, RecoverySequenceResult,
    MAX_SNAPSHOTS, examine_s0_recovery_sequence_candidate as inspect,
)
from backend.tests.test_f02_s0_lookup_alignment_candidate import case


def scenario(*rows, context=ClaimedContext.SAME_CONTEXT_UNVERIFIED,
             obs=None, binding=None, sha=None):
    o,b,original,h=case()
    if not rows:
        rows=(original,)
    return inspect(obs if obs is not None else o,
                   binding if binding is not None else b,
                   sha if sha is not None else h, tuple(rows), context)


def fixtures():
    obs,bind,p,sha=case()
    first=dict(p,state="RECORDED_REVIEW_ONLY")
    later=dict(p,revision="2",
               observed_at=(datetime.fromisoformat(p["observed_at"])
                            +timedelta(minutes=1)).isoformat())
    return obs,bind,first,later,sha


def negative(ref, state):
    return {**ref,"state":state,"review_ref":None,"revision":None,
            "observed_at":None,"request_sha256":None,"expires_at":None}


class S0RecoverySequenceTests(unittest.TestCase):
    def test_01_single_persisted_is_untrusted_baseline_only(self):
        self.assertIs(scenario().status,Gate.BASELINE_SHAPE_RECHECK_ONLY)

    def test_02_exact_snapshot_replay_no_new_action(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(p,p).status,
                      Gate.EXACT_SNAPSHOT_REPLAY_NO_ACTION)

    def test_03_monotonic_revision_is_shape_only(self):
        _,_,p,q,_=fixtures()
        self.assertIs(scenario(p,q).status,
                      Gate.CONTINUITY_SHAPE_RECHECK_ONLY)

    def test_04_two_states_same_revision_no_approval(self):
        _,_,p,q,_=fixtures()
        q=dict(q,revision="1",state="REPLAY_REVIEW_ONLY")
        self.assertIs(scenario(p,q).status,
                      Gate.CONTINUITY_SHAPE_RECHECK_ONLY)

    def test_05_one_unavailable_is_outage_not_rollback(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(negative(p,"UNAVAILABLE")).status,
                      Gate.OUTAGE_RECHECK_REQUIRED)

    def test_06_persisted_then_unavailable_holds_history(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(p,negative(p,"UNAVAILABLE")).status,
                      Gate.OUTAGE_RECHECK_REQUIRED)

    def test_07_same_result_after_outage_requires_S0_lookup(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(p,negative(p,"UNAVAILABLE"),p).status,
                      Gate.REAPPEARED_SHAPE_RECHECK_ONLY)

    def test_08_new_revision_after_outage_is_shape_only(self):
        _,_,p,q,_=fixtures()
        self.assertIs(scenario(p,negative(p,"UNAVAILABLE"),q).status,
                      Gate.REAPPEARED_SHAPE_RECHECK_ONLY)

    def test_09_unavailable_before_first_persisted_is_not_baseline(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(negative(p,"UNAVAILABLE"),p).status,
                      Gate.NO_BASELINE_RECHECK_REQUIRED)

    def test_10_repeated_unavailable_cannot_create_a_review(self):
        _,_,p,_,_=fixtures()
        u=negative(p,"UNAVAILABLE")
        self.assertIs(scenario(u,u).status,Gate.OUTAGE_RECHECK_REQUIRED)

    def test_11_withdrawn_is_terminal(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(dict(p,state="WITHDRAWN_REVIEW_ONLY")).status,
                      Gate.TERMINAL_REVIEW_HOLD)

    def test_12_expired_is_terminal(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(dict(p,state="EXPIRED_REVIEW_ONLY")).status,
                      Gate.TERMINAL_REVIEW_HOLD)

    def test_13_terminal_cannot_be_resurrected(self):
        _,_,p,q,_=fixtures()
        old=dict(p,state="WITHDRAWN_REVIEW_ONLY")
        self.assertIs(scenario(old,q).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_14_terminal_outage_then_resurrection_rejected(self):
        _,_,p,q,_=fixtures()
        old=dict(p,state="EXPIRED_REVIEW_ONLY")
        self.assertIs(scenario(old,negative(p,"UNAVAILABLE"),q).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_15_terminal_followed_by_outage_remains_terminal(self):
        _,_,p,_,_=fixtures()
        old=dict(p,state="EXPIRED_REVIEW_ONLY")
        self.assertIs(scenario(old,negative(p,"UNAVAILABLE")).status,
                      Gate.TERMINAL_REVIEW_HOLD)

    def test_16_all_non_unavailable_negatives_are_holds(self):
        _,_,p,_,_=fixtures()
        for state in ("INPUT_REJECTED","DENIED","STALE",
                      "IDEMPOTENCY_CONFLICT","REQUEST_EXPIRED",
                      "REVIEW_REQUEST_NOT_FOUND","CLOCK_RECHECK_REQUIRED"):
            with self.subTest(state=state):
                self.assertIs(scenario(negative(p,state)).status,
                              Gate.NEGATIVE_REVIEW_HOLD)

    def test_17_negative_after_persisted_does_not_erase_old_record(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(p,negative(p,"DENIED")).status,
                      Gate.NEGATIVE_REVIEW_HOLD)

    def test_18_outage_then_negative_is_not_a_replay(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(p,negative(p,"UNAVAILABLE"),
                               negative(p,"DENIED")).status,
                      Gate.NEGATIVE_REVIEW_HOLD)

    def test_19_invalid_negative_field_shape_rejected(self):
        _,_,p,_,_=fixtures()
        bad=negative(p,"UNAVAILABLE")
        bad["review_ref"]=str(uuid4())
        self.assertIs(scenario(p,bad).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_20_previous_revision_cannot_decrease(self):
        _,_,p,_,_=fixtures()
        older=dict(p,revision="7")
        self.assertIs(scenario(older,p).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_21_previous_observed_at_cannot_move_backward(self):
        _,_,p,_,_=fixtures()
        old=dict(p,observed_at=(
            datetime.fromisoformat(p["observed_at"])
            +timedelta(hours=1)).isoformat())
        self.assertIs(scenario(old,p).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_22_previous_review_ref_cannot_be_swapped(self):
        _,_,p,q,_=fixtures()
        q=dict(q,review_ref=str(uuid4()))
        self.assertIs(scenario(p,q).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_23_original_hash_change_between_snapshots_denied(self):
        _,_,p,q,_=fixtures()
        q=dict(q,request_sha256="b"*64)
        self.assertIs(scenario(p,q).status,
                      Gate.RESULT_BINDING_RECHECK_REQUIRED)

    def test_24_original_expected_S0_hash_is_independent_of_F02(self):
        obs,bind,p,_,_=fixtures()
        self.assertIs(scenario(p,sha=obs.payload_sha256).status,
                      Gate.RESULT_BINDING_RECHECK_REQUIRED)

    def test_25_changed_binding_is_rejected(self):
        obs,bind,p,_,_=fixtures()
        self.assertIs(scenario(p,obs=obs,
                    binding=replace(bind,shop_id=uuid4())).status,
                    Gate.RESULT_BINDING_RECHECK_REQUIRED)

    def test_26_lost_context_always_holds(self):
        self.assertIs(scenario(context=ClaimedContext.LOST_CONTEXT).status,
                      Gate.AUTH_CONTEXT_RECHECK_REQUIRED)

    def test_27_changed_session_always_holds(self):
        self.assertIs(scenario(context=ClaimedContext.CHANGED_SESSION).status,
                      Gate.AUTH_CONTEXT_RECHECK_REQUIRED)

    def test_28_unknown_context_always_holds(self):
        self.assertIs(scenario(context=ClaimedContext.UNKNOWN_CONTEXT).status,
                      Gate.AUTH_CONTEXT_RECHECK_REQUIRED)

    def test_29_malicious_string_context_does_not_pass_enum(self):
        o,b,p,h=case()
        self.assertIs(inspect(o,b,h,(p,),"SAME_CONTEXT_UNVERIFIED").status,
                      Gate.DENIED_MALFORMED)

    def test_30_no_history_does_not_prove_request_was_deleted(self):
        o,b,p,h=case()
        self.assertIs(inspect(o,b,h,(),
                      ClaimedContext.SAME_CONTEXT_UNVERIFIED).status,
                      Gate.NO_BASELINE_RECHECK_REQUIRED)

    def test_31_more_than_32_snapshots_denied(self):
        o,b,p,h=case()
        self.assertIs(inspect(o,b,h,(p,)*(MAX_SNAPSHOTS+1),
                      ClaimedContext.SAME_CONTEXT_UNVERIFIED).status,
                      Gate.DENIED_MALFORMED)

    def test_32_history_list_cannot_be_accepted_as_tuple(self):
        o,b,p,h=case()
        self.assertIs(inspect(o,b,h,[p],
                      ClaimedContext.SAME_CONTEXT_UNVERIFIED).status,
                      Gate.DENIED_MALFORMED)

    def test_33_result_with_fake_send_authority_denied(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(dict(p,send_authorized=True)).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_34_unratified_S0_schema_version_denied(self):
        _,_,p,_,_=fixtures()
        self.assertIs(scenario(dict(p,schema="prumo.s0.f02.review.result/1.0")).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_35_relative_timezone_offsets_for_same_expiry_accepted(self):
        _,_,p,q,_=fixtures()
        q=dict(q,expires_at=(
            datetime.fromisoformat(q["expires_at"])
            .astimezone(timezone(timedelta(hours=-3))).isoformat()))
        self.assertIs(scenario(p,q).status,
                      Gate.CONTINUITY_SHAPE_RECHECK_ONLY)

    def test_36_outage_does_not_relax_identity_checks(self):
        _,_,p,q,_=fixtures()
        q=dict(q,review_ref=str(uuid4()))
        self.assertIs(scenario(p,negative(p,"UNAVAILABLE"),q).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_37_outage_does_not_relax_time_checks(self):
        _,_,p,q,_=fixtures()
        q=dict(q,observed_at=(
            datetime.fromisoformat(p["observed_at"])
            -timedelta(minutes=1)).isoformat())
        self.assertIs(scenario(p,negative(p,"UNAVAILABLE"),q).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_38_outage_does_not_relax_revision_checks(self):
        _,_,p,q,_=fixtures()
        p=dict(p,revision="8")
        self.assertIs(scenario(p,negative(p,"UNAVAILABLE"),q).status,
                      Gate.RESULT_HISTORY_RECHECK_REQUIRED)

    def test_39_no_status_or_result_contains_execution_grants(self):
        self.assertEqual([f.name for f in fields(RecoverySequenceResult)],["status"])
        self.assertTrue(all("AUTHORIZED" not in x.value
            and "APPROVED" not in x.value
            and "SEND" not in x.value for x in Gate))
