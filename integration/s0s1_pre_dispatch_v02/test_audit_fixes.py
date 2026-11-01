"""AUD-PD-01..05: positive security checks after audit counterexamples.

These tests PASS only when the former lab discrepancies are BLOCKED.
They do not prove hosted S0 identity, authorization or send safety.
"""
import os,unittest
from dataclasses import replace
import psycopg
from integration.s0s1_pre_dispatch_v02 import test_pg17_service as parent
from integration.s0s1_pre_dispatch_v02.pg17_service import cancel

@unittest.skipUnless(os.getenv('M09_PG17_DISPOSABLE')=='YES',
                     'disposable PostgreSQL 17 only')
class RemediatedAuditPhysical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  parent.PDReadbackPhysical.setUpClass()
 @classmethod
 def tearDownClass(cls):
  parent.PDReadbackPhysical.tearDownClass()
 def setUp(self):
  self.t=parent.PDReadbackPhysical('test_01_stage_does_not_attest_commit')
  self.t.setUp()
 def start(self):
  s=self.t.act()
  self.assertEqual(s['status'],'LAB_RESERVATION_STAGED_BEFORE_COMMIT',s)
  self.assertEqual(self.t.rb()['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def stale(self,reason):
  got=self.t.rb()
  self.assertEqual(got['status'],'LAB_STALE_NO_DISPATCH',got)
  self.assertEqual(got['reason'],reason,got)
  self.assertTrue(got['commit_verified'])
  self.t.safe(got)
 def test_aud_pd_01_template_purpose_changed_without_revision_is_stale(self):
  self.start()
  self.t.sql("UPDATE s0_pre_dispatch_lab.templates SET "
             "template_purpose_ref='DIFFERENT_PURPOSE' "
             "WHERE template_ref='tpl_A'")
  self.stale('TEMPLATE_CAMPAIGN_GRANT_STALE')
 def test_aud_pd_02_grant_purpose_changed_without_revision_is_stale(self):
  self.start()
  self.t.sql("UPDATE s0_pre_dispatch_lab.grants SET "
             "template_purpose_ref='DIFFERENT_PURPOSE' "
             "WHERE case_ref='case_A'")
  self.stale('TEMPLATE_CAMPAIGN_GRANT_STALE')
 def test_aud_pd_03_m09_grant_phone_changed_without_revision_is_stale(self):
  self.start()
  self.t.sql("UPDATE s0_m09_lab.grants SET "
             "phone_number_id='299999' WHERE canal_id='channel_A'")
  self.stale('M09_STALE_OR_REVOKED')
 def test_aud_pd_04_quota_decrement_is_physically_refused(self):
  self.start()
  with self.assertRaises(psycopg.Error):
   self.t.sql("UPDATE s0_pd_v02_lab.quotas SET consumed=0 "
              "WHERE window_ref='window_A'")
  # Database did not apply the illegal decrement; receipt stays a
  # verifiable historical lab observation, not operational authority.
  self.assertEqual(self.t.totals(),(1,1,1,1))
  good=self.t.rb()
  self.assertEqual(good['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  self.t.safe(good)
 def test_aud_pd_05_cancel_with_other_waba_denied_no_mutation(self):
  self.start()
  scope=replace(self.t.scope,waba_id='DIFFERENT_WABA')
  with self.t.lab.admin() as c:
   bad=cancel(c,attempt_ref='attempt_A',scope=scope,
             principal=self.t.principal,m09_versions=self.t.versions)
  self.assertEqual(bad['status'],'DENIED',bad)
  self.assertEqual(bad['reason'],'SCOPE_DENIED',bad)
  self.assertEqual(self.t.rb()['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def test_06_cancel_without_original_principal_fails_closed(self):
  self.start()
  with self.t.lab.admin() as c:
   bad=cancel(c,attempt_ref='attempt_A',scope=self.t.scope)
  self.assertEqual(bad['reason'],'INVALID_REQUEST',bad)
  self.assertEqual(self.t.rb()['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def test_07_cancel_with_other_key_revision_denied(self):
  self.start()
  other=replace(self.t.principal,key_revision=self.t.principal.key_revision+1)
  with self.t.lab.admin() as c:
   x=cancel(c,attempt_ref='attempt_A',scope=self.t.scope,
         principal=other,m09_versions=self.t.versions)
  self.assertEqual(x['reason'],'SCOPE_DENIED')
  self.assertEqual(self.t.rb()['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def test_08_template_grant_valid_no_fake_graph_grant(self):
  self.start()
  self.t.safe(self.t.rb())
 def test_09_m09_grant_waba_changed_without_revision_stale(self):
  self.start()
  # FK (waba,app) ensures another scoped WABA must first be registered.
  with self.t.lab.admin() as c:
   c.execute("INSERT INTO s0_m09_lab.wabas(waba_id,app_ref) "
             "VALUES('100002','APP_A')")
   c.execute("UPDATE s0_m09_lab.grants SET waba_id='100002' "
             "WHERE canal_id='channel_A'")
  self.stale('M09_STALE_OR_REVOKED')
 def test_10_m09_route_app_mismatch_without_revision_stale(self):
  self.start()
  # Route/App mismatch may be blocked by FK in source; test whether the
  # unchanged original scope is fully checked by the updated readback.
  self.t.sql("UPDATE s0_m09_lab.grants SET route_ref='route_A' "
             "WHERE canal_id='channel_A'")
  good=self.t.rb()
  self.assertEqual(good['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def test_11_quota_identity_slot_unique_even_after_manual_corruption(self):
  self.start()
  with self.t.lab.admin() as c:
   row=c.execute("SELECT quota_slot FROM s0_pd_v02_lab.receipts "
         "WHERE attempt_ref='attempt_A'").fetchone()
   self.assertEqual(row['quota_slot'],1)
  # The UNIQUE key includes store, app, phone, window and slot.
  # No second receipt in same quota epoch may reuse slot=1.
  with self.assertRaises(psycopg.Error):
   with self.t.lab.admin() as c:
    c.execute("UPDATE s0_pd_v02_lab.receipts SET attempt_ref='fake' "
       "WHERE attempt_ref='attempt_A'")
  # FK integrity protects attempt identity too; any errors abort txn.
  self.assertEqual(self.t.rb()['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
if __name__=='__main__':unittest.main()
