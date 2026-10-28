"""E04 A38: S0 candidate review-result recovery after a lost response.

Pure lab validation. Prior snapshots and claimed binding are supplied by the
caller; neither is an S0 source of truth. UNAVAILABLE never proves rollback.
Session loss/change cannot be repaired by an unsigned F02 projection. This
module NEVER reads DB, calls S0/Meta/OpenAI, sends or schedules messages.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.f02_s0_lookup_alignment_candidate import (
    LookupBindingClaim, LookupGate, inspect_s0_lookup_alignment_candidate,
)
from backend.f02_s0_review_projection_candidate import _PERSISTED, _TERMINAL, _NEGATIVE
from backend.f02_version_chain_replay_candidate import ReplayObservation

MAX_SNAPSHOTS = 32  # Laboratory resource cap; not a business retention rule.


class ClaimedContext(str, Enum):
    SAME_CONTEXT_UNVERIFIED = "SAME_CONTEXT_UNVERIFIED"
    LOST_CONTEXT = "LOST_CONTEXT"
    CHANGED_SESSION = "CHANGED_SESSION"
    UNKNOWN_CONTEXT = "UNKNOWN_CONTEXT"


class RecoveryGate(str, Enum):
    BASELINE_SHAPE_RECHECK_ONLY = "BASELINE_SHAPE_RECHECK_ONLY"
    CONTINUITY_SHAPE_RECHECK_ONLY = "CONTINUITY_SHAPE_RECHECK_ONLY"
    REAPPEARED_SHAPE_RECHECK_ONLY = "REAPPEARED_SHAPE_RECHECK_ONLY"
    EXACT_SNAPSHOT_REPLAY_NO_ACTION = "EXACT_SNAPSHOT_REPLAY_NO_ACTION"
    TERMINAL_REVIEW_HOLD = "TERMINAL_REVIEW_HOLD"
    OUTAGE_RECHECK_REQUIRED = "OUTAGE_RECHECK_REQUIRED"
    NEGATIVE_REVIEW_HOLD = "NEGATIVE_REVIEW_HOLD"
    AUTH_CONTEXT_RECHECK_REQUIRED = "AUTH_CONTEXT_RECHECK_REQUIRED"
    NO_BASELINE_RECHECK_REQUIRED = "NO_BASELINE_RECHECK_REQUIRED"
    RESULT_HISTORY_RECHECK_REQUIRED = "RESULT_HISTORY_RECHECK_REQUIRED"
    RESULT_BINDING_RECHECK_REQUIRED = "RESULT_BINDING_RECHECK_REQUIRED"
    DENIED_MALFORMED = "DENIED_MALFORMED"


@dataclass(frozen=True, slots=True)
class RecoverySequenceResult:
    status: RecoveryGate


def examine_s0_recovery_sequence_candidate(
    observation: ReplayObservation,
    binding: LookupBindingClaim,
    expected_s0_request_sha256: str,
    snapshots: tuple[dict, ...],
    claimed_context: ClaimedContext,
) -> RecoverySequenceResult:
    """Evaluate declared chronology, NEVER authorize recovery or dispatch.

    Snapshot sequence is untrusted/incomplete unless S0 later provides an
    authenticated, complete source. Even a "SHAPE" result needs S0/CFI lookup
    and fresh S1/Meta/policy checks before any real-world operation.
    """
    def out(v: RecoveryGate) -> RecoverySequenceResult:
        return RecoverySequenceResult(v)

    if (type(snapshots) is not tuple
        or len(snapshots) > MAX_SNAPSHOTS
        or type(claimed_context) is not ClaimedContext
        or type(observation) is not ReplayObservation
        or type(binding) is not LookupBindingClaim
        or type(expected_s0_request_sha256) is not str
        or any(type(row) is not dict for row in snapshots)):
        return out(RecoveryGate.DENIED_MALFORMED)

    # A locally asserted same-context flag never authenticates S0. An explicit
    # loss, change or unknown must stop BEFORE any claimed positive result.
    if claimed_context is not ClaimedContext.SAME_CONTEXT_UNVERIFIED:
        return out(RecoveryGate.AUTH_CONTEXT_RECHECK_REQUIRED)
    if not snapshots:
        return out(RecoveryGate.NO_BASELINE_RECHECK_REQUIRED)

    last_persisted: dict | None = None
    seen_negative = False
    outage_after_persisted = False
    seen_outage = False
    last_was_replay = False
    for index, row in enumerate(snapshots):
        # For a transient UNAVAILABLE, validate the exact pinned negative
        # shape without allowing the negative row to erase persisted history.
        # For later persisted rows, bridge only from the last persisted row.
        previous = last_persisted if row.get("state") in _PERSISTED else None
        checked = inspect_s0_lookup_alignment_candidate(
            observation, binding, row,
            expected_s0_request_sha256=expected_s0_request_sha256,
            previous_result=previous,
        )
        if checked.status not in (
            LookupGate.PERSISTED_SHAPE_RECHECK_ONLY,
            LookupGate.TERMINAL_REVIEW_HOLD,
            LookupGate.NEGATIVE_REVIEW_HOLD,
        ):
            if checked.status is LookupGate.DENIED_MALFORMED:
                return out(RecoveryGate.DENIED_MALFORMED)
            if checked.status in (LookupGate.CLAIM_SCOPE_RECHECK_REQUIRED,
                                  LookupGate.S0_REQUEST_DIGEST_RECHECK_REQUIRED):
                return out(RecoveryGate.RESULT_BINDING_RECHECK_REQUIRED)
            return out(RecoveryGate.RESULT_HISTORY_RECHECK_REQUIRED)

        state = row["state"]
        if state in _NEGATIVE:
            if state == "UNAVAILABLE":
                seen_outage = True
                if last_persisted is not None:
                    outage_after_persisted = True
                last_was_replay = False
                continue
            # Any other negative result is a hard block in this candidate
            # sequence, even if later untrusted snapshots appear.
            seen_negative = True
            return out(RecoveryGate.NEGATIVE_REVIEW_HOLD)

        if seen_negative:
            return out(RecoveryGate.NEGATIVE_REVIEW_HOLD)

        # An earlier UNAVAILABLE is NOT a proven lack of a prior record. The
        # next claimed "positive" cannot become a clean baseline.
        if last_persisted is None and seen_outage:
            return out(RecoveryGate.NO_BASELINE_RECHECK_REQUIRED)
        if last_persisted is None and index > 0:
            return out(RecoveryGate.NO_BASELINE_RECHECK_REQUIRED)

        last_was_replay = last_persisted == row if last_persisted else False
        last_persisted = row
        if state in _TERMINAL:
            # Terminal is the only permitted final state, never a resume.
            # Do NOT return early: subsequent forged reactivation must be
            # rejected by the existing A37 continuity gate.
            continue

    if last_persisted is None:
        if seen_outage:
            return out(RecoveryGate.OUTAGE_RECHECK_REQUIRED)
        return out(RecoveryGate.NO_BASELINE_RECHECK_REQUIRED)

    if last_persisted["state"] in _TERMINAL:
        return out(RecoveryGate.TERMINAL_REVIEW_HOLD)

    if snapshots[-1]["state"] == "UNAVAILABLE":
        return out(RecoveryGate.OUTAGE_RECHECK_REQUIRED)
    if outage_after_persisted:
        # Even an identical post-outage projection needs authenticated S0
        # lookup; never mistake a replay for proof the outage was resolved.
        return out(RecoveryGate.REAPPEARED_SHAPE_RECHECK_ONLY)
    if last_was_replay:
        return out(RecoveryGate.EXACT_SNAPSHOT_REPLAY_NO_ACTION)
    if len(snapshots) == 1:
        return out(RecoveryGate.BASELINE_SHAPE_RECHECK_ONLY)
    return out(RecoveryGate.CONTINUITY_SHAPE_RECHECK_ONLY)
