"""Experimental F02/S0 proof-reference structural binding; NEVER source attestation.

All evidence, scope, references and timestamps are caller-supplied. This
function checks consistency of the *candidate description* of four proofs,
NOT their existence, HMAC validity, completeness, revocation or provenance.
Only a future S0 authenticated read of the physical producer can do that.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hmac import compare_digest
import re
from uuid import UUID

from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal, HandoffState, prepare_handoff,
)

SCHEMA = "prumo.f02.s0.claimed_proof_binding/0.1-lab"
SOURCE_STATE = "UNVERIFIED_CANDIDATE_ONLY"
AUTHORITY_STATE = "NO_S0_SOURCE_ATTESTATION"
_PROOF_SOURCES = {
    "f03_receipt_sha256": (
        "backend/s0_f03_history_manifest_local.py",
        "S0F03LocalHistoryManifestBridge.inspect",
    ),
    "c08_local_witness_sha256": (
        "backend/s0_f02_legacy_cancellation_witness_local.py",
        "S0F02LocalLegacyCancellationWitness.inspect_and_seal",
    ),
    "origin_ledger_sha256": (
        "backend/s0_f02_legacy_observed_origin_local.py",
        "S0F02LegacyObservedOriginBridge.inspect",
    ),
    "human_intent_sha256": (
        "backend/s0_f02_posthuman_intent_local.py",
        "S0F02LocalPostHumanIntentStore.record",
    ),
}
_PACKET_KEYS = frozenset((
    "schema", "scope", "closure_at", "handoff_sha256", "review_window", "proofs",
    "source_state", "source_authority", "s1_ratified", "meta_verified",
    "send_authorized",
))
_PROOF_KEYS = frozenset((
    "producer", "symbol", "source_ref", "source_revision",
    "canonicalization_version", "verifier_version", "digest_sha256",
    "observed_at", "cutoff_at", "scope", "source_state",
))
_SCOPE_KEYS = frozenset(("shop_id", "lead_id", "case_id", "closure_id"))
_HEX = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_REF = re.compile(r"[A-Za-z0-9._:-]{8,128}\Z", re.ASCII)
_VER = re.compile(r"[A-Za-z0-9._:-]{2,80}\Z", re.ASCII)
_REV = re.compile(r"[1-9][0-9]{0,17}\Z", re.ASCII)


class ProofBindingGate(str, Enum):
    CANDIDATE_CONSISTENT_NOT_ATTESTED = "CANDIDATE_CONSISTENT_NOT_ATTESTED"
    DENIED_MALFORMED = "DENIED_MALFORMED"
    SOURCE_CONTRACT_RECHECK_REQUIRED = "SOURCE_CONTRACT_RECHECK_REQUIRED"
    SCOPE_RECHECK_REQUIRED = "SCOPE_RECHECK_REQUIRED"
    HANDOFF_RECHECK_REQUIRED = "HANDOFF_RECHECK_REQUIRED"
    DIGEST_RECHECK_REQUIRED = "DIGEST_RECHECK_REQUIRED"
    TEMPORAL_RECHECK_REQUIRED = "TEMPORAL_RECHECK_REQUIRED"
    WINDOW_RECHECK_REQUIRED = "WINDOW_RECHECK_REQUIRED"


@dataclass(frozen=True, slots=True)
class ProofBindingResult:
    status: ProofBindingGate


def _time(x: object) -> datetime | None:
    if type(x) is not str:
        return None
    try:
        stamp = datetime.fromisoformat(x)
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            return None
        return stamp.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def _scope(x: object, ids: tuple[UUID, ...]) -> bool:
    if type(x) is not dict or frozenset(x) != _SCOPE_KEYS:
        return False
    return all(type(x.get(k)) is str and x[k] == str(v)
               for k, v in zip(("shop_id", "lead_id", "case_id", "closure_id"), ids))


def inspect_claimed_proof_binding(
    evidence: ClaimedS0Evidence,
    proposal: ReviewOnlyProposal,
    window: ReviewWindow,
    packet: dict,
) -> ProofBindingResult:
    """Structure/correlation-only gate; no database, signature, send or approval.

    Even a matching time window is caller supplied and cannot be trusted.
    Every source ID/revision, even a locally consistent one, remains entirely
    unauthenticated. In particular C08 local cancellation is not Meta cancel,
    and a synthetic manager intent is not human operational ratification.
    """
    def out(status: ProofBindingGate) -> ProofBindingResult:
        return ProofBindingResult(status)

    if (type(evidence) is not ClaimedS0Evidence
        or type(proposal) is not ReviewOnlyProposal
        or type(window) is not ReviewWindow
        or type(packet) is not dict
        or frozenset(packet) != _PACKET_KEYS):
        return out(ProofBindingGate.DENIED_MALFORMED)
    if (packet["schema"] != SCHEMA
        or packet["source_state"] != SOURCE_STATE
        or packet["source_authority"] != AUTHORITY_STATE
        or packet["s1_ratified"] is not False
        or packet["meta_verified"] is not False
        or packet["send_authorized"] is not False):
        return out(ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    handoff = prepare_handoff(evidence, proposal)
    if (handoff.status is not HandoffState.HANDOFF_REVIEW_ONLY
        or type(packet["handoff_sha256"]) is not str
        or _HEX.fullmatch(packet["handoff_sha256"]) is None
        or not compare_digest(handoff.untrusted_request_sha256,
                               packet["handoff_sha256"])):
        return out(ProofBindingGate.HANDOFF_RECHECK_REQUIRED)

    # The F02 unsigned handoff hash does NOT include the original time window.
    # S0's persisted document does. Compare UTC instants before proceeding.
    # Neither this window nor the rest of the packet is authenticated.
    original = packet["review_window"]
    if (type(original) is not dict
        or set(original) != {"requested_at", "expires_at"}
        or type(window.requested_at) is not datetime
        or type(window.expires_at) is not datetime
        or window.requested_at.tzinfo is None
        or window.requested_at.utcoffset() is None
        or window.expires_at.tzinfo is None
        or window.expires_at.utcoffset() is None):
        return out(ProofBindingGate.WINDOW_RECHECK_REQUIRED)
    requested, expires = _time(original["requested_at"]), _time(original["expires_at"])
    start = window.requested_at.astimezone(timezone.utc)
    end = window.expires_at.astimezone(timezone.utc)
    if (requested is None or expires is None
        or not start < end or requested != start or expires != end):
        return out(ProofBindingGate.WINDOW_RECHECK_REQUIRED)

    ids = (evidence.shop_id, evidence.lead_id,
           evidence.case_id, evidence.closure_id)
    if not _scope(packet["scope"], ids):
        return out(ProofBindingGate.SCOPE_RECHECK_REQUIRED)

    closure = _time(packet["closure_at"])
    proposed = proposal.proposed_at.astimezone(timezone.utc)
    if closure is None or closure > proposed:
        return out(ProofBindingGate.TEMPORAL_RECHECK_REQUIRED)

    proofs = packet["proofs"]
    if type(proofs) is not dict or frozenset(proofs) != frozenset(_PROOF_SOURCES):
        return out(ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)

    for field, (expected_path, expected_symbol) in _PROOF_SOURCES.items():
        p = proofs[field]
        if type(p) is not dict or frozenset(p) != _PROOF_KEYS:
            return out(ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)
        if (type(p["producer"]) is not str
            or p["producer"] != expected_path
            or type(p["symbol"]) is not str
            or p["symbol"] != expected_symbol
            or p["source_state"] != SOURCE_STATE
            or type(p["source_ref"]) is not str
            or _REF.fullmatch(p["source_ref"]) is None
            or type(p["source_revision"]) is not str
            or _REV.fullmatch(p["source_revision"]) is None
            or type(p["canonicalization_version"]) is not str
            or _VER.fullmatch(p["canonicalization_version"]) is None
            or type(p["verifier_version"]) is not str
            or _VER.fullmatch(p["verifier_version"]) is None):
            return out(ProofBindingGate.SOURCE_CONTRACT_RECHECK_REQUIRED)
        if not _scope(p["scope"], ids):
            return out(ProofBindingGate.SCOPE_RECHECK_REQUIRED)
        digest = p["digest_sha256"]
        if (type(digest) is not str or _HEX.fullmatch(digest) is None
            or not compare_digest(digest, getattr(evidence, field))):
            return out(ProofBindingGate.DIGEST_RECHECK_REQUIRED)
        seen, cutoff = _time(p["observed_at"]), _time(p["cutoff_at"])
        if (seen is None or cutoff is None or not
            (closure <= seen <= cutoff <= proposed)):
            return out(ProofBindingGate.TEMPORAL_RECHECK_REQUIRED)

    return out(ProofBindingGate.CANDIDATE_CONSISTENT_NOT_ATTESTED)
