"""Synthetic OAI-07 F03 outcome -> CF-OP-02 F02 proposal routing.

A closed human conversation is not a closed commercial/banking cycle. Never
schedule a commercial recontact when the conversational assessment suggests
bank remittance/review or withdrawal. A clarification plan is evaluated only
when a separate fictional S0 decision authorizes this *specific* stage.

All S0 authorities, source-topic annotations and bank flags are fabricated
laboratory values; this is a candidate design [P/R], NOT a physical endpoint,
AI quality evaluation, bank verification or permission to write/send anything.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .f02_offline_gate import F02Capture, F02Current
from .f03_outcome_offline_gate import (
    ConversationOutcome, ModelOutcomeCandidate, OutcomeSnapshot, OutcomeStatus,
    S0OutcomeAuthority, review_f03_outcome_offline,
)
from .f03_f02_offline_bridge import (
    BridgeStatus, F03Receipt, S0PlanningAuthorization,
    review_f03_to_f02_offline,
)


class RouterStatus(str, Enum):
    DENIED = 'DENIED'
    STALE = 'STALE'
    INVALID_OUTCOME = 'INVALID_OUTCOME'
    HUMAN_REVIEW = 'HUMAN_REVIEW'
    COMMERCIAL_RECONTACT_BLOCKED = 'COMMERCIAL_RECONTACT_BLOCKED'
    INVALID_PLAN = 'INVALID_PLAN'
    REVIEW_ONLY = 'REVIEW_ONLY'


@dataclass(frozen=True)
class S0StageDecision:
    """Illustrative S0-owned, stage-specific planning authorization, NOT a token."""
    store: str
    case: str
    closure_event_id: str
    case_version: int
    form_version: int
    snapshot_hash: str
    message_watermark: str
    clarification_recontact_approved: bool


@dataclass(frozen=True)
class RouterReview:
    status: RouterStatus
    regular_template_refs: tuple[tuple[str, str], ...] = ()
    final_template_ref: tuple[str, str] | None = None
    # Never exposes suggested text, source messages, bank status or send time.


def route_f03_outcome_to_f02_offline(
    outcome_snapshot: OutcomeSnapshot,
    outcome_current: S0OutcomeAuthority,
    model_outcome: object,
    receipt: F03Receipt,
    s0_grant: S0PlanningAuthorization,
    stage: S0StageDecision,
    capture: F02Capture,
    current: F02Current,
    candidate_plan: object,
) -> RouterReview:
    """Conservative offline review only; even REVIEW_ONLY has no effect.

    Status precedence: DENIED (including revoked access/opt-out) before STALE;
    no model advisory can override S0 banking evidence or stage permission.
    """
    denied = RouterReview(RouterStatus.DENIED)
    if (type(outcome_snapshot) is not OutcomeSnapshot
            or type(outcome_current) is not S0OutcomeAuthority
            or type(receipt) is not F03Receipt
            or type(s0_grant) is not S0PlanningAuthorization
            or type(stage) is not S0StageDecision
            or type(capture) is not F02Capture
            or type(current) is not F02Current):
        return denied
    # First establish current S0/S1 scope; do not expose stale status to
    # callers whose own permission to see the case has been revoked.
    flags = (outcome_current.authenticated_session, outcome_current.store_grant,
             outcome_current.human_closure_verified, outcome_current.human_owner_valid,
             outcome_current.bank_submission_proved,
             current.session_authorized, current.store_authorized,
             current.case_eligible, current.plan_authorized,
             current.opted_out, current.bank_submitted,
             current.sold_or_historical_sale, current.post_sale_support,
             current.has_handoff_history,
             s0_grant.valid_human_closure, s0_grant.explicit_planning_request,
             s0_grant.authorized_for_post_human,
             s0_grant.unresolved_compliance_hold,
             stage.clarification_recontact_approved)
    if any(type(x) is not bool for x in flags):
        return denied
    if (not outcome_current.authenticated_session
            or not outcome_current.store_grant
            or not outcome_current.human_closure_verified
            or not outcome_current.human_owner_valid
            or not current.session_authorized
            or not current.store_authorized
            or not current.case_eligible
            or not current.plan_authorized
            or current.opted_out
            or current.bank_submitted
            or current.sold_or_historical_sale
            or current.post_sale_support
            or not s0_grant.valid_human_closure
            or not s0_grant.explicit_planning_request
            or not s0_grant.authorized_for_post_human
            or s0_grant.unresolved_compliance_hold):
        return denied
    ids = (outcome_snapshot.store, outcome_snapshot.case,
           outcome_snapshot.closure_event_id, outcome_snapshot.snapshot_hash,
           outcome_snapshot.message_watermark, stage.store, stage.case,
           stage.closure_event_id, stage.snapshot_hash, stage.message_watermark)
    if any(type(x) is not str or not x or len(x) > 128 for x in ids):
        return denied
    if (outcome_snapshot.store != stage.store
            or outcome_snapshot.case != stage.case
            or stage.store != outcome_current.store
            or stage.case != outcome_current.case
            or stage.store != receipt.store
            or stage.case != receipt.case
            or stage.store != s0_grant.store
            or stage.case != s0_grant.case
            or stage.store != capture.store
            or stage.case != capture.case
            or stage.store != current.store
            or stage.case != current.case):
        return denied
    versions = (outcome_snapshot.case_version, outcome_snapshot.form_version,
                stage.case_version, stage.form_version)
    if any(type(x) is not int or x < 1 for x in versions):
        return denied
    if (outcome_snapshot.closure_event_id != stage.closure_event_id
            or outcome_snapshot.snapshot_hash != stage.snapshot_hash
            or outcome_snapshot.message_watermark != stage.message_watermark
            or outcome_snapshot.case_version != stage.case_version
            or outcome_snapshot.form_version != stage.form_version
            or stage.closure_event_id != outcome_current.closure_event_id
            or stage.snapshot_hash != outcome_current.snapshot_hash
            or stage.message_watermark != outcome_current.message_watermark
            or stage.case_version != outcome_current.case_version
            or stage.form_version != outcome_current.form_version
            or stage.closure_event_id != receipt.closure_event_id
            or stage.snapshot_hash != receipt.snapshot_hash
            or stage.message_watermark != receipt.message_watermark
            or stage.case_version != receipt.case_version
            or stage.form_version != receipt.form_version
            or stage.closure_event_id != s0_grant.closure_event_id
            or stage.snapshot_hash != s0_grant.snapshot_hash
            or stage.message_watermark != s0_grant.message_watermark
            or stage.case_version != s0_grant.case_version
            or stage.form_version != s0_grant.form_version):
        return RouterReview(RouterStatus.STALE)

    result = review_f03_outcome_offline(
        outcome_snapshot, outcome_current, model_outcome)
    if result.status is OutcomeStatus.DENIED:
        return denied
    if result.status is OutcomeStatus.STALE:
        return RouterReview(RouterStatus.STALE)
    if result.status is OutcomeStatus.INVALID:
        return RouterReview(RouterStatus.INVALID_OUTCOME)
    if result.status is OutcomeStatus.HUMAN_REVIEW:
        return RouterReview(RouterStatus.HUMAN_REVIEW)
    if result.status is not OutcomeStatus.REVIEW_ONLY:
        return denied
    # Even a perfectly-formed model claim cannot authorize a commercial
    # recontact after bank-related conversation or withdrawal.
    if result.proposed_outcome in (
        ConversationOutcome.NEGOTIATION_READY_FOR_BANK_HANDOFF,
        ConversationOutcome.CONTINUE_TO_BANK_REVIEW,
        ConversationOutcome.CUSTOMER_WITHDREW,
        ConversationOutcome.NO_FURTHER_COMMERCIAL_INTEREST,
    ):
        return RouterReview(RouterStatus.COMMERCIAL_RECONTACT_BLOCKED)
    if result.proposed_outcome is not ConversationOutcome.NEEDS_CLARIFICATION:
        return RouterReview(RouterStatus.HUMAN_REVIEW)
    # Approval is a distinct fictional S0 input. OAI-07 classification cannot
    # itself be treated as consent or as a real request to resume contact.
    if outcome_current.missing_required_field_codes:
        # Missing essential data returns to a human, not a marketing chain.
        # The catalogue and its required flags are owned by S0.
        return RouterReview(RouterStatus.HUMAN_REVIEW)
    if not stage.clarification_recontact_approved:
        return RouterReview(RouterStatus.HUMAN_REVIEW)
    if outcome_current.bank_submission_proved:
        # A verified existing remittance takes precedence over proposing a
        # new commercial clarification chain, regardless of model text.
        return RouterReview(RouterStatus.COMMERCIAL_RECONTACT_BLOCKED)
    if current.owner_route != 'human' or not current.has_handoff_history:
        return denied

    plan = review_f03_to_f02_offline(
        receipt, s0_grant, capture, current, candidate_plan)
    if plan.status is BridgeStatus.DENIED:
        return denied
    if plan.status is BridgeStatus.STALE:
        return RouterReview(RouterStatus.STALE)
    if plan.status is BridgeStatus.INVALID_PROPOSAL:
        return RouterReview(RouterStatus.INVALID_PLAN)
    if plan.status in (BridgeStatus.HUMAN_REVIEW, BridgeStatus.NOT_ELIGIBLE):
        return RouterReview(RouterStatus.HUMAN_REVIEW)
    if plan.status is not BridgeStatus.REVIEW_ONLY:
        return denied
    return RouterReview(RouterStatus.REVIEW_ONLY,
                        plan.regular_template_refs, plan.final_template_ref)
