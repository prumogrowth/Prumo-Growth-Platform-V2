"""E04/F02 proposed read-only S0 lookup alignment; NO transport or authority.

The pinned S0 result has no shop/lead/case or channel. These are separately
claimed and cannot establish source identity, authorization, persistence,
completeness, or S0/GoTrue/CFI provenance. The S0 request digest covers an
internal request and MUST NOT be silently equated to F02's handoff digest.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hmac import compare_digest
import re
from uuid import UUID

from backend.f02_s0_review_projection_candidate import (
    SCHEMA as PINNED_S0_SCHEMA, EVIDENCE_SCOPE, HUMAN_RATIFICATION,
    _PERSISTED, _TERMINAL, _NEGATIVE, _data, _timestamp, _uuid,
)
from backend.f02_version_chain_replay_candidate import (
    ReplayObservation, SCHEMA as REPLAY_SCHEMA, SOURCE_STATE as REPLAY_SOURCE,
    _valid_observation as replay_shape,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_REV = re.compile(r"[1-9][0-9]{0,9}\Z", re.ASCII)
SOURCE = "F02_UNVERIFIED_READ_ONLY_S0_LOOKUP_CLAIM"
MAX_LOOKUP_CLAIM_AGE_DAYS = None  # Deliberately NO inferred S0 business TTL.


class LookupGate(str, Enum):
    PERSISTED_SHAPE_RECHECK_ONLY = "PERSISTED_SHAPE_RECHECK_ONLY"
    TERMINAL_REVIEW_HOLD = "TERMINAL_REVIEW_HOLD"
    NEGATIVE_REVIEW_HOLD = "NEGATIVE_REVIEW_HOLD"
    DENIED_MALFORMED = "DENIED_MALFORMED"
    CLAIM_SCOPE_RECHECK_REQUIRED = "CLAIM_SCOPE_RECHECK_REQUIRED"
    S0_REQUEST_DIGEST_RECHECK_REQUIRED = "S0_REQUEST_DIGEST_RECHECK_REQUIRED"
    S0_RESULT_CONTRACT_RECHECK_REQUIRED = "S0_RESULT_CONTRACT_RECHECK_REQUIRED"
    S0_RESULT_CONTINUITY_RECHECK_REQUIRED = "S0_RESULT_CONTINUITY_RECHECK_REQUIRED"


@dataclass(frozen=True, slots=True)
class LookupBindingClaim:
    """Proposed F02-side lookup keys; nothing here is an S0-issued token."""
    shop_id: UUID
    lead_id: UUID
    case_id: UUID
    closure_id: UUID
    channel_id: UUID
    idempotency_key: str
    route_id: UUID
    f03_event_id: UUID
    f02_event_id: UUID
    candidate_source: str = SOURCE


@dataclass(frozen=True, slots=True)
class S0LookupAlignment:
    status: LookupGate


def _ids_valid(v: object) -> bool:
    return type(v) is UUID and v.int != 0


def _validate_row(row: object) -> bool:
    """Strict pinned result shape; never infer authenticity from it."""
    if not _data(row):
        return False
    state = row["state"]
    neutral = (row["review_ref"], row["revision"], row["observed_at"],
               row["request_sha256"], row["expires_at"])
    if state in _NEGATIVE:
        return neutral == (None,) * 5
    if (not _uuid(row["review_ref"])
        or type(row["revision"]) is not str
        or _REV.fullmatch(row["revision"]) is None
        or int(row["revision"]) > 2147483647
        or _timestamp(row["observed_at"]) is None
        or type(row["request_sha256"]) is not str
        or _SHA.fullmatch(row["request_sha256"]) is None
        or _timestamp(row["expires_at"]) is None):
        return False
    return _timestamp(row["observed_at"]) is not None


def inspect_s0_lookup_alignment_candidate(
    observation: ReplayObservation,
    binding: LookupBindingClaim,
    result: dict,
    *,
    expected_s0_request_sha256: str,
    previous_result: dict | None = None,
) -> S0LookupAlignment:
    """Cross-check *caller-supplied* lookup claims and pinned S0 projection.

    The expected S0 request SHA is an independent claimed reference to the
    internal S0 request, NOT the F02 handoff digest and not a signature.
    A positive result never implies that the lookup happened at all.
    """
    def out(code: LookupGate) -> S0LookupAlignment:
        return S0LookupAlignment(code)
    if (type(observation) is not ReplayObservation
        or type(binding) is not LookupBindingClaim
        or type(result) is not dict
        or (previous_result is not None and type(previous_result) is not dict)
        or type(expected_s0_request_sha256) is not str
        or _SHA.fullmatch(expected_s0_request_sha256) is None):
        return out(LookupGate.DENIED_MALFORMED)
    if (not replay_shape(observation)
        or binding.candidate_source != SOURCE
        or not all(_ids_valid(getattr(binding, name)) for name in (
            "shop_id", "lead_id", "case_id", "closure_id", "channel_id",
            "route_id", "f03_event_id", "f02_event_id"))
        or type(binding.idempotency_key) is not str
        or not 8 <= len(binding.idempotency_key) <= 128
        or (observation.shop_id, observation.lead_id,
            observation.case_id, observation.closure_id,
            observation.channel_id, observation.route_id,
            observation.f03_event_id, observation.f02_event_id,
            observation.idempotency_key) != (
            binding.shop_id, binding.lead_id,
            binding.case_id, binding.closure_id,
            binding.channel_id, binding.route_id,
            binding.f03_event_id, binding.f02_event_id,
            binding.idempotency_key)):
        return out(LookupGate.CLAIM_SCOPE_RECHECK_REQUIRED)

    if not _validate_row(result) or (
        previous_result is not None and not _validate_row(previous_result)):
        return out(LookupGate.S0_RESULT_CONTRACT_RECHECK_REQUIRED)

    for row in (result, previous_result):
        if row is not None and row["state"] in _PERSISTED:
            if not compare_digest(row["request_sha256"],
                                  expected_s0_request_sha256):
                return out(LookupGate.S0_REQUEST_DIGEST_RECHECK_REQUIRED)

    if previous_result is not None:
        old, cur = previous_result, result
        if old["state"] in _PERSISTED:
            if cur["state"] in _NEGATIVE:
                return out(LookupGate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)
            if (cur["review_ref"] != old["review_ref"]
                or _timestamp(cur["expires_at"]) != _timestamp(old["expires_at"])
                or int(cur["revision"]) < int(old["revision"])
                or _timestamp(cur["observed_at"])
                   < _timestamp(old["observed_at"])
                or (old["state"] in _TERMINAL
                    and cur["state"] != old["state"])):
                return out(LookupGate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)
    if result["state"] in _NEGATIVE:
        return out(LookupGate.NEGATIVE_REVIEW_HOLD)
    if result["state"] in _TERMINAL:
        return out(LookupGate.TERMINAL_REVIEW_HOLD)
    if (_timestamp(result["observed_at"])
        >= _timestamp(result["expires_at"])):
        return out(LookupGate.S0_RESULT_CONTINUITY_RECHECK_REQUIRED)
    # Even this positive label is only a format check for an untrusted,
    # caller-supplied result. No S0 adapter or source authentication exists.
    return out(LookupGate.PERSISTED_SHAPE_RECHECK_ONLY)
