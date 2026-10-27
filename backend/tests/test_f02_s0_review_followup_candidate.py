"""F02 S0 review-only followup classification; synthetic and non-executable."""
import json
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from uuid import uuid4

from backend.f02_reconciled_human_authorization_handoff import (
    HandoffResult, HandoffState,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_s0_review_followup_candidate import (
    FollowupState, FollowupResult, classify_s0_review_followup,
    _STATE_TO_FOLLOWUP,
)
from backend.f02_s0_review_projection_candidate import (
    EVIDENCE_SCOPE, HUMAN_RATIFICATION, SCHEMA,
)

MANIFEST = Path(__file__).resolve().parents[2] / (
    "docs/contracts/OAI_E04_F02_S0_REVIEW_PROJECTION_PIN.json"
)


def fixture():
    now = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    window = ReviewWindow(now, now + timedelta(hours=24))
    handoff = HandoffResult(HandoffState.HANDOFF_REVIEW_ONLY, "a" * 64)
    projection = {
        "schema": SCHEMA, "state": "RECORDED_REVIEW_ONLY",
        "review_ref": str(uuid4()), "revision": "1",
        "observed_at": (now + timedelta(minutes=1)).isoformat(),
        "request_sha256": "a" * 64,
        "expires_at": window.expires_at.isoformat(),
        "evidence_scope": EVIDENCE_SCOPE,
        "human_ratification": HUMAN_RATIFICATION,
        "send_authorized": False, "scheduling_authorized": False,
        "commercial_transition_authorized": False,
    }
    return projection, handoff, window


def outcome(projection, handoff, window, previous=None):
    return classify_s0_review_followup(
        projection, handoff, window, previous=previous
    ).status


def negative(p, state):
    q = dict(p, state=state)
    for k in ("review_ref", "revision", "observed_at",
              "request_sha256", "expires_at"):
        q[k] = None
    return q


class FollowupTests(unittest.TestCase):
    def test_01_recorded_is_pending_evidence_never_approval(self):
        p,h,w=fixture()
        self.assertIs(outcome(p,h,w),FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)

    def test_02_replay_is_not_new_sending_right(self):
        p,h,w=fixture()
        self.assertIs(outcome(dict(p,state="REPLAY_REVIEW_ONLY"),h,w),
                      FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)

    def test_03_current_is_pending_not_ratified(self):
        p,h,w=fixture()
        self.assertIs(outcome(dict(p,state="CURRENT_REVIEW_ONLY"),h,w),
                      FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)

    def test_04_withdrawn_stops_technical_request_only(self):
        p,h,w=fixture()
        self.assertIs(outcome(dict(p,state="WITHDRAWN_REVIEW_ONLY"),h,w),
                      FollowupState.STOP_TECHNICAL_REVIEW_REQUEST_ONLY)

    def test_05_expired_stops_technical_request_only(self):
        p,h,w=fixture()
        self.assertIs(outcome(dict(p,state="EXPIRED_REVIEW_ONLY"),h,w),
                      FollowupState.STOP_TECHNICAL_REVIEW_REQUEST_ONLY)

    def test_06_input_rejected_requires_offline_correction(self):
        p,h,w=fixture()
        self.assertIs(outcome(negative(p,"INPUT_REJECTED"),h,w),
                      FollowupState.OFFLINE_INPUT_CORRECTION_ONLY)

    def test_07_denied_requires_authenticated_s0_context(self):
        p,h,w=fixture()
        self.assertIs(outcome(negative(p,"DENIED"),h,w),
                      FollowupState.REFRESH_AUTHENTICATED_S0_CONTEXT_ONLY)

    def test_08_stale_requires_authenticated_s0_context(self):
        p,h,w=fixture()
        self.assertIs(outcome(negative(p,"STALE"),h,w),
                      FollowupState.REFRESH_AUTHENTICATED_S0_CONTEXT_ONLY)

    def test_09_conflict_cannot_choose_a_new_key(self):
        p,h,w=fixture()
        self.assertIs(outcome(negative(p,"IDEMPOTENCY_CONFLICT"),h,w),
                      FollowupState.MANUAL_S0_IDEMPOTENCY_REVIEW_ONLY)

    def test_10_expired_first_request_cannot_auto_renew(self):
        p,h,w=fixture()
        self.assertIs(outcome(negative(p,"REQUEST_EXPIRED"),h,w),
                      FollowupState.EXPIRED_REQUEST_NO_AUTO_RENEWAL_ONLY)

    def test_11_not_found_requires_original_s0_lookup(self):
        p,h,w=fixture()
        self.assertIs(outcome(negative(p,"REVIEW_REQUEST_NOT_FOUND"),h,w),
                      FollowupState.S0_READ_ORIGINAL_REQUEST_ONLY)

    def test_12_server_clock_requires_s0_recheck(self):
        p,h,w=fixture()
        self.assertIs(outcome(negative(p,"CLOCK_RECHECK_REQUIRED"),h,w),
                      FollowupState.S0_CLOCK_RECHECK_ONLY)

    def test_13_unavailable_requires_original_s0_read_not_resubmit(self):
        p,h,w=fixture()
        self.assertIs(outcome(negative(p,"UNAVAILABLE"),h,w),
                      FollowupState.S0_READ_ORIGINAL_REQUEST_ONLY)

    def test_14_negative_response_does_not_erase_prior_persisted_claim(self):
        p,h,w=fixture()
        new=negative(p,"UNAVAILABLE")
        self.assertIs(outcome(new,h,w,previous=p),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_15_terminal_reopening_is_blocked(self):
        p,h,w=fixture()
        old=dict(p,state="WITHDRAWN_REVIEW_ONLY")
        self.assertIs(outcome(dict(p,revision="2"),h,w,previous=old),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_16_revision_regression_blocked(self):
        p,h,w=fixture()
        prev=dict(p,revision="3")
        self.assertIs(outcome(p,h,w,previous=prev),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_17_changed_reference_blocked(self):
        p,h,w=fixture()
        newer=dict(p,review_ref=str(uuid4()))
        self.assertIs(outcome(newer,h,w,previous=p),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_18_changed_request_hash_is_blocked(self):
        p,h,w=fixture()
        self.assertIs(outcome(dict(p,request_sha256="b"*64),h,w),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_19_false_send_flag_is_blocked(self):
        p,h,w=fixture()
        self.assertIs(outcome(dict(p,send_authorized=True),h,w),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_20_false_ratification_is_blocked(self):
        p,h,w=fixture()
        self.assertIs(outcome(dict(p,human_ratification="APPROVED"),h,w),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_21_wrong_contract_version_fails_closed(self):
        p,h,w=fixture()
        self.assertIs(outcome(dict(p,schema="v1.0"),h,w),
                      FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_22_wrong_window_handoff_type_is_blocked(self):
        p,h,w=fixture()
        for args in ((p,None,w),(p,h,None),({},h,w)):
            self.assertIs(outcome(*args),FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)

    def test_23_followup_never_exposes_payload_or_operations(self):
        p,h,w=fixture()
        obj=classify_s0_review_followup(p,h,w)
        self.assertEqual([f.name for f in fields(FollowupResult)],["status"])
        for method in ("approve","send","schedule","retry","persist",
                       "dispatch","create_key","authorize","review_ref"):
            self.assertFalse(hasattr(obj,method))

    def test_24_pinned_s0_candidate_states_all_classified_exhaustively(self):
        pin=json.loads(MANIFEST.read_text())
        self.assertEqual(set(_STATE_TO_FOLLOWUP),set(pin["persisted_states"])
                         |set(pin["negative_states"]))
        self.assertEqual(len(_STATE_TO_FOLLOWUP),13)
        self.assertFalse(pin["operationally_ratified"])
        self.assertFalse(pin["has_authenticated_transport"])
        self.assertTrue(all(isinstance(v,FollowupState)
                            for v in _STATE_TO_FOLLOWUP.values()))

    def test_25_status_does_not_change_client_inputs(self):
        p,h,w=fixture()
        original=dict(p)
        self.assertIs(outcome(p,h,w),FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY)
        self.assertEqual(p,original)

    def test_26_forged_input_does_not_yield_automatic_permissions(self):
        p,h,w=fixture()
        for injected in (dict(p,approved=True),
                         dict(p,commercial_transition_authorized=True),
                         dict(p,scheduling_authorized=True)):
            self.assertIs(outcome(injected,h,w),
                          FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)


if __name__ == "__main__":
    unittest.main()
