"""F01 synthetic sales_reply gate; proposals for S0 review, NEVER send.

Uses invented trusted fixtures, not actual S0 grants/Meta state. No bank claims,
commercial facts or actual text-safety compliance are decided by this module.
A provider response is not a permission to speak, make offers or send a message.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class F01Status(str, Enum):
    DENIED = "DENIED"
    STALE = "STALE"
    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    REVIEW_ONLY = "REVIEW_ONLY"


@dataclass(frozen=True)
class F01Capture:
    store: str
    case: str
    cycle: str
    request_id: str
    case_version: int
    message_watermark: str
    knowledge_version: str
    prompt_version: str
    allowed_message_refs: tuple[str, ...]


@dataclass(frozen=True)
class F01Current:
    store: str
    case: str
    cycle: str
    case_version: int
    message_watermark: str
    knowledge_version: str
    prompt_version: str
    session_authorized: bool
    store_authorized: bool
    ai_is_owner: bool
    ai_suspended: bool
    has_handoff_history: bool
    opted_out: bool
    purpose: str


@dataclass(frozen=True)
class F01ModelProposal:
    request_id: str
    operation_kind: str
    proposed_text: str
    source_message_refs: tuple[str, ...]


@dataclass(frozen=True)
class F01Review:
    status: F01Status
    review_text: str = ""
    source_message_refs: tuple[str, ...] = ()


def review_f01_offline(
    captured: F01Capture, current: F01Current, proposal: object
) -> F01Review:
    """Fail closed; REVIEW_ONLY still requires authoritative S0 recheck.

    A valid review cannot publish to Meta or call an LLM. No natural-language
    verification is made of promises, bank claims, numbers or opt-out phrases.
    """
    denied = F01Review(F01Status.DENIED)
    if not isinstance(captured, F01Capture) or not isinstance(current, F01Current):
        return denied
    flags = (current.session_authorized, current.store_authorized,
             current.ai_is_owner, current.ai_suspended,
             current.has_handoff_history, current.opted_out)
    if any(type(flag) is not bool for flag in flags):
        return denied
    identifiers = (captured.store, captured.case, captured.cycle, captured.request_id,
                   captured.message_watermark, captured.knowledge_version,
                   captured.prompt_version, current.store, current.case,
                   current.cycle, current.message_watermark, current.knowledge_version,
                   current.prompt_version)
    if any(type(v) is not str or not v or len(v) > 128 for v in identifiers):
        return denied
    if (captured.store != current.store or captured.case != current.case
            or captured.cycle != current.cycle or not current.session_authorized
            or not current.store_authorized or not current.ai_is_owner
            or current.ai_suspended or current.has_handoff_history
            or current.opted_out or current.purpose != "sales_reply"):
        return denied
    if (type(captured.case_version) is not int or captured.case_version < 1
            or type(current.case_version) is not int or current.case_version < 1):
        return denied
    if (captured.case_version != current.case_version
            or captured.message_watermark != current.message_watermark
            or captured.knowledge_version != current.knowledge_version
            or captured.prompt_version != current.prompt_version):
        return F01Review(F01Status.STALE)
    if (type(captured.allowed_message_refs) is not tuple or
            not captured.allowed_message_refs or
            any(type(v) is not str or not v or len(v) > 128
                for v in captured.allowed_message_refs) or
            len(set(captured.allowed_message_refs)) != len(captured.allowed_message_refs)):
        return denied
    if not isinstance(proposal, F01ModelProposal):
        return F01Review(F01Status.INVALID_PROPOSAL)
    if (type(proposal.request_id) is not str or
            proposal.request_id != captured.request_id or
            type(proposal.operation_kind) is not str or
            proposal.operation_kind != "sales_reply" or
            type(proposal.proposed_text) is not str or
            not proposal.proposed_text.strip() or
            len(proposal.proposed_text) > 2000 or
            type(proposal.source_message_refs) is not tuple or
            not proposal.source_message_refs or
            len(proposal.source_message_refs) > 24 or
            any(type(v) is not str or v not in captured.allowed_message_refs
                for v in proposal.source_message_refs) or
            len(set(proposal.source_message_refs)) != len(proposal.source_message_refs)):
        return F01Review(F01Status.INVALID_PROPOSAL)
    # A plain string cannot certify that invented model statements are legal,
    # bank-approved or safe. Retain only in restricted offline review output.
    return F01Review(F01Status.REVIEW_ONLY, proposal.proposed_text,
                     proposal.source_message_refs)
