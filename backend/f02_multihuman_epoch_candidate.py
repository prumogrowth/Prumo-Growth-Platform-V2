"""E04 F01/F02/F03 multiple-human-cycle proof/versions guard — LAB ONLY.

This module composes the already-certified candidate route+F02 proof checker
and the original pinned S2 Node validators. It checks separate F03 and
posthuman F02 snapshots for EACH closure episode in a repeated journey.
Every purported S0 event, version and snapshot is synthetic, NOT authenticated.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from backend.f01_f02_f03_route_ledger_candidate import (
    RouteScope, RouteEvent, RouteKind,
)
from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_multiroute_s2_validation_candidate import (
    S2RouteStatus, check_routed_proof_with_pinned_s2,
)

VERSION_KEYS = ("case", "cycle", "form", "catalog", "assignment")


class EpochStatus(str, Enum):
    MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY = "MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY"
    DENIED_MALFORMED = "DENIED_MALFORMED"
    ROUTE_OR_S2_RECHECK_REQUIRED = "ROUTE_OR_S2_RECHECK_REQUIRED"
    EPISODE_RECHECK_REQUIRED = "EPISODE_RECHECK_REQUIRED"
    VERSION_RECHECK_REQUIRED = "VERSION_RECHECK_REQUIRED"
    VERSION_REGRESSION_RECHECK_REQUIRED = "VERSION_REGRESSION_RECHECK_REQUIRED"


@dataclass(frozen=True, slots=True)
class HumanEpochClaim:
    # Source identities and version vector are untrusted caller assertions.
    closure_id: UUID
    closure_event_id: UUID
    f03_event_id: UUID
    f02_event_id: UUID
    versions: tuple[int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class HumanEpochResult:
    status: EpochStatus


def _valid_id(value: object) -> bool:
    return type(value) is UUID and value.int != 0


def _valid_versions(value: object) -> bool:
    return (type(value) is tuple and len(value) == len(VERSION_KEYS)
            and all(type(x) is int and 0 <= x <= 2**53-1 for x in value))


def _version_matches(step: dict, versions: tuple[int, ...]) -> bool:
    req = step.get("req") if type(step) is dict else None
    scope = req.get("scope") if type(req) is dict else None
    if type(scope) is not dict:
        return False
    expected = scope.get("expected")
    current = scope.get("current")
    return (type(expected) is dict and type(current) is dict
            and all(type(expected.get(k)) is int and
                    type(current.get(k)) is int and
                    expected[k] == v and current[k] == v
                    for k,v in zip(VERSION_KEYS, versions)))


def check_multi_human_epoch_candidate(
    scope: RouteScope,
    events: tuple[RouteEvent, ...],
    evidence: ClaimedS0Evidence,
    proposal: ReviewOnlyProposal,
    window: ReviewWindow,
    proof_packet: dict,
    s2_visits: tuple[dict, ...],
    synthetic_person_id: str,
    epoch_claims: tuple[HumanEpochClaim, ...],
) -> HumanEpochResult:
    """Only correlation across claimed episodes; never a source attestation.

    The version tuple is explicitly an E04 comparison aid. It is not an S0
    counter, does not establish transaction ordering, nor dictate whether S0
    must increment versions at human closure.
    """
    def out(status: EpochStatus) -> HumanEpochResult:
        return HumanEpochResult(status)

    if (type(events) is not tuple or type(s2_visits) is not tuple
        or type(epoch_claims) is not tuple or not epoch_claims
        or any(type(x) is not HumanEpochClaim
               or not all(_valid_id(i) for i in
                          (x.closure_id, x.closure_event_id,
                           x.f03_event_id, x.f02_event_id))
               or not _valid_versions(x.versions)
               for x in epoch_claims)):
        return out(EpochStatus.DENIED_MALFORMED)

    # Preserve the existing last-closure proof/route gate and invoke the
    # exact pinned S2 JS validators for every visit before any success.
    whole = check_routed_proof_with_pinned_s2(
        scope,events,evidence,proposal,window,
        proof_packet,s2_visits,synthetic_person_id)
    if whole.status is not S2RouteStatus.MULTIROUTE_AND_S2_SHAPE_RECHECK_ONLY:
        return out(EpochStatus.ROUTE_OR_S2_RECHECK_REQUIRED)

    closures = [e for e in events if e.kind is RouteKind.S0_HUMAN_CLOSURE]
    f03s = [e for e in events if e.kind is RouteKind.F03_PROPOSAL]
    posthumans = [e for e in events
                  if e.kind is RouteKind.S0_F02_POSTHUMAN_REQUEST]
    if (len(closures) != len(f03s)
        or len(closures) != len(posthumans)
        or len(closures) != len(epoch_claims)
        or len({x.closure_id for x in epoch_claims}) != len(epoch_claims)):
        return out(EpochStatus.EPISODE_RECHECK_REQUIRED)

    # Reconstruct visits in the exact same event order used by the pinned S2
    # bridge. This is not a second independent route transition engine.
    mapping = {
        RouteKind.F01_OPEN: "F01",
        RouteKind.S0_F01_RESUME_REQUEST: "F01",
        RouteKind.S0_F02_PREHUMAN_REQUEST: "F02",
        RouteKind.S0_F02_POSTHUMAN_REQUEST: "F02",
        RouteKind.F03_PROPOSAL: "F03",
    }
    source_visits = [event for event in events if event.kind in mapping]
    if len(source_visits) != len(s2_visits):
        return out(EpochStatus.EPISODE_RECHECK_REQUIRED)
    visits = {event.event_id: step
              for event,step in zip(source_visits,s2_visits)}
    previous_versions: tuple[int, ...] | None = None
    for close, f03, post, claim in zip(closures,f03s,posthumans,epoch_claims):
        if (claim.closure_id != close.closure_id
            or claim.closure_event_id != close.event_id
            or claim.f03_event_id != f03.event_id
            or claim.f02_event_id != post.event_id
            or f03.closure_id != close.closure_id
            or post.closure_id != close.closure_id):
            return out(EpochStatus.EPISODE_RECHECK_REQUIRED)
        if not (_version_matches(visits[f03.event_id],claim.versions)
                and _version_matches(visits[post.event_id],claim.versions)):
            return out(EpochStatus.VERSION_RECHECK_REQUIRED)
        # A decreasing declared version across human cycles is suspicious.
        # Keeping equal values is allowed; S0 has not defined an epoch bump.
        if (previous_versions is not None
            and any(a > b for a,b in zip(previous_versions,claim.versions))):
            return out(EpochStatus.VERSION_REGRESSION_RECHECK_REQUIRED)
        previous_versions = claim.versions

    return out(EpochStatus.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY)
