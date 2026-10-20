"""Offline-only safety/shape checks of the UNRATIFIED F03 candidate wire format."""
import copy
from dataclasses import replace
import unittest

from backend.s0_openai_bridge.f03_offline_gate import (
    Evidence, FieldRule, Snapshot,
)
from backend.s0_openai_bridge.f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority,
)
from backend.s0_openai_bridge.f03_candidate_wire import (
    WireStatus, inspect_f03_candidate_wire,
)


def fixtures():
    snap = Snapshot(
        'store-A', 'case-1', 'close-1', 'hash-1', 2, 3, 'cat-1',
        True, True, True, 'human_bank_collection',
        (FieldRule('A', True, True), FieldRule('B', False, True)),
        (Evidence('msg-1', 'store-A', 'case-1', 'customer', {'A': 'DEMO'}),),
    )
    close = ClosingSnapshot('store-A', 'case-1', 'close-1', 'operator-1',
                            'assignment-1', 2, 3, 'msg-1', 'hash-1', 'cat-1')
    current = CurrentAuthority('store-A', 'case-1', 'close-1', 'operator-1',
                               'assignment-1', 2, 3, 'msg-1', 'hash-1', 'cat-1',
                               True, True, True, True, 'human_bank_collection',
                               False, True)
    raw = {
        'contract_version': 's0-openai.v0.2-candidate',
        'request_id': 'req-1',
        'operation_kind': 'human_close_extract',
        'closure_event_id': 'close-1',
        'snapshot_hash': 'hash-1',
        'form_version_observed': 3,
        'outcome': 'PROPOSED',
        'fields_proposed': [{'field_code': 'A', 'proposed_value': 'DEMO',
                             'source_message_refs': ['msg-1'],
                             'source_kind': 'client_statement', 'certainty': 'explicit'}],
        'missing_fields': [], 'conflicts': [], 'extraction_warnings': [],
    }
    return raw, snap, close, current


