"""E04 OpenAI F01/F02/F03: pure multi-route ledger candidate, never an S0 authority.

Unlike the older single-route synthetic 'journey.mjs', this lab reducer may
visit F01 and pre-human F02 multiple times before a distinct human closure
leads to F03 and optional post-human F02 review. Events, scopes, timestamps
and alleged S0 requests are ALL caller-supplied, hence NEVER authorization.
No model call, DB, Meta send, scheduler, permission or business mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

SCHEMA = "prumo.openai.f01_f02_f03.route_ledger/0.1-lab"
UNTRUSTED_SOURCE = "E04_SYNTHETIC_ROUTE_CLAIM_ONLY"
MAX_EVENTS = 64


class RouteKind(str, Enum):
    F01_OPEN = "F01_OPEN"
    S0_F02_PREHUMAN_REQUEST = "S0_F02_PREHUMAN_REQUEST"
    CUSTOMER_INBOUND = "CUSTOMER_INBOUND"
    S0_PREHUMAN_F02_RECONCILED = "S0_PREHUMAN_F02_RECONCILED"
    S0_F01_RESUME_REQUEST = "S0_F01_RESUME_REQUEST"
    S0_HUMAN_HANDOFF = "S0_HUMAN_HANDOFF"
    S0_HUMAN_CLOSURE = "S0_HUMAN_CLOSURE"
    F03_PROPOSAL = "F03_PROPOSAL"
    S0_F02_POSTHUMAN_REQUEST = "S0_F02_POSTHUMAN_REQUEST"
    S0_HUMAN_REOPEN_REQUEST = "S0_HUMAN_REOPEN_REQUEST"
    META_EXTERNAL_OUTCOME_UNCERTAIN = "META_EXTERNAL_OUTCOME_UNCERTAIN"
    OPT_OUT = "OPT_OUT"


class RouteStage(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    F01 = "F01"
    F02_PREHUMAN = "F02_PREHUMAN"
    F02_PREHUMAN_INBOUND = "F02_PREHUMAN_INBOUND"
    F02_PREHUMAN_RECONCILED = "F02_PREHUMAN_RECONCILED"
    HUMAN = "HUMAN"
    HUMAN_CLOSED = "HUMAN_CLOSED"
    F03 = "F03"
    F02_POSTHUMAN = "F02_POSTHUMAN"
    F02_POSTHUMAN_INBOUND = "F02_POSTHUMAN_INBOUND"
    META_UNCERTAIN_HOLD = "META_UNCERTAIN_HOLD"
    OPTED_OUT = "OPTED_OUT"


class RouteStatus(str, Enum):
    ROUTE_SHAPE_RECHECK_ONLY = "ROUTE_SHAPE_RECHECK_ONLY"
    DENIED_MALFORMED = "DENIED_MALFORMED"
    SCOPE_RECHECK_REQUIRED = "SCOPE_RECHECK_REQUIRED"
    EVENT_ORDER_RECHECK_REQUIRED = "EVENT_ORDER_RECHECK_REQUIRED"
    TRANSITION_RECHECK_REQUIRED = "TRANSITION_RECHECK_REQUIRED"
    HUMAN_ROUTE_RECHECK_REQUIRED = "HUMAN_ROUTE_RECHECK_REQUIRED"
    META_UNCERTAINTY_RECHECK_REQUIRED = "META_UNCERTAINTY_RECHECK_REQUIRED"


@dataclass(frozen=True, slots=True)
class RouteScope:
    route_id: UUID
    shop_id: UUID
    lead_id: UUID
    case_id: UUID


@dataclass(frozen=True, slots=True)
class RouteEvent:
    event_id: UUID
    route_id: UUID
    shop_id: UUID
    lead_id: UUID
    case_id: UUID
    sequence: int
    occurred_at: datetime
    kind: RouteKind
    claimed_source: str = UNTRUSTED_SOURCE
    closure_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RouteAssessment:
    status: RouteStatus
    # Diagnostic labels only. No token, action command or authorized status.
    current_stage: RouteStage | None = None
    openai_visits: tuple[str, ...] = ()


def _uuid(x: object) -> bool:
    return type(x) is UUID and x.int != 0


def _time(x: object) -> bool:
    return (type(x) is datetime and x.tzinfo is not None
            and x.utcoffset() is not None)


def classify_route_candidate(
    scope: RouteScope,
    events: tuple[RouteEvent, ...],
) -> RouteAssessment:
    """Classify an UNTRUSTED claimed route; no automatic handoffs or resumes.

    Event names prefixed S0 identify what a future S0-authenticated producer
    MUST attest, NOT actual signed S0 events. This function never verifies
    origin, timing, permissions, external disposition or human approval.
    """
    def reject(status: RouteStatus) -> RouteAssessment:
        return RouteAssessment(status)

    if (type(scope) is not RouteScope
        or not all(_uuid(x) for x in (scope.route_id, scope.shop_id,
                                     scope.lead_id, scope.case_id))
        or type(events) is not tuple or not 1 <= len(events) <= MAX_EVENTS):
        return reject(RouteStatus.DENIED_MALFORMED)
    stage = RouteStage.NOT_STARTED
    visits: list[str] = []
    active_closure: UUID | None = None
    used_ids: set[UUID] = set()
    previous_seq = 0
    previous_time: datetime | None = None
    expected_scope = (scope.route_id, scope.shop_id, scope.lead_id, scope.case_id)

    for event in events:
        if (type(event) is not RouteEvent
            or not _uuid(event.event_id)
            or type(event.sequence) is not int or event.sequence <= 0
            or type(event.kind) is not RouteKind
            or not _time(event.occurred_at)
            or event.claimed_source != UNTRUSTED_SOURCE
            or event.closure_id is not None and not _uuid(event.closure_id)):
            return reject(RouteStatus.DENIED_MALFORMED)
        if (event.route_id, event.shop_id, event.lead_id, event.case_id) != expected_scope:
            return reject(RouteStatus.SCOPE_RECHECK_REQUIRED)
        instant = event.occurred_at.astimezone(timezone.utc)
        if (event.event_id in used_ids
            or event.sequence <= previous_seq
            or previous_time is not None and instant < previous_time):
            return reject(RouteStatus.EVENT_ORDER_RECHECK_REQUIRED)
        used_ids.add(event.event_id)
        previous_seq, previous_time = event.sequence, instant

        kind = event.kind
        # Closure refs appear only in events directly tied to an actual
        # human-closure episode, not in pre-human seller/recontact traffic.
        if kind is RouteKind.S0_HUMAN_CLOSURE:
            if (stage is not RouteStage.HUMAN
                or not _uuid(event.closure_id)
                or event.closure_id == active_closure):
                return reject(RouteStatus.HUMAN_ROUTE_RECHECK_REQUIRED)
            active_closure = event.closure_id
            stage = RouteStage.HUMAN_CLOSED
            continue
        if kind in (RouteKind.F03_PROPOSAL,
                    RouteKind.S0_F02_POSTHUMAN_REQUEST,
                    RouteKind.S0_HUMAN_REOPEN_REQUEST):
            if active_closure is None or event.closure_id != active_closure:
                return reject(RouteStatus.HUMAN_ROUTE_RECHECK_REQUIRED)
        elif (stage in (RouteStage.F02_POSTHUMAN,
                        RouteStage.F02_POSTHUMAN_INBOUND)
              and kind in (RouteKind.CUSTOMER_INBOUND, RouteKind.OPT_OUT,
                           RouteKind.META_EXTERNAL_OUTCOME_UNCERTAIN)):
            if event.closure_id != active_closure:
                return reject(RouteStatus.HUMAN_ROUTE_RECHECK_REQUIRED)
        elif event.closure_id is not None:
            return reject(RouteStatus.HUMAN_ROUTE_RECHECK_REQUIRED)

        if stage is RouteStage.META_UNCERTAIN_HOLD:
            if kind is RouteKind.OPT_OUT:
                stage = RouteStage.OPTED_OUT
                continue
            return reject(RouteStatus.META_UNCERTAINTY_RECHECK_REQUIRED)
        if stage is RouteStage.OPTED_OUT:
            return reject(RouteStatus.TRANSITION_RECHECK_REQUIRED)
        if kind is RouteKind.OPT_OUT:
            stage = RouteStage.OPTED_OUT
        elif kind is RouteKind.META_EXTERNAL_OUTCOME_UNCERTAIN:
            if stage not in (RouteStage.F02_PREHUMAN,
                             RouteStage.F02_PREHUMAN_INBOUND,
                             RouteStage.F02_POSTHUMAN,
                             RouteStage.F02_POSTHUMAN_INBOUND):
                return reject(RouteStatus.TRANSITION_RECHECK_REQUIRED)
            stage = RouteStage.META_UNCERTAIN_HOLD
        elif kind is RouteKind.F01_OPEN and stage is RouteStage.NOT_STARTED:
            stage = RouteStage.F01
            visits.append("F01")
        elif kind is RouteKind.S0_F02_PREHUMAN_REQUEST and stage is RouteStage.F01:
            stage = RouteStage.F02_PREHUMAN
            visits.append("F02")
        elif kind is RouteKind.CUSTOMER_INBOUND:
            if stage is RouteStage.F02_PREHUMAN:
                stage = RouteStage.F02_PREHUMAN_INBOUND
            elif stage is RouteStage.F02_POSTHUMAN:
                stage = RouteStage.F02_POSTHUMAN_INBOUND
            else:
                return reject(RouteStatus.TRANSITION_RECHECK_REQUIRED)
        elif (kind is RouteKind.S0_PREHUMAN_F02_RECONCILED
              and stage is RouteStage.F02_PREHUMAN_INBOUND):
            stage = RouteStage.F02_PREHUMAN_RECONCILED
        elif kind is RouteKind.S0_F01_RESUME_REQUEST:
            # A customer reply alone can never resume F01. Nor can
            # post-human F02 reactivate the seller AI for a human case.
            if stage is not RouteStage.F02_PREHUMAN_RECONCILED:
                return reject(RouteStatus.HUMAN_ROUTE_RECHECK_REQUIRED)
            stage = RouteStage.F01
            visits.append("F01")
        elif (kind is RouteKind.S0_HUMAN_HANDOFF
              and stage in (RouteStage.F01,
                            RouteStage.F02_PREHUMAN_RECONCILED)):
            stage = RouteStage.HUMAN
        elif kind is RouteKind.F03_PROPOSAL and stage is RouteStage.HUMAN_CLOSED:
            stage = RouteStage.F03
            visits.append("F03")
        elif (kind is RouteKind.S0_F02_POSTHUMAN_REQUEST
              and stage is RouteStage.F03):
            stage = RouteStage.F02_POSTHUMAN
            visits.append("F02")
        elif (kind is RouteKind.S0_HUMAN_REOPEN_REQUEST
              and stage is RouteStage.F02_POSTHUMAN_INBOUND):
            stage = RouteStage.HUMAN
        else:
            return reject(RouteStatus.TRANSITION_RECHECK_REQUIRED)

    return RouteAssessment(RouteStatus.ROUTE_SHAPE_RECHECK_ONLY, stage, tuple(visits))
