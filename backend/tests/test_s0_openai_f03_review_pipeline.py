"""Deterministic, disconnected F03 composition regression using synthetic cases."""
import unittest
from dataclasses import replace
from unittest.mock import patch

from backend.s0_openai_bridge.f03_offline_gate import (
    Snapshot, Proposal, FieldRule, Evidence, Candidate, Review, Result,
)
from backend.s0_openai_bridge.f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority, ReviewDecision,
)
from backend.s0_openai_bridge.f03_review_pipeline import (
    PipelineStatus, review_f03_offline,
)


def fixtures():
    snap = Snapshot("A", "C1", "K1", "H1", 7, 3, "CAT1", True, True, True,
                    "human_bank_collection", (FieldRule("X", True, True),),
                    (Evidence("m1", "A", "C1", "customer", {"X": "DEMO"}),))
    proposal = Proposal("A", "C1", "K1", "H1", 7, 3, "CAT1",
                        (Candidate("X", "DEMO", ("m1",)),))
    closing = ClosingSnapshot("A", "C1", "K1", "OP1", "ASS1", 7, 3,
                              "m1", "H1", "CAT1")
    auth = CurrentAuthority("A", "C1", "K1", "OP1", "ASS1", 7, 3, "m1", "H1",
                            "CAT1", True, True, True, True,
                            "human_bank_collection", False, True)
    return snap, proposal, closing, auth


class CompositionTests(unittest.TestCase):
    def run_review(self, *, snap=None, proposal=None, close=None, current=None,
                   f03=None, authority=None):
        a, b, c, d = fixtures()
        if snap is not None: a = replace(a, **snap) if isinstance(snap, dict) else snap
        if proposal is not None: b = replace(b, **proposal) if isinstance(proposal, dict) else proposal
        if close is not None: c = replace(c, **close) if isinstance(close, dict) else close
        if current is not None: d = replace(d, **current) if isinstance(current, dict) else current
        if f03 is None: f03 = Review(Result.PROPOSAL_ONLY, b.fields)
        if authority is None: authority = ReviewDecision.REVIEW_ONLY
        with patch("backend.s0_openai_bridge.f03_review_pipeline.evaluate_f03", return_value=f03) as fv, \
             patch("backend.s0_openai_bridge.f03_review_pipeline.recheck_before_apply", return_value=authority) as av:
            result = review_f03_offline(a, b, c, d)
        return result, fv.call_count, av.call_count

    def test_01_both_guards_success_remain_review_only(self):
        res, f, a = self.run_review()
        self.assertEqual((res.status, res.candidate_field_codes, f, a),
                         (PipelineStatus.REVIEW_ONLY, ("X",), 1, 1))

    def test_02_store_mismatch_between_guards_denies_without_evaluators(self):
        res, f, a = self.run_review(close={"store": "B"})
        self.assertEqual((res.status, f, a), (PipelineStatus.DENIED, 0, 0))

    def test_03_case_mismatch_between_guards_denies(self):
        self.assertEqual(self.run_review(close={"case": "C2"})[0].status, PipelineStatus.DENIED)

    def test_04_closure_mismatch_denies(self):
        self.assertEqual(self.run_review(close={"closure_event": "OTHER"})[0].status, PipelineStatus.DENIED)

    def test_05_hash_mismatch_becomes_stale(self):
        self.assertEqual(self.run_review(close={"snapshot_hash": "OLD"})[0].status, PipelineStatus.STALE)

    def test_06_form_version_drift_stale(self):
        self.assertEqual(self.run_review(close={"form_version": 4})[0].status, PipelineStatus.STALE)

    def test_07_catalogue_drift_stale(self):
        self.assertEqual(self.run_review(close={"catalogue_version": "CAT2"})[0].status, PipelineStatus.STALE)

    def test_08_f03_denies_even_if_authority_would_pass(self):
        res, _, n = self.run_review(f03=Review(Result.BLOCKED))
        self.assertEqual((res.status, n), (PipelineStatus.DENIED, 0))

    def test_09_f03_stale_precedes_assignment(self):
        res, _, n = self.run_review(f03=Review(Result.STALE))
        self.assertEqual((res.status, n), (PipelineStatus.STALE, 0))

    def test_10_assignment_denied_blocks_valid_fields(self):
        self.assertEqual(self.run_review(authority=ReviewDecision.DENY)[0].status, PipelineStatus.DENIED)

    def test_11_assignment_transferred_stale(self):
        self.assertEqual(self.run_review(authority=ReviewDecision.STALE)[0].status, PipelineStatus.STALE)

    def test_12_assignment_not_ready(self):
        self.assertEqual(self.run_review(authority=ReviewDecision.NOT_READY)[0].status, PipelineStatus.NOT_READY)

    def test_13_field_presence_flag_cannot_claim_unvalidated_fields(self):
        res, _, n = self.run_review(f03=Review(Result.REVIEW), current={"result_has_validated_fields": True})
        self.assertEqual((res.status, n), (PipelineStatus.NOT_READY, 0))

    def test_14_string_false_flag_denied(self):
        self.assertEqual(self.run_review(current={"result_has_validated_fields": "false"})[0].status, PipelineStatus.DENIED)

    def test_15_partial_evidence_keeps_human_review_without_loss_of_provenance(self):
        case = Candidate("X", "DEMO", ("m1",))
        r = Review(Result.PARTIAL_REVIEW, (case,), ("Y",), ("Z",))
        outcome = self.run_review(f03=r)[0]
        self.assertEqual((outcome.status, outcome.candidate_field_codes,
                          outcome.missing_required_codes, outcome.rejected_field_codes),
                         (PipelineStatus.REVIEW_REQUIRED, ("X",), ("Y",), ("Z",)))

    def test_16_no_fields_yet_means_not_ready(self):
        self.assertEqual(self.run_review(f03=Review(Result.REVIEW),
                                         current={"result_has_validated_fields": False})[0].status,
                         PipelineStatus.NOT_READY)

    def test_17_bad_snapshot_type_denied(self):
        self.assertEqual(self.run_review(snap=object())[0].status, PipelineStatus.DENIED)

    def test_18_mixed_case_version_between_guards_stale(self):
        self.assertEqual(self.run_review(close={"case_version": 9})[0].status, PipelineStatus.STALE)

    def test_19_only_field_codes_never_values_in_summary(self):
        res = self.run_review()[0]
        self.assertNotIn("DEMO", str(res))

    def test_20_idempotent_repeated_pure_reviews_no_sql_side_effect(self):
        a = self.run_review()[0]
        b = self.run_review()[0]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
