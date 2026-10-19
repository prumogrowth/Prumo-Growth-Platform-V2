"""Second-time F03 authorization check for disposable synthetic lab ONLY.

This is not an S1 implementation, trusted identity provider, SQL transaction,
or a grant to apply fields. S0 must fetch current facts from authoritative S1,
commercial storage and session verification immediately before writing, inside
a transaction with concurrency control. Boolean inputs here are fake fixtures.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReviewDecision(str, Enum):
    DENY = "DENY"
    STALE = "STALE"
    NOT_READY = "NOT_READY"
    REVIEW_ONLY = "REVIEW_ONLY"


@dataclass(frozen=True)
class ClosingSnapshot:
    store: str
    case: str
    closure_event: str
    operator: str
    assignment: str
    case_version: int
    form_version: int
    watermark: str
    snapshot_hash: str
    catalogue_version: str


@dataclass(frozen=True)
class CurrentAuthority:
    store: str
    case: str
    closure_event: str
    operator: str
    assignment: str
    case_version: int
    form_version: int
    watermark: str
    snapshot_hash: str
    catalogue_version: str
    authenticated_session: bool
    operator_active: bool
    store_grant: bool
    case_human: bool
    purpose: str
    opted_out: bool
    result_has_validated_fields: bool


def recheck_before_apply(start: ClosingSnapshot, current: CurrentAuthority) -> ReviewDecision:
    """REVIEW_ONLY means a further authoritative S0 atomic check, not APPLY.

    A manager supervising a team is not automatically granted customer data.
    Any operator pause/transfer changing assignment must fail closed even if
    the same person later gets a new assignment for the case.
    """
    s, c = start, current
    if not isinstance(s, ClosingSnapshot) or not isinstance(c, CurrentAuthority):
        return ReviewDecision.DENY
    # A string "false" or number 1 cannot impersonate a verified S0/S1 flag.
    if any(type(flag) is not bool for flag in
           (c.authenticated_session, c.operator_active, c.store_grant,
            c.case_human, c.opted_out, c.result_has_validated_fields)):
        return ReviewDecision.DENY
    ids = (s.store, s.case, s.closure_event, s.operator, s.assignment,
           s.watermark, s.snapshot_hash, s.catalogue_version,
           c.store, c.case, c.closure_event, c.operator, c.assignment,
           c.watermark, c.snapshot_hash, c.catalogue_version)
    if any(not isinstance(v, str) or not v for v in ids):
        return ReviewDecision.DENY
    if (s.store != c.store or s.case != c.case or s.closure_event != c.closure_event
            or not c.authenticated_session or not c.operator_active or not c.store_grant
            or not c.case_human or c.purpose != "human_bank_collection" or c.opted_out):
        return ReviewDecision.DENY
    if any(type(v) is not int or v < 1 for v in
           (s.case_version, c.case_version, s.form_version, c.form_version)):
        return ReviewDecision.DENY
    if (s.operator != c.operator or s.assignment != c.assignment
            or s.case_version != c.case_version or s.form_version != c.form_version
            or s.watermark != c.watermark or s.snapshot_hash != c.snapshot_hash
            or s.catalogue_version != c.catalogue_version):
        return ReviewDecision.STALE
    if not c.result_has_validated_fields:
        return ReviewDecision.NOT_READY
    return ReviewDecision.REVIEW_ONLY
