"""F03 offline safety regression: deterministic race/order matrix over real gates.

No mocks, network, database, Meta, or OpenAI API. CurrentAuthority is a
synthetic stand-in for a single S0/S1 authoritative read. This is NOT an
atomicity, locking, S1 grant, or real PostgreSQL concurrency test.
"""
import unittest
from dataclasses import replace

from backend.s0_openai_bridge.f03_offline_gate import (
    Candidate, Evidence, FieldRule, Proposal, Snapshot,
)
from backend.s0_openai_bridge.f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority,
)
from backend.s0_openai_bridge.f03_review_pipeline import (
    PipelineStatus, review_f03_offline,
)


def fixture(store="shop-A", case="case-1", closure="close-1"):
    snapshot = Snapshot(
        store, case, closure, "hash-1", 11, 4, "catalog-v1",
        True, True, True, "human_bank_collection",
        (FieldRule("required", True, True), FieldRule("optional", False, True)),
        (Evidence("msg-1", store, case, "customer", {"required": "TEST"}),),
    )
    proposal = Proposal(
        store, case, closure, "hash-1", 11, 4, "catalog-v1",
        (Candidate("required", "TEST", ("msg-1",)),),
    )
    closing = ClosingSnapshot(
        store, case, closure, "operator-1", "assignment-1", 11, 4,
        "msg-1", "hash-1", "catalog-v1",
    )
    current = CurrentAuthority(
        store, case, closure, "operator-1", "assignment-1", 11, 4,
        "msg-1", "hash-1", "catalog-v1", True, True, True, True,
        "human_bank_collection", False, True,
    )
    return snapshot, proposal, closing, current


def review(*, snapshot=None, proposal=None, closing=None, current=None):
    original = fixture()
    return review_f03_offline(
        snapshot if snapshot is not None else original[0],
        proposal if proposal is not None else original[1],
        closing if closing is not None else original[2],
        current if current is not None else original[3],
    )


