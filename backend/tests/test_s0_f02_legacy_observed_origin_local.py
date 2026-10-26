"""S0 F02 observed-origin gate: never infer external delivery from S0 ledger."""
import unittest
from backend.s0_f02_legacy_observed_origin_local import (
 S0F02LegacyObservedOriginBridge,OriginState,OriginResult,_STATUS
)
class Tests(unittest.TestCase):
 def test_01_requires_physical_witness(self):
  with self.assertRaises(TypeError):
   S0F02LegacyObservedOriginBridge(object())
 def test_02_late_timestamp_blocks(self):
  self.assertIs(_STATUS['LATE_OBSERVED_SOURCE'],
                OriginState.LATE_ORIGIN_REVIEW_REQUIRED)
 def test_03_mutated_digest_blocks(self):
  self.assertIs(_STATUS['MUTATED_ORIGIN'],
                OriginState.MUTATED_ORIGIN_REVIEW_REQUIRED)
 def test_04_no_legacy_is_not_evidence(self):
  self.assertIs(_STATUS['NO_LEGACY_CHAIN'],
                OriginState.INCOMPLETE_ORIGIN_REVIEW_REQUIRED)
 def test_05_reserved_external_is_undetermined(self):
  self.assertIs(_STATUS['RESERVED_EXTERNAL_UNKNOWN'],
                OriginState.RESERVED_EXTERNAL_UNKNOWN)
 def test_06_unknown_status_is_fail_closed(self):
  self.assertIs(_STATUS.get('MODEL_GRANTED',OriginState.S0_REVIEW_REQUIRED),
                OriginState.S0_REVIEW_REQUIRED)
 def test_07_response_has_no_customer_or_send_fields(self):
  self.assertEqual(tuple(vars(OriginResult(OriginState.LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY))),
                   ('state',))
if __name__=='__main__':
 unittest.main()
