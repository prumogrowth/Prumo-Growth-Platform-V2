"""Focused F02 E04 digest-to-proposal/evidence binding regressions, no S0 IO."""
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
    UntrustedRevocation, UntrustedTimeline,
    evaluate_bound_review_lifecycle, evaluate_review_lifecycle,
)


def fixture():
    shop, lead, case, close = (uuid4() for _ in range(4))
    evidence = ClaimedS0Evidence(
        shop, lead, case, close, LOCAL_RECONCILED, LOCAL_ORIGIN, LAB_SOURCE,
        "a" * 64, "b" * 64, "c" * 64, "d" * 64,
        UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN)
    proposal = ReviewOnlyProposal(
        shop, lead, case, close, uuid4(), uuid4(), "v1", "policy-001",
        datetime(2026, 11, 10, 18, tzinfo=timezone.utc),
        "bound-review-0001", REQUEST_ONLY)
    start = datetime(2026, 11, 1, 16, tzinfo=timezone.utc)
    window = ReviewWindow(start, start + timedelta(hours=24))
    timeline = UntrustedTimeline(start + timedelta(hours=1))
    return evidence, prepare_handoff(evidence, proposal), proposal, window, timeline


def bound(e, h, p, w, t):
    return evaluate_bound_review_lifecycle(e, h, p, w, t).status


class BoundReviewTests(unittest.TestCase):
    def test_01_exact_claim_only_ready_for_s0_recheck(self):
        self.assertIs(bound(*fixture()), LifecycleState.READY_FOR_S0_RECHECK_ONLY)

    def test_02_exact_claimed_replay_remains_non_authorizing(self):
        e, h, p, w, t = fixture()
        row = UntrustedRecordedRequest(p.shop_id, p.lead_id, p.case_id,
            p.closure_id, p.idempotency_key, h.untrusted_request_sha256,
            w.requested_at, w.expires_at)
        self.assertIs(bound(e, h, p, w, replace(t, records=(row,))),
                      LifecycleState.UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY)

    def test_03_changed_proposed_contact_time_rejected(self):
        e, h, p, w, t = fixture()
        self.assertIs(bound(e, h, replace(p, proposed_at=p.proposed_at + timedelta(hours=1)), w, t),
                      LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_04_changed_channel_template_and_policy_rejected(self):
        e, h, p, w, t = fixture()
        for changed in (replace(p, channel_id=uuid4()),
                        replace(p, template_id=uuid4()),
                        replace(p, template_version="v2"),
                        replace(p, policy_version="policy-002")):
            with self.subTest(changed=changed):
                self.assertIs(bound(e, h, changed, w, t),
                              LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_05_changed_evidence_digest_rejected(self):
        e, h, p, w, t = fixture()
        for key in ("f03_receipt_sha256", "c08_local_witness_sha256",
                    "origin_ledger_sha256", "human_intent_sha256"):
            with self.subTest(key=key):
                self.assertIs(bound(replace(e, **{key: "e" * 64}), h, p, w, t),
                              LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_06_changed_scope_rejected_even_if_tenant_valid(self):
        e, h, p, w, t = fixture()
        for key in ("shop_id", "lead_id", "case_id", "closure_id"):
            with self.subTest(key=key):
                new = uuid4()
                self.assertIs(bound(replace(e, **{key: new}), h,
                                    replace(p, **{key: new}), w, t),
                              LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_07_changed_idempotency_key_rejected(self):
        e, h, p, w, t = fixture()
        self.assertIs(bound(e, h, replace(p, idempotency_key="other-bound-0001"), w, t),
                      LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_08_cannot_swap_another_approved_shape_digest(self):
        e, h, p, w, t = fixture()
        other = replace(p, proposed_at=p.proposed_at + timedelta(days=1))
        other_h = prepare_handoff(e, other)
        self.assertIs(bound(e, other_h, p, w, t),
                      LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_09_fake_handoff_contract_version_rejected_on_both_paths(self):
        e, h, p, w, t = fixture()
        forged = replace(h, contract_version="F02_S0_RECONCILED_HUMAN_HANDOFF_V999")
        self.assertIs(bound(e, forged, p, w, t),
                      LifecycleState.RECONCILIATION_RECHECK_REQUIRED)
        self.assertIs(evaluate_review_lifecycle(forged, p, w, t).status,
                      LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_10_send_action_cannot_be_rebound(self):
        e, h, p, w, t = fixture()
        self.assertIs(bound(e, h, replace(p, action="SEND_NOW"), w, t),
                      LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_11_external_cancel_claim_not_authoritative(self):
        e, h, p, w, t = fixture()
        self.assertIs(bound(replace(e, external_disposition="META_CANCELLED"),
                            h, p, w, t), LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_12_human_authorization_claim_not_authoritative(self):
        e, h, p, w, t = fixture()
        self.assertIs(bound(replace(e, human_operational_ratification="APPROVED"),
                            h, p, w, t), LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_13_equal_utc_instant_in_other_offset_is_equivalent(self):
        e, h, p, w, t = fixture()
        brt = timezone(timedelta(hours=-3))
        same_instant = replace(p, proposed_at=p.proposed_at.astimezone(brt))
        self.assertIs(bound(e, h, same_instant, w, t),
                      LifecycleState.READY_FOR_S0_RECHECK_ONLY)

    def test_14_revocation_still_blocks_valid_bound_claim(self):
        e, h, p, w, t = fixture()
        rev = UntrustedRevocation(p.shop_id, p.closure_id, p.idempotency_key,
                                  t.observed_at, "f" * 64)
        self.assertIs(bound(e, h, p, w, replace(t, revocations=(rev,))),
                      LifecycleState.REVOKED_CLAIM_REVIEW_REQUIRED)

    def test_15_expiration_still_blocks_valid_bound_claim(self):
        e, h, p, w, t = fixture()
        self.assertIs(bound(e, h, p, w, replace(t, observed_at=w.expires_at)),
                      LifecycleState.EXPIRED_REVIEW_REQUIRED)

    def test_16_invalid_types_and_digests_fail_closed(self):
        e, h, p, w, t = fixture()
        for parts in ((None, h, p, w, t), (e, {}, p, w, t),
                      (e, h, None, w, t), (e, h, p, {}, t),
                      (e, h, p, w, None)):
            self.assertIs(bound(*parts), LifecycleState.DENIED_MALFORMED)
        for invalid in (None, "0" * 63, "Z" * 64):
            self.assertIs(bound(e, replace(h, untrusted_request_sha256=invalid),
                                p, w, t), LifecycleState.RECONCILIATION_RECHECK_REQUIRED)

    def test_17_output_cannot_execute_or_persist(self):
        from dataclasses import fields
        from backend.f02_reconciled_review_lifecycle import LifecycleResult
        e, h, p, w, t = fixture()
        result = evaluate_bound_review_lifecycle(e, h, p, w, t)
        self.assertEqual([field.name for field in fields(result)], ["status"])
        self.assertFalse(any(hasattr(result, a) for a in
                             ("approve", "send", "schedule", "persist", "authorize")))


if __name__ == "__main__":
    unittest.main()
