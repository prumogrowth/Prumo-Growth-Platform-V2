"""Synthetic-only OpenAI F03 candidate response boundary for CFI-01 [P/R].

This is NOT the homologated S0↔OpenAI API. No service calls, SQL, media,
side effects, credentials, or authority to persist. Input is a hypothetical
structured-output response with fictional field values. S0 still owns the
physical envelope, customer provenance and any future atomic application.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .f03_offline_gate import Candidate, Proposal, Snapshot
from .f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority, ReviewDecision, recheck_before_apply,
)
from .f03_review_pipeline import PipelineStatus, review_f03_offline


class WireStatus(str, Enum):
    DENIED = 'DENIED'
    STALE = 'STALE'
    INVALID_MODEL_OUTPUT = 'INVALID_MODEL_OUTPUT'
    NOT_READY = 'NOT_READY'
    REVIEW_REQUIRED = 'REVIEW_REQUIRED'
    REVIEW_ONLY = 'REVIEW_ONLY'


@dataclass(frozen=True)
class WireReview:
    status: WireStatus
    candidate_field_codes: tuple[str, ...] = ()
    missing_required_codes: tuple[str, ...] = ()
    rejected_field_codes: tuple[str, ...] = ()
    omitted_informed_optional_codes: tuple[str, ...] = ()


# Explicitly a provisional, synthetic shape drawn from OAI-05 and the CFI-01
# proposed reconciliation. Never advertise this as a negotiated physical API.
_ALLOWED_TOP = frozenset({
    'contract_version', 'request_id', 'operation_kind', 'closure_event_id',
    'snapshot_hash', 'form_version_observed', 'outcome', 'fields_proposed',
    'missing_fields', 'conflicts', 'extraction_warnings',
})
_REQUIRED_TOP = _ALLOWED_TOP - {'extraction_warnings'}
_ALLOWED_FIELD = frozenset({
    'field_code', 'proposed_value', 'source_message_refs', 'source_kind', 'certainty',
})
_REQUIRED_FIELD = frozenset({'field_code', 'proposed_value', 'source_message_refs'})


def _valid_id(value: object, max_chars: int = 128) -> bool:
    return type(value) is str and 0 < len(value) <= max_chars and value.strip() == value


def _build_candidate(
    model_output: object, snapshot: Snapshot, request_id: str, contract_version: str,
) -> tuple[Proposal | None, bool]:
    """Return a proposal plus advisory review signal, never an action.

    Raw values remain confined to Proposal sent to the trusted synthetic field
    evaluator. WireReview never copies raw values to logs/diagnostics.
    """
    if type(model_output) is not dict or not all(type(k) is str for k in model_output):
        return None, False
    raw: dict[str, Any] = model_output
    if not _REQUIRED_TOP.issubset(raw.keys()) or not raw.keys() <= _ALLOWED_TOP:
        return None, False
    if (raw['contract_version'] != contract_version or
            raw['request_id'] != request_id or
            raw['operation_kind'] != 'human_close_extract' or
            raw['closure_event_id'] != snapshot.closure_event_id):
        return None, False
    if (raw['snapshot_hash'] != snapshot.snapshot_hash or
            type(raw['form_version_observed']) is not int or
            raw['form_version_observed'] != snapshot.form_version):
        return None, False
    if (raw['outcome'] not in ('PROPOSED', 'PARTIAL', 'NEEDS_REVIEW', 'FAILED') or
            type(raw['outcome']) is not str):
        return None, False
    fields = raw['fields_proposed']
    missing = raw['missing_fields']
    conflicts = raw['conflicts']
    warnings = raw.get('extraction_warnings', [])
    if (type(fields) is not list or len(fields) > 64 or
            type(missing) is not list or len(missing) > 64 or
            type(conflicts) is not list or len(conflicts) > 64 or
            type(warnings) is not list or len(warnings) > 32):
        return None, False
    # Format of missing_field/conflict detail is still [R]. Rather than
    # invent and silently misread it, reject nonempty unsupported structures.
    if missing or conflicts or warnings:
        return None, False
    parsed: list[Candidate] = []
    for entry in fields:
        if (type(entry) is not dict or not _REQUIRED_FIELD.issubset(entry)
                or not entry.keys() <= _ALLOWED_FIELD):
            return None, False
        code, value, sources = (entry['field_code'], entry['proposed_value'],
                                entry['source_message_refs'])
        if (not _valid_id(code, 96) or type(value) is not str or
                not value.strip() or len(value) > 4096 or
                type(sources) is not list or not (1 <= len(sources) <= 16)
                or any(not _valid_id(ref) for ref in sources)
                or len(set(sources)) != len(sources)):
            return None, False
        if ('source_kind' in entry and entry['source_kind'] != 'client_statement'):
            return None, False
        if ('certainty' in entry and entry['certainty'] != 'explicit'):
            return None, False
        parsed.append(Candidate(code, value, tuple(sources)))
    # A model failure is not a usable output even if it accidentally contains
    # fields. It cannot cause a form write or a commercial status transition.
    if raw['outcome'] == 'FAILED':
        return None, False
    proposal = Proposal(snapshot.store, snapshot.case, snapshot.closure_event_id,
                        snapshot.snapshot_hash, snapshot.case_version,
                        snapshot.form_version, snapshot.catalogue_version,
                        tuple(parsed))
    return proposal, raw['outcome'] in ('PARTIAL', 'NEEDS_REVIEW')


def inspect_f03_candidate_wire(
    model_output: object, snapshot: Snapshot, closure: ClosingSnapshot,
    current: CurrentAuthority, *, request_id: str,
    contract_version: str = 's0-openai.v0.2-candidate',
) -> WireReview:
    """Review provisional model output, first checking synthetic S0/S1 scope.

    These are *not* real S0/S1 facts. No cached CurrentAuthority is durable
    authorization; any future writes need transaction-local reread + locks.
    """
    if (not isinstance(snapshot, Snapshot) or
            not isinstance(closure, ClosingSnapshot) or
            not isinstance(current, CurrentAuthority)):
        return WireReview(WireStatus.DENIED)
    authority = recheck_before_apply(closure, current)
    if authority == ReviewDecision.DENY:
        return WireReview(WireStatus.DENIED)
    if authority == ReviewDecision.STALE:
        return WireReview(WireStatus.STALE)
    if authority not in (ReviewDecision.REVIEW_ONLY, ReviewDecision.NOT_READY):
        return WireReview(WireStatus.DENIED)
    if not _valid_id(request_id) or not _valid_id(contract_version):
        return WireReview(WireStatus.DENIED)
    # Before parsing the model response, reject drift between the two trusted
    # synthetic envelopes as the underlying F03 composition also does.
    if (snapshot.store != closure.store or snapshot.case != closure.case or
            snapshot.closure_event_id != closure.closure_event):
        return WireReview(WireStatus.DENIED)
    if (snapshot.snapshot_hash != closure.snapshot_hash or
            snapshot.case_version != closure.case_version or
            snapshot.form_version != closure.form_version or
            snapshot.catalogue_version != closure.catalogue_version):
        return WireReview(WireStatus.STALE)
    parsed, advisory_review = _build_candidate(model_output, snapshot, request_id, contract_version)
    if parsed is None:
        return WireReview(WireStatus.INVALID_MODEL_OUTPUT)
    review = review_f03_offline(snapshot, parsed, closure, current)
    mapping = {
        PipelineStatus.DENIED: WireStatus.DENIED,
        PipelineStatus.STALE: WireStatus.STALE,
        PipelineStatus.NOT_READY: WireStatus.NOT_READY,
        PipelineStatus.REVIEW_REQUIRED: WireStatus.REVIEW_REQUIRED,
        PipelineStatus.REVIEW_ONLY: WireStatus.REVIEW_ONLY,
    }
    mapped = mapping.get(review.status, WireStatus.DENIED)
    if advisory_review and mapped == WireStatus.REVIEW_ONLY:
        mapped = WireStatus.REVIEW_REQUIRED
    if mapped in (WireStatus.DENIED, WireStatus.STALE):
        return WireReview(mapped)
    return WireReview(mapped, review.candidate_field_codes,
                      review.missing_required_codes, review.rejected_field_codes,
                      review.omitted_informed_optional_codes)
