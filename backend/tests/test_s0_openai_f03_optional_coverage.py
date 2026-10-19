"""Offline coverage of optional fields explicitly informed by customer.

No mocks, network, production auth, external data, persistence, or model calls.
This checks only synthetic asserted_fields annotations, not natural language.
"""
import unittest
from dataclasses import replace

from backend.s0_openai_bridge.f03_offline_gate import (
    Snapshot, Proposal, FieldRule, Evidence, Candidate,
)
from backend.s0_openai_bridge.f03_assignment_recheck import (
    ClosingSnapshot, CurrentAuthority,
)
from backend.s0_openai_bridge.f03_review_pipeline import (
    review_f03_offline, PipelineStatus,
)


def fixture():
    s = Snapshot('store-A', 'case-1', 'close-1', 'hash-1', 7, 3,
                 'catalog-1', True, True, True, 'human_bank_collection',
                 (FieldRule('required', True, True),
                  FieldRule('optional', False, True)),
                 (Evidence('m1', 'store-A', 'case-1', 'customer',
                           {'required': 'A', 'optional': 'B'}),))
    p = Proposal('store-A', 'case-1', 'close-1', 'hash-1', 7, 3,
                 'catalog-1', (Candidate('required', 'A', ('m1',)),))
    c = ClosingSnapshot('store-A', 'case-1', 'close-1', 'operator-1',
                        'assignment-1', 7, 3, 'm1', 'hash-1', 'catalog-1')
    a = CurrentAuthority('store-A', 'case-1', 'close-1', 'operator-1',
                         'assignment-1', 7, 3, 'm1', 'hash-1', 'catalog-1',
                         True, True, True, True, 'human_bank_collection', False, True)
    return s, p, c, a


