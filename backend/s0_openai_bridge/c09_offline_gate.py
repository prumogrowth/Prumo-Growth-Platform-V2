"""Fail-closed C09 evidence review, exclusively for synthetic S0/OpenAI tests.

NOT deployed, not used by commercial flows, and does not implement C09 status
changes. The S0 domain must ratify state eligibility before any real ALLOW.
WhatsApp/Meta owns authentication and correlation of provider evidence; this
module only checks already-labelled synthetic observations. A true flag supplied
here is NOT proof of a Meta event in a real environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class Decision(str, Enum):
    DENY = "DENY"
    NOT_READY = "NOT_READY"
    POLICY_PENDING = "POLICY_PENDING"


@dataclass(frozen=True)
class Observation:
    case_store: str
    case_id: str
    commercial_status: str
    human_handoff: bool
    plan_active: bool
    opt_out: bool
    final_template_is_separate: bool
    final_event_store: str
    final_event_case: str
    final_event_kind: str
    final_event_authenticated: bool
    final_sent_at: datetime | None
    latest_customer_inbound_at: datetime | None
    observed_at: datetime


HARD_DENY = frozenset({"cadastro enviado ao banco", "vendido", "perdido"})
KNOWN_STATUS = frozenset({
    "aguardando primeiro disparo", "primeiro disparo enviado",
    "em atendimento pela IA", "em atendimento pelo operador",
    "cadastro enviado ao operador", "cadastro enviado ao banco",
    "vendido", "perdido",
})


def _aware(dt: datetime | None) -> bool:
    return dt is not None and dt.tzinfo is not None and dt.utcoffset() is not None


def evaluate_c09(observation: Observation) -> Decision:
    """Never returns ALLOW; physical status transition remains exclusively S0.

    Evidence is fictitious. A future S0 integration MUST bind all inputs to
    authenticated case snapshots, validated Meta callbacks and an approved
    domain policy; never accept this dataclass directly from a web client.
    """
    o = observation
    if (not o.case_store or not o.case_id or not isinstance(o.commercial_status, str)
            or o.commercial_status not in KNOWN_STATUS
            or o.commercial_status in HARD_DENY or o.opt_out):
        return Decision.DENY
    if not o.plan_active or not o.final_template_is_separate:
        return Decision.NOT_READY
    if (o.final_event_store != o.case_store or o.final_event_case != o.case_id
            or not o.final_event_authenticated or o.final_event_kind != "sent"):
        return Decision.NOT_READY
    if not _aware(o.final_sent_at) or not _aware(o.observed_at):
        return Decision.NOT_READY
    if o.latest_customer_inbound_at is not None and not _aware(o.latest_customer_inbound_at):
        return Decision.NOT_READY
    if o.final_sent_at > o.observed_at:
        return Decision.NOT_READY
    if o.latest_customer_inbound_at is not None:
        if o.latest_customer_inbound_at > o.observed_at:
            return Decision.NOT_READY
        if o.latest_customer_inbound_at >= o.final_sent_at:
            return Decision.NOT_READY
    if o.observed_at - o.final_sent_at < timedelta(hours=24):
        return Decision.NOT_READY
    # Even perfect synthetic evidence cannot approve human-stage C09. Nor does
    # a seller-stage observation authorize a transition without domain policy.
    return Decision.POLICY_PENDING
