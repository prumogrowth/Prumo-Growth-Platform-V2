"""Real-validator F03 composition integration, offline fixtures only; no mocks.

This suite uses the actual evaluate_f03 and recheck_before_apply imported
by review_f03_offline. It is not production Auth/S1 or OpenAI integration.
"""
import unittest
from dataclasses import replace

from backend.s0_openai_bridge.f03_offline_gate import (
    Snapshot, Proposal, FieldRule, Evidence, Candidate,
)
from backend.s0_openai_bridge.f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority,
)
from backend.s0_openai_bridge.f03_review_pipeline import PipelineStatus, review_f03_offline


def fixtures():
    snap = Snapshot(
        "store-A", "case-1", "close-1", "hash-1", 7, 3, "catalog-1",
        True, True, True, "human_bank_collection",
        (FieldRule("required", True, True), FieldRule("optional", False, True)),
        (Evidence("m1", "store-A", "case-1", "customer", {"required": "value-X"}),
         Evidence("m2", "store-A", "case-1", "customer", {"optional": "value-Y"})),
    )
    proposal = Proposal(
        "store-A", "case-1", "close-1", "hash-1", 7, 3, "catalog-1",
        (Candidate("required", "value-X", ("m1",)),
         Candidate("optional", "value-Y", ("m2",))),
    )
    closing = ClosingSnapshot(
        "store-A", "case-1", "close-1", "operator-1", "assignment-1",
        7, 3, "m2", "hash-1", "catalog-1",
    )
    current = CurrentAuthority(
        "store-A", "case-1", "close-1", "operator-1", "assignment-1",
        7, 3, "m2", "hash-1", "catalog-1", True, True, True,
        True, "human_bank_collection", False, True,
    )
    return snap, proposal, closing, current


