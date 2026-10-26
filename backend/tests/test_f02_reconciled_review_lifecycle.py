"""Pure F02 review lifecycle tests; no database or S0 ownership changes."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, LAB_SOURCE, LOCAL_RECONCILED,
    LOCAL_ORIGIN, UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN, REQUEST_ONLY,
    prepare_handoff,
)
from backend.f02_reconciled_review_lifecycle import (
    LifecycleState, ReviewWindow, UntrustedRecordedRequest,
    UntrustedRevocation, UntrustedTimeline, evaluate_review_lifecycle,
)


def fixture():
    shop, lead, case, close = (uuid4() for _ in range(4))
    e = ClaimedS0Evidence(
        shop, lead, case, close, LOCAL_RECONCILED, LOCAL_ORIGIN, LAB_SOURCE,
        "a" * 64, "b" * 64, "c" * 64, "d" * 64,
        UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN)
    proposal = ReviewOnlyProposal(
        shop, lead, case, close, uuid4(), uuid4(), "v1", "policy-001",
        datetime(2026, 11, 10, 18, tzinfo=timezone.utc),
        "reconciled-review-0001", REQUEST_ONLY)
    start = datetime(2026, 11, 1, 16, tzinfo=timezone.utc)
    window = ReviewWindow(start, start + timedelta(hours=24))
    timeline = UntrustedTimeline(start + timedelta(hours=1))
    return prepare_handoff(e, proposal), proposal, window, timeline


def prior(handoff, proposal, window):
    return UntrustedRecordedRequest(
        proposal.shop_id, proposal.lead_id, proposal.case_id,
        proposal.closure_id, proposal.idempotency_key,
        handoff.untrusted_request_sha256, window.requested_at,
        window.expires_at)


class Tests(unittest.TestCase):
    def test_01_only_request_review_is_ready(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p, w, t).status,
                      LifecycleState.READY_FOR_S0_RECHECK_ONLY)

    def test_02_no_authority_fields(self):
        from dataclasses import fields
        from backend.f02_reconciled_review_lifecycle import LifecycleResult
        self.assertEqual([f.name for f in fields(LifecycleResult)], ["status"])

    def test_03_expired_at_exact_boundary(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                 replace(t, observed_at=w.expires_at)).status,
                      LifecycleState.EXPIRED_REVIEW_REQUIRED)

    def test_04_unbounded_ttl_rejected(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p,
                    replace(w, expires_at=w.requested_at + timedelta(days=3)), t).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_05_no_negative_window(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p,
                    replace(w, expires_at=w.requested_at), t).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_06_no_naive_times(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p,
                    replace(w, requested_at=w.requested_at.replace(tzinfo=None)), t).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, observed_at=t.observed_at.replace(tzinfo=None))).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_07_future_submitted_time_denied(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, observed_at=w.requested_at - timedelta(seconds=1))).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_08_exact_claimed_replay_only(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=(prior(h, p, w),))).status,
                      LifecycleState.UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY)

    def test_09_same_key_different_digest_conflict(self):
        h, p, w, t = fixture()
        old = replace(prior(h, p, w), request_sha256="e" * 64)
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=(old,))).status,
                      LifecycleState.IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED)

    def test_10_same_closure_different_key_conflict(self):
        h, p, w, t = fixture()
        old = replace(prior(h, p, w), idempotency_key="other-unique-key")
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=(old,))).status,
                      LifecycleState.IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED)

    def test_11_changed_expiry_is_not_exact_replay(self):
        h, p, w, t = fixture()
        old = replace(prior(h, p, w), expires_at=w.expires_at - timedelta(hours=1))
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=(old,))).status,
                      LifecycleState.IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED)

    def test_12_foreign_tenant_history_denied(self):
        h, p, w, t = fixture()
        old = replace(prior(h, p, w), shop_id=uuid4())
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=(old,))).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_13_duplicate_rows_are_not_idempotent_proof(self):
        h, p, w, t = fixture()
        old = prior(h, p, w)
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=(old, old))).status,
                      LifecycleState.IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED)

    def test_14_matching_revocation_claim_denies(self):
        h, p, w, t = fixture()
        rev = UntrustedRevocation(p.shop_id, p.closure_id,
                                  p.idempotency_key, t.observed_at, "f" * 64)
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, revocations=(rev,))).status,
                      LifecycleState.REVOKED_CLAIM_REVIEW_REQUIRED)

    def test_15_revoked_exact_replay_still_denied(self):
        h, p, w, t = fixture()
        rev = UntrustedRevocation(p.shop_id, p.closure_id,
                                  p.idempotency_key, t.observed_at, "f" * 64)
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=(prior(h, p, w),),
                            revocations=(rev,))).status,
                      LifecycleState.REVOKED_CLAIM_REVIEW_REQUIRED)

    def test_16_future_revocation_claim_denied_as_invalid(self):
        h, p, w, t = fixture()
        rev = UntrustedRevocation(p.shop_id, p.closure_id,
                                  p.idempotency_key,
                                  t.observed_at + timedelta(minutes=1), "f" * 64)
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, revocations=(rev,))).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_17_cross_tenant_revocation_denied(self):
        h, p, w, t = fixture()
        rev = UntrustedRevocation(uuid4(), p.closure_id,
                                  p.idempotency_key, t.observed_at, "f" * 64)
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, revocations=(rev,))).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_18_foreign_key_revocation_does_not_grant_approval(self):
        h, p, w, t = fixture()
        rev = UntrustedRevocation(p.shop_id, p.closure_id,
                                  "other-key-1234", t.observed_at, "f" * 64)
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, revocations=(rev,))).status,
                      LifecycleState.READY_FOR_S0_RECHECK_ONLY)

    def test_19_reject_fake_positive_handoff(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(replace(h,
                        untrusted_request_sha256=None), p, w, t).status,
                      LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_20_malformed_snapshot_type_denied(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=[])).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_21_strict_reject_external_forged_records(self):
        h, p, w, t = fixture()
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=({"approved": True},))).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_22_history_row_created_in_future_denied(self):
        h, p, w, t = fixture()
        old = replace(prior(h, p, w),
                      requested_at=t.observed_at + timedelta(minutes=1),
                      expires_at=t.observed_at + timedelta(hours=2))
        self.assertIs(evaluate_review_lifecycle(h, p, w,
                    replace(t, records=(old,))).status,
                      LifecycleState.TIME_OR_HISTORY_INVALID)

    def test_23_null_inputs_denied(self):
        h, p, w, t = fixture()
        for args in ((None, p, w, t), (h, {}, w, t),
                     (h, p, None, t), (h, p, w, None)):
            self.assertIs(evaluate_review_lifecycle(*args).status,
                          LifecycleState.DENIED_MALFORMED)

    def test_24_caller_supplied_clock_is_not_a_real_s0_attestation(self):
        from backend.f02_reconciled_review_lifecycle import LifecycleResult
        self.assertFalse(any(hasattr(LifecycleResult, x) for x in
                             ("approve", "send", "schedule", "persist", "authorize")))


if __name__ == "__main__":
    unittest.main()
