"""Policy ratified by the project owner's manual-provisioning instruction.

Diagnostic only. This module cannot execute SQL or authenticate an operator.
"""
ACTIONS = frozenset(("APPOINT", "REVOKE", "REACTIVATE"))


def policy(action):
    if type(action) is not str or action not in ACTIONS | {"SUBSTITUTE"}:
        raise ValueError("I86M_UNKNOWN_ACTION")
    return {
        "version": "prumo.i86.manual-policy.v1",
        "state": "MANUAL_PRIVILEGED_ONLY",
        "ordinary_application_enabled": False,
        "mcp_or_agent_enabled": False,
        "manual_act_evidence_required": True,
        "numeric_director_limit": None,
        "continuity_details_pending": action == "SUBSTITUTE",
    }
