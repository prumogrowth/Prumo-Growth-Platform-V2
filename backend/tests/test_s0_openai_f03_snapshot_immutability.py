"""Protect the synthetic F03 source fixture against mutable evidence aliases.

No provider, SQL, production identity, integration deployment, or bank decisions.
These checks do not prove immutability of a real S0 physical snapshot.
"""
import unittest
from collections import UserDict
from dataclasses import replace
from types import MappingProxyType

from backend.s0_openai_bridge.f03_offline_gate import (
    Candidate, Evidence, FieldRule, Proposal, Result, Snapshot, evaluate_f03,
)
from backend.s0_openai_bridge.f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority,
)
from backend.s0_openai_bridge.f03_review_pipeline import (
    PipelineStatus, review_f03_offline,
)


def scenario(fields=None, source=None):
    fields = {'required': 'OLD'} if fields is None else fields
    message = Evidence('msg-1', 'store-A', 'case-1', 'customer', fields)
    snapshot = Snapshot('store-A', 'case-1', 'close-1', 'hash-1', 7, 3,
                        'catalog-1', True, True, True, 'human_bank_collection',
                        (FieldRule('required', True, True), FieldRule('optional', False, True)),
                        (message,))
    proposal = Proposal('store-A', 'case-1', 'close-1', 'hash-1', 7, 3,
                        'catalog-1', (Candidate('required', 'NEW', ('msg-1',)),))
    close = ClosingSnapshot('store-A', 'case-1', 'close-1', 'operator-1',
                            'assignment-1', 7, 3, 'msg-1', 'hash-1', 'catalog-1')
    authority = CurrentAuthority('store-A', 'case-1', 'close-1', 'operator-1',
                                 'assignment-1', 7, 3, 'msg-1', 'hash-1', 'catalog-1',
                                 True, True, True, True,
                                 'human_bank_collection', False, False)
    return snapshot, proposal, close, authority


