"""Reconciliation review must never grant scheduling or send rights."""
import unittest
from backend.s0_f02_posthuman_legacy_reconciliation_local import (
    S0F02LegacyReconciliationReview,LegacyReviewState,LegacyReviewResult,_MAP
)
from backend.s0_f02_legacy_observed_origin_local import OriginState
class Tests(unittest.TestCase):
 def test_01_requires_physical_s0_origin(self):
  with self.assertRaises(TypeError):
   S0F02LegacyReconciliationReview(object())
 def test_02_late_origin_requires_review(self):
  self.assertIs(_MAP[OriginState.LATE_ORIGIN_REVIEW_REQUIRED],
                LegacyReviewState.LATE_ORIGIN_REVIEW_REQUIRED)
 def test_03_reserved_external_never_approved(self):
  self.assertIs(_MAP[OriginState.RESERVED_EXTERNAL_UNKNOWN],
                LegacyReviewState.EXTERNAL_DISPATCH_UNKNOWN)
 def test_04_missing_origin_never_approved(self):
  self.assertIs(_MAP[OriginState.INCOMPLETE_ORIGIN_REVIEW_REQUIRED],
                LegacyReviewState.MISSING_ORIGIN_REVIEW_REQUIRED)
 def test_05_mutated_origin_never_approved(self):
  self.assertIs(_MAP[OriginState.MUTATED_ORIGIN_REVIEW_REQUIRED],
                LegacyReviewState.MUTATED_ORIGIN_REVIEW_REQUIRED)
 def test_06_report_carries_only_review_state(self):
  self.assertEqual(tuple(vars(LegacyReviewResult(
    LegacyReviewState.LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY))),('state',))
if __name__=='__main__':
 unittest.main()
