"""Pure, fail-closed F02/S0 JOINT acceptance assessment (lab candidate).

A valid unsigned request and well-formed S0 projection only establish local
shape consistency. This assessment always returns hard integration blockers.
No origin authenticity, ratification, privileged lookup, S0 I/O, scheduling,
retry, Meta transport or automatic promotion to production is provided.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, HandoffResult, ReviewOnlyProposal,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_s0_review_followup_candidate import (
    FollowupState, classify_bound_s0_review_followup,
)


class JointGate(str, Enum):
    S0_SCHEMA_RATIFICATION = "G01_S0_SCHEMA_RATIFICATION"
    AUTHENTICATED_TRANSPORT_AND_LOOKUP = "G02_AUTHENTICATED_TRANSPORT_AND_LOOKUP"
    F03_C08_ORIGIN_PROVENANCE = "G03_F03_C08_ORIGIN_PROVENANCE"
    S1_DISTINCT_MANAGER_RATIFICATION = "G04_S1_DISTINCT_MANAGER_RATIFICATION"
    META_OPTOUT_TEMPLATE_DISPOSITION = "G05_META_OPTOUT_TEMPLATE_DISPOSITION"
    APPROVED_TIME_RETENTION_POLICY = "G06_APPROVED_TIME_RETENTION_POLICY"
    F01_F03_F02_INTEGRATED_PATH = "G07_F01_F03_F02_INTEGRATED_PATH"


# No caller-supplied booleans or self-declared evidence may clear these gates.
# S0 and domain owners need independently ratified contracts and real proofs.
ALL_UNRESOLVED = tuple(JointGate)


class JointStatus(str, Enum):
    CANDIDATE_CONSISTENT_NOT_HOMOLOGATED = "CANDIDATE_CONSISTENT_NOT_HOMOLOGATED"
    S0_RECHECK_NOT_HOMOLOGATED = "S0_RECHECK_NOT_HOMOLOGATED"
    CONTRACT_RECHECK_NOT_HOMOLOGATED = "CONTRACT_RECHECK_NOT_HOMOLOGATED"


@dataclass(frozen=True, slots=True)
class JointAssessment:
    status: JointStatus
    followup: FollowupState
    blockers: tuple[JointGate, ...]


_LOCAL_CONSISTENT = frozenset((
    FollowupState.AWAIT_S0_EVIDENCE_RECHECK_ONLY,
    FollowupState.STOP_TECHNICAL_REVIEW_REQUEST_ONLY,
))
_BLOCKED = FollowupState.BLOCK_AND_RECHECK_CONTRACT_ONLY


def assess_joint_review_candidate(
    evidence: ClaimedS0Evidence,
    proposal: ReviewOnlyProposal,
    handoff: HandoffResult,
    window: ReviewWindow,
    projection: dict,
    *,
    previous: dict | None = None,
) -> JointAssessment:
    """Assess only compatibility, never production or operational readiness.

    Each call reiterates every outstanding blocker. Even with all syntactic
    checks passing, the result grants no authority and cannot clear a gate.
    """
    followup = classify_bound_s0_review_followup(
        evidence, proposal, handoff, window, projection, previous=previous,
    ).status
    if followup is _BLOCKED:
        status = JointStatus.CONTRACT_RECHECK_NOT_HOMOLOGATED
    elif followup in _LOCAL_CONSISTENT:
        status = JointStatus.CANDIDATE_CONSISTENT_NOT_HOMOLOGATED
    else:
        status = JointStatus.S0_RECHECK_NOT_HOMOLOGATED
    return JointAssessment(status, followup, ALL_UNRESOLVED)
