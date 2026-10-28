"""E04 A36: deterministic synthetic chain identity and local replay classification.

No persistent ledger, transaction, S0 attestation, message, OpenAI model call,
credential, Meta operation, scheduling, or permission to apply an F02 plan.
All payloads and prior observations are UNSIGNED and caller-supplied.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import re
from uuid import UUID

from backend.f01_f02_f03_route_ledger_candidate import RouteEvent, RouteScope
from backend.f02_multihuman_epoch_candidate import (
    HumanEpochClaim, VersionTransitionClaim, EpochStatus,
    check_multi_human_epoch_candidate,
)
from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow

SCHEMA = "prumo.openai.f02.version_chain_replay/0.1-lab"
SOURCE_STATE = "E04_UNVERIFIED_REPLAY_OBSERVATION_ONLY"
MAX_PRIOR_OBSERVATIONS = 64
MAX_SNAPSHOT_BYTES = 262144
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class ReplayStatus(str, Enum):
    NEW_CHAIN_CANDIDATE_ONLY = "NEW_CHAIN_CANDIDATE_ONLY"
    IDENTICAL_REPLAY_NO_NEW_ACTION = "IDENTICAL_REPLAY_NO_NEW_ACTION"
    REQUEST_CONFLICT_RECHECK_REQUIRED = "REQUEST_CONFLICT_RECHECK_REQUIRED"
    EVENT_ID_REUSE_RECHECK_REQUIRED = "EVENT_ID_REUSE_RECHECK_REQUIRED"
    IDEMPOTENCY_KEY_RECHECK_REQUIRED = "IDEMPOTENCY_KEY_RECHECK_REQUIRED"
    PRIOR_OBSERVATIONS_RECHECK_REQUIRED = "PRIOR_OBSERVATIONS_RECHECK_REQUIRED"
    ROUTE_OR_VERSION_RECHECK_REQUIRED = "ROUTE_OR_VERSION_RECHECK_REQUIRED"
    DENIED_MALFORMED = "DENIED_MALFORMED"


@dataclass(frozen=True, slots=True)
class ReplayObservation:
    """Unsigned deterministic candidate receipt, NEVER durable S0 evidence."""
    schema: str
    source_state: str
    route_id: UUID
    shop_id: UUID
    lead_id: UUID
    case_id: UUID
    closure_id: UUID
    f03_event_id: UUID
    f02_event_id: UUID
    channel_id: UUID
    idempotency_key: str
    payload_sha256: str
    event_digests: tuple[tuple[UUID, str], ...]


@dataclass(frozen=True, slots=True)
class ReplayResult:
    status: ReplayStatus
    candidate_observation: ReplayObservation | None = None


def _id(value: object) -> bool:
    return type(value) is UUID and value.int != 0


def _digest(data: object) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False)
    if len(payload.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
        raise ValueError("oversized synthetic replay snapshot")
    return sha256(payload.encode("utf-8")).hexdigest()


def _instant(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _event_view(event: RouteEvent) -> dict:
    return {
        "event_id": str(event.event_id),
        "route_id": str(event.route_id),
        "shop_id": str(event.shop_id),
        "lead_id": str(event.lead_id),
        "case_id": str(event.case_id),
        "closure_id": str(event.closure_id) if event.closure_id else None,
        "sequence": event.sequence,
        "occurred_at_utc": _instant(event.occurred_at),
        "kind": event.kind.value,
        "claimed_source": event.claimed_source,
    }


def _version_view(claim: VersionTransitionClaim) -> dict:
    return {
        "event_id": str(claim.event_id),
        "shop_id": str(claim.shop_id),
        "lead_id": str(claim.lead_id),
        "case_id": str(claim.case_id),
        "closure_id": str(claim.closure_id),
        "f03_event_id": str(claim.f03_event_id),
        "f02_event_id": str(claim.f02_event_id),
        "from_versions": list(claim.from_versions),
        "to_versions": list(claim.to_versions),
        "source_state": claim.source_state,
    }


def _valid_observation(row: object) -> bool:
    return (type(row) is ReplayObservation
            and row.schema == SCHEMA and row.source_state == SOURCE_STATE
            and all(_id(getattr(row, k)) for k in (
                "route_id", "shop_id", "lead_id", "case_id",
                "closure_id", "f03_event_id", "f02_event_id",
                "channel_id"))
            and type(row.idempotency_key) is str
            and 8 <= len(row.idempotency_key) <= 128
            and type(row.payload_sha256) is str
            and _SHA.fullmatch(row.payload_sha256) is not None
            and type(row.event_digests) is tuple
            and 0 <= len(row.event_digests) <= 16
            and all(type(pair) is tuple and len(pair) == 2
                    and _id(pair[0]) and type(pair[1]) is str
                    and _SHA.fullmatch(pair[1]) is not None
                    for pair in row.event_digests)
            and len({p[0] for p in row.event_digests}) == len(row.event_digests))


def _request_identity(row: ReplayObservation) -> tuple[UUID, ...]:
    return (row.route_id, row.shop_id, row.lead_id, row.case_id,
            row.closure_id, row.f03_event_id, row.f02_event_id)


def _validate_observation_history(history: tuple[ReplayObservation, ...]) -> bool:
    """Reject contradictory prior keys and cross-request event reuse.

    This detects structural inconsistencies in *supplied* history; it does not
    establish that history was complete or persisted by S0.
    """
    by_request: dict[tuple[UUID, ...], ReplayObservation] = {}
    by_event: dict[UUID, tuple[tuple[UUID, ...], str]] = {}
    by_key: dict[tuple[UUID, UUID, str], tuple[UUID, ...]] = {}
    for row in history:
        if not _valid_observation(row):
            return False
        key = _request_identity(row)
        other = by_request.get(key)
        if other is not None and other != row:
            return False
        by_request[key] = row
        scoped_key = (row.shop_id, row.channel_id, row.idempotency_key)
        if scoped_key in by_key and by_key[scoped_key] != key:
            return False
        by_key[scoped_key] = key
        for event_id, digest in row.event_digests:
            observed = by_event.get(event_id)
            if observed is not None and observed != (key, digest):
                return False
            by_event[event_id] = (key, digest)
    return True


def classify_version_chain_replay_candidate(
    scope: RouteScope,
    events: tuple[RouteEvent, ...],
    evidence: ClaimedS0Evidence,
    proposal: ReviewOnlyProposal,
    window: ReviewWindow,
    proof_packet: dict,
    s2_visits: tuple[dict, ...],
    synthetic_person_id: str,
    epoch_claims: tuple[HumanEpochClaim, ...],
    version_updates: tuple[VersionTransitionClaim, ...],
    prior_observations: tuple[ReplayObservation, ...] = (),
) -> ReplayResult:
    """Classify unsigned re-evaluation; never emit authorized or send fields."""
    def out(status: ReplayStatus,
            candidate: ReplayObservation | None = None) -> ReplayResult:
        return ReplayResult(status, candidate)

    if (type(prior_observations) is not tuple
        or len(prior_observations) > MAX_PRIOR_OBSERVATIONS
        or type(version_updates) is not tuple
        or type(events) is not tuple
        or type(epoch_claims) is not tuple
        or type(s2_visits) is not tuple):
        return out(ReplayStatus.DENIED_MALFORMED)
    if not _validate_observation_history(prior_observations):
        return out(ReplayStatus.PRIOR_OBSERVATIONS_RECHECK_REQUIRED)

    original = check_multi_human_epoch_candidate(
        scope, events, evidence, proposal, window, proof_packet,
        s2_visits, synthetic_person_id, epoch_claims, version_updates)
    if original.status is not EpochStatus.MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY:
        return out(ReplayStatus.ROUTE_OR_VERSION_RECHECK_REQUIRED)

    closes = [event for event in events if event.kind.value == "S0_HUMAN_CLOSURE"]
    f03s = [event for event in events if event.kind.value == "F03_PROPOSAL"]
    f02s = [event for event in events
            if event.kind.value == "S0_F02_POSTHUMAN_REQUEST"]
    if not closes or not f03s or not f02s or not epoch_claims:
        return out(ReplayStatus.ROUTE_OR_VERSION_RECHECK_REQUIRED)

    # Canonical request content includes all declared route, proof and S2
    # fixture fields. Hash equality is a repeatability check, NOT authenticity.
    try:
        snapshot = {
            "schema": SCHEMA,
            "scope": [str(scope.route_id), str(scope.shop_id),
                      str(scope.lead_id), str(scope.case_id)],
            "events": [_event_view(x) for x in events],
            "epoch_claims": [{
                "closure_id": str(x.closure_id),
                "closure_event_id": str(x.closure_event_id),
                "f03_event_id": str(x.f03_event_id),
                "f02_event_id": str(x.f02_event_id),
                "versions": list(x.versions),
            } for x in epoch_claims],
            "updates": [_version_view(x) for x in version_updates],
            "evidence": {key: str(value) if isinstance(value, UUID)
                         else value for key, value in ((f.name, getattr(evidence, f.name))
                          for f in fields(evidence))},
            "proposal": {key: str(value) if isinstance(value, UUID)
                         else _instant(value) if isinstance(value, datetime)
                         else value for key, value in ((f.name, getattr(proposal, f.name))
                          for f in fields(proposal))},
            "window": [_instant(window.requested_at), _instant(window.expires_at)],
            "proof_packet": proof_packet,
            "s2_visits": s2_visits,
            "synthetic_person_id": synthetic_person_id,
        }
        # Avoid an incomplete receipt if any JSON shape cannot be serialized.
        fingerprint = _digest(snapshot)
        claim_by_event = {claim.event_id: claim for claim in version_updates}
        # Only the current closure episode is idempotency-scoped. Prior
        # episodes remain in the route snapshot but must not make a future
        # human closure look like illegal reuse of its own history.
        last_f03_id = epoch_claims[-1].f03_event_id
        last_f02_id = epoch_claims[-1].f02_event_id
        index_f03 = next(i for i, ev in enumerate(events)
                         if ev.event_id == last_f03_id)
        index_f02 = next(i for i, ev in enumerate(events)
                         if ev.event_id == last_f02_id)
        event_hashes = tuple(
            (event.event_id, _digest({
                "event": _event_view(event),
                "claim": _version_view(claim_by_event[event.event_id]),
            }))
            for event in events[index_f03+1:index_f02]
            if event.event_id in claim_by_event)
    except (ValueError, TypeError, AttributeError, OverflowError):
        return out(ReplayStatus.DENIED_MALFORMED)

    last_epoch = epoch_claims[-1]
    candidate = ReplayObservation(
        schema=SCHEMA, source_state=SOURCE_STATE,
        route_id=scope.route_id, shop_id=scope.shop_id,
        lead_id=scope.lead_id, case_id=scope.case_id,
        closure_id=last_epoch.closure_id,
        f03_event_id=last_epoch.f03_event_id,
        f02_event_id=last_epoch.f02_event_id,
        channel_id=proposal.channel_id,
        idempotency_key=proposal.idempotency_key,
        payload_sha256=fingerprint, event_digests=event_hashes,
    )
    identity = _request_identity(candidate)
    for prior in prior_observations:
        if _request_identity(prior) == identity:
            if prior == candidate:
                return out(ReplayStatus.IDENTICAL_REPLAY_NO_NEW_ACTION,
                           candidate)
            return out(ReplayStatus.REQUEST_CONFLICT_RECHECK_REQUIRED)
        # Same claimed update event may not be reused for a different request
        # even if its hash happens to match. This is local-only detection.
        old_ids = {i for i, _ in prior.event_digests}
        if any(i in old_ids for i, _ in candidate.event_digests):
            return out(ReplayStatus.EVENT_ID_REUSE_RECHECK_REQUIRED)
        if ((prior.shop_id, prior.channel_id, prior.idempotency_key)
            == (candidate.shop_id, candidate.channel_id,
                candidate.idempotency_key)):
            return out(ReplayStatus.IDEMPOTENCY_KEY_RECHECK_REQUIRED)
    return out(ReplayStatus.NEW_CHAIN_CANDIDATE_ONLY, candidate)
