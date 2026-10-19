"""Synthetic-only F03 evaluator. NO persistence, API, Meta calls or production authority.

Evidence.asserted_fields is a trusted FICTIONAL test annotation: a source
citation alone cannot prove that a model extracted the right value in reality.
Do not connect this stub to a commercial database or accept client-supplied
snapshot/permissions. Real field semantics and physical envelope need CFI-01.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class Result(str, Enum):
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    REVIEW = "REVIEW"
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    PARTIAL_REVIEW = "PARTIAL_REVIEW"


@dataclass(frozen=True)
class FieldRule:
    code: str
    required: bool
    auto_apply_allowed: bool


@dataclass(frozen=True)
class Evidence:
    ref: str
    store: str
    case: str
    actor: str
    asserted_fields: Mapping[str, str]
    authorized: bool = True


@dataclass(frozen=True)
class Candidate:
    field_code: str
    proposed_value: str
    source_message_refs: tuple[str, ...]


@dataclass(frozen=True)
class Snapshot:
    store: str
    case: str
    closure_event_id: str
    snapshot_hash: str
    case_version: int
    form_version: int
    catalogue_version: str
    actor_authorized_now: bool
    closure_authorized: bool
    original_snapshot_current: bool
    purpose: str
    rules: tuple[FieldRule, ...]
    messages: tuple[Evidence, ...]


@dataclass(frozen=True)
class Proposal:
    store: str
    case: str
    closure_event_id: str
    snapshot_hash: str
    case_version: int
    form_version: int
    catalogue_version: str
    fields: tuple[Candidate, ...]


@dataclass(frozen=True)
class Review:
    status: Result
    accepted: tuple[Candidate, ...] = ()
    needs_human_fields: tuple[str, ...] = ()
    rejected_fields: tuple[str, ...] = ()


def evaluate_f03(snapshot: Snapshot, proposal: Proposal) -> Review:
    """Only validate a fictional proposal, NEVER write or approve bank submission.

    A result in 'accepted' is an S0-review candidate; no caller should read
    it as an instruction to persist or evidence of verified model quality.
    """
    s, p = snapshot, proposal
    if (not s.store or not s.case or not s.closure_event_id or not s.snapshot_hash
            or not s.catalogue_version or not s.actor_authorized_now
            or not s.closure_authorized or s.purpose != "human_bank_collection"):
        return Review(Result.BLOCKED)
    if (p.store != s.store or p.case != s.case or p.closure_event_id != s.closure_event_id
            or p.catalogue_version != s.catalogue_version):
        return Review(Result.BLOCKED)
    if (not s.original_snapshot_current or p.snapshot_hash != s.snapshot_hash
            or p.case_version != s.case_version or p.form_version != s.form_version):
        return Review(Result.STALE)

    rules = {r.code: r for r in s.rules}
    messages = {m.ref: m for m in s.messages}
    if (not rules or len(rules) != len(s.rules) or len(messages) != len(s.messages)
            or any(not r.code for r in s.rules)):
        return Review(Result.BLOCKED)

    # Any cross-store/case provenance is a protocol boundary violation.
    if any(m.store != s.store or m.case != s.case for m in s.messages):
        return Review(Result.BLOCKED)

    accepted: list[Candidate] = []
    rejected: list[str] = []
    used: set[str] = set()
    for field in p.fields:
        code = field.field_code
        if not isinstance(code, str) or code not in rules:
            return Review(Result.BLOCKED)
        if code in used:
            rejected.append(code)
            accepted = [x for x in accepted if x.field_code != code]
            continue
        used.add(code)
        if (not rules[code].auto_apply_allowed or not isinstance(field.proposed_value, str)
                or not field.proposed_value.strip() or not field.source_message_refs):
            rejected.append(code)
            continue
        refs = field.source_message_refs
        if len(set(refs)) != len(refs):
            rejected.append(code)
            continue
        valid = True
        for ref in refs:
            m = messages.get(ref)
            if (m is None or m.actor != "customer" or not m.authorized
                    or m.asserted_fields.get(code) != field.proposed_value):
                valid = False
                break
        if valid:
            accepted.append(field)
        else:
            rejected.append(code)
    covered = {f.field_code for f in accepted}
    required_missing = sorted(r.code for r in s.rules if r.required and r.code not in covered)
    if required_missing or rejected:
        return Review(Result.PARTIAL_REVIEW if accepted else Result.REVIEW,
                      tuple(accepted), tuple(required_missing), tuple(sorted(set(rejected))))
    return Review(Result.PROPOSAL_ONLY, tuple(accepted))
