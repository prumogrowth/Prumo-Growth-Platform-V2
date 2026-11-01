"""Read-only audit COUNTEREXAMPLES: existing S0 v0.2 readback, PG17 disposable.

Each test verifies a discrepancy is OBSERVABLE in the frozen candidate.
It is NOT a compliant behavior test and MUST be removed/reworked after fixes.
No implementation source is edited. No test uses a live account or sends.
"""
import os
import unittest
from dataclasses import replace
from integration.s0s1_pre_dispatch_v02.test_pg17_service import PDReadbackPhysical

@unittest.skipUnless(os.getenv('M09_PG17_DISPOSABLE')=='YES',
  'only disposable PG17')
class AuditS0V02Counterexamples(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  PDReadbackPhysical.setUpClass()
 @classmethod
 def tearDownClass(cls):
  PDReadbackPhysical.tearDownClass()
 def setUp(self):
  self.t=PDReadbackPhysical('test_01_stage_does_not_attest_commit')
  self.t.setUp()
 def begin(self):
  stage=self.t.act()
  self.assertEqual(stage['status'],'LAB_RESERVATION_STAGED_BEFORE_COMMIT')
  before=self.t.rb()
  self.assertEqual(before['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def positive_despite_drift(self):
  got=self.t.rb()
  self.assertEqual(got['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH',got)
  self.assertTrue(got['commit_verified'])
  self.assertFalse(got['send_authorized'])
  self.assertFalse(got['graph_dispatch_authorized'])
  return got
 def test_01_template_purpose_modified_without_revision_not_detected(self):
  self.begin()
  self.t.sql("UPDATE s0_pre_dispatch_lab.templates "
    "SET template_purpose_ref='DIFFERENT_PURPOSE' "
    "WHERE template_ref='tpl_A'")
  self.positive_despite_drift()
 def test_02_grant_template_purpose_modified_without_revision_not_detected(self):
  self.begin()
  self.t.sql("UPDATE s0_pre_dispatch_lab.grants "
    "SET template_purpose_ref='DIFFERENT_PURPOSE' "
    "WHERE case_ref='case_A'")
  self.positive_despite_drift()
 def test_03_m09_grant_phone_modified_without_revision_not_detected(self):
  self.begin()
  self.t.sql("UPDATE s0_m09_lab.grants "
    "SET phone_number_id='299999' WHERE canal_id='channel_A'")
  self.positive_despite_drift()
 def test_04_quota_counter_reset_without_revision_not_detected(self):
  self.begin()
  self.t.sql("UPDATE s0_pd_v02_lab.quotas SET consumed=0 "
   "WHERE window_ref='window_A'")
  self.positive_despite_drift()
 def test_05_cancel_accepts_different_waba_in_supplied_scope(self):
  self.begin()
  other=replace(self.t.scope,waba_id='DIFFERENT_WABA')
  from integration.s0s1_pre_dispatch_v02.pg17_service import cancel
  with self.t.lab.admin() as c:
   response=cancel(c,attempt_ref=self.t.req2['attempt_ref'],scope=other)
  self.assertEqual(response['status'],'LAB_CANCEL_STAGED_BEFORE_COMMIT',response)
  got=self.t.rb()
  self.assertEqual(got['status'],'LAB_CANCELLED_NO_DISPATCH')
  self.assertFalse(got['send_authorized'])
if __name__=='__main__':
 unittest.main()
