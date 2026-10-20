"""F02 synthetic recontact planning review: proposed templates only, no execution.

Candidate OAI-08 / CF-OP-02 contract [P/R], not a ratified S0 endpoint.
The caller supplies FICTIONAL S0/S1 authorization and policy fixtures. The
model can never route replies, decide C09, write plans or send via Meta.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class F02Status(str, Enum):
    DENIED = 'DENIED'
    STALE = 'STALE'
    INVALID_PROPOSAL = 'INVALID_PROPOSAL'
    REVIEW_ONLY = 'REVIEW_ONLY'


@dataclass(frozen=True)
class F02Capture:
    store: str
    case: str
    cycle: str
    request_id: str
    case_version: int
    message_watermark: str
    template_catalogue_version: str
    purpose: str  # post_human | ai_owned | operator_requested; candidate only
    allowed_template_versions: tuple[tuple[str, str], ...]
    allowed_evidence_refs: tuple[str, ...]
    regular_min: int
    regular_max: int
    window_start: str  # ISO 8601 with offset supplied by S0
    window_end: str


@dataclass(frozen=True)
class F02Current:
    store: str
    case: str
    cycle: str
    case_version: int
    message_watermark: str
    template_catalogue_version: str
    purpose: str
    session_authorized: bool
    store_authorized: bool
    case_eligible: bool
    plan_authorized: bool
    opted_out: bool
    bank_submitted: bool
    sold_or_historical_sale: bool
    post_sale_support: bool
    has_handoff_history: bool
    owner_route: str  # supplied by S0, never accepted from model


@dataclass(frozen=True)
class F02Attempt:
    template_id: str
    template_version: str
    scheduled_at: str
    evidence_refs: tuple[str, ...]
    reason_code: str


@dataclass(frozen=True)
class F02Proposal:
    request_id: str
    operation_kind: str
    proposed_attempts: tuple[F02Attempt, ...]
    final_template_candidate: F02Attempt


@dataclass(frozen=True)
class F02Review:
    status: F02Status
    regular_template_refs: tuple[tuple[str, str], ...] = ()
    final_template_ref: tuple[str, str] | None = None
    # Never output text, schedule, a C09 decision or a command to persist.


def _id(value: object) -> bool:
    return type(value) is str and 0 < len(value) <= 128 and value.strip() == value


def _timestamp(value: object) -> datetime | None:
    if type(value) is not str or len(value) > 40 or not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None and dt.utcoffset() is not None else None


def review_f02_offline(
    captured: F02Capture, current: F02Current, proposal: object,
) -> F02Review:
    """Validate proposed plan against frozen, SYNTHETIC S0 constraints.

    REVIEW_ONLY is permission to show a proposal for S0 review, NOT to
    schedule, enqueue/send a template, alter owner route or mark a case lost.
    S0 must re-query permissions/opt-out and catalogues atomically at apply.
    """
    deny = F02Review(F02Status.DENIED)
    if not isinstance(captured, F02Capture) or not isinstance(current, F02Current):
        return deny
    flags = (current.session_authorized, current.store_authorized,
             current.case_eligible, current.plan_authorized, current.opted_out,
             current.bank_submitted, current.sold_or_historical_sale,
             current.post_sale_support, current.has_handoff_history)
    if any(type(flag) is not bool for flag in flags):
        return deny
    ids = (captured.store, captured.case, captured.cycle, captured.request_id,
           captured.message_watermark, captured.template_catalogue_version,
           current.store, current.case, current.cycle, current.message_watermark,
           current.template_catalogue_version)
    if any(not _id(v) for v in ids):
        return deny
    if (captured.store != current.store or captured.case != current.case
            or captured.cycle != current.cycle
            or captured.purpose != current.purpose
            or captured.purpose not in ('post_human', 'ai_owned', 'operator_requested')
            or not current.session_authorized or not current.store_authorized
            or not current.case_eligible or not current.plan_authorized
            or current.opted_out or current.bank_submitted
            or current.sold_or_historical_sale or current.post_sale_support
            or current.owner_route not in ('human', 'seller_ai')
            or (captured.purpose == 'post_human' and not current.has_handoff_history)
            or (captured.purpose == 'operator_requested' and current.owner_route != 'human')
            or (current.has_handoff_history and current.owner_route != 'human')
            or (captured.purpose == 'ai_owned' and current.has_handoff_history)
            or (captured.purpose == 'ai_owned' and current.owner_route != 'seller_ai')):
        return deny
    if (type(captured.case_version) is not int or captured.case_version < 1
            or type(current.case_version) is not int or current.case_version < 1):
        return deny
    if (captured.case_version != current.case_version
            or captured.message_watermark != current.message_watermark
            or captured.template_catalogue_version != current.template_catalogue_version):
        return F02Review(F02Status.STALE)

    if (type(captured.regular_min) is not int or type(captured.regular_max) is not int
            or not 1 <= captured.regular_min <= captured.regular_max <= 5
            or (captured.purpose == 'post_human' and captured.regular_min < 2)):
        return deny
    start, end = _timestamp(captured.window_start), _timestamp(captured.window_end)
    if start is None or end is None or start >= end:
        return deny
    if (type(captured.allowed_template_versions) is not tuple or
            not captured.allowed_template_versions or
            len(captured.allowed_template_versions) > 100 or
            any(type(item) is not tuple or len(item) != 2 or
                not all(_id(v) for v in item)
                for item in captured.allowed_template_versions) or
            len(set(captured.allowed_template_versions)) != len(captured.allowed_template_versions)):
        return deny
    if (type(captured.allowed_evidence_refs) is not tuple or
            not captured.allowed_evidence_refs or
            len(captured.allowed_evidence_refs) > 200 or
            any(not _id(v) for v in captured.allowed_evidence_refs) or
            len(set(captured.allowed_evidence_refs)) != len(captured.allowed_evidence_refs)):
        return deny
    if not isinstance(proposal, F02Proposal):
        return F02Review(F02Status.INVALID_PROPOSAL)
    if (proposal.request_id != captured.request_id or
            proposal.operation_kind != 'recontact_plan' or
            type(proposal.proposed_attempts) is not tuple or
            not captured.regular_min <= len(proposal.proposed_attempts) <= captured.regular_max or
            not isinstance(proposal.final_template_candidate, F02Attempt)):
        return F02Review(F02Status.INVALID_PROPOSAL)

    approved = set(captured.allowed_template_versions)
    evidence = set(captured.allowed_evidence_refs)
    regular_keys: list[tuple[str, str]] = []
    last_date: datetime | None = None
    for attempt in (*proposal.proposed_attempts, proposal.final_template_candidate):
        if not isinstance(attempt, F02Attempt):
            return F02Review(F02Status.INVALID_PROPOSAL)
        key = (attempt.template_id, attempt.template_version)
        dt = _timestamp(attempt.scheduled_at)
        if (not all(_id(v) for v in key) or key not in approved or
                not _id(attempt.reason_code) or dt is None or
                not start <= dt <= end or (last_date is not None and dt <= last_date)
                or key in regular_keys or type(attempt.evidence_refs) is not tuple
                or not attempt.evidence_refs or len(attempt.evidence_refs) > 24 or
                any(not _id(ref) or ref not in evidence for ref in attempt.evidence_refs)
                or len(set(attempt.evidence_refs)) != len(attempt.evidence_refs)):
            return F02Review(F02Status.INVALID_PROPOSAL)
        last_date = dt
        regular_keys.append(key)
    return F02Review(F02Status.REVIEW_ONLY,
                     tuple(regular_keys[:-1]), regular_keys[-1])
