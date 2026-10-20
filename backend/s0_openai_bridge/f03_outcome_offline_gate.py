"""Synthetic F03 conversational outcome review (OAI-07, unratified candidate).

Differentiate an operator's completed *conversation* from a completed sale.
No provider calls, bank decision, change of business status, plan, persistence,
Meta event, or automatic execution. All authority and evidence annotations are
FICTIONAL S0 test fixtures; message citations do not prove real NLP accuracy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConversationOutcome(str, Enum):
    NEGOTIATION_READY_FOR_BANK_HANDOFF = "NEGOTIATION_READY_FOR_BANK_HANDOFF"
    CONTINUE_TO_BANK_REVIEW = "CONTINUE_TO_BANK_REVIEW"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    CUSTOMER_WITHDREW = "CUSTOMER_WITHDREW"
    NO_FURTHER_COMMERCIAL_INTEREST = "NO_FURTHER_COMMERCIAL_INTEREST"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvidenceTopic(str, Enum):
    CONFIRMED_INTEREST = "CONFIRMED_INTEREST"
    MENTIONED_BANK_RETURN = "MENTIONED_BANK_RETURN"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    EXPLICIT_WITHDRAWAL = "EXPLICIT_WITHDRAWAL"
    EXPLICIT_NO_INTEREST = "EXPLICIT_NO_INTEREST"
    AMBIGUOUS = "AMBIGUOUS"


class OutcomeStatus(str, Enum):
    DENIED = "DENIED"
    STALE = "STALE"
    INVALID = "INVALID"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REVIEW_ONLY = "REVIEW_ONLY"


class NextStepAdvisory(str, Enum):
    HUMAN_CHECK_BANK_SUBMISSION = "HUMAN_CHECK_BANK_SUBMISSION"
    BANK_RETURN_PENDING_REVIEW = "BANK_RETURN_PENDING_REVIEW"
    HUMAN_BANK_SUBMISSION = "HUMAN_BANK_SUBMISSION"
    HUMAN_COLLECT_REQUIRED = "HUMAN_COLLECT_REQUIRED"
    HUMAN_CLARIFY = "HUMAN_CLARIFY"
    HUMAN_CONFIRM_WITHDRAWAL = "HUMAN_CONFIRM_WITHDRAWAL"
    HUMAN_REVIEW_OUTCOME = "HUMAN_REVIEW_OUTCOME"


@dataclass(frozen=True)
class OutcomeEvidence:
    ref: str
    store: str
    case: str
    speaker: str
    topic: EvidenceTopic
    authorized: bool


@dataclass(frozen=True)
class OutcomeSnapshot:
    store: str
    case: str
    closure_event_id: str
    snapshot_hash: str
    message_watermark: str
    case_version: int
    form_version: int
    evidence: tuple[OutcomeEvidence, ...]


@dataclass(frozen=True)
class S0OutcomeAuthority:
    store: str
    case: str
    closure_event_id: str
    snapshot_hash: str
    message_watermark: str
    case_version: int
    form_version: int
    authenticated_session: bool
    store_grant: bool
    human_closure_verified: bool
    human_owner_valid: bool
    bank_submission_proved: bool
    missing_required_field_codes: tuple[str, ...]


@dataclass(frozen=True)
class ModelOutcomeCandidate:
    outcome: ConversationOutcome
    reason_code: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class OutcomeReview:
    status: OutcomeStatus
    proposed_outcome: ConversationOutcome | None = None
    next_step: NextStepAdvisory | None = None
    evidence_refs: tuple[str, ...] = ()
    missing_required_field_codes: tuple[str, ...] = ()
    # No sale/bank decision, write command, customer text, or plan.


_REASONS = {
    ConversationOutcome.NEGOTIATION_READY_FOR_BANK_HANDOFF:
        ("CLIENT_CONFIRMED_INTENT", EvidenceTopic.CONFIRMED_INTEREST),
    ConversationOutcome.CONTINUE_TO_BANK_REVIEW:
        ("BANK_RETURN_MENTIONED", EvidenceTopic.MENTIONED_BANK_RETURN),
    ConversationOutcome.NEEDS_CLARIFICATION:
        ("NEEDS_INFORMATION", EvidenceTopic.NEEDS_INFORMATION),
    ConversationOutcome.CUSTOMER_WITHDREW:
        ("CUSTOMER_EXPLICIT_WITHDRAWAL", EvidenceTopic.EXPLICIT_WITHDRAWAL),
    ConversationOutcome.NO_FURTHER_COMMERCIAL_INTEREST:
        ("CUSTOMER_NO_FURTHER_INTEREST", EvidenceTopic.EXPLICIT_NO_INTEREST),
    ConversationOutcome.INCONCLUSIVE:
        ("UNCLEAR_RESULT", EvidenceTopic.AMBIGUOUS),
}


def _identifier(value: object) -> bool:
    return type(value) is str and 0 < len(value) <= 128 and value.strip() == value


def _codes(value: object, limit: int) -> bool:
    return (type(value) is tuple and len(value) <= limit
            and all(_identifier(x) for x in value)
            and len(set(value)) == len(value))


def review_f03_outcome_offline(
    snapshot: OutcomeSnapshot, current: S0OutcomeAuthority,
    proposed: object,
) -> OutcomeReview:
    """Review conversation outcome; never infer commercial or bank status.

    Bank-submission proof is exclusively a synthetic S0 fact, NOT text, model
    confidence or a manager's informal assurance. All results require actual
    S0 transaction-local revalidation before an eventual system effect.
    """
    denied = OutcomeReview(OutcomeStatus.DENIED)
    if type(snapshot) is not OutcomeSnapshot or type(current) is not S0OutcomeAuthority:
        return denied
    flags = (current.authenticated_session, current.store_grant,
             current.human_closure_verified, current.human_owner_valid,
             current.bank_submission_proved)
    if any(type(x) is not bool for x in flags):
        return denied
    identifiers = (snapshot.store, snapshot.case, snapshot.closure_event_id,
                   snapshot.snapshot_hash, snapshot.message_watermark,
                   current.store, current.case, current.closure_event_id,
                   current.snapshot_hash, current.message_watermark)
    if not all(_identifier(x) for x in identifiers):
        return denied
    if (snapshot.store != current.store or snapshot.case != current.case
            or not current.authenticated_session or not current.store_grant
            or not current.human_closure_verified or not current.human_owner_valid):
        return denied
    if any(type(x) is not int or x < 1 for x in
           (snapshot.case_version, snapshot.form_version,
            current.case_version, current.form_version)):
        return denied
    if (snapshot.closure_event_id != current.closure_event_id
            or snapshot.snapshot_hash != current.snapshot_hash
            or snapshot.message_watermark != current.message_watermark
            or snapshot.case_version != current.case_version
            or snapshot.form_version != current.form_version):
        return OutcomeReview(OutcomeStatus.STALE)
    if not _codes(current.missing_required_field_codes, 64):
        return denied
    if (type(snapshot.evidence) is not tuple or len(snapshot.evidence) > 200
            or any(type(e) is not OutcomeEvidence or not _identifier(e.ref)
                   or not _identifier(e.store) or not _identifier(e.case)
                   or e.store != snapshot.store or e.case != snapshot.case
                   or e.speaker not in ("customer", "operator")
                   or type(e.topic) is not EvidenceTopic
                   or type(e.authorized) is not bool for e in snapshot.evidence)
            or len({e.ref for e in snapshot.evidence}) != len(snapshot.evidence)):
        return denied
    if type(proposed) is not ModelOutcomeCandidate:
        return OutcomeReview(OutcomeStatus.INVALID)
    if (type(proposed.outcome) is not ConversationOutcome
            or not _identifier(proposed.reason_code)
            or not _codes(proposed.evidence_refs, 24)
            or not proposed.evidence_refs
            or proposed.reason_code != _REASONS[proposed.outcome][0]):
        return OutcomeReview(OutcomeStatus.INVALID)
    sources = {e.ref: e for e in snapshot.evidence}
    for ref in proposed.evidence_refs:
        e = sources.get(ref)
        if (e is None or not e.authorized or e.speaker != "customer"
                or e.topic is not _REASONS[proposed.outcome][1]):
            return OutcomeReview(OutcomeStatus.HUMAN_REVIEW)
    missing = current.missing_required_field_codes
    # Only catalogued essential fields count. Optional gaps NEVER block by
    # their mere absence; the trusted S0 fixture creates this list.
    if missing and proposed.outcome in (
        ConversationOutcome.NEGOTIATION_READY_FOR_BANK_HANDOFF,
        ConversationOutcome.CONTINUE_TO_BANK_REVIEW,
    ):
        return OutcomeReview(OutcomeStatus.HUMAN_REVIEW, proposed.outcome,
                             NextStepAdvisory.HUMAN_COLLECT_REQUIRED,
                             proposed.evidence_refs, missing)
    if proposed.outcome is ConversationOutcome.CONTINUE_TO_BANK_REVIEW:
        step = (NextStepAdvisory.BANK_RETURN_PENDING_REVIEW
                if current.bank_submission_proved
                else NextStepAdvisory.HUMAN_CHECK_BANK_SUBMISSION)
    elif proposed.outcome is ConversationOutcome.NEGOTIATION_READY_FOR_BANK_HANDOFF:
        step = (NextStepAdvisory.HUMAN_CHECK_BANK_SUBMISSION
                if current.bank_submission_proved
                else NextStepAdvisory.HUMAN_BANK_SUBMISSION)
    elif proposed.outcome is ConversationOutcome.NEEDS_CLARIFICATION:
        step = NextStepAdvisory.HUMAN_CLARIFY
    elif proposed.outcome in (ConversationOutcome.CUSTOMER_WITHDREW,
                              ConversationOutcome.NO_FURTHER_COMMERCIAL_INTEREST):
        step = NextStepAdvisory.HUMAN_CONFIRM_WITHDRAWAL
    else:
        step = NextStepAdvisory.HUMAN_REVIEW_OUTCOME
    state = (OutcomeStatus.HUMAN_REVIEW if proposed.outcome is ConversationOutcome.INCONCLUSIVE
             else OutcomeStatus.REVIEW_ONLY)
    return OutcomeReview(state, proposed.outcome, step, proposed.evidence_refs)
