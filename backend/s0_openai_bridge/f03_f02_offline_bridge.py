"""F03 -> F02 synthetic S0-mediated bridge, never a planner or send command.

OAI-05/OAI-08/CF-OP-02 candidate [P/R]. All receipts/grants here are made-up
trusted fixture inputs. In production only S0 may establish these facts inside
its own authorization and transaction boundaries, not an LLM or this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .f02_offline_gate import (
    F02Capture, F02Current, F02Proposal, F02Status, review_f02_offline,
)


class F03ReviewState(str, Enum):
    DENIED = "DENIED"
    STALE = "STALE"
    NOT_READY = "NOT_READY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REVIEW_ONLY = "REVIEW_ONLY"


class FollowupNeed(str, Enum):
    YES = "YES"
    NO = "NO"
    UNCERTAIN = "UNCERTAIN"


class BridgeStatus(str, Enum):
    DENIED = "DENIED"
    STALE = "STALE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    REVIEW_ONLY = "REVIEW_ONLY"


@dataclass(frozen=True)
class F03Receipt:
    """Synthetic S0-side summary, NOT directly untrusted OpenAI JSON."""
    store: str
    case: str
    closure_event_id: str
    snapshot_hash: str
    case_version: int
    form_version: int
    message_watermark: str
    review_state: F03ReviewState
    followup_need: FollowupNeed
    followup_evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class S0PlanningAuthorization:
    """Synthetic fresh S0 fact, never inferred from a provider response."""
    store: str
    case: str
    cycle: str
    closure_event_id: str
    snapshot_hash: str
    case_version: int
    form_version: int
    message_watermark: str
    planning_request_id: str
    allowed_evidence_refs: tuple[str, ...]
    valid_human_closure: bool
    explicit_planning_request: bool
    authorized_for_post_human: bool
    unresolved_compliance_hold: bool


@dataclass(frozen=True)
class BridgeReview:
    status: BridgeStatus
    regular_template_refs: tuple[tuple[str, str], ...] = ()
    final_template_ref: tuple[str, str] | None = None
    # No field values, message content, timestamps, send flags or C09 status.


def _id(value: object) -> bool:
    return type(value) is str and 0 < len(value) <= 128 and value.strip() == value


def _refs(value: object, maximum: int) -> bool:
    return (type(value) is tuple and len(value) <= maximum
            and all(_id(ref) for ref in value)
            and len(value) == len(set(value)))


def review_f03_to_f02_offline(
    f03: F03Receipt,
    permission: S0PlanningAuthorization,
    capture: F02Capture,
    current: F02Current,
    candidate_plan: object,
) -> BridgeReview:
    """Only review a proposed F02 chain after explicit S0 planning request.

    The F03 advisory is NEVER itself authorization. A positive result has no
    persistence/publication method and MUST be reevaluated against current S0
    data before any future production effect. This is not the real S0 adapter.
    """
    denied = BridgeReview(BridgeStatus.DENIED)
    if not (type(f03) is F03Receipt and type(permission) is S0PlanningAuthorization
            and type(capture) is F02Capture and type(current) is F02Current):
        return denied
    flags = (permission.valid_human_closure, permission.explicit_planning_request,
             permission.authorized_for_post_human, permission.unresolved_compliance_hold)
    if any(type(flag) is not bool for flag in flags):
        return denied
    if (not permission.valid_human_closure or not permission.explicit_planning_request
            or not permission.authorized_for_post_human
            or permission.unresolved_compliance_hold):
        return denied
    ids = (f03.store, f03.case, f03.closure_event_id, f03.snapshot_hash,
           f03.message_watermark, permission.store, permission.case,
           permission.cycle, permission.closure_event_id, permission.snapshot_hash,
           permission.message_watermark, permission.planning_request_id)
    if not all(_id(item) for item in ids):
        return denied
    if (type(f03.case_version) is not int or f03.case_version < 1
            or type(f03.form_version) is not int or f03.form_version < 1
            or type(permission.case_version) is not int or permission.case_version < 1
            or type(permission.form_version) is not int or permission.form_version < 1):
        return denied
    if (f03.store != permission.store or f03.case != permission.case
            or capture.store != permission.store or current.store != permission.store
            or capture.case != permission.case or current.case != permission.case
            or capture.cycle != permission.cycle or current.cycle != permission.cycle):
        return denied
    if (f03.closure_event_id != permission.closure_event_id
            or f03.snapshot_hash != permission.snapshot_hash
            or f03.case_version != permission.case_version
            or f03.form_version != permission.form_version
            or f03.message_watermark != permission.message_watermark
            or permission.case_version != capture.case_version
            or permission.case_version != current.case_version
            or permission.message_watermark != capture.message_watermark
            or permission.message_watermark != current.message_watermark):
        return BridgeReview(BridgeStatus.STALE)
    # Live S0/S1 flags (still invented in this lab) must outrank model hints;
    # never expose even review metadata on revoked or ineligible cases.
    current_flags = (current.session_authorized, current.store_authorized,
                     current.case_eligible, current.plan_authorized,
                     current.opted_out, current.bank_submitted,
                     current.sold_or_historical_sale, current.post_sale_support,
                     current.has_handoff_history)
    if any(type(flag) is not bool for flag in current_flags):
        return denied
    if (not current.session_authorized or not current.store_authorized
            or not current.case_eligible or not current.plan_authorized
            or current.opted_out or current.bank_submitted
            or current.sold_or_historical_sale or current.post_sale_support):
        return denied
    if capture.template_catalogue_version != current.template_catalogue_version:
        return BridgeReview(BridgeStatus.STALE)
    if (capture.request_id != permission.planning_request_id
            or capture.purpose != "post_human" or current.purpose != "post_human"
            or current.owner_route != "human" or not current.has_handoff_history):
        return denied
    if (not _refs(permission.allowed_evidence_refs, 200)
            or not permission.allowed_evidence_refs
            or capture.allowed_evidence_refs != permission.allowed_evidence_refs
            or not _refs(f03.followup_evidence_refs, 24)
            or type(f03.review_state) is not F03ReviewState
            or type(f03.followup_need) is not FollowupNeed):
        return denied
    # A receipt that S0 considers denied/stale is not a planning basis.
    if f03.review_state is F03ReviewState.DENIED:
        return denied
    if f03.review_state is F03ReviewState.STALE:
        return BridgeReview(BridgeStatus.STALE)
    if f03.review_state in (F03ReviewState.REVIEW_REQUIRED, F03ReviewState.NOT_READY):
        return BridgeReview(BridgeStatus.HUMAN_REVIEW)
    if f03.review_state is not F03ReviewState.REVIEW_ONLY:
        return denied
    if f03.followup_need is FollowupNeed.NO:
        return BridgeReview(BridgeStatus.NOT_ELIGIBLE)
    if f03.followup_need is FollowupNeed.UNCERTAIN:
        return BridgeReview(BridgeStatus.HUMAN_REVIEW)
    if (not f03.followup_evidence_refs or
            not set(f03.followup_evidence_refs).issubset(permission.allowed_evidence_refs)):
        return BridgeReview(BridgeStatus.HUMAN_REVIEW)

    # Critically, F03 only *permits proceeding to the F02 validator* if S0
    # independently requested planning. F02 guards are checked again here.
    plan = review_f02_offline(capture, current, candidate_plan)
    if plan.status is F02Status.DENIED:
        return denied
    if plan.status is F02Status.STALE:
        return BridgeReview(BridgeStatus.STALE)
    if plan.status is F02Status.INVALID_PROPOSAL:
        return BridgeReview(BridgeStatus.INVALID_PROPOSAL)
    if plan.status is not F02Status.REVIEW_ONLY:
        return denied
    return BridgeReview(BridgeStatus.REVIEW_ONLY,
                        plan.regular_template_refs, plan.final_template_ref)
