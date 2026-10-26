"""F02 E04 post-human reconciliation: isolated authorization REVIEW handoff.

No import from S0, no database, no transport, no approval capability.

The input evidence is UNTRUSTED and its asserted S0 states cannot be used as
proof by the S0 authority. A handoff digest provides deterministic identity
for a *request to review*, not authenticity, permission, or a signed receipt.
S0/Codex must independently authenticate the principal, check scoped
database evidence, revoke/opt-out, Meta disposition, policy, and explicitly
ratify any subsequent operational authorization.

This module deliberately has NO 'approve', 'schedule', 'send', or 'persist'.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import re
from uuid import UUID


CONTRACT_VERSION = "F02_S0_RECONCILED_HUMAN_HANDOFF_V1"
LAB_SOURCE = "E04_SYNTHETIC_S0_C08_REVIEW"
LOCAL_RECONCILED = "LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY"
LOCAL_ORIGIN = "LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY"
UNVERIFIED_EXTERNAL = "EXTERNAL_DISPATCH_UNVERIFIED"
UNRATIFIED_HUMAN = "HUMAN_OPERATIONAL_AUTHORIZATION_NOT_RATIFIED"
REQUEST_ONLY = "REQUEST_S0_HUMAN_RATIFICATION_ONLY"
_HEX = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_KEY = re.compile(r"[A-Za-z0-9._:-]{8,128}\Z", re.ASCII)
_VERSION = re.compile(r"[A-Za-z0-9._:-]{4,80}\Z", re.ASCII)


class HandoffState(str, Enum):
    HANDOFF_REVIEW_ONLY = "HANDOFF_REVIEW_ONLY"
    DENIED_MALFORMED = "DENIED_MALFORMED"
    S0_RECONCILIATION_REQUIRED = "S0_RECONCILIATION_REQUIRED"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    EXTERNAL_DISPOSITION_NOT_ATTESTED = "EXTERNAL_DISPOSITION_NOT_ATTESTED"
    OPERATIONAL_RATIFICATION_NOT_ATTESTED = "OPERATIONAL_RATIFICATION_NOT_ATTESTED"


@dataclass(frozen=True, slots=True)
class ClaimedS0Evidence:
    # These are claims for independent S0 verification, NOT S0 proof tokens.
    shop_id: UUID
    lead_id: UUID
    case_id: UUID
    closure_id: UUID
    reconciliation_state: str
    origin_state: str
    source: str
    f03_receipt_sha256: str
    c08_local_witness_sha256: str
    origin_ledger_sha256: str
    human_intent_sha256: str
    external_disposition: str
    human_operational_ratification: str


@dataclass(frozen=True, slots=True)
class ReviewOnlyProposal:
    shop_id: UUID
    lead_id: UUID
    case_id: UUID
    closure_id: UUID
    channel_id: UUID
    template_id: UUID
    template_version: str
    policy_version: str
    proposed_at: datetime
    idempotency_key: str
    action: str


@dataclass(frozen=True, slots=True)
class HandoffResult:
    status: HandoffState
    # This is ONLY the hash of an untrusted request, not a MAC or signature.
    untrusted_request_sha256: str | None = None
    contract_version: str = CONTRACT_VERSION


def _uuid(value: object) -> bool:
    return type(value) is UUID and value.int != 0


def _digest(value: object) -> bool:
    return type(value) is str and _HEX.fullmatch(value) is not None


def _match(regex: re.Pattern[str], value: object) -> bool:
    return type(value) is str and regex.fullmatch(value) is not None


def prepare_handoff(
    evidence: ClaimedS0Evidence,
    proposal: ReviewOnlyProposal,
) -> HandoffResult:
    """Prepare a non-authorizing, deterministic packet for Codex/S0 review.

    No call to an S0 service is made. An 'HANDOFF_REVIEW_ONLY' response is
    NOT an authorization and must not be converted into an approval boolean.
    """
    denied = HandoffResult(HandoffState.DENIED_MALFORMED)
    if type(evidence) is not ClaimedS0Evidence or type(proposal) is not ReviewOnlyProposal:
        return denied
    scope_e = (evidence.shop_id, evidence.lead_id,
               evidence.case_id, evidence.closure_id)
    scope_p = (proposal.shop_id, proposal.lead_id,
               proposal.case_id, proposal.closure_id)
    if not all(_uuid(x) for x in scope_e + scope_p +
               (proposal.channel_id, proposal.template_id)):
        return denied
    if scope_e != scope_p:
        return HandoffResult(HandoffState.SCOPE_MISMATCH)
    if not all(_digest(x) for x in (
        evidence.f03_receipt_sha256,
        evidence.c08_local_witness_sha256,
        evidence.origin_ledger_sha256,
        evidence.human_intent_sha256,
    )):
        return denied
    if (not _match(_VERSION, proposal.template_version)
        or not _match(_VERSION, proposal.policy_version)
        or not _match(_KEY, proposal.idempotency_key)
        or type(proposal.proposed_at) is not datetime
        or proposal.proposed_at.tzinfo is None
        or proposal.proposed_at.utcoffset() is None
        or type(proposal.action) is not str
        or proposal.action != REQUEST_ONLY
        or type(evidence.source) is not str):
        return denied
    if (evidence.source != LAB_SOURCE
        or evidence.reconciliation_state != LOCAL_RECONCILED
        or evidence.origin_state != LOCAL_ORIGIN):
        return HandoffResult(HandoffState.S0_RECONCILIATION_REQUIRED)
    # A claimed externally verified or approved status does NOT elevate the
    # request. It must be validated by S0 itself through a future contract.
    if evidence.external_disposition != UNVERIFIED_EXTERNAL:
        return HandoffResult(HandoffState.EXTERNAL_DISPOSITION_NOT_ATTESTED)
    if evidence.human_operational_ratification != UNRATIFIED_HUMAN:
        return HandoffResult(HandoffState.OPERATIONAL_RATIFICATION_NOT_ATTESTED)
    packet = {
        "action": REQUEST_ONLY,
        "contract": CONTRACT_VERSION,
        "scope": [str(x) for x in scope_p],
        "channel_id": str(proposal.channel_id),
        "template": [str(proposal.template_id),
                     proposal.template_version, proposal.policy_version],
        "proposed_at_utc": proposal.proposed_at.astimezone(
            timezone.utc).isoformat(timespec="microseconds"),
        "idempotency_key": proposal.idempotency_key,
        "evidence": {
            "source": evidence.source,
            "reconciliation": evidence.reconciliation_state,
            "origin": evidence.origin_state,
            "f03_receipt_sha256": evidence.f03_receipt_sha256,
            "c08_local_witness_sha256": evidence.c08_local_witness_sha256,
            "origin_ledger_sha256": evidence.origin_ledger_sha256,
            "human_intent_sha256": evidence.human_intent_sha256,
            "external_disposition": evidence.external_disposition,
            "human_ratification": evidence.human_operational_ratification,
        },
    }
    digest = sha256(json.dumps(
        packet, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return HandoffResult(HandoffState.HANDOFF_REVIEW_ONLY, digest)
