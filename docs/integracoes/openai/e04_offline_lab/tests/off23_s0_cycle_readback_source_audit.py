"""OFF23: executable forensic audit of the exact S0 F02 cycle readback function.

Loads only the readback AST node from a pinned S0 source (not reimplemented
readback). The cursor is a local synthetic object, NOT PostgreSQL; each
passing test records code behavior rather than operational correctness.
Two named tests intentionally reproduce a state mismatch accepted by the
candidate S0 lab. They are evidence of a possible defect, NOT a fix.
"""
from __future__ import annotations
import ast
from dataclasses import dataclass
import os
from pathlib import Path
import re
import unittest

PINNED_S0 = "054261b23b312421a6956b51ff5b37d36f10babb"
HASH = "a" * 64


@dataclass(frozen=True)
class HostActor:
    actor_ref: str = "ACTOR_A"
    store_ref: str = "store-A"
    service_ref: str = "M09_KEY_A"
    case_ref: str = "case_A"
    flow_ref: str = "flow_A"


NO_GRANT = dict(
    lab_only=True, host_authenticated=False,
    cycle_source_operational=False, consent_source_authenticated=False,
    schedule_authorized=False, send_authorized=False,
    graph_authorized=False, production_authorized=False,
)


def ident(value):
    return type(value) is str and bool(re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", value))


def reply(status, reason, **kwargs):
    return dict(contract_version="prumo.s0.f02-cycle-command/0.1-lab",
                status=status, reason=reason, **NO_GRANT, **kwargs)


def pinned_readback():
    path = Path(os.environ["S0_CYCLE_PINNED_SOURCE"])
    root = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    match = [node for node in root.body if isinstance(node, ast.FunctionDef)
             and node.name == "readback"]
    if len(match) != 1:
        raise AssertionError("Expected exactly one S0 cycle readback")
    # Compile the unaltered source function, with minimal inert test globals.
    module = ast.fix_missing_locations(ast.Module(body=match, type_ignores=[]))
    namespace = {"ident": ident, "HostActor": HostActor, "reply": reply, "re": re}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["readback"]


READBACK = pinned_readback()


class FakeCursor:
    """Covers only the 3 known readback SELECT shapes; no SQL semantics."""
    def __init__(self):
        self.event = dict(
            command_ref="cmd_1", case_ref="case_A", request_digest=HASH,
            actor_ref="ACTOR_A", actor_key_revision=1, after_revision=2,
            after_state="ACTIVE", action="ADVANCE",
        )
        self.authority = dict(
            case_ref="case_A", actor_ref="ACTOR_A", store_ref="store-A",
            service_ref="M09_KEY_A", flow_ref="flow_A",
            cycle_revision=2, last_command_ref="cmd_1", state="ACTIVE",
            actor_enabled=True, actor_key_revision=1,
        )
        self.source = dict(flow_ref="flow_A", cycle_revision=2)
        self.exc = False
        self.observed = []
        self.current = None

    def execute(self, sql, args=None):
        if self.exc:
            raise RuntimeError("Synthetic SQL unavailable")
        self.observed.append((sql, args))
        if "FROM s0_f02_cycle_lab.commands " in sql:
            self.current = self.event
        elif "FROM s0_f02_cycle_lab.authorities " in sql:
            self.current = self.authority
        elif "FROM s0_f02_lab.case_cycles " in sql:
            self.current = self.source
        else:
            raise AssertionError("Unexpected SELECT in pinned readback: " + sql[:110])
        return self

    def fetchone(self):
        return self.current

    def check(self, host=None, command="cmd_1", digest=HASH):
        return READBACK(self, command_ref=command, host=host or HostActor(),
                        request_hash=digest)


class CycleReadbackPinnedSourceReview(unittest.TestCase):
    def assert_no_grant(self, result):
        for k in NO_GRANT:
            self.assertEqual(result[k], NO_GRANT[k], k)

    def status(self, mutator, expected, reason=None):
        c = FakeCursor()
        if mutator:
            mutator(c)
        out = c.check()
        self.assertEqual(out["status"], expected, out)
        if reason is not None:
            self.assertEqual(out["reason"], reason)
        self.assert_no_grant(out)
        return out

    def test_01_matching_event_and_current_authority_yields_lab_readback(self):
        out = self.status(None, "LAB_COMMITTED_CYCLE_READBACK")
        self.assertEqual(out["state"], "ACTIVE")
        self.assertTrue(out["commit_verified"])

    def test_02_state_drift_to_paused_is_still_misclassified_as_committed(self):
        # AUD-OAI23-01: source function does NOT compare authority.state
        # with command.after_state. Test deliberately documents the bug.
        out = self.status(lambda c: c.authority.__setitem__("state", "PAUSED"),
                          "LAB_COMMITTED_CYCLE_READBACK")
        self.assertEqual(out["state"], "ACTIVE")

    def test_03_state_drift_to_revoked_is_still_misclassified_as_committed(self):
        out = self.status(lambda c: c.authority.__setitem__("state", "REVOKED"),
                          "LAB_COMMITTED_CYCLE_READBACK")
        self.assertEqual(out["state"], "ACTIVE")

    def test_04_journal_state_altered_but_same_revision_appears_committed(self):
        out = self.status(lambda c: c.event.__setitem__("after_state", "REVOKED"),
                          "LAB_COMMITTED_CYCLE_READBACK")
        self.assertEqual(out["state"], "REVOKED")

    def test_05_journal_actor_differs_but_receipt_appears_committed(self):
        # AUD-OAI23-02: event.actor_ref not compared against HostActor.
        self.status(lambda c: c.event.__setitem__("actor_ref", "OTHER_ACTOR"),
                    "LAB_COMMITTED_CYCLE_READBACK")

    def test_06_no_event_is_commit_unknown_not_success(self):
        self.status(lambda c: setattr(c, "event", None),
                    "LAB_COMMIT_UNKNOWN", "NO_DURABLE_EVENT")

    def test_07_authority_missing_is_denied(self):
        self.status(lambda c: setattr(c, "authority", None),
                    "DENIED", "SCOPE_CHANGED")

    def test_08_actor_ref_mismatch_is_denied(self):
        self.status(lambda c: c.authority.__setitem__("actor_ref", "OTHER"),
                    "DENIED", "SCOPE_CHANGED")

    def test_09_store_scope_mismatch_is_denied(self):
        self.status(lambda c: c.authority.__setitem__("store_ref", "store-B"),
                    "DENIED", "SCOPE_CHANGED")

    def test_10_service_scope_mismatch_is_denied(self):
        self.status(lambda c: c.authority.__setitem__("service_ref", "OTHER"),
                    "DENIED", "SCOPE_CHANGED")

    def test_11_case_scope_mismatch_is_denied(self):
        self.status(lambda c: c.authority.__setitem__("case_ref", "OTHER"),
                    "DENIED", "SCOPE_CHANGED")

    def test_12_flow_scope_mismatch_is_denied(self):
        self.status(lambda c: c.authority.__setitem__("flow_ref", "OTHER"),
                    "DENIED", "SCOPE_CHANGED")

    def test_13_wrong_request_hash_is_denied(self):
        c = FakeCursor()
        out = c.check(digest="b" * 64)
        self.assertEqual(out["status"], "DENIED")
        self.assertEqual(out["reason"], "COMMAND_COLLISION")
        self.assert_no_grant(out)

    def test_14_missing_cycle_source_is_denied(self):
        self.status(lambda c: setattr(c, "source", None),
                    "DENIED", "CYCLE_SOURCE_DIVERGED")

    def test_15_flow_changed_in_cycle_source_is_denied(self):
        self.status(lambda c: c.source.__setitem__("flow_ref", "flow_B"),
                    "DENIED", "CYCLE_SOURCE_DIVERGED")

    def test_16_cycle_revision_changed_only_in_source_is_denied(self):
        self.status(lambda c: c.source.__setitem__("cycle_revision", 3),
                    "DENIED", "CYCLE_SOURCE_DIVERGED")

    def test_17_command_superseded_by_new_revision_is_not_current(self):
        out = self.status(lambda c: (c.authority.__setitem__("cycle_revision", 3),
                                     c.source.__setitem__("cycle_revision", 3)),
                          "LAB_COMMAND_SUPERSEDED", "NEWER_CYCLE_TRANSITION")
        self.assertTrue(out["commit_verified"])

    def test_18_changed_last_command_is_superseded_not_current(self):
        self.status(lambda c: c.authority.__setitem__("last_command_ref", "cmd_2"),
                    "LAB_COMMAND_SUPERSEDED", "NEWER_CYCLE_TRANSITION")

    def test_19_invalid_command_ref_is_denied_before_select(self):
        c = FakeCursor()
        out = c.check(command="bad ref with spaces")
        self.assertEqual(out["status"], "DENIED")
        self.assertEqual(c.observed, [])
        self.assert_no_grant(out)

    def test_20_invalid_host_type_denied_before_select(self):
        c = FakeCursor()
        out = READBACK(c, command_ref="cmd_1", host={"actor_ref": "ACTOR_A"},
                       request_hash=HASH)
        self.assertEqual(out["status"], "DENIED")
        self.assertEqual(c.observed, [])

    def test_21_malformed_hash_denied_before_select(self):
        c = FakeCursor()
        out = c.check(digest="zz")
        self.assertEqual(out["status"], "DENIED")
        self.assertEqual(c.observed, [])

    def test_22_select_exception_is_unavailable_not_success(self):
        self.status(lambda c: setattr(c, "exc", True),
                    "UNAVAILABLE", "DEPENDENCY_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
