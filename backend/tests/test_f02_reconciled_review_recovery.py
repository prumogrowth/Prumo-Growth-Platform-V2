"""E04 F02 resumed review history: synthetic, pure, no S0 authority."""
import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, LAB_SOURCE, LOCAL_RECONCILED,
    LOCAL_ORIGIN, UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN, REQUEST_ONLY,
    prepare_handoff,
)
from backend.f02_reconciled_review_lifecycle import (
    ReviewWindow, UntrustedRecordedRequest, UntrustedRevocation, UntrustedTimeline,
)
from backend.f02_reconciled_review_recovery import (
    RecoveryResult, RecoveryState, UntrustedRecoverySnapshot,
    evaluate_review_recovery,
)


def scenario():
    shop, lead, case, closure = (uuid4() for _ in range(4))
    evidence = ClaimedS0Evidence(
        shop, lead, case, closure, LOCAL_RECONCILED, LOCAL_ORIGIN,
        LAB_SOURCE, "a" * 64, "b" * 64, "c" * 64, "d" * 64,
        UNVERIFIED_EXTERNAL, UNRATIFIED_HUMAN)
    proposal = ReviewOnlyProposal(
        shop, lead, case, closure, uuid4(), uuid4(), "v1", "policy-001",
        datetime(2026, 11, 10, 18, tzinfo=timezone.utc),
        "review-recovery-0001", REQUEST_ONLY)
    at = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    snap = UntrustedRecoverySnapshot(
        evidence, prepare_handoff(evidence, proposal), proposal,
        ReviewWindow(at, at + timedelta(hours=24)),
        UntrustedTimeline(at + timedelta(minutes=10)))
    later = replace(snap, timeline=replace(
        snap.timeline, observed_at=at + timedelta(hours=1)))
    return snap, later


def prior_row(s):
    p, w, h = s.proposal, s.window, s.handoff
    return UntrustedRecordedRequest(
        p.shop_id, p.lead_id, p.case_id, p.closure_id,
        p.idempotency_key, h.untrusted_request_sha256,
        w.requested_at, w.expires_at)


def foreign_revocation(s):
    return UntrustedRevocation(
        s.proposal.shop_id, s.proposal.closure_id,
        "different-key-0001", s.timeline.observed_at, "f" * 64)


def matching_revocation(s):
    return replace(foreign_revocation(s),
                   idempotency_key=s.proposal.idempotency_key)


def check(a, b):
    return evaluate_review_recovery(a, b).status


