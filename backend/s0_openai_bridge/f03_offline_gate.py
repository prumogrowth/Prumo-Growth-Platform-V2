"""Synthetic-only F03 evaluator. NO persistence, API, Meta calls or production authority.

Evidence.asserted_fields is a trusted FICTIONAL test annotation: a source
citation alone cannot prove that a model extracted the right value in reality.
Do not connect this stub to a commercial database or accept client-supplied
snapshot/permissions. Real field semantics and physical envelope need CFI-01.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
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

    def __post_init__(self) -> None:
        # A frozen dataclass alone does not freeze a nested dict: an upstream
        # caller could alter "asserted_fields" AFTER S0 captured the snapshot,
        # making previously unsupported proposals appear evidenced.
        # Copy into a read-only mapping at the evidence boundary, preserving
        # malformed non-mappings for evaluate_f03 to reject fail-closed.
        if isinstance(self.asserted_fields, Mapping):
            object.__setattr__(self, "asserted_fields",
                               MappingProxyType(dict(self.asserted_fields)))


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
    # Strings such as "false" are truthy in Python and MUST NOT grant authority.
    # Versions also reject bool because bool is a subclass of int.
    if not isinstance(s, Snapshot) or not isinstance(p, Proposal):
        return Review(Result.BLOCKED)
    if (any(type(flag) is not bool for flag in
            (s.actor_authorized_now, s.closure_authorized, s.original_snapshot_current))
            or any(type(v) is not int or v < 1 for v in
                   (s.case_version, s.form_version, p.case_version, p.form_version))
            or any(not isinstance(v, str) or not v for v in
                   (s.store, s.case, s.closure_event_id, s.snapshot_hash,
                    s.catalogue_version, p.store, p.case, p.closure_event_id,
                    p.snapshot_hash, p.catalogue_version))):
        return Review(Result.BLOCKED)
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

    # The model-facing envelope is untrusted: malformed arrays must fail closed.
    if (not isinstance(s.rules, tuple) or not isinstance(s.messages, tuple)
            or not isinstance(p.fields, tuple)
            or any(not isinstance(r, FieldRule) or not isinstance(r.code, str)
                   or not r.code or type(r.required) is not bool
                   or type(r.auto_apply_allowed) is not bool for r in s.rules)
            or any(not isinstance(m, Evidence) or not isinstance(m.ref, str)
                   or not m.ref or not isinstance(m.store, str)
                   or not isinstance(m.case, str) or not isinstance(m.actor, str)
                   or type(m.authorized) is not bool
                   or not isinstance(m.asserted_fields, Mapping)
                   or any(not isinstance(key, str) or not isinstance(value, str)
                          for key, value in m.asserted_fields.items())
                   for m in s.messages)
            or any(not isinstance(f, Candidate) for f in p.fields)):
        return Review(Result.BLOCKED)
    rules = {r.code: r for r in s.rules}
    messages = {m.ref: m for m in s.messages}
    if not rules or len(rules) != len(s.rules) or len(messages) != len(s.messages):
        return Review(Result.BLOCKED)

    # Any cross-store/case provenance is a protocol boundary violation.
    if any(m.store != s.store or m.case != s.case for m in s.messages):
        return Review(Result.BLOCKED)

    # A cited assertion is NOT sufficient if another authorized CUSTOMER
    # statement in the same snapshot disagrees. Ordering/correction precedence
    # belongs to S0 and is still unratified; never pick a winner here.
    customer_values: dict[str, set[str]] = {}
    for msg in s.messages:
        if msg.actor == "customer" and msg.authorized:
            for code, value in msg.asserted_fields.items():
                if (isinstance(code, str) and code in rules and
                        isinstance(value, str) and value.strip()):
                    customer_values.setdefault(code, set()).add(value)
    conflicts = {code for code, values in customer_values.items() if len(values) > 1}

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
        if (code in conflicts or not rules[code].auto_apply_allowed
                or not isinstance(field.proposed_value, str)
                or not field.proposed_value.strip() or not field.source_message_refs):
            rejected.append(code)
            continue
        refs = field.source_message_refs
        if (not isinstance(refs, tuple) or
                any(not isinstance(ref, str) or not ref for ref in refs) or
                len(set(refs)) != len(refs)):
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