class RaceAndIsolationMatrix(unittest.TestCase):
    def test_01_baseline_remains_review_only(self):
        res = review()
        self.assertEqual((res.status, res.candidate_field_codes),
                         (PipelineStatus.REVIEW_ONLY, ("required",)))
        self.assertFalse(hasattr(res, "applied"))

    def test_02_late_reply_after_new_inbound_is_stale(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, watermark="msg-2")).status,
                         PipelineStatus.STALE)

    def test_03_form_edit_after_close_is_stale(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, form_version=5)).status,
                         PipelineStatus.STALE)

    def test_04_case_transition_after_close_is_stale(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, case_version=12)).status,
                         PipelineStatus.STALE)

    def test_05_snapshot_recut_after_close_is_stale(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, snapshot_hash="hash-2")).status,
                         PipelineStatus.STALE)

    def test_06_s0_catalog_revision_invalidates_old_output(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, catalogue_version="catalog-v2")).status,
                         PipelineStatus.STALE)

    def test_07_operator_transfer_invalidates_old_output(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, operator="operator-2",
                                                 assignment="assignment-2")).status,
                         PipelineStatus.STALE)

    def test_08_reassignment_to_same_operator_still_stale(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, assignment="assignment-2")).status,
                         PipelineStatus.STALE)

    def test_09_operator_global_pause_denies_prior_success(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, operator_active=False)).status,
                         PipelineStatus.DENIED)

    def test_10_store_grant_revocation_denies_prior_success(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, store_grant=False)).status,
                         PipelineStatus.DENIED)

    def test_11_session_loss_denies_prior_success(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, authenticated_session=False)).status,
                         PipelineStatus.DENIED)

    def test_12_opt_out_denies_even_if_fields_are_valid(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, opted_out=True)).status,
                         PipelineStatus.DENIED)

    def test_13_store_revocation_outweighs_new_inbound_staleness(self):
        _, _, _, now = fixture()
        out = review(current=replace(now, store_grant=False, watermark="msg-2"))
        self.assertEqual(out.status, PipelineStatus.DENIED)
        self.assertEqual(out.candidate_field_codes, ())

    def test_14_paused_operator_outweighs_reassignment_staleness(self):
        _, _, _, now = fixture()
        out = review(current=replace(now, operator_active=False, assignment="assignment-2"))
        self.assertEqual(out.status, PipelineStatus.DENIED)
        self.assertEqual(out.missing_required_codes, ())

    def test_15_untrusted_type_outweighs_obsolete_form(self):
        _, _, _, now = fixture()
        out = review(current=replace(now, store_grant="false", form_version=5))
        self.assertEqual(out.status, PipelineStatus.DENIED)

    def test_16_latest_closure_cannot_resurrect_old_closure(self):
        _, _, _, now = fixture()
        self.assertEqual(review(current=replace(now, closure_event="close-2")).status,
                         PipelineStatus.DENIED)

    def test_17_stale_model_case_version_cannot_be_accepted(self):
        _, proposal, _, _ = fixture()
        self.assertEqual(review(proposal=replace(proposal, case_version=10)).status,
                         PipelineStatus.STALE)

    def test_18_model_from_other_store_denied(self):
        _, proposal, _, _ = fixture()
        self.assertEqual(review(proposal=replace(proposal, store="shop-B")).status,
                         PipelineStatus.DENIED)

    def test_19_cross_store_evidence_denies_even_when_not_cited(self):
        snapshot, _, _, _ = fixture()
        injected = Evidence("msg-evil", "shop-B", "case-1", "customer",
                            {"optional": "secret"})
        out = review(snapshot=replace(snapshot, messages=snapshot.messages + (injected,)))
        self.assertEqual(out.status, PipelineStatus.DENIED)
        self.assertEqual(out.omitted_informed_optional_codes, ())

    def test_20_cross_case_evidence_denies_even_when_not_cited(self):
        snapshot, _, _, _ = fixture()
        injected = Evidence("msg-evil", "shop-A", "case-2", "customer",
                            {"optional": "secret"})
        out = review(snapshot=replace(snapshot, messages=snapshot.messages + (injected,)))
        self.assertEqual(out.status, PipelineStatus.DENIED)

    def test_21_conflicting_customer_statements_require_review(self):
        snapshot, _, _, _ = fixture()
        conflict = Evidence("msg-2", "shop-A", "case-1", "customer",
                            {"required": "OTHER"})
        out = review(snapshot=replace(snapshot, messages=snapshot.messages + (conflict,)),
                     current=replace(fixture()[3], result_has_validated_fields=False))
        self.assertEqual(out.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertIn("required", out.rejected_field_codes)

    def test_22_missing_required_after_stale_assignment_does_not_leak(self):
        snapshot, proposal, closing, now = fixture()
        proposal = replace(proposal, fields=())
        out = review(snapshot=snapshot, proposal=proposal, closing=closing,
                     current=replace(now, result_has_validated_fields=False,
                                     assignment="assignment-2"))
        self.assertEqual(out.status, PipelineStatus.STALE)
        self.assertEqual(out.missing_required_codes, ())

    def test_23_informed_optional_after_revocation_does_not_leak(self):
        snapshot, proposal, closing, now = fixture()
        informed = replace(snapshot.messages[0],
                           asserted_fields={"required": "TEST", "optional": "VALUED"})
        out = review(snapshot=replace(snapshot, messages=(informed,)),
                     proposal=proposal, closing=closing,
                     current=replace(now, store_grant=False))
        self.assertEqual(out.status, PipelineStatus.DENIED)
        self.assertEqual(out.omitted_informed_optional_codes, ())

    def test_24_another_store_can_still_be_reviewed_in_its_own_scope(self):
        s, p, c, a = fixture("shop-B", "case-10", "close-99")
        out = review_f03_offline(s, p, c, a)
        self.assertEqual((out.status, out.candidate_field_codes),
                         (PipelineStatus.REVIEW_ONLY, ("required",)))

    def test_25_shop_a_grant_revoked_does_not_modify_shop_b_fixture(self):
        sa, pa, ca, aa = fixture("shop-A", "case-1", "close-1")
        sb, pb, cb, ab = fixture("shop-B", "case-2", "close-2")
        self.assertEqual(review_f03_offline(sa, pa, ca, replace(aa, store_grant=False)).status,
                         PipelineStatus.DENIED)
        self.assertEqual(review_f03_offline(sb, pb, cb, ab).status,
                         PipelineStatus.REVIEW_ONLY)

    def test_26_replay_of_old_assignment_never_matches_new_current(self):
        s, p, c, now = fixture()
        new_now = replace(now, assignment="assignment-3", case_version=12)
        self.assertEqual(review_f03_offline(s, p, c, new_now).status,
                         PipelineStatus.STALE)
        self.assertEqual(review_f03_offline(s, p, c, now).status,
                         PipelineStatus.REVIEW_ONLY)
        # Last assertion is intentionally about an OLD synthetic authority object;
        # a real S0 must never reuse it as proof after the case has changed.

    def test_27_no_validated_fields_but_new_customer_message_stale_not_review(self):
        _, p, _, now = fixture()
        out = review(proposal=replace(p, fields=()),
                     current=replace(now, watermark="msg-2", result_has_validated_fields=False))
        self.assertEqual(out.status, PipelineStatus.STALE)

    def test_28_invalid_boolean_auth_does_not_surface_fields(self):
        _, _, _, now = fixture()
        out = review(current=replace(now, authenticated_session="false"))
        self.assertEqual(out.status, PipelineStatus.DENIED)
        self.assertEqual(out.candidate_field_codes, ())
        self.assertEqual(out.rejected_field_codes, ())


if __name__ == "__main__":
    unittest.main()
