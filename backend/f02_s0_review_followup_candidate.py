"""F02 read-only S0 review-result FOLLOWUP classification, candidate 0.1.

No I/O, authentication, retry, approval, scheduling or transport. All input
projections are caller-supplied and untrusted; status labels are only
non-executable guidance for a future S0-authenticated workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.f02_reconciled_human_authorization_handoff import HandoffResult
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_s0_review_projection_candidate import (
    ProjectionGate, inspect_s0_review_projection,
)


class FollowupState(str, Enum):
    AWAIT_S0_EVIDENCE_RECHECK_ONLY = "AWAIT_S0_EVIDENCE_RECHECK_ONLY"
    STOP_TECHNICAL_REVIEW_REQUEST_ONLY = "STOP_TECHNICAL_REVIEW_REQUEST_ONLY"
    S0_READ_ORIGINAL_REQUEST_ONLY = "S0_READ_ORIGINAL_REQUEST_ONLY"
    REFRESH_AUTHENTICATED_S0_CONTEXT_ONLY = "REFRESH_AUTHENTICATED_S0_CONTEXT_ONLY"
    OFFLINE_INPUT_CORRECTION_ONLY = "OFFLINE_INPUT_CORRECTION_ONLY"
    MANUAL_S0_IDEMPOTENCY_REVIEW_ONLY = "MANUAL_S0_IDEMPOTENCY_REVIEW_ONLY"
    EXPIRED_REQUEST_NO_AUTO_RENEWAL_ONLY = "EXPIRED_REQUEST_NO_AUTO_RENEWAL_ONLY"
    S0_CLOCK_RECHECK_ONLY = "S0_CLOCK_RECHECK_ONLY"
    BLOCK_AND_RECHECK_CONTRACT_ONLY = "BLOCK_AND_RECHECK_CONTRACT_ONLY"


@dataclass(frozen=True, slots=True)
class FollowupResult:
    status: FollowupState


# Exhaustive, frozen meaning of the pinned S0 0.1-candidate result codes.
# These are descriptions of what to review, NOT operations/callable commands.
_STATE_TO_FOLLOWUP = {
    "RECORDED_REVIEW_ONLY": FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY,
    "REPLAY_REVIEW_ONLY": FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY,
    "CURRENT_REVIEW_ONLY": FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY,
    "WITHDRAWN_REVIEW_ONLY": FollowupState.STOP_TECHNICAL_REVIEW_REQUEST_ONLY,
    "EXPIRED_REVIEW_ONLY": FollowupState.STOP_TECHNICAL_REVIEW_REQUEST_ONLY,
    "INPUT_REJECTED": FollowupState.OFFLINE_INPUT_CORRECTION_ONLY,
    "DENIED": FollowupState.REFRESH_AUTHENTICATED_S0_CONTEXT_ONLY,
    "STALE": FollowupState.REFRESH_AUTHENTICATED_S0_CONTEXT_ONLY,
    "IDEMPOTENCY_CONFLICT": FollowupState.MANUAL_S0_IDEMPOTENCY_REVIEW_ONLY,
    "REQUEST_EXPIRED": FollowupState.EXPIRED_REQUEST_NO_AUTO_RENEWAL_ONLY,
    "REVIEW_REQUEST_NOT_FOUND": FollowupState.S0_READ_ORIGINAL_REQUEST_ONLY,
    "CLOCK_RECHECK_REQUIRED": FollowupState.S0_CLOCK_RECHECK_ONLY,
    "UNAVAILABLE": FollowupState.S0_READ_ORIGINAL_REQUEST_ONLY,
}


def classify_s0_review_followup(
    projection: dict,
    handoff: HandoffResult,
    window: ReviewWindow,
    *,
    previous: dict | None = None,
) -> FollowupResult:
    """Classify a local copy of an S0 candidate result; NEVER perform action.

    In uncertain/failed output, the original key/document is not changed.
    A future S0 owner must independently authenticate, read and decide any
    follow-up; this function cannot do so and returns no bearer/identifier.
    """
    gate = inspect_s0_review_projection(
        projection, handoff, window, previous=previous
    ).status
    if gate not in (
        ProjectionGate.PERSISTED_REVIEW_STATE_ONLY,
        ProjectionGate.TERMINAL_REVIEW_STATE_ONLY,
        ProjectionGate.NEGATIVE_RESULT_RECHECK_ONLY,
    ):
        return FollowupResult(FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY)
    # The projection has already been strictly validated; no fallback
    # or auto-retry path exists for unknown or future states.
    code = _STATE_TO_FOLLOWUP.get(projection["state"])
    return FollowupResult(
        code if code is not None
        else FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY
    )
