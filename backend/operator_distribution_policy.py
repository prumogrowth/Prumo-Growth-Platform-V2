"""S0 candidate: selective pause allocation POLICY only, with no DB effects.

Input snapshots MUST originate from an authenticated, authorized and versioned
S0 transaction. This function does not grant access, authenticate identities,
change availability, assign cases, or write audit history.

Pause intake != suspend account. No reason, medical data, dates or SLA.
"""
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class CaseSnapshot:
    case_ref: str
    shop_ref: str
    owner_operator: str
    manager_ref: str
    assignment_version: str
    # Must come from durable proof of first operator/human interaction.
    # None means unverified; AI messages, opening or reading do not count.
    first_human_contact_confirmed: Optional[bool]
    # Terminal or historical cases must never be automatically reassigned.
    active_case_confirmed: bool = False


@dataclass(frozen=True)
class CandidateSnapshot:
    operator_ref: str
    manager_ref: str
    active_account: bool
    intake_receiving: bool
    granted_shops: Tuple[str, ...]


@dataclass(frozen=True)
class PauseRoutingProposal:
    disposition: str
    proposed_operator: Optional[str] = None
    # No changes to existing commercial status, assignment or grants.
    mutates_case: bool = False


def _reference(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_case(case: object) -> bool:
    return isinstance(case, CaseSnapshot) and all(_reference(value) for value in (
        case.case_ref, case.shop_ref, case.owner_operator, case.manager_ref,
        case.assignment_version,
    ))


def _valid_candidate(target: object) -> bool:
    return (
        isinstance(target, CandidateSnapshot)
        and _reference(target.operator_ref)
        and _reference(target.manager_ref)
        and isinstance(target.active_account, bool)
        and isinstance(target.intake_receiving, bool)
        and isinstance(target.granted_shops, tuple)
        and all(_reference(shop) for shop in target.granted_shops)
    )


def propose_selective_pause_case(
    case: CaseSnapshot,
    paused_operator: str,
    manager_ref: str,
    candidates: Tuple[CandidateSnapshot, ...],
) -> PauseRoutingProposal:
    """Pure proposal only; S1 must lock/version/authorize before any transfer."""
    if (
        not _valid_case(case)
        or not _reference(paused_operator)
        or not _reference(manager_ref)
        or case.owner_operator != paused_operator
        or case.manager_ref != manager_ref
        or not isinstance(candidates, tuple)
    ):
        return PauseRoutingProposal("DENIED_OR_UNVERIFIED")
    if case.active_case_confirmed is not True:
        return PauseRoutingProposal("RETAIN_NOT_ACTIVE_OR_UNVERIFIED")
    if case.first_human_contact_confirmed is True:
        return PauseRoutingProposal("RETAIN_STARTED")
    if case.first_human_contact_confirmed is not False:
        return PauseRoutingProposal("RETAIN_CONTACT_UNVERIFIED")
    for target in candidates:
        if not _valid_candidate(target):
            return PauseRoutingProposal("DENIED_OR_UNVERIFIED")
    eligible = sorted(
        {
            target.operator_ref
            for target in candidates
            if target.operator_ref
            and target.operator_ref != paused_operator
            and target.manager_ref == manager_ref
            and target.active_account is True
            and target.intake_receiving is True
            and isinstance(target.granted_shops, tuple)
            and case.shop_ref in target.granted_shops
        }
    )
    if not eligible:
        # New rule: do NOT unassign or send to an off-team operator.
        return PauseRoutingProposal("RETAIN_NO_SAME_TEAM_RECIPIENT")
    return PauseRoutingProposal("PROPOSE_SAME_TEAM_REASSIGNMENT", eligible[0])


def classify_manual_transfer_target(
    case: CaseSnapshot,
    manager_ref: str,
    target: CandidateSnapshot,
) -> str:
    """A missing shop grant requires an S1 case-scoped authorization path.

    The return value is NEVER a permission to execute a write. An S0/S1
    command must still verify actor/session, version and access in DB.
    """
    if (
        not _valid_case(case)
        or not _valid_candidate(target)
        or not _reference(manager_ref)
        or case.manager_ref != manager_ref
        or case.active_case_confirmed is not True
        or target.manager_ref != manager_ref
        or target.active_account is not True
        or target.intake_receiving is not True
        or not target.operator_ref
        or not case.assignment_version
    ):
        return "DENIED"
    if isinstance(target.granted_shops, tuple) and case.shop_ref in target.granted_shops:
        return "S1_STANDARD_AUTH_REQUIRED"
    return "S1_CASE_SCOPED_EXCEPTION_REQUIRED"
