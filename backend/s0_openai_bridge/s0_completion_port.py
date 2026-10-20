"""CFI-01 candidate orchestration port. No ratified S0 transport exists yet.

This code models the correct *order* of calls, not authorization itself:
S0 owns GoTrue/session, store scope, human assignment, closure event, snapshot,
version and ALL persistent effects. The public request cannot supply those.

No real adapter, HTTP client, SQL, OpenAI call or banking side effect exists.
Injectable ports are for explicit synthetic tests; a fake port is NOT evidence
of real permission. The only positive result requires further S0 validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class S0AnswerKind(str, Enum):
    ACCEPTED = 'ACCEPTED'  # synthetic S0 completion/snapshot capture
    DENIED = 'DENIED'
    STALE = 'STALE'
    UNAVAILABLE = 'UNAVAILABLE'


class CompletionState(str, Enum):
    BLOCKED_BY_S0_CONTRACT = 'BLOCKED_BY_S0_CONTRACT'
    INVALID_REQUEST = 'INVALID_REQUEST'
    DENIED = 'DENIED'
    STALE = 'STALE'
    INVALID_S0_RESPONSE = 'INVALID_S0_RESPONSE'
    MODEL_UNAVAILABLE = 'MODEL_UNAVAILABLE'
    S0_VALIDATION_REQUIRED = 'S0_VALIDATION_REQUIRED'


@dataclass(frozen=True)
class CompletionRequest:
    case_ref: str
    expected_case_version: int
    idempotency_key: str
    # No actor, store, authorization flag or snapshot supplied by browser.


@dataclass(frozen=True)
class S0ClosedSnapshot:
    store_ref: str
    case_ref: str
    closure_event_ref: str
    snapshot_hash: str
    message_watermark: str
    case_version: int
    form_version: int
    catalogue_version: str
    # Model input deliberately NOT defined until OAI-05 schema is ratified.


@dataclass(frozen=True)
class S0Answer:
    kind: S0AnswerKind
    snapshot: S0ClosedSnapshot | None = None


@dataclass(frozen=True)
class CompletionReview:
    state: CompletionState
    # No field values, evidence, raw model text, bank state, or write command.


class S0CompletionPort(Protocol):
    """To be owned/implemented by S0 after CFI-01 and S1 approval."""
    def begin(self, request: CompletionRequest) -> S0Answer: ...
    def recheck(self, captured: S0ClosedSnapshot) -> S0Answer: ...


class F03CandidatePort(Protocol):
    """Untrusted model output; does not authenticate or authorize anything."""
    def propose(self, captured: S0ClosedSnapshot) -> object: ...


def _id(value: object) -> bool:
    return type(value) is str and 0 < len(value) <= 128 and value.strip() == value


def _valid_snapshot(value: object) -> bool:
    if type(value) is not S0ClosedSnapshot:
        return False
    return (all(_id(x) for x in (value.store_ref, value.case_ref,
                               value.closure_event_ref, value.snapshot_hash,
                               value.message_watermark, value.catalogue_version))
            and type(value.case_version) is int and value.case_version >= 1
            and type(value.form_version) is int and value.form_version >= 1)


def prepare_f03_completion_review(
    request: CompletionRequest,
    *,
    s0: S0CompletionPort | None = None,
    model: F03CandidatePort | None = None,
) -> CompletionReview:
    """Prepare review with TWO S0 reads, without accepting a model as S0 fact.

    The default is BLOCKED. A port provided by tests is not a real service.
    Even S0_VALIDATION_REQUIRED means S0 has yet to parse, authorize and
    commit any fields; no `APPLIED`/`SENT` path exists in this module.
    """
    if (type(request) is not CompletionRequest
            or not _id(request.case_ref)
            or not _id(request.idempotency_key)
            or type(request.expected_case_version) is not int
            or request.expected_case_version < 1):
        return CompletionReview(CompletionState.INVALID_REQUEST)
    if s0 is None or model is None:
        return CompletionReview(CompletionState.BLOCKED_BY_S0_CONTRACT)
    try:
        initial = s0.begin(request)
    except Exception:
        return CompletionReview(CompletionState.BLOCKED_BY_S0_CONTRACT)
    if type(initial) is not S0Answer or type(initial.kind) is not S0AnswerKind:
        return CompletionReview(CompletionState.INVALID_S0_RESPONSE)
    if initial.kind is S0AnswerKind.DENIED:
        return CompletionReview(CompletionState.DENIED)
    if initial.kind is S0AnswerKind.STALE:
        return CompletionReview(CompletionState.STALE)
    if initial.kind is S0AnswerKind.UNAVAILABLE:
        return CompletionReview(CompletionState.BLOCKED_BY_S0_CONTRACT)
    snap = initial.snapshot
    if not _valid_snapshot(snap):
        return CompletionReview(CompletionState.INVALID_S0_RESPONSE)
    if (snap.case_ref != request.case_ref
            or snap.case_version != request.expected_case_version):
        return CompletionReview(CompletionState.DENIED)
    try:
        _untrusted_model_result = model.propose(snap)
    except Exception:
        return CompletionReview(CompletionState.MODEL_UNAVAILABLE)
    # Untrusted model output is NOT interpreted or copied out of this boundary.
    # In the real path, its parsing belongs to the ratified F03 validator.
    try:
        fresh = s0.recheck(snap)
    except Exception:
        return CompletionReview(CompletionState.BLOCKED_BY_S0_CONTRACT)
    if type(fresh) is not S0Answer or type(fresh.kind) is not S0AnswerKind:
        return CompletionReview(CompletionState.INVALID_S0_RESPONSE)
    if fresh.kind is S0AnswerKind.DENIED:
        return CompletionReview(CompletionState.DENIED)
    if fresh.kind is S0AnswerKind.STALE:
        return CompletionReview(CompletionState.STALE)
    if fresh.kind is S0AnswerKind.UNAVAILABLE:
        return CompletionReview(CompletionState.BLOCKED_BY_S0_CONTRACT)
    if not _valid_snapshot(fresh.snapshot):
        return CompletionReview(CompletionState.INVALID_S0_RESPONSE)
    if fresh.snapshot != snap:
        return CompletionReview(CompletionState.STALE)
    return CompletionReview(CompletionState.S0_VALIDATION_REQUIRED)