class EvidenceImmutabilityTests(unittest.TestCase):
    def test_01_external_mutation_cannot_make_forged_candidate_valid(self):
        fields = {'required': 'OLD'}
        snap, proposal, _, _ = scenario(fields)
        self.assertEqual(evaluate_f03(snap, proposal).status, Result.REVIEW)
        fields['required'] = 'NEW'
        self.assertEqual(evaluate_f03(snap, proposal).status, Result.REVIEW)

    def test_02_direct_frozen_evidence_mapping_mutation_is_denied(self):
        snap, _, _, _ = scenario()
        with self.assertRaises(TypeError):
            snap.messages[0].asserted_fields['required'] = 'NEW'

    def test_03_external_deletion_cannot_erase_a_source_value(self):
        fields = {'required': 'OLD'}
        snap, _, _, _ = scenario(fields)
        fields.clear()
        self.assertEqual(snap.messages[0].asserted_fields['required'], 'OLD')

    def test_04_external_optional_addition_does_not_create_new_omission(self):
        fields = {'required': 'OLD'}
        snap, proposal, close, current = scenario(fields)
        proposal = replace(proposal, fields=(Candidate('required', 'OLD', ('msg-1',)),))
        current = replace(current, result_has_validated_fields=True)
        fields['optional'] = 'INJECTED'
        result = review_f03_offline(snap, proposal, close, current)
        self.assertEqual(result.status, PipelineStatus.REVIEW_ONLY)
        self.assertEqual(result.omitted_informed_optional_codes, ())

    def test_05_optional_present_at_capture_remains_visible_for_review(self):
        fields = {'required': 'OLD', 'optional': 'INFORMED'}
        snap, proposal, close, current = scenario(fields)
        proposal = replace(proposal, fields=(Candidate('required', 'OLD', ('msg-1',)),))
        current = replace(current, result_has_validated_fields=True)
        fields.pop('optional')
        result = review_f03_offline(snap, proposal, close, current)
        self.assertEqual(result.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(result.omitted_informed_optional_codes, ('optional',))

    def test_06_external_mutation_cannot_hide_a_conflict(self):
        fields = {'required': 'OLD'}
        snap, proposal, _, _ = scenario(fields)
        proposal = replace(proposal, fields=(Candidate('required', 'OLD', ('msg-1',)),))
        conflicting = Evidence('msg-2', 'store-A', 'case-1', 'customer', {'required': 'DIFFERENT'})
        snap = replace(snap, messages=snap.messages + (conflicting,))
        fields['required'] = 'DIFFERENT'
        review = evaluate_f03(snap, proposal)
        self.assertEqual(review.status, Result.REVIEW)
        self.assertEqual(review.rejected_fields, ('required',))

    def test_07_source_dict_can_change_without_mutating_captured_snapshot(self):
        fields = {'required': 'OLD'}
        snap, _, _, _ = scenario(fields)
        self.assertIsNot(snap.messages[0].asserted_fields, fields)
        fields.update({'required': 'NEW', 'optional': 'NEW'})
        self.assertEqual(dict(snap.messages[0].asserted_fields), {'required': 'OLD'})

    def test_08_two_messages_from_same_input_dict_get_distinct_captures(self):
        fields = {'required': 'OLD'}
        one = Evidence('msg-1', 'store-A', 'case-1', 'customer', fields)
        fields['required'] = 'NEW'
        two = Evidence('msg-2', 'store-A', 'case-1', 'customer', fields)
        self.assertEqual(one.asserted_fields['required'], 'OLD')
        self.assertEqual(two.asserted_fields['required'], 'NEW')

    def test_09_custom_mutable_mapping_is_copied(self):
        fields = UserDict({'required': 'OLD'})
        msg = Evidence('msg-1', 'store-A', 'case-1', 'customer', fields)
        fields['required'] = 'NEW'
        self.assertEqual(msg.asserted_fields['required'], 'OLD')
        with self.assertRaises(TypeError):
            msg.asserted_fields['required'] = 'NEW'

    def test_10_existing_mapping_proxy_is_copied(self):
        original = {'required': 'OLD'}
        msg = Evidence('msg-1', 'store-A', 'case-1', 'customer', MappingProxyType(original))
        original['required'] = 'NEW'
        self.assertEqual(msg.asserted_fields['required'], 'OLD')

    def test_11_malformed_non_mapping_still_fails_closed(self):
        snap, proposal, _, _ = scenario()
        bad = replace(snap.messages[0], asserted_fields=['unexpected'])
        self.assertEqual(evaluate_f03(replace(snap, messages=(bad,)), proposal).status,
                         Result.BLOCKED)

    def test_12_invalid_field_value_type_is_not_coerced_into_a_string(self):
        snap, proposal, _, _ = scenario()
        bad = replace(snap.messages[0], asserted_fields={'required': 123})
        self.assertEqual(evaluate_f03(replace(snap, messages=(bad,)), proposal).status,
                         Result.BLOCKED)

    def test_13_concurrent_external_dict_edit_cannot_upgrade_pipeline(self):
        fields = {'required': 'OLD'}
        snap, proposal, close, current = scenario(fields)
        before = review_f03_offline(snap, proposal, close, current)
        fields['required'] = 'NEW'
        after = review_f03_offline(snap, proposal, close, current)
        self.assertEqual(before.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(before, after)
        self.assertEqual(after.candidate_field_codes, ())

    def test_14_replacing_evidence_creates_new_record_not_old_mutation(self):
        snap, proposal, _, _ = scenario()
        new = replace(snap.messages[0], asserted_fields={'required': 'NEW'})
        new_snapshot = replace(snap, messages=(new,))
        self.assertEqual(evaluate_f03(new_snapshot, proposal).status, Result.PROPOSAL_ONLY)
        self.assertEqual(evaluate_f03(snap, proposal).status, Result.REVIEW)

    def test_15_store_scoped_evidence_is_not_promoted_by_shared_dict_alias(self):
        shared = {'required': 'OLD'}
        one = Evidence('msg-a', 'store-A', 'case-a', 'customer', shared)
        two = Evidence('msg-b', 'store-B', 'case-b', 'customer', shared)
        shared['required'] = 'NEW'
        self.assertEqual(one.asserted_fields['required'], 'OLD')
        self.assertEqual(two.asserted_fields['required'], 'OLD')
        self.assertEqual((one.store, two.store), ('store-A', 'store-B'))


if __name__ == '__main__':
    unittest.main()