class OptionalCoverage(unittest.TestCase):
    def result(self, s=None, p=None, c=None, a=None):
        orig = fixture()
        def edit(x, updates):
            return replace(x, **updates) if isinstance(updates, dict) else (updates or x)
        return review_f03_offline(edit(orig[0], s), edit(orig[1], p),
                                  edit(orig[2], c), edit(orig[3], a))

    def test_01_informed_optional_omission_requires_review(self):
        r = self.result()
        self.assertEqual(r.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(r.missing_required_codes, ())
        self.assertEqual(r.omitted_informed_optional_codes, ('optional',))
        self.assertEqual(r.candidate_field_codes, ('required',))

    def test_02_present_optional_proposal_keeps_review_only(self):
        p = fixture()[1]
        out = self.result(p={'fields': p.fields + (Candidate('optional', 'B', ('m1',)),)})
        self.assertEqual((out.status, out.omitted_informed_optional_codes),
                         (PipelineStatus.REVIEW_ONLY, ()))

    def test_03_uninformed_optional_does_not_force_review(self):
        msg = Evidence('m1', 'store-A', 'case-1', 'customer', {'required': 'A'})
        r = self.result(s={'messages': (msg,)})
        self.assertEqual((r.status, r.omitted_informed_optional_codes),
                         (PipelineStatus.REVIEW_ONLY, ()))

    def test_04_operator_statement_not_customer_data(self):
        s = fixture()[0]
        msg = Evidence('m2', 'store-A', 'case-1', 'operator', {'optional': 'B'})
        no_optional = replace(s.messages[0], asserted_fields={'required': 'A'})
        out = self.result(s={'messages': (no_optional, msg)})
        self.assertEqual(out.status, PipelineStatus.REVIEW_ONLY)

    def test_05_untrusted_customer_not_authoritative(self):
        s = fixture()[0]
        no_optional = replace(s.messages[0], asserted_fields={'required': 'A'})
        untrusted = Evidence('m2', 'store-A', 'case-1', 'customer',
                             {'optional': 'B'}, authorized=False)
        self.assertEqual(self.result(s={'messages': (no_optional, untrusted)}).status,
                         PipelineStatus.REVIEW_ONLY)

    def test_06_revoked_store_grant_does_not_expose_omission(self):
        r = self.result(a={'store_grant': False})
        self.assertEqual(r.status, PipelineStatus.DENIED)
        self.assertEqual(r.omitted_informed_optional_codes, ())

    def test_07_transferred_operator_does_not_expose_omission(self):
        r = self.result(a={'assignment': 'assignment-2'})
        self.assertEqual(r.status, PipelineStatus.STALE)
        self.assertEqual(r.omitted_informed_optional_codes, ())

    def test_08_changed_customer_watermark_does_not_expose_omission(self):
        r = self.result(a={'watermark': 'm2'})
        self.assertEqual(r.status, PipelineStatus.STALE)
        self.assertEqual(r.omitted_informed_optional_codes, ())

    def test_09_foreign_store_evidence_cannot_trigger_review(self):
        s = fixture()[0]
        evil = Evidence('m2', 'store-B', 'case-1', 'customer', {'optional': 'B'})
        r = self.result(s={'messages': s.messages + (evil,)})
        self.assertEqual(r.status, PipelineStatus.DENIED)
        self.assertEqual(r.omitted_informed_optional_codes, ())

    def test_10_multiple_optional_omissions_sorted(self):
        s = fixture()[0]
        rules = s.rules + (FieldRule('extra', False, True),)
        msg = replace(s.messages[0], asserted_fields={
            'required': 'A', 'optional': 'B', 'extra': 'C'})
        r = self.result(s={'rules': rules, 'messages': (msg,)})
        self.assertEqual(r.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(r.omitted_informed_optional_codes, ('extra', 'optional'))

    def test_11_empty_optional_value_is_not_informed(self):
        s = fixture()[0]
        msg = replace(s.messages[0], asserted_fields={'required': 'A', 'optional': '  '})
        self.assertEqual(self.result(s={'messages': (msg,)}).status, PipelineStatus.REVIEW_ONLY)

    def test_12_proposed_but_rejected_optional_follows_rejection_route(self):
        p = fixture()[1]
        offered = Candidate('optional', 'WRONG', ('m1',))
        r = self.result(p={'fields': p.fields + (offered,)})
        self.assertEqual(r.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(r.rejected_field_codes, ('optional',))
        self.assertEqual(r.omitted_informed_optional_codes, ())


    def test_13_only_optional_informed_and_no_model_fields_still_requires_review(self):
        s = fixture()[0]
        msg = replace(s.messages[0], asserted_fields={'optional': 'B'})
        r = self.result(s={'rules': (FieldRule('optional', False, True),),
                           'messages': (msg,)},
                        p={'fields': ()}, a={'result_has_validated_fields': False})
        self.assertEqual(r.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(r.missing_required_codes, ())
        self.assertEqual(r.omitted_informed_optional_codes, ('optional',))

    def test_14_no_fields_preserves_required_and_optional_gaps_separately(self):
        r = self.result(p={'fields': ()}, a={'result_has_validated_fields': False})
        self.assertEqual(r.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(r.missing_required_codes, ('required',))
        self.assertEqual(r.omitted_informed_optional_codes, ('optional',))

    def test_15_no_informed_fields_means_not_ready_not_invented(self):
        s = fixture()[0]
        empty = replace(s.messages[0], asserted_fields={})
        r = self.result(s={'rules': (FieldRule('optional', False, True),),
                           'messages': (empty,)},
                        p={'fields': ()}, a={'result_has_validated_fields': False})
        self.assertEqual(r.status, PipelineStatus.NOT_READY)
        self.assertEqual(r.omitted_informed_optional_codes, ())

    def test_16_informed_optional_without_autoapply_is_still_flagged_not_applied(self):
        s = fixture()[0]
        r = self.result(s={'rules': (s.rules[0], FieldRule('optional', False, False))})
        self.assertEqual(r.status, PipelineStatus.REVIEW_REQUIRED)
        self.assertEqual(r.omitted_informed_optional_codes, ('optional',))
        self.assertFalse(hasattr(r, 'applied'))


if __name__ == '__main__':
    unittest.main()