class RealF03IntegrationTests(unittest.TestCase):
    def review(self, *, s=None, p=None, c=None, a=None):
        default = fixtures()
        def edit(original, change):
            if change is None:
                return original
            return replace(original, **change) if isinstance(change, dict) else change
        return review_f03_offline(*(
            edit(default[0], s), edit(default[1], p),
            edit(default[2], c), edit(default[3], a),
        ))

    def status(self, expected, **kwargs):
        self.assertEqual(self.review(**kwargs).status, expected)

    def test_01_full_match_is_review_only_not_application(self):
        result = self.review()
        self.assertEqual(result.status, PipelineStatus.REVIEW_ONLY)
        self.assertEqual(result.candidate_field_codes, ("required", "optional"))
        self.assertFalse(hasattr(result, "applied"))

    def test_02_informed_optional_omission_requires_review_without_essential_gap(self):
        result = self.review(p={"fields": (Candidate("required", "value-X", ("m1",)),)})
        self.assertEqual((result.status, result.missing_required_codes,
                          result.omitted_informed_optional_codes),
                         (PipelineStatus.REVIEW_REQUIRED, (), ("optional",)))

    def test_03_missing_required_without_candidate_goes_to_human(self):
        result = self.review(p={"fields": ()}, a={"result_has_validated_fields": False})
        self.assertEqual((result.status, result.missing_required_codes), (PipelineStatus.REVIEW_REQUIRED, ("required",)))

    def test_04_only_optional_with_missing_required_stays_review(self):
        result = self.review(p={"fields": (Candidate("optional", "value-Y", ("m2",)),)})
        self.assertEqual((result.status, result.candidate_field_codes, result.missing_required_codes),
                         (PipelineStatus.REVIEW_REQUIRED, ("optional",), ("required",)))

    def test_05_two_customer_values_same_field_conflict(self):
        s, _, _, _ = fixtures()
        msg = Evidence("m3", "store-A", "case-1", "customer", {"required": "DIFFERENT"})
        result = self.review(s={"messages": s.messages + (msg,)})
        self.assertEqual(result.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(result.candidate_field_codes, ("optional",))
        self.assertIn("required", result.rejected_field_codes)
        self.assertIn("required", result.missing_required_codes)

    def test_06_unauthorized_customer_statement_does_not_override(self):
        s, _, _, _ = fixtures()
        msg = Evidence("m3", "store-A", "case-1", "customer", {"required": "DIFFERENT"}, False)
        self.status(PipelineStatus.REVIEW_ONLY, s={"messages": s.messages + (msg,)})

    def test_07_operator_statement_cannot_supply_value(self):
        s, p, _, _ = fixtures()
        operator_msg = Evidence("operator-msg", "store-A", "case-1", "operator", {"required": "value-X"})
        replacement = (Candidate("required", "value-X", ("operator-msg",)), p.fields[1])
        result = self.review(s={"messages": s.messages + (operator_msg,)}, p={"fields": replacement})
        self.assertEqual((result.status, result.candidate_field_codes),
                         (PipelineStatus.REVIEW_REQUIRED, ("optional",)))

    def test_08_wrong_claim_even_with_real_reference_is_rejected(self):
        p = fixtures()[1]
        result = self.review(p={"fields": (Candidate("required", "INVENTED", ("m1",)), p.fields[1])})
        self.assertEqual(result.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(result.candidate_field_codes, ("optional",))

    def test_09_foreign_store_in_evidence_denies_all(self):
        s, _, _, _ = fixtures()
        foreign = Evidence("m3", "store-B", "case-1", "customer", {"required": "value-X"})
        self.status(PipelineStatus.DENIED, s={"messages": s.messages + (foreign,)})

    def test_10_foreign_case_in_evidence_denies_all(self):
        s, _, _, _ = fixtures()
        foreign = Evidence("m3", "store-A", "case-2", "customer", {"required": "value-X"})
        self.status(PipelineStatus.DENIED, s={"messages": s.messages + (foreign,)})

    def test_11_proposal_foreign_store_denied(self):
        self.status(PipelineStatus.DENIED, p={"store": "store-B"})

    def test_12_proposal_foreign_case_denied(self):
        self.status(PipelineStatus.DENIED, p={"case": "case-2"})

    def test_13_closing_foreign_store_denied(self):
        self.status(PipelineStatus.DENIED, c={"store": "store-B"})

    def test_14_closing_wrong_event_denied(self):
        self.status(PipelineStatus.DENIED, c={"closure_event": "close-old"})

    def test_15_result_from_old_hash_stale(self):
        self.status(PipelineStatus.STALE, p={"snapshot_hash": "hash-old"})

    def test_16_closing_snapshot_hash_changed_stale(self):
        self.status(PipelineStatus.STALE, c={"snapshot_hash": "hash-new"})

    def test_17_form_version_changed_after_close_stale(self):
        self.status(PipelineStatus.STALE, a={"form_version": 4})

    def test_18_case_version_changed_after_close_stale(self):
        self.status(PipelineStatus.STALE, a={"case_version": 8})

    def test_19_new_inbound_watermark_stale(self):
        self.status(PipelineStatus.STALE, a={"watermark": "m3"})

    def test_20_catalogue_changed_after_close_stale(self):
        self.status(PipelineStatus.STALE, a={"catalogue_version": "catalog-2"})

    def test_21_operator_transfer_stale(self):
        self.status(PipelineStatus.STALE, a={"operator": "operator-2"})

    def test_22_same_operator_new_assignment_stale(self):
        self.status(PipelineStatus.STALE, a={"assignment": "assignment-2"})

    def test_23_paused_operator_denied(self):
        self.status(PipelineStatus.DENIED, a={"operator_active": False})

    def test_24_revoked_store_grant_denied(self):
        self.status(PipelineStatus.DENIED, a={"store_grant": False})

    def test_25_session_revoked_denied(self):
        self.status(PipelineStatus.DENIED, a={"authenticated_session": False})

    def test_26_opt_out_denied(self):
        self.status(PipelineStatus.DENIED, a={"opted_out": True})

    def test_27_no_longer_human_case_denied(self):
        self.status(PipelineStatus.DENIED, a={"case_human": False})

    def test_28_bad_purpose_denied(self):
        self.status(PipelineStatus.DENIED, a={"purpose": "post_sale_unapproved"})

    def test_29_malformed_boolean_never_grants(self):
        self.status(PipelineStatus.DENIED, a={"store_grant": "false"})

    def test_30_malformed_case_version_never_grants(self):
        self.status(PipelineStatus.DENIED, a={"case_version": True})

    def test_31_unexpected_catalogue_field_denies(self):
        p = fixtures()[1]
        self.status(PipelineStatus.DENIED,
                    p={"fields": p.fields + (Candidate("secret", "anything", ("m1",)),)})

    def test_32_duplicate_field_needs_review(self):
        p = fixtures()[1]
        res = self.review(p={"fields": p.fields + (p.fields[0],)})
        self.assertEqual(res.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(res.candidate_field_codes, ("optional",))

    def test_33_mismatched_validation_flag_not_ready(self):
        self.status(PipelineStatus.NOT_READY, a={"result_has_validated_fields": False})

    def test_34_denied_operator_with_mismatched_flag_must_still_be_denied(self):
        # Rechecking actual permission must outrank inconsistently supplied flags.
        self.status(PipelineStatus.DENIED,
                    a={"store_grant": False, "result_has_validated_fields": False})

    def test_35_stale_assignment_with_mismatched_flag_stays_stale(self):
        self.status(PipelineStatus.STALE,
                    a={"assignment": "assignment-old", "result_has_validated_fields": False})

    def test_36_malformed_authorization_flag_with_mismatched_flag_denied(self):
        self.status(PipelineStatus.DENIED,
                    a={"authenticated_session": "false", "result_has_validated_fields": False})

    def test_37_stale_snapshot_does_not_require_current_validated_flag(self):
        self.status(PipelineStatus.STALE, s={"original_snapshot_current": False})

    def test_38_unapproved_close_denied(self):
        self.status(PipelineStatus.DENIED, s={"closure_authorized": False})

    def test_39_no_customer_source_requires_human_review(self):
        p = fixtures()[1]
        res = self.review(p={"fields": (Candidate("required", "value-X", ("absent",)), p.fields[1])})
        self.assertEqual(res.status, PipelineStatus.REVIEW_REQUIRED)

    def test_40_empty_evidence_source_requires_human_review(self):
        p = fixtures()[1]
        res = self.review(p={"fields": (Candidate("required", "value-X", ()), p.fields[1])})
        self.assertEqual(res.status, PipelineStatus.REVIEW_REQUIRED)

    def test_41_revocation_outweighs_stale_model_proposal(self):
        self.status(PipelineStatus.DENIED,
                    p={"snapshot_hash": "old-model-hash"}, a={"store_grant": False})

    def test_42_revocation_outweighs_stale_closing_snapshot(self):
        self.status(PipelineStatus.DENIED,
                    c={"snapshot_hash": "old-closing-hash"}, a={"operator_active": False})

    def test_43_authorized_stale_model_stays_stale(self):
        self.status(PipelineStatus.STALE, p={"case_version": 6})

    def test_44_revoked_session_cannot_leak_missing_required_fields(self):
        result = self.review(p={"fields": ()}, a={"authenticated_session": False,
                                                 "result_has_validated_fields": False})
        self.assertEqual(result.status, PipelineStatus.DENIED)
        self.assertEqual(result.missing_required_codes, ())
        self.assertEqual(result.rejected_field_codes, ())


if __name__ == "__main__":
    unittest.main()
