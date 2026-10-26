"""F02 isolated *untrusted* review-request lifecycle precheck (E04 lab).

No S0, SQL, IO, persistence, signature, approval or transport dependencies.
All records/clock/revocations in this module are *caller supplied claims*.
A positive outcome only means internally coherent INPUT FOR S0 RECHECK.
It does NOT attest that no revocation exists in the real S0 source.

Experimental review TTL: <=48 hours; not adopted business policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from hmac import compare_digest
from datetime import datetime, timedelta, timezone
from enum import Enum
import re
from uuid import UUID

from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, CONTRACT_VERSION, HandoffResult, HandoffState,
    ReviewOnlyProposal, prepare_handoff,
)

_REVIEW_TTL = timedelta(hours=48)
_HEX = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_MAX_ITEMS = 32


class LifecycleState(str, Enum):
    READY_FOR_S0_RECHECK_ONLY = "READY_FOR_S0_RECHECK_ONLY"
    UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY = "UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY"
    RECONCILIATION_RECHECK_REQUIRED = "RECONCILIATION_RECHECK_REQUIRED"
    TIME_OR_HISTORY_INVALID = "TIME_OR_HISTORY_INVALID"
    EXPIRED_REVIEW_REQUIRED = "EXPIRED_REVIEW_REQUIRED"
    REVOKED_CLAIM_REVIEW_REQUIRED = "REVOKED_CLAIM_REVIEW_REQUIRED"
    IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED = "IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED"
    DENIED_MALFORMED = "DENIED_MALFORMED"


@dataclass(frozen=True, slots=True)
class ReviewWindow:
    requested_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class UntrustedRecordedRequest:
    shop_id: UUID
    lead_id: UUID
    case_id: UUID
    closure_id: UUID
    idempotency_key: str
    request_sha256: str
    requested_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class UntrustedRevocation:
    shop_id: UUID
    closure_id: UUID
    idempotency_key: str
    occurred_at: datetime
    # This is only a caller-supplied marker, never an S0 signature.
    reference_sha256: str


@dataclass(frozen=True, slots=True)
class UntrustedTimeline:
    observed_at: datetime
    records: tuple[UntrustedRecordedRequest, ...] = ()
    revocations: tuple[UntrustedRevocation, ...] = ()


@dataclass(frozen=True, slots=True)
class LifecycleResult:
    status: LifecycleState


def _time(value: object) -> bool:
    return (type(value) is datetime
            and value.tzinfo is not None
            and value.utcoffset() is not None)


def _uuid(value: object) -> bool:
    return type(value) is UUID and value.int != 0


def _digest(value: object) -> bool:
    return type(value) is str and _HEX.fullmatch(value) is not None


def _window(start: datetime, end: datetime) -> bool:
    return (_time(start) and _time(end)
            and timedelta(0) < end - start <= _REVIEW_TTL)


def _scope(proposal: ReviewOnlyProposal) -> tuple[UUID, UUID, UUID, UUID]:
    return (proposal.shop_id, proposal.lead_id,
            proposal.case_id, proposal.closure_id)


def evaluate_review_lifecycle(
    handoff: HandoffResult,
    proposal: ReviewOnlyProposal,
    window: ReviewWindow,
    timeline: UntrustedTimeline,
) -> LifecycleResult:
    """Fail-closed pre-validation of an UNSIGNED F02 request for S0/Codex.

    Callers MUST NOT treat the snapshot or this return as S0 authorization.
    It has no mutation or durable idempotency; all such assertions require S0.
    """
    def state(value: LifecycleState) -> LifecycleResult:
        return LifecycleResult(value)

    if (type(handoff) is not HandoffResult
        or type(proposal) is not ReviewOnlyProposal
        or type(window) is not ReviewWindow
        or type(timeline) is not UntrustedTimeline):
        return state(LifecycleState.DENIED_MALFORMED)
    if (handoff.status is not HandoffState.HANDOFF_REVIEW_ONLY
        or handoff.contract_version != CONTRACT_VERSION
        or not _digest(handoff.untrusted_request_sha256)):
        return state(LifecycleState.RECONCILIATION_RECHECK_REQUIRED)
    scope = _scope(proposal)
    if (not all(_uuid(x) for x in scope)
        or type(proposal.idempotency_key) is not str
        or not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}\Z",
                            proposal.idempotency_key, re.ASCII)):
        return state(LifecycleState.DENIED_MALFORMED)
    if (not _window(window.requested_at, window.expires_at)
        or not _time(timeline.observed_at)
        or timeline.observed_at < window.requested_at
        or type(timeline.records) is not tuple
        or type(timeline.revocations) is not tuple
        or len(timeline.records) > _MAX_ITEMS
        or len(timeline.revocations) > _MAX_ITEMS):
        return state(LifecycleState.TIME_OR_HISTORY_INVALID)
    # Convert times to UTC for reliable cross-timezone comparisons.
    now = timeline.observed_at.astimezone(timezone.utc)
    if now >= window.expires_at.astimezone(timezone.utc):
        return state(LifecycleState.EXPIRED_REVIEW_REQUIRED)

    recorded = []
    for old in timeline.records:
        if (type(old) is not UntrustedRecordedRequest
            or not all(_uuid(x) for x in (
                old.shop_id, old.lead_id, old.case_id, old.closure_id))
            or not _digest(old.request_sha256)
            or type(old.idempotency_key) is not str
            or not _window(old.requested_at, old.expires_at)
            or old.requested_at > now
            or (old.shop_id, old.lead_id, old.case_id, old.closure_id) != scope):
            return state(LifecycleState.TIME_OR_HISTORY_INVALID)
        recorded.append(old)

    for rev in timeline.revocations:
        if (type(rev) is not UntrustedRevocation
            or not _uuid(rev.shop_id) or not _uuid(rev.closure_id)
            or rev.shop_id != proposal.shop_id
            or rev.closure_id != proposal.closure_id
            or type(rev.idempotency_key) is not str
            or not _digest(rev.reference_sha256)
            or not _time(rev.occurred_at)
            or rev.occurred_at > now):
            return state(LifecycleState.TIME_OR_HISTORY_INVALID)
        if rev.idempotency_key == proposal.idempotency_key:
            return state(LifecycleState.REVOKED_CLAIM_REVIEW_REQUIRED)

    # Any record for this closure with another key OR the same key with
    # different digest/window is a conflict, even if locally expired.
    if len(recorded) > 1:
        return state(LifecycleState.IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED)
    if recorded:
        old = recorded[0]
        if (old.idempotency_key != proposal.idempotency_key
            or old.request_sha256 != handoff.untrusted_request_sha256
            or old.requested_at != window.requested_at
            or old.expires_at != window.expires_at):
            return state(LifecycleState.IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED)
        return state(LifecycleState.UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY)
    return state(LifecycleState.READY_FOR_S0_RECHECK_ONLY)


def evaluate_bound_review_lifecycle(
    evidence: ClaimedS0Evidence,
    handoff: HandoffResult,
    proposal: ReviewOnlyProposal,
    window: ReviewWindow,
    timeline: UntrustedTimeline,
) -> LifecycleResult:
    """Bind the *untrusted* handoff to exactly these evidence/proposal fields.

    This is a pure, non-authorizing F02 preflight. Recomputing a plain SHA256
    only detects mismatch between caller-supplied claims; it is NOT an HMAC,
    signature, persisted record, S0 authenticity or consent verification.
    Future S0 consumers must use this bound path rather than assuming the
    legacy evaluate_review_lifecycle digest matches its proposal.
    """
    if (type(evidence) is not ClaimedS0Evidence
        or type(handoff) is not HandoffResult
        or type(proposal) is not ReviewOnlyProposal
        or type(window) is not ReviewWindow
        or type(timeline) is not UntrustedTimeline):
        return LifecycleResult(LifecycleState.DENIED_MALFORMED)
    expected = prepare_handoff(evidence, proposal)
    if (expected.status is not HandoffState.HANDOFF_REVIEW_ONLY
        or handoff.status is not HandoffState.HANDOFF_REVIEW_ONLY
        or handoff.contract_version != CONTRACT_VERSION
        or not _digest(expected.untrusted_request_sha256)
        or not _digest(handoff.untrusted_request_sha256)
        or not compare_digest(expected.untrusted_request_sha256,
                              handoff.untrusted_request_sha256)):
        return LifecycleResult(LifecycleState.RECONCILIATION_RECHECK_REQUIRED)
    return evaluate_review_lifecycle(handoff, proposal, window, timeline)
