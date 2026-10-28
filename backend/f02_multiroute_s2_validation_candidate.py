"""E04 route plus original pinned S2 F01/F02/F03 validators (lab ONLY).

Runs the unchanged pinned S2 core.mjs with Node from the local CI checkout.
No OpenAI API, Supabase hosted, S0 authority, Meta, send, PII, or mutations.
The S2 true/false fixture flags are NOT actual session/role attestations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path
import subprocess

from backend.f01_f02_f03_route_ledger_candidate import (
    RouteEvent, RouteKind, RouteScope,
)
from backend.f02_reconciled_human_authorization_handoff import (
    ClaimedS0Evidence, ReviewOnlyProposal,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_multiroute_proof_gate_candidate import (
    RoutedProofStatus, check_routed_posthuman_proof,
)

ROOT = Path(__file__).resolve().parent  # backend; ROOT.parent is repository
NODE_CLI = ROOT / "tests/s2_pinned_route_validator.mjs"
S2_SOURCE = ROOT.parent / ".s2-e04-source/docs/integracoes/openai/e04_offline_lab/core.mjs"
CI_PIN = "ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c"
_MAX_PAYLOAD = 65536


class S2RouteStatus(str, Enum):
    MULTIROUTE_AND_S2_SHAPE_RECHECK_ONLY = "MULTIROUTE_AND_S2_SHAPE_RECHECK_ONLY"
    DENIED_MALFORMED = "DENIED_MALFORMED"
    ROUTE_OR_F02_PROOF_RECHECK_REQUIRED = "ROUTE_OR_F02_PROOF_RECHECK_REQUIRED"
    STAGE_BINDING_RECHECK_REQUIRED = "STAGE_BINDING_RECHECK_REQUIRED"
    S2_VALIDATION_RECHECK_REQUIRED = "S2_VALIDATION_RECHECK_REQUIRED"
    S2_PINNED_RUNTIME_UNAVAILABLE = "S2_PINNED_RUNTIME_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class S2RouteResult:
    status: S2RouteStatus


def _stages(events: tuple[RouteEvent, ...]) -> list[tuple[str, RouteEvent]]:
    kinds = {
        RouteKind.F01_OPEN: "F01",
        RouteKind.S0_F01_RESUME_REQUEST: "F01",
        RouteKind.S0_F02_PREHUMAN_REQUEST: "F02",
        RouteKind.S0_F02_POSTHUMAN_REQUEST: "F02",
        RouteKind.F03_PROPOSAL: "F03",
    }
    return [(kinds[event.kind], event) for event in events if event.kind in kinds]


def check_routed_proof_with_pinned_s2(
    scope: RouteScope,
    events: tuple[RouteEvent, ...],
    evidence: ClaimedS0Evidence,
    proposal: ReviewOnlyProposal,
    window: ReviewWindow,
    proof_packet: dict,
    s2_visits: tuple[dict, ...],
    synthetic_person_id: str,
) -> S2RouteResult:
    """Checks stage *claims* against the actual S2 JS functions at pinned SHA.

    Positive means all synthetic stage candidates passed shape and S2
    validators; it CANNOT authorize model prompts, send, schedule, or DB writes.
    """
    def result(status: S2RouteStatus) -> S2RouteResult:
        return S2RouteResult(status)

    if (type(scope) is not RouteScope or type(events) is not tuple
        or type(s2_visits) is not tuple
        or type(synthetic_person_id) is not str
        or not 1 <= len(synthetic_person_id) <= 100):
        return result(S2RouteStatus.DENIED_MALFORMED)
    route = check_routed_posthuman_proof(
        scope, events, evidence, proposal, window, proof_packet)
    if route.status is not RoutedProofStatus.F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY:
        return result(S2RouteStatus.ROUTE_OR_F02_PROOF_RECHECK_REQUIRED)

    expected = _stages(events)
    if len(expected) != len(s2_visits):
        return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)
    body: list[dict] = []
    for (stage, event), item in zip(expected, s2_visits):
        if (type(item) is not dict or set(item) != {"stage", "req", "proposal"}
            or item.get("stage") != stage
            or type(item.get("req")) is not dict
            or type(item.get("proposal")) is not dict):
            return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)
        req = item["req"]
        current_scope = req.get("scope")
        if (type(current_scope) is not dict
            or current_scope.get("storeId") != str(scope.shop_id)
            or current_scope.get("caseId") != str(scope.case_id)):
            return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)

        if stage == "F01":
            if (req.get("owner") != "ai" or req.get("handoff") is not False
                or req.get("humanized") is not False):
                return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)
        elif stage == "F02":
            if event.kind is RouteKind.S0_F02_PREHUMAN_REQUEST:
                if (req.get("purpose") != "pre_human"
                    or req.get("ownerRoute") != "seller_ai"):
                    return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)
            else:
                if (req.get("purpose") != "post_human"
                    or req.get("ownerRoute") != "human"):
                    return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)
                entries = item["proposal"].get("attempts")
                last = item["proposal"].get("finalTemplate")
                if type(entries) is not list:
                    return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)
                selected = list(entries) + ([] if last is None else [last])
                if not any(
                    type(x) is dict
                    and x.get("templateId") == str(proposal.template_id)
                    and x.get("version") == proposal.template_version
                    for x in selected
                ):
                    return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)
        else:
            if (req.get("closureId") != str(event.closure_id)
                or req.get("personId") != synthetic_person_id):
                return result(S2RouteStatus.STAGE_BINDING_RECHECK_REQUIRED)
            # The original journey.mjs treats even a structurally valid
            # withdrawal/loss advisory as HUMAN review, not an F02 trigger.
            # validateF03Proposal alone returns PROPOSED for some advisories.
            if (item["proposal"].get("commercialAdvisory", ...) is not None):
                return result(S2RouteStatus.S2_VALIDATION_RECHECK_REQUIRED)
        body.append(item)

    if not S2_SOURCE.is_file() or not NODE_CLI.is_file():
        return result(S2RouteStatus.S2_PINNED_RUNTIME_UNAVAILABLE)
    try:
        packed = json.dumps({"steps": body}, allow_nan=False,
                            ensure_ascii=True, separators=(",", ":"))
        if len(packed.encode("utf-8")) > _MAX_PAYLOAD:
            return result(S2RouteStatus.DENIED_MALFORMED)
        executed = subprocess.run(
            ["node", str(NODE_CLI)], input=packed, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd=ROOT.parent, timeout=10, check=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
        if executed.returncode != 0 or len(executed.stdout) > 65536:
            return result(S2RouteStatus.S2_PINNED_RUNTIME_UNAVAILABLE)
        response = json.loads(executed.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
        return result(S2RouteStatus.S2_PINNED_RUNTIME_UNAVAILABLE)
    if (type(response) is not dict or set(response) != {"results"}
        or type(response["results"]) is not list
        or len(response["results"]) != len(expected)):
        return result(S2RouteStatus.S2_VALIDATION_RECHECK_REQUIRED)
    for item, (stage, _event) in zip(response["results"], expected):
        if (type(item) is not dict or set(item) != {"stage", "status"}
            or item["stage"] != stage or item["status"] != "PROPOSED"):
            return result(S2RouteStatus.S2_VALIDATION_RECHECK_REQUIRED)
    return result(S2RouteStatus.MULTIROUTE_AND_S2_SHAPE_RECHECK_ONLY)