class CandidateWireTests(unittest.TestCase):
    def check(self, expected, *, raw=None, snap=None, close=None, current=None,
              request_id='req-1', contract_version='s0-openai.v0.2-candidate'):
        a, b, c, d = fixtures()
        res = inspect_f03_candidate_wire(
            a if raw is None else raw, b if snap is None else snap,
            c if close is None else close, d if current is None else current,
            request_id=request_id, contract_version=contract_version,
        )
        self.assertEqual(res.status, expected, str(res))
        return res

    def mutate(self, key, value):
        raw, _, _, _ = fixtures()
        raw[key] = value
        return raw

    def test_01_exact_provisional_shape_remains_review_only(self):
        result = self.check(WireStatus.REVIEW_ONLY)
        self.assertEqual(result.candidate_field_codes, ('A',))
        self.assertNotIn('DEMO', str(result))
        self.assertFalse(hasattr(result, 'applied'))

    def test_02_not_a_write_or_status_transition(self):
        raw, snapshot, closing, current = fixtures()
        previous = copy.deepcopy(raw)
        self.check(WireStatus.REVIEW_ONLY, raw=raw)
        self.assertEqual(raw, previous)
        self.assertEqual(snapshot.case_version, 2)
        self.assertEqual(closing.case_version, current.case_version)

    def test_03_unknown_top_level_key_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=self.mutate('send_whatsapp', True))

    def test_04_unknown_field_key_rejected(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'][0]['apply_by_s0'] = True
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=raw)

    def test_05_wrong_request_id_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=self.mutate('request_id', 'other'))

    def test_06_wrong_contract_version_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT,
                   raw=self.mutate('contract_version', 'other'))

    def test_07_wrong_operation_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=self.mutate('operation_kind', 'sales_reply'))

    def test_08_wrong_closure_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT,
                   raw=self.mutate('closure_event_id', 'other'))

    def test_09_wrong_snapshot_rejected_as_invalid_model_output(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=self.mutate('snapshot_hash', 'old'))

    def test_10_wrong_form_version_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT,
                   raw=self.mutate('form_version_observed', 4))

    def test_11_boolean_form_version_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT,
                   raw=self.mutate('form_version_observed', True))

    def test_12_invalid_output_shape_list_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=[])

    def test_13_empty_field_value_rejected(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'][0]['proposed_value'] = '  '
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=raw)

    def test_14_invented_field_blocked_by_real_catalog_validator(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'][0]['field_code'] = 'INVENTED'
        self.check(WireStatus.DENIED, raw=raw)

    def test_15_unknown_evidence_rejected_by_field_validator(self):
        raw, _, _, current = fixtures()
        raw['fields_proposed'][0]['source_message_refs'] = ['msg-unknown']
        out = self.check(WireStatus.REVIEW_REQUIRED, raw=raw,
                         current=replace(current, result_has_validated_fields=False))
        self.assertEqual(out.missing_required_codes, ('A',))

    def test_16_non_customer_source_requires_review(self):
        raw, snap, _, current = fixtures()
        actor = replace(snap.messages[0], actor='operator')
        out = self.check(WireStatus.REVIEW_REQUIRED, raw=raw,
                         snap=replace(snap, messages=(actor,)),
                         current=replace(current, result_has_validated_fields=False))
        self.assertEqual(out.candidate_field_codes, ())

    def test_17_source_mismatch_store_denied(self):
        raw, snap, _, _ = fixtures()
        source = replace(snap.messages[0], store='store-B')
        self.check(WireStatus.DENIED, raw=raw, snap=replace(snap, messages=(source,)))

    def test_18_malformed_references_rejected_without_exception(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'][0]['source_message_refs'] = [[1]]
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=raw)

    def test_19_duplicate_references_rejected(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'][0]['source_message_refs'] = ['msg-1', 'msg-1']
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=raw)

    def test_20_conflict_structure_not_yet_ratified_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT,
                   raw=self.mutate('conflicts', [{'field_code': 'A'}]))

    def test_21_missing_field_structure_not_yet_ratified_rejected(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT,
                   raw=self.mutate('missing_fields', [{'field_code': 'B'}]))

    def test_22_unratified_followup_advisory_not_construed_as_plan(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT,
                   raw=self.mutate('followup_need_advisory', {'suggested': 'YES'}))

    def test_23_failed_model_output_cannot_become_proposal(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT,
                   raw=self.mutate('outcome', 'FAILED'))

    def test_24_partial_outcome_forces_review_of_valid_fields(self):
        out = self.check(WireStatus.REVIEW_REQUIRED, raw=self.mutate('outcome', 'PARTIAL'))
        self.assertEqual(out.candidate_field_codes, ('A',))

    def test_25_needs_review_outcome_forces_review(self):
        self.check(WireStatus.REVIEW_REQUIRED,
                   raw=self.mutate('outcome', 'NEEDS_REVIEW'))

    def test_26_empty_fields_not_ready(self):
        raw, _, _, current = fixtures()
        raw['fields_proposed'] = []
        result = self.check(WireStatus.REVIEW_REQUIRED, raw=raw,
                            current=replace(current, result_has_validated_fields=False))
        self.assertEqual(result.missing_required_codes, ('A',))

    def test_27_revoked_store_grant_outweighs_malformed_model(self):
        _, _, _, current = fixtures()
        result = self.check(WireStatus.DENIED, raw={},
                            current=replace(current, store_grant=False))
        self.assertEqual(result.candidate_field_codes, ())

    def test_28_transferred_assignment_outweighs_model_mismatch(self):
        _, _, _, current = fixtures()
        self.check(WireStatus.STALE, raw={},
                   current=replace(current, assignment='new'))

    def test_29_new_inbound_outweighs_model_mismatch(self):
        _, _, _, current = fixtures()
        self.check(WireStatus.STALE, raw={},
                   current=replace(current, watermark='msg-2'))

    def test_30_invalid_synthetic_scope_outweighs_model(self):
        _, _, closing, _ = fixtures()
        self.check(WireStatus.DENIED, raw={}, close=replace(closing, store='store-B'))

    def test_31_stale_synthetic_snapshot_outweighs_model(self):
        _, _, closing, _ = fixtures()
        self.check(WireStatus.STALE, raw={}, close=replace(closing, snapshot_hash='old'))

    def test_32_lost_session_no_field_codes(self):
        _, _, _, current = fixtures()
        out = self.check(WireStatus.DENIED,
                         current=replace(current, authenticated_session=False))
        self.assertEqual(out.missing_required_codes, ())

    def test_33_empty_optional_model_validates_no_extra(self):
        raw, snap, _, current = fixtures()
        raw['fields_proposed'] = [{'field_code': 'A', 'proposed_value': 'DEMO',
                                   'source_message_refs': ['msg-1']}]
        snap = replace(snap, rules=(FieldRule('A', True, True),))
        self.check(WireStatus.REVIEW_ONLY, raw=raw, snap=snap)

    def test_34_overlong_field_value_rejected(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'][0]['proposed_value'] = 'X' * 4097
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=raw)

    def test_35_malformed_source_kind_rejected(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'][0]['source_kind'] = 'operator_note'
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=raw)

    def test_36_model_confidence_cannot_replace_explicit_evidence(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'][0]['certainty'] = 'high_confidence'
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=raw)

    def test_37_non_dictionary_field_rejected(self):
        raw, _, _, _ = fixtures()
        raw['fields_proposed'] = ['malformed']
        self.check(WireStatus.INVALID_MODEL_OUTPUT, raw=raw)

    def test_38_no_request_id_is_not_authority(self):
        self.check(WireStatus.DENIED, request_id='')

    def test_39_wrong_declared_expected_contract_version_fails_closed(self):
        self.check(WireStatus.INVALID_MODEL_OUTPUT, contract_version='other')

    def test_40_forged_synthetic_authority_flag_denied(self):
        _, _, _, current = fixtures()
        self.check(WireStatus.DENIED,
                   current=replace(current, store_grant='true'))


if __name__ == '__main__':
    unittest.main()
