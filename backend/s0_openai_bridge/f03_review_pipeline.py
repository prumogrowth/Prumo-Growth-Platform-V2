"""F03 offline composition: model suggestions + current S0/S1 authority check.

Pure contract fixture only. A successful REVIEW_ONLY is NEVER database permission:
S0 still must repeat authorization, provenance, versions and locks in the SAME
transaction that writes eligible fields. Never call this module from a browser.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .f03_offline_gate import Proposal, Result, Snapshot, evaluate_f03
from .f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority, ReviewDecision, recheck_before_apply,
)


class PipelineStatus(str, Enum):
    DENIED = "DENIED"
    STALE = "STALE"
    NOT_READY = "NOT_READY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REVIEW_ONLY = "REVIEW_ONLY"


@dataclass(frozen=True)
class PipelineReview:
    status: PipelineStatus
    candidate_field_codes: tuple[str, ...] = ()
    missing_required_codes: tuple[str, ...] = ()
    rejected_field_codes: tuple[str, ...] = ()
    # Synthetic-only advisory: optional catalogue fields informed by an
    # authorized customer but absent from the proposal; never invent values.
    omitted_informed_optional_codes: tuple[str, ...] = ()


def review_f03_offline(
    snapshot: Snapshot,
    proposal: Proposal,
    closure: ClosingSnapshot,
    current: CurrentAuthority,
) -> PipelineReview:
    """Review both boundaries without any write, plan, send or bank decision.

    Provenance assertions in the Snapshot remain FICTIONAL test annotations,
    not NLP verification. A synthetically valid review has no actual authority.
    """
    if (not isinstance(snapshot, Snapshot) or not isinstance(proposal, Proposal)
            or not isinstance(closure, ClosingSnapshot)
            or not isinstance(current, CurrentAuthority)):
        return PipelineReview(PipelineStatus.DENIED)

    # Recheck current authority before inspecting or exposing extraction state.
    # A revoked session/store grant must outrank a malformed/stale model result,
    # and stale operator/assignment versions must outrank readiness flags.
    # NOT_READY only means no validated fields yet; other S0/S1 guards passed.
    authority = recheck_before_apply(closure, current)
    if authority == ReviewDecision.DENY:
        return PipelineReview(PipelineStatus.DENIED)
    if authority == ReviewDecision.STALE:
        return PipelineReview(PipelineStatus.STALE)
    if authority not in (ReviewDecision.NOT_READY, ReviewDecision.REVIEW_ONLY):
        return PipelineReview(PipelineStatus.DENIED)

    # The two guards cannot be fed unrelated snapshots or events, even when
    # each would individually be approved by its own fixture.
    if (snapshot.store != closure.store or snapshot.case != closure.case
            or snapshot.closure_event_id != closure.closure_event):
        return PipelineReview(PipelineStatus.DENIED)
    if (snapshot.snapshot_hash != closure.snapshot_hash
            or snapshot.case_version != closure.case_version
            or snapshot.form_version != closure.form_version
            or snapshot.catalogue_version != closure.catalogue_version):
        return PipelineReview(PipelineStatus.STALE)

    field_review = evaluate_f03(snapshot, proposal)
    if field_review.status == Result.BLOCKED:
        return PipelineReview(PipelineStatus.DENIED)
    if field_review.status == Result.STALE:
        return PipelineReview(PipelineStatus.STALE)
    if field_review.status not in (Result.PROPOSAL_ONLY, Result.PARTIAL_REVIEW, Result.REVIEW):
        return PipelineReview(PipelineStatus.DENIED)

    candidates = tuple(item.field_code for item in field_review.accepted)
    # A missing optional field is NOT a missing mandatory field. Still, an
    # optional field explicitly stated by the authorized customer must not be
    # silently lost if the model omitted it. Only validated synthetic snapshot
    # annotations count; an operator note is never customer testimony.
    proposed_codes = {item.field_code for item in proposal.fields}
    omitted_optional = tuple(sorted(
        rule.code for rule in snapshot.rules
        if not rule.required and rule.code not in proposed_codes
        and any(message.actor == "customer" and message.authorized
                and isinstance(message.asserted_fields.get(rule.code), str)
                and message.asserted_fields[rule.code].strip()
                for message in snapshot.messages)
    ))
    # This is a consistency check only: the flag itself is not trusted as
    # proof of field correctness, actor identity or permission to persist.
    if type(current.result_has_validated_fields) is not bool:
        return PipelineReview(PipelineStatus.DENIED)
    if current.result_has_validated_fields != bool(candidates):
        return PipelineReview(PipelineStatus.NOT_READY)

    if authority == ReviewDecision.NOT_READY:
        # Recheck can return NOT_READY simply because no field was validated.
        # Still surface evidenced essential gaps to a human once its OTHER
        # session/grant/version guards have succeeded.
        if (not candidates and
                (field_review.needs_human_fields or field_review.rejected_fields
                 or omitted_optional)):
            return PipelineReview(
                PipelineStatus.REVIEW_REQUIRED, (),
                tuple(field_review.needs_human_fields),
                tuple(field_review.rejected_fields),
                omitted_optional,
            )
        return PipelineReview(PipelineStatus.NOT_READY)
    if authority != ReviewDecision.REVIEW_ONLY:
        return PipelineReview(PipelineStatus.DENIED)

    if (not candidates and not field_review.needs_human_fields
            and not field_review.rejected_fields and not omitted_optional):
        return PipelineReview(PipelineStatus.NOT_READY)
    if field_review.status != Result.PROPOSAL_ONLY or not candidates or omitted_optional:
        return PipelineReview(
            PipelineStatus.REVIEW_REQUIRED,
            candidates,
            tuple(field_review.needs_human_fields),
            tuple(field_review.rejected_fields),
            omitted_optional,
        )
    return PipelineReview(PipelineStatus.REVIEW_ONLY, candidates)
