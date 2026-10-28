"""E04 cross-check of candidate multi-route and F02 proof descriptions.

Calls BOTH existing pure validators. No S0 authenticating read, no AI model,
no Meta action, no human approval and no server side effects. Caller owns
all data and can forge this entire timeline; success means shape only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from backend.f01_f02_f03_route_ledger_candidate import (
    RouteEvent, RouteKind, RouteScope, RouteStage, RouteStatus,
    classify_route_candidate,
)
from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, HandoffState, prepare_handoff,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_s0_proof_binding_candidate import (
    ProofBindingGate, inspect_claimed_proof_binding,
)


class RoutedProofStatus(str, Enum):
    F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY = "F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY"
    DENIED_MALFORMED = "DENIED_MALFORMED"
    ROUTE_RECHECK_REQUIRED = "ROUTE_RECHECK_REQUIRED"
    WRONG_F02_PHASE_RECHECK_REQUIRED = "WRONG_F02_PHASE_RECHECK_REQUIRED"
    SCOPE_RECHECK_REQUIRED = "SCOPE_RECHECK_REQUIRED"
    CLOSURE_RECHECK_REQUIRED = "CLOSURE_RECHECK_REQUIRED"
    TIMELINE_RECHECK_REQUIRED = "TIMELINE_RECHECK_REQUIRED"
    PROOF_RECHECK_REQUIRED = "PROOF_RECHECK_REQUIRED"


@dataclass(frozen=True, slots=True)
class RoutedProofResult:
    status: RoutedProofStatus


def check_routed_posthuman_proof(
    scope: RouteScope,
    events: tuple[RouteEvent, ...],
    evidence: ClaimedS0Evidence,
    proposal: ReviewOnlyProposal,
    window: ReviewWindow,
    packet: dict,
) -> RoutedProofResult:
    """Only coherent candidate INPUT for independent S0 review.

    A positive status is NOT a signature, durable provenance, human
    ratification, consent or a command to schedule/send anything.
    """
    def out(status: RoutedProofStatus) -> RoutedProofResult:
        return RoutedProofResult(status)

    if (type(scope) is not RouteScope or type(events) is not tuple
        or type(evidence) is not ClaimedS0Evidence
        or type(proposal) is not ReviewOnlyProposal
        or type(window) is not ReviewWindow
        or type(packet) is not dict):
        return out(RoutedProofStatus.DENIED_MALFORMED)

    route = classify_route_candidate(scope, events)
    if route.status is not RouteStatus.ROUTE_SHAPE_RECHECK_ONLY:
        return out(RoutedProofStatus.ROUTE_RECHECK_REQUIRED)
    if route.current_stage is not RouteStage.F02_POSTHUMAN:
        return out(RoutedProofStatus.WRONG_F02_PHASE_RECHECK_REQUIRED)

    # The candidate route MUST end in a post-human F02 S0 request and
    # contain a preceding F03 proposal for the same human closure.
    if not events or events[-1].kind is not RouteKind.S0_F02_POSTHUMAN_REQUEST:
        return out(RoutedProofStatus.WRONG_F02_PHASE_RECHECK_REQUIRED)
    closes = [(i,e) for i,e in enumerate(events)
              if e.kind is RouteKind.S0_HUMAN_CLOSURE]
    if not closes:
        return out(RoutedProofStatus.CLOSURE_RECHECK_REQUIRED)
    last_i, last_closure = closes[-1]
    closure_id = last_closure.closure_id

    if ((evidence.shop_id,evidence.lead_id,evidence.case_id) !=
            (scope.shop_id,scope.lead_id,scope.case_id)
        or (proposal.shop_id,proposal.lead_id,proposal.case_id) !=
            (scope.shop_id,scope.lead_id,scope.case_id)):
        return out(RoutedProofStatus.SCOPE_RECHECK_REQUIRED)
    if (closure_id is None
        or evidence.closure_id != closure_id
        or proposal.closure_id != closure_id
        or events[-1].closure_id != closure_id):
        return out(RoutedProofStatus.CLOSURE_RECHECK_REQUIRED)

    candidates = [(i,e) for i,e in enumerate(events[last_i+1:],last_i+1)
                  if e.kind is RouteKind.F03_PROPOSAL
                  and e.closure_id == closure_id]
    if not candidates or candidates[-1][0] >= len(events)-1:
        return out(RoutedProofStatus.CLOSURE_RECHECK_REQUIRED)

    def as_utc(dt: object) -> datetime | None:
        if type(dt) is not datetime or dt.tzinfo is None or dt.utcoffset() is None:
            return None
        return dt.astimezone(timezone.utc)

    closure_at = as_utc(last_closure.occurred_at)
    f03_at = as_utc(candidates[-1][1].occurred_at)
    requested_at = as_utc(events[-1].occurred_at)
    proposed_at = as_utc(proposal.proposed_at)
    window_at = as_utc(window.requested_at)
    if (None in (closure_at, f03_at, requested_at, proposed_at, window_at)
        or not (closure_at <= f03_at <= requested_at <= proposed_at <= window_at)):
        return out(RoutedProofStatus.TIMELINE_RECHECK_REQUIRED)
    try:
        stated_close = datetime.fromisoformat(packet["closure_at"])
        stated_close = as_utc(stated_close)
    except (KeyError, TypeError, ValueError, OverflowError):
        stated_close = None
    if stated_close != closure_at:
        return out(RoutedProofStatus.CLOSURE_RECHECK_REQUIRED)

    # Reuse, not duplicate, F02's existing handoff and four-proof gates.
    # All documents still come from the caller and remain unauthenticated.
    handoff = prepare_handoff(evidence, proposal)
    if handoff.status is not HandoffState.HANDOFF_REVIEW_ONLY:
        return out(RoutedProofStatus.PROOF_RECHECK_REQUIRED)
    checked = inspect_claimed_proof_binding(evidence, proposal, window, packet)
    if checked.status is not ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED:
        return out(RoutedProofStatus.PROOF_RECHECK_REQUIRED)
    return out(RoutedProofStatus.F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY)
