"""F02 read-only adapter for S0's 0.1-candidate review-result projection.

This is a strict *shape and local request-continuity* check, not a signature,
S0 authentication, a source-of-truth read, ratification, scheduling or send.
All supplied dictionaries may be forged. Transport/lookup remains S0-owned.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hmac import compare_digest
import re
from uuid import UUID

from backend.f02_reconciled_human_authorization_handoff import (
    CONTRACT_VERSION, HandoffResult, HandoffState,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow

SCHEMA = "prumo.s0.f02.review.result/0.1-candidate"
EVIDENCE_SCOPE = "CFI_CONTEXT_ONLY_F02_EVIDENCE_PENDING"
HUMAN_RATIFICATION = "NOT_IMPLEMENTED_CONTRACT_PENDING"

_PERSISTED = frozenset((
    "RECORDED_REVIEW_ONLY", "REPLAY_REVIEW_ONLY", "CURRENT_REVIEW_ONLY",
    "WITHDRAWN_REVIEW_ONLY", "EXPIRED_REVIEW_ONLY",
))
_TERMINAL = frozenset(("WITHDRAWN_REVIEW_ONLY", "EXPIRED_REVIEW_ONLY"))
_NEGATIVE = frozenset((
    "INPUT_REJECTED", "DENIED", "STALE", "IDEMPOTENCY_CONFLICT",
    "REQUEST_EXPIRED", "REVIEW_REQUEST_NOT_FOUND",
    "CLOCK_RECHECK_REQUIRED", "UNAVAILABLE",
))
_KEYS = frozenset((
    "schema", "state", "review_ref", "revision", "observed_at",
    "request_sha256", "expires_at", "evidence_scope",
    "human_ratification", "send_authorized", "scheduling_authorized",
    "commercial_transition_authorized",
))
_SHA = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_REV = re.compile(r"[1-9][0-9]{0,9}\Z", re.ASCII)


class ProjectionGate(str, Enum):
    PERSISTED_REVIEW_STATE_ONLY = "PERSISTED_REVIEW_STATE_ONLY"
    TERMINAL_REVIEW_STATE_ONLY = "TERMINAL_REVIEW_STATE_ONLY"
    NEGATIVE_RESULT_RECHECK_ONLY = "NEGATIVE_RESULT_RECHECK_ONLY"
    CONTRACT_RECHECK_REQUIRED = "CONTRACT_RECHECK_REQUIRED"
    REQUEST_BINDING_RECHECK_REQUIRED = "REQUEST_BINDING_RECHECK_REQUIRED"
    CONTINUITY_RECHECK_REQUIRED = "CONTINUITY_RECHECK_REQUIRED"
    DENIED_MALFORMED = "DENIED_MALFORMED"


@dataclass(frozen=True, slots=True)
class ProjectionGateResult:
    status: ProjectionGate


def _aware(value: object) -> bool:
    return type(value) is datetime and value.tzinfo is not None and value.utcoffset() is not None


def _timestamp(value: object) -> datetime | None:
    if type(value) is not str:
        return None
    try:
        stamp = datetime.fromisoformat(value)
        return stamp.astimezone(timezone.utc) if _aware(stamp) else None
    except (OverflowError, TypeError, ValueError):
        return None


def _uuid(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        parsed = UUID(value)
        return parsed.int != 0 and str(parsed) == value
    except (ValueError, AttributeError):
        return False


def _data(value: object) -> bool:
    return (
        type(value) is dict
        and frozenset(value) == _KEYS
        and value.get("schema") == SCHEMA
        and type(value.get("state")) is str
        and value["state"] in _PERSISTED | _NEGATIVE
        and value.get("evidence_scope") == EVIDENCE_SCOPE
        and value.get("human_ratification") == HUMAN_RATIFICATION
        and value.get("send_authorized") is False
        and value.get("scheduling_authorized") is False
        and value.get("commercial_transition_authorized") is False
    )


def inspect_s0_review_projection(
    projection: dict,
    handoff: HandoffResult,
    window: ReviewWindow,
    *,
    previous: dict | None = None,
) -> ProjectionGateResult:
    """Fail closed; no signed source proof is implied by a valid projection.

    The previous projection, if supplied, is also untrusted, and is only
    used to detect internally inconsistent claimed continuity, not real
    historical completeness. Never use the result to schedule or send.
    """
    def outcome(code: ProjectionGate) -> ProjectionGateResult:
        return ProjectionGateResult(code)

    if (type(projection) is not dict
        or type(handoff) is not HandoffResult
        or type(window) is not ReviewWindow
        or (previous is not None and type(previous) is not dict)):
        return outcome(ProjectionGate.DENIED_MALFORMED)

    if (handoff.status is not HandoffState.HANDOFF_REVIEW_ONLY
        or handoff.contract_version != CONTRACT_VERSION
        or type(handoff.untrusted_request_sha256) is not str
        or _SHA.fullmatch(handoff.untrusted_request_sha256) is None
        or not _aware(window.requested_at)
        or not _aware(window.expires_at)
        or window.requested_at >= window.expires_at):
        return outcome(ProjectionGate.REQUEST_BINDING_RECHECK_REQUIRED)

    if not _data(projection) or (previous is not None and not _data(previous)):
        return outcome(ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def fields(row: dict):
        """Strict structural validation of nullable result fields."""
        state = row["state"]
        values = (row["review_ref"], row["revision"], row["observed_at"],
                  row["request_sha256"], row["expires_at"])
        if state in _NEGATIVE:
            return values == (None,) * 5
        if (not _uuid(row["review_ref"])
            or type(row["revision"]) is not str
            or _REV.fullmatch(row["revision"]) is None
            or int(row["revision"]) > 2147483647
            or _timestamp(row["observed_at"]) is None
            or type(row["request_sha256"]) is not str
            or _SHA.fullmatch(row["request_sha256"]) is None
            or _timestamp(row["expires_at"]) is None):
            return False
        return True

    if not fields(projection) or (previous is not None and not fields(previous)):
        return outcome(ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    expiry = window.expires_at.astimezone(timezone.utc)

    def bound(row: dict) -> bool:
        return (row["state"] in _NEGATIVE
            or (compare_digest(row["request_sha256"], handoff.untrusted_request_sha256)
                and _timestamp(row["expires_at"]) == expiry))

    if not bound(projection) or (previous is not None and not bound(previous)):
        return outcome(ProjectionGate.REQUEST_BINDING_RECHECK_REQUIRED)

    if previous is not None:
        pstate, nstate = previous["state"], projection["state"]
        if pstate in _PERSISTED:
            # An error response may be transient; never erase a prior
            # persisted claim based solely on a failed subsequent response.
            if nstate in _NEGATIVE:
                return outcome(ProjectionGate.CONTINUITY_RECHECK_REQUIRED)
            if (previous["review_ref"] != projection["review_ref"]
                or int(projection["revision"]) < int(previous["revision"])
                or _timestamp(projection["observed_at"]) < _timestamp(previous["observed_at"])
                or (pstate in _TERMINAL and nstate != pstate)):
                return outcome(ProjectionGate.CONTINUITY_RECHECK_REQUIRED)

    state = projection["state"]
    if state in _NEGATIVE:
        return outcome(ProjectionGate.NEGATIVE_RESULT_RECHECK_ONLY)
    if state in _TERMINAL:
        return outcome(ProjectionGate.TERMINAL_REVIEW_STATE_ONLY)
    # Recorded/current/replay only attests the caller supplied a compatible
    # *shape*. Even these states cannot be trusted without an S0-owned channel.
    if _timestamp(projection["observed_at"]) >= expiry:
        return outcome(ProjectionGate.CONTINUITY_RECHECK_REQUIRED)
    return outcome(ProjectionGate.PERSISTED_REVIEW_STATE_ONLY)
