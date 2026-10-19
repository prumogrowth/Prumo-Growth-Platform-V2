"""Synthetic F03 contract tests. No external API, DB, network or user data."""
import unittest
from dataclasses import replace

from backend.s0_openai_bridge.f03_offline_gate import (
    Candidate, Evidence, FieldRule, Proposal, Result, Snapshot, evaluate_f03,
)

RULES = (FieldRule("A", True, True), FieldRule("B", False, True), FieldRule("C", True, True))
SOURCES = (Evidence("m1", "LOJA_A", "CASO_A", "customer", {"A": "ALFA", "B": "BETA"}),
           Evidence("m2", "LOJA_A", "CASO_A", "customer", {"C": "GAMA"}))


def fixtures():
    snap = Snapshot("LOJA_A", "CASO_A", "close1", "hash1", 7, 2, "CAT1",
                    True, True, True, "human_bank_collection", RULES, SOURCES)
    prop = Proposal("LOJA_A", "CASO_A", "close1", "hash1", 7, 2, "CAT1",
                    (Candidate("A", "ALFA", ("m1",)), Candidate("C", "GAMA", ("m2",))))
    return snap, prop


class F03OfflineTests(unittest.TestCase):
    def check(self, expected, snap_over=None, prop_over=None, fields=None):
        s, p = fixtures()
        s = replace(s, **(snap_over or {}))
        p = replace(p, **(prop_over or {}))
        if fields is not None:
            p = replace(p, fields=fields)
        result = evaluate_f03(s, p)
        self.assertEqual(result.status, expected)
        return result

    def test_01_required_fields_with_evidence(self):
        self.assertEqual(len(self.check(Result.PROPOSAL_ONLY).accepted), 2)

    def test_02_optional_missing_does_not_block(self):
        self.assertEqual(self.check(Result.PROPOSAL_ONLY).needs_human_fields, ())

    def test_03_optional_explicit_is_retained(self):
        s, p = fixtures()
        more = p.fields + (Candidate("B", "BETA", ("m1",)),)
        self.assertEqual(len(self.check(Result.PROPOSAL_ONLY, fields=more).accepted), 3)

    def test_04_missing_essential_requests_human(self):
        r = self.check(Result.PARTIAL_REVIEW, fields=(Candidate("A", "ALFA", ("m1",)),))
        self.assertEqual(r.needs_human_fields, ("C",))

    def test_05_no_fields_requests_human(self):
        self.assertEqual(self.check(Result.REVIEW, fields=()).needs_human_fields, ("A", "C"))

    def test_06_no_source_ref(self):
        r = self.check(Result.PARTIAL_REVIEW, fields=(Candidate("A", "ALFA", ("m1",)), Candidate("C", "GAMA", ())))
        self.assertEqual(r.rejected_fields, ("C",))

    def test_07_unknown_field_denied(self):
        self.check(Result.BLOCKED, fields=(Candidate("BAD", "X", ("m1",)),))

    def test_08_other_tenant_in_envelope_denied(self):
        self.check(Result.BLOCKED, prop_over={"store": "LOJA_B"})

    def test_09_other_case_in_envelope_denied(self):
        self.check(Result.BLOCKED, prop_over={"case": "CASO_B"})

    def test_10_mismatched_closure_denied(self):
        self.check(Result.BLOCKED, prop_over={"closure_event_id": "forged"})

    def test_11_catalogue_mismatch_denied(self):
        self.check(Result.BLOCKED, prop_over={"catalogue_version": "CAT2"})

    def test_12_snapshot_changed(self):
        self.check(Result.STALE, prop_over={"snapshot_hash": "old"})

    def test_13_form_edited_during_processing(self):
        self.check(Result.STALE, snap_over={"form_version": 3})

    def test_14_case_version_changed(self):
        self.check(Result.STALE, snap_over={"case_version": 8})

    def test_15_customer_new_message(self):
        self.check(Result.STALE, snap_over={"original_snapshot_current": False})

    def test_16_operator_revoked(self):
        self.check(Result.BLOCKED, snap_over={"actor_authorized_now": False})

    def test_17_closure_not_authenticated(self):
        self.check(Result.BLOCKED, snap_over={"closure_authorized": False})

    def test_18_post_sale_support_not_automated(self):
        self.check(Result.BLOCKED, snap_over={"purpose": "post_sale_support"})

    def test_19_operator_message_cannot_prove_field(self):
        m = Evidence("m1", "LOJA_A", "CASO_A", "operator", {"A": "ALFA"})
        r = self.check(Result.PARTIAL_REVIEW, snap_over={"messages": (m, SOURCES[1])})
        self.assertEqual(r.needs_human_fields, ("A",))

    def test_20_wrong_value_despite_citation(self):
        r = self.check(Result.PARTIAL_REVIEW, fields=(Candidate("A", "INVENTADO", ("m1",)), Candidate("C", "GAMA", ("m2",))))
        self.assertEqual(r.rejected_fields, ("A",))

    def test_21_wrong_case_provenance_denies_whole_result(self):
        wrong = Evidence("m1", "LOJA_A", "OUTRO", "customer", {"A": "ALFA"})
        self.check(Result.BLOCKED, snap_over={"messages": (wrong, SOURCES[1])})

    def test_22_wrong_store_provenance_denies_whole_result(self):
        wrong = Evidence("m1", "LOJA_B", "CASO_A", "customer", {"A": "ALFA"})
        self.check(Result.BLOCKED, snap_over={"messages": (wrong, SOURCES[1])})

    def test_23_duplicate_field_is_rejected(self):
        fs = (Candidate("A", "ALFA", ("m1",)), Candidate("A", "ALFA", ("m1",)), Candidate("C", "GAMA", ("m2",)))
        r = self.check(Result.PARTIAL_REVIEW, fields=fs)
        self.assertEqual(r.rejected_fields, ("A",))

    def test_24_duplicate_evidence_is_rejected(self):
        fs = (Candidate("A", "ALFA", ("m1", "m1")), Candidate("C", "GAMA", ("m2",)))
        r = self.check(Result.PARTIAL_REVIEW, fields=fs)
        self.assertEqual(r.rejected_fields, ("A",))

    def test_25_noneligible_field_does_not_apply(self):
        rules = (FieldRule("A", True, False), RULES[1], RULES[2])
        self.check(Result.PARTIAL_REVIEW, snap_over={"rules": rules})

    def test_26_missing_source_message(self):
        fs = (Candidate("A", "ALFA", ("missing",)), Candidate("C", "GAMA", ("m2",)))
        self.check(Result.PARTIAL_REVIEW, fields=fs)

    def test_27_duplicate_catalogue_denied(self):
        self.check(Result.BLOCKED, snap_over={"rules": RULES + (RULES[0],)})

    def test_28_duplicate_messages_denied(self):
        self.check(Result.BLOCKED, snap_over={"messages": SOURCES + (SOURCES[0],)})

    def test_29_untrusted_message_does_not_prove_field(self):
        untrusted = replace(SOURCES[0], authorized=False)
        self.check(Result.PARTIAL_REVIEW, snap_over={"messages": (untrusted, SOURCES[1])})

    def test_30_no_persistence_side_effects(self):
        s, p = fixtures()
        original = (s.form_version, s.case_version, p.fields)
        evaluate_f03(s, p)
        self.assertEqual((s.form_version, s.case_version, p.fields), original)


if __name__ == "__main__":
    unittest.main()