class ReviewRecoveryTests(unittest.TestCase):
    def test_01_monotonic_resume_requires_s0_recheck(self):
        self.assertIs(check(*scenario()), RecoveryState.RESUME_FOR_S0_RECHECK_ONLY)

    def test_02_new_matching_claimed_row_is_replay_only(self):
        old, new = scenario()
        new = replace(new, timeline=replace(
            new.timeline, records=(prior_row(old),)))
        self.assertIs(check(old, new),
                      RecoveryState.RESUME_EXACT_REPLAY_S0_RECHECK_ONLY)

    def test_03_prior_claimed_replay_cannot_vanish(self):
        old, new = scenario()
        old = replace(old, timeline=replace(
            old.timeline, records=(prior_row(old),)))
        self.assertIs(check(old, new),
                      RecoveryState.CLAIMED_HISTORY_ERASURE_REVIEW_REQUIRED)

    def test_04_prior_foreign_revocation_cannot_vanish(self):
        old, new = scenario()
        old = replace(old, timeline=replace(
            old.timeline, revocations=(foreign_revocation(old),)))
        self.assertIs(check(old, new),
                      RecoveryState.CLAIMED_HISTORY_ERASURE_REVIEW_REQUIRED)

    def test_05_unchanged_prior_revocation_can_remain(self):
        old, new = scenario()
        rev = foreign_revocation(old)
        old = replace(old, timeline=replace(old.timeline, revocations=(rev,)))
        new = replace(new, timeline=replace(new.timeline, revocations=(rev,)))
        self.assertIs(check(old, new), RecoveryState.RESUME_FOR_S0_RECHECK_ONLY)

    def test_06_valid_but_different_evidence_is_not_continuity(self):
        old, new = scenario()
        e = replace(new.evidence, origin_ledger_sha256="e" * 64)
        new = replace(new, evidence=e, handoff=prepare_handoff(e, new.proposal))
        self.assertIs(check(old, new), RecoveryState.REQUEST_DRIFT_REVIEW_REQUIRED)

    def test_07_valid_but_different_proposal_is_not_continuity(self):
        old, new = scenario()
        p = replace(new.proposal, proposed_at=new.proposal.proposed_at
                    + timedelta(minutes=30))
        new = replace(new, proposal=p, handoff=prepare_handoff(new.evidence, p))
        self.assertIs(check(old, new), RecoveryState.REQUEST_DRIFT_REVIEW_REQUIRED)

    def test_08_new_key_and_digest_cannot_mask_restart(self):
        old, new = scenario()
        p = replace(new.proposal, idempotency_key="review-recovery-0002")
        new = replace(new, proposal=p, handoff=prepare_handoff(new.evidence, p))
        self.assertIs(check(old, new), RecoveryState.REQUEST_DRIFT_REVIEW_REQUIRED)

    def test_09_changed_review_window_is_not_same_request(self):
        old, new = scenario()
        new = replace(new, window=replace(
            new.window, expires_at=new.window.expires_at + timedelta(hours=1)))
        self.assertIs(check(old, new), RecoveryState.REQUEST_DRIFT_REVIEW_REQUIRED)

    def test_10_clock_regression_cannot_reopen_review(self):
        old, new = scenario()
        new = replace(new, timeline=replace(
            new.timeline, observed_at=old.timeline.observed_at - timedelta(minutes=1)))
        self.assertIs(check(old, new), RecoveryState.CLOCK_REGRESSION_REVIEW_REQUIRED)

    def test_11_prior_revoked_claim_cannot_be_resumed(self):
        old, new = scenario()
        old = replace(old, timeline=replace(
            old.timeline, revocations=(matching_revocation(old),)))
        self.assertIs(check(old, new), RecoveryState.PRIOR_RECHECK_REQUIRED)

    def test_12_prior_expired_claim_cannot_be_resumed(self):
        old, new = scenario()
        old = replace(old, timeline=replace(
            old.timeline, observed_at=old.window.expires_at))
        self.assertIs(check(old, new), RecoveryState.PRIOR_RECHECK_REQUIRED)

    def test_13_new_revocation_blocks_even_with_continuity(self):
        old, new = scenario()
        new = replace(new, timeline=replace(
            new.timeline, revocations=(matching_revocation(new),)))
        self.assertIs(check(old, new), RecoveryState.CURRENT_RECHECK_REQUIRED)

    def test_14_new_conflicting_request_blocks(self):
        old, new = scenario()
        conflict = replace(prior_row(old), idempotency_key="other-review-key-0001")
        new = replace(new, timeline=replace(new.timeline, records=(conflict,)))
        self.assertIs(check(old, new), RecoveryState.CURRENT_RECHECK_REQUIRED)

    def test_15_current_expiry_remains_blocking(self):
        old, new = scenario()
        new = replace(new, timeline=replace(
            new.timeline, observed_at=new.window.expires_at))
        self.assertIs(check(old, new), RecoveryState.CURRENT_RECHECK_REQUIRED)

    def test_16_forged_current_digest_is_not_continuity(self):
        old, new = scenario()
        new = replace(new, handoff=replace(
            new.handoff, untrusted_request_sha256="e" * 64))
        self.assertIs(check(old, new), RecoveryState.REQUEST_DRIFT_REVIEW_REQUIRED)

    def test_17_equivalent_timezone_clock_is_monotonic(self):
        old, new = scenario()
        other_zone = timezone(timedelta(hours=-3))
        new = replace(new, timeline=replace(
            new.timeline, observed_at=new.timeline.observed_at.astimezone(other_zone)))
        self.assertIs(check(old, new), RecoveryState.RESUME_FOR_S0_RECHECK_ONLY)

    def test_18_prior_invalid_snapshot_not_resumable(self):
        old, new = scenario()
        old = replace(old, timeline=replace(
            old.timeline, records=({"approved": True},)))
        self.assertIs(check(old, new), RecoveryState.PRIOR_RECHECK_REQUIRED)

    def test_19_invalid_current_snapshot_is_not_resumable(self):
        old, new = scenario()
        new = replace(new, timeline=replace(new.timeline, records=[]))
        self.assertIs(check(old, new), RecoveryState.CURRENT_RECHECK_REQUIRED)

    def test_20_malformed_object_is_denied(self):
        old, new = scenario()
        self.assertIs(check(None, new), RecoveryState.DENIED_MALFORMED)
        self.assertIs(check(old, {}), RecoveryState.DENIED_MALFORMED)

    def test_21_output_is_state_only_without_execution_powers(self):
        old, new = scenario()
        outcome = evaluate_review_recovery(old, new)
        self.assertEqual([field.name for field in fields(RecoveryResult)],
                         ["status"])
        self.assertFalse(any(hasattr(outcome, action) for action in
                             ("approve", "send", "schedule", "persist", "authorize")))


if __name__ == "__main__":
    unittest.main()
