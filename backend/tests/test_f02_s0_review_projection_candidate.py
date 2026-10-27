"""Strict shape/continuity checks against pinned S0 0.1-candidate projection."""
import json
from pathlib import Path
import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.f02_reconciled_human_authorization_handoff import (
    HandoffResult, HandoffState,
)
from backend.f02_reconciled_review_lifecycle import ReviewWindow
from backend.f02_s0_review_projection_candidate import (
    EVIDENCE_SCOPE, HUMAN_RATIFICATION, SCHEMA,
    ProjectionGate, ProjectionGateResult, inspect_s0_review_projection,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/contracts/OAI_E04_F02_S0_REVIEW_PROJECTION_PIN.json"


def case():
    issued = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    w = ReviewWindow(issued, issued + timedelta(hours=24))
    h = HandoffResult(HandoffState.HANDOFF_REVIEW_ONLY, "a" * 64)
    o = {
        "schema": SCHEMA, "state": "RECORDED_REVIEW_ONLY",
        "review_ref": str(uuid4()), "revision": "1",
        "observed_at": (issued + timedelta(minutes=1)).isoformat(),
        "request_sha256": h.untrusted_request_sha256,
        "expires_at": w.expires_at.isoformat(),
        "evidence_scope": EVIDENCE_SCOPE,
        "human_ratification": HUMAN_RATIFICATION,
        "send_authorized": False, "scheduling_authorized": False,
        "commercial_transition_authorized": False,
    }
    return o, h, w


def gate(projection, h, w, previous=None):
    return inspect_s0_review_projection(projection, h, w, previous=previous).status


class CandidateS0ProjectionTests(unittest.TestCase):
    def test_01_record_is_review_only(self):
        o, h, w = case()
        self.assertIs(gate(o, h, w), ProjectionGate.PERSISTED_REVIEW_STATE_ONLY)

    def test_02_replay_and_current_are_never_approval(self):
        o, h, w = case()
        for st in ("REPLAY_REVIEW_ONLY", "CURRENT_REVIEW_ONLY"):
            self.assertIs(gate(dict(o, state=st), h, w),
                          ProjectionGate.PERSISTED_REVIEW_STATE_ONLY)

    def test_03_terminal_states_only_mark_terminal(self):
        o, h, w = case()
        for st in ("WITHDRAWN_REVIEW_ONLY", "EXPIRED_REVIEW_ONLY"):
            self.assertIs(gate(dict(o, state=st), h, w),
                          ProjectionGate.TERMINAL_REVIEW_STATE_ONLY)

    def test_04_all_negative_states_require_recheck(self):
        o, h, w = case()
        manifest = json.loads(MANIFEST.read_text())
        for st in manifest["negative_states"]:
            q = dict(o, state=st)
            for k in ("review_ref", "revision", "observed_at",
                      "request_sha256", "expires_at"):
                q[k] = None
            self.assertIs(gate(q, h, w), ProjectionGate.NEGATIVE_RESULT_RECHECK_ONLY)

    def test_05_true_boolean_authority_flags_rejected(self):
        o, h, w = case()
        for field in ("send_authorized", "scheduling_authorized",
                      "commercial_transition_authorized"):
            self.assertIs(gate(dict(o, **{field: True}), h, w),
                          ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def test_06_unexpected_fields_rejected_including_model_approval(self):
        o, h, w = case()
        self.assertIs(gate(dict(o, approved=True), h, w),
                      ProjectionGate.CONTRACT_RECHECK_REQUIRED)
        t = dict(o)
        t.pop("evidence_scope")
        self.assertIs(gate(t, h, w), ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def test_07_wrong_schema_or_authority_markers_rejected(self):
        o, h, w = case()
        for patch in ({"schema": "prumo.s0.f02.review.result/1.0"},
                      {"evidence_scope": "ALL_F03_PROOFS_VERIFIED"},
                      {"human_ratification": "APPROVED"}):
            self.assertIs(gate(dict(o, **patch), h, w),
                          ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def test_08_request_digest_tamper_rejected(self):
        o, h, w = case()
        self.assertIs(gate(dict(o, request_sha256="b"*64), h, w),
                      ProjectionGate.REQUEST_BINDING_RECHECK_REQUIRED)

    def test_09_window_change_and_expiry_change_rejected(self):
        o, h, w = case()
        self.assertIs(gate(o, h, replace(w, expires_at=w.expires_at
                               + timedelta(hours=1))),
                      ProjectionGate.REQUEST_BINDING_RECHECK_REQUIRED)
        self.assertIs(gate(dict(o, expires_at=(w.expires_at
                        + timedelta(minutes=1)).isoformat()), h, w),
                      ProjectionGate.REQUEST_BINDING_RECHECK_REQUIRED)

    def test_10_equivalent_timezones_normalize(self):
        o, h, w = case()
        offset = timezone(timedelta(hours=-3))
        o = dict(o, expires_at=w.expires_at.astimezone(offset).isoformat(),
                 observed_at=datetime.fromisoformat(o["observed_at"])
                             .astimezone(offset).isoformat())
        self.assertIs(gate(o, h, w), ProjectionGate.PERSISTED_REVIEW_STATE_ONLY)

    def test_11_malformed_timestamps_fail(self):
        o, h, w = case()
        for raw in ("2026-11-01T12:01:00", "not-a-time", 12, None):
            self.assertIs(gate(dict(o, observed_at=raw), h, w),
                          ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def test_12_malformed_uuid_or_nil_rejected(self):
        o, h, w = case()
        for s in ("invalid", str(uuid4()).upper(),
                  "00000000-0000-0000-0000-000000000000", None):
            self.assertIs(gate(dict(o, review_ref=s), h, w),
                          ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def test_13_revision_must_be_canonical_pg_integer(self):
        o, h, w = case()
        for value in ("0", "01", "2147483648", 1, True, None, "-1"):
            self.assertIs(gate(dict(o, revision=value), h, w),
                          ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def test_14_negative_cannot_sneak_reference_or_digest(self):
        o, h, w = case()
        q = dict(o, state="UNAVAILABLE")
        self.assertIs(gate(q, h, w), ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def test_15_replay_continuity_same_ref_monotonic_revision(self):
        o, h, w = case()
        new = dict(o, state="REPLAY_REVIEW_ONLY", revision="2",
                   observed_at=(datetime.fromisoformat(o["observed_at"])
                        + timedelta(minutes=1)).isoformat())
        self.assertIs(gate(new, h, w, previous=o),
                      ProjectionGate.PERSISTED_REVIEW_STATE_ONLY)

    def test_16_changed_reference_cannot_claim_same_continuity(self):
        o, h, w = case()
        self.assertIs(gate(dict(o, review_ref=str(uuid4())), h, w, previous=o),
                      ProjectionGate.CONTINUITY_RECHECK_REQUIRED)

    def test_17_revision_regression_denied(self):
        o, h, w = case()
        p = dict(o, revision="4")
        self.assertIs(gate(o, h, w, previous=p),
                      ProjectionGate.CONTINUITY_RECHECK_REQUIRED)

    def test_18_observed_clock_regression_denied(self):
        o, h, w = case()
        p = dict(o, observed_at=(datetime.fromisoformat(o["observed_at"])
                      + timedelta(seconds=1)).isoformat())
        self.assertIs(gate(o, h, w, previous=p),
                      ProjectionGate.CONTINUITY_RECHECK_REQUIRED)

    def test_19_withdrawn_or_expired_does_not_reopen(self):
        o, h, w = case()
        for terminal in ("WITHDRAWN_REVIEW_ONLY", "EXPIRED_REVIEW_ONLY"):
            old = dict(o, state=terminal)
            self.assertIs(gate(dict(o, revision="2"), h, w, previous=old),
                          ProjectionGate.CONTINUITY_RECHECK_REQUIRED)

    def test_20_terminal_state_does_not_switch_to_other_terminal(self):
        o, h, w = case()
        old = dict(o, state="WITHDRAWN_REVIEW_ONLY")
        new = dict(o, state="EXPIRED_REVIEW_ONLY", revision="2")
        self.assertIs(gate(new, h, w, previous=old),
                      ProjectionGate.CONTINUITY_RECHECK_REQUIRED)

    def test_21_transient_negative_never_erases_prior_record(self):
        o, h, w = case()
        error = dict(o, state="UNAVAILABLE")
        for f in ("review_ref","revision","observed_at","request_sha256","expires_at"):
            error[f] = None
        self.assertIs(gate(error, h, w, previous=o),
                      ProjectionGate.CONTINUITY_RECHECK_REQUIRED)

    def test_22_malformed_prior_claim_rejected(self):
        o, h, w = case()
        self.assertIs(gate(o, h, w, previous=dict(o, approved=True)),
                      ProjectionGate.CONTRACT_RECHECK_REQUIRED)

    def test_23_expired_active_claim_rejected(self):
        o, h, w = case()
        future = dict(o, observed_at=w.expires_at.isoformat())
        self.assertIs(gate(future, h, w),
                      ProjectionGate.CONTINUITY_RECHECK_REQUIRED)

    def test_24_wrong_handoff_or_window_type_denied(self):
        o, h, w = case()
        for args in ((None, h, w), (o, {}, w), (o, h, {}),
                     (o, h, w, [])):
            if len(args) == 3:
                self.assertIs(gate(*args), ProjectionGate.DENIED_MALFORMED)
            else:
                self.assertIs(gate(*args), ProjectionGate.DENIED_MALFORMED)

    def test_25_wrong_version_or_digest_in_local_handoff(self):
        o, h, w = case()
        for bad in (replace(h, contract_version="v900"),
                    replace(h, untrusted_request_sha256="b"),
                    replace(h, status=HandoffState.DENIED_MALFORMED)):
            self.assertIs(gate(o, bad, w),
                          ProjectionGate.REQUEST_BINDING_RECHECK_REQUIRED)

    def test_26_expiry_before_start_denied_even_for_s0_valid_shape(self):
        o, h, w = case()
        self.assertIs(gate(o, h, replace(w, requested_at=w.expires_at)),
                      ProjectionGate.REQUEST_BINDING_RECHECK_REQUIRED)

    def test_27_result_has_no_authority_or_identifier_fields(self):
        o, h, w = case()
        value = inspect_s0_review_projection(o, h, w)
        self.assertEqual([f.name for f in fields(ProjectionGateResult)], ["status"])
        self.assertFalse(any(hasattr(value, name) for name in
                         ("approve", "send", "schedule", "persist", "authorize",
                          "review_ref", "session", "token")))

    def test_28_pinned_s0_manifest_tracks_all_known_states_and_schema(self):
        m = json.loads(MANIFEST.read_text())
        self.assertEqual(m["schema"], SCHEMA)
        self.assertEqual(m["evidence_scope"], EVIDENCE_SCOPE)
        self.assertEqual(m["human_ratification"], HUMAN_RATIFICATION)
        self.assertEqual(set(m["persisted_states"]),
            {"RECORDED_REVIEW_ONLY","REPLAY_REVIEW_ONLY","CURRENT_REVIEW_ONLY",
             "WITHDRAWN_REVIEW_ONLY","EXPIRED_REVIEW_ONLY"})
        self.assertEqual(len(m["negative_states"]), 8)
        self.assertEqual(set(m["required_keys"]), set(case()[0]))
        self.assertFalse(m["operationally_ratified"])


if __name__ == "__main__":
    unittest.main()
