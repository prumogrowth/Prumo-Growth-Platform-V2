"""E04/F02 review-only cross-snapshot recovery guard for synthetic claims.

Compares two caller-supplied snapshots to flag *declared* record/revocation
loss, request drift or time regression. Does NOT prove snapshot completeness,
authenticity, real S0 revocation status or operational permission.
No SQL, network, S0 import, persistence, dispatch or scheduler.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, HandoffResult, ReviewOnlyProposal,
)
from backend.f02_reconciled_review_lifecycle import (
    LifecycleState, ReviewWindow, UntrustedTimeline,
    evaluate_bound_review_lifecycle,
)


class RecoveryState(str, Enum):
    RESUME_FOR_S0_RECHECK_ONLY = "RESUME_FOR_S0_RECHECK_ONLY"
    RESUME_EXACT_REPLAY_S0_RECHECK_ONLY = "RESUME_EXACT_REPLAY_S0_RECHECK_ONLY"
    PRIOR_RECHECK_REQUIRED = "PRIOR_RECHECK_REQUIRED"
    REQUEST_DRIFT_REVIEW_REQUIRED = "REQUEST_DRIFT_REVIEW_REQUIRED"
    CLOCK_REGRESSION_REVIEW_REQUIRED = "CLOCK_REGRESSION_REVIEW_REQUIRED"
    CLAIMED_HISTORY_ERASURE_REVIEW_REQUIRED = "CLAIMED_HISTORY_ERASURE_REVIEW_REQUIRED"
    CURRENT_RECHECK_REQUIRED = "CURRENT_RECHECK_REQUIRED"
    DENIED_MALFORMED = "DENIED_MALFORMED"


@dataclass(frozen=True, slots=True)
class UntrustedRecoverySnapshot:
    evidence: ClaimedS0Evidence
    handoff: HandoffResult
    proposal: ReviewOnlyProposal
    window: ReviewWindow
    timeline: UntrustedTimeline


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    status: RecoveryState


_READY = frozenset((
    LifecycleState.READY_FOR_S0_RECHECK_ONLY,
    LifecycleState.UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY,
))


def evaluate_review_recovery(
    previous: UntrustedRecoverySnapshot,
    current: UntrustedRecoverySnapshot,
) -> RecoveryResult:
    """Pure local consistency check for a resumed *review* only.

    Both snapshots, their contents and their clocks are untrusted. Passing
    cannot establish S0 source truth or supply authorization or scheduling.
    An omitted earlier snapshot cannot be detected by this API; callers
    must not mistake it for a durable or authoritative history ledger.
    """
    def result(code: RecoveryState) -> RecoveryResult:
        return RecoveryResult(code)

    if (type(previous) is not UntrustedRecoverySnapshot
        or type(current) is not UntrustedRecoverySnapshot):
        return result(RecoveryState.DENIED_MALFORMED)

    def lifecycle(snapshot: UntrustedRecoverySnapshot) -> LifecycleState:
        return evaluate_bound_review_lifecycle(
            snapshot.evidence, snapshot.handoff, snapshot.proposal,
            snapshot.window, snapshot.timeline,
        ).status

    # A prior negative result cannot become reviewable just by presenting
    # a later contradictory snapshot.
    if lifecycle(previous) not in _READY:
        return result(RecoveryState.PRIOR_RECHECK_REQUIRED)

    # A fresh SHA256 for a changed review request is not continuity.
    if (previous.evidence != current.evidence
        or previous.handoff != current.handoff
        or previous.proposal != current.proposal
        or previous.window != current.window):
        return result(RecoveryState.REQUEST_DRIFT_REVIEW_REQUIRED)

    if lifecycle(current) not in _READY:
        return result(RecoveryState.CURRENT_RECHECK_REQUIRED)

    if current.timeline.observed_at < previous.timeline.observed_at:
        return result(RecoveryState.CLOCK_REGRESSION_REVIEW_REQUIRED)

    # Preserve multiplicity: identical caller-supplied rows/revocations
    # cannot silently disappear during a claimed resume/recheck.
    # With <=32 items each, these are small, typed and hashable dataclasses.
    old_records = Counter(previous.timeline.records)
    new_records = Counter(current.timeline.records)
    old_revocations = Counter(previous.timeline.revocations)
    new_revocations = Counter(current.timeline.revocations)
    if (any(new_records[item] < count for item, count in old_records.items())
        or any(new_revocations[item] < count
               for item, count in old_revocations.items())):
        return result(RecoveryState.CLAIMED_HISTORY_ERASURE_REVIEW_REQUIRED)

    if lifecycle(current) is LifecycleState.UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY:
        return result(RecoveryState.RESUME_EXACT_REPLAY_S0_RECHECK_ONLY)
    return result(RecoveryState.RESUME_FOR_S0_RECHECK_ONLY)
