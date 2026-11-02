"""G2 PG17 consistent historical readback, NOT a send/Graph lease."""
import os,unittest
from integration.s0s1_pre_dispatch_v02 import test_pg17_service as base
from integration.s0s1_pd_g2.snapshot import classify_historical_snapshot as run,G2_VERSION

@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE')=='YES',
                     'requires disposable PG17')
class SnapshotReadbackPhysical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  base.PDReadbackPhysical.setUpClass()
 @classmethod
 def tearDownClass(cls):
  base.PDReadbackPhysical.tearDownClass()
 def setUp(self):
  self.t=base.PDReadbackPhysical('test_01_stage_does_not_attest_commit')
  self.t.setUp()
 def reserve(self):
  s=self.t.act()
  self.assertEqual(s['status'],'LAB_RESERVATION_STAGED_BEFORE_COMMIT',s)
 def snap(self,hook=None,request=None):
  with self.t.lab.admin() as c:
   return run(c,request or self.t.req2,
    scope=self.t.scope,principal=self.t.principal,
    m09_versions=self.t.versions,_lab_interleave=hook)
 def safe(self,x):
  self.assertEqual(x['contract_version'],G2_VERSION)
  self.assertFalse(x['snapshot_current_authority'])
  self.assertFalse(x['authenticated_actor'])
  self.assertFalse(x['authenticated_receipt'])
  self.assertFalse(x['attested_attempt_binding'])
  for f in ('outbox_authorized','lease_issued',
    'graph_dispatch_authorized','send_authorized',
    'automatic_retry_authorized','production_authorized'):
   self.assertIs(x[f],False,f)
 def test_01_postcommit_consistent_snapshot_classifies_historical_only(self):
  self.reserve();x=self.snap()
  self.assertEqual(x['status'],'LAB_HISTORICAL_SNAPSHOT_NO_DISPATCH',x)
  self.assertTrue(x['snapshot_consistent_during_read'])
  self.assertEqual(x['transaction_isolation'],'REPEATABLE_READ_READ_ONLY')
  self.assertEqual(x['classification']['status'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  self.safe(x)
 def test_02_precommitted_consent_revoke_is_stale(self):
  self.reserve()
  self.t.sql("UPDATE s0_pre_dispatch_lab.consents "
    "SET state='REVOKED',revision=revision+1 WHERE case_ref='case_A'")
  x=self.snap()
  self.assertEqual(x['classification']['reason'],'CONSENT_STALE_OR_REVOKED')
  self.safe(x)
 def test_03_concurrent_consent_revoke_after_snapshot_is_historical_not_authority(self):
  self.reserve()
  def revoke():
   self.t.sql("UPDATE s0_pre_dispatch_lab.consents "
    "SET state='REVOKED',revision=revision+1 WHERE case_ref='case_A'")
  x=self.snap(revoke)
  self.assertEqual(x['classification']['status'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH',x)
  self.safe(x)
  fresh=self.snap()
  self.assertEqual(fresh['classification']['reason'],
                   'CONSENT_STALE_OR_REVOKED')
  self.safe(fresh)
 def test_04_cancel_after_snapshot_is_historical_and_next_snapshot_cancelled(self):
  self.reserve()
  def cancel_after_snapshot():
   self.assertEqual(self.t.stop()['status'],
                    'LAB_CANCEL_STAGED_BEFORE_COMMIT')
  before=self.snap(cancel_after_snapshot)
  self.assertEqual(before['classification']['status'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  self.safe(before)
  after=self.snap()
  self.assertEqual(after['classification']['status'],
                   'LAB_CANCELLED_NO_DISPATCH')
  self.safe(after)
 def test_05_m09_grant_phone_changed_after_snapshot_not_mixed_read(self):
  self.reserve()
  def mutate():
   self.t.sql("UPDATE s0_m09_lab.grants "
    "SET phone_number_id='299999' WHERE canal_id='channel_A'")
  old=self.snap(mutate)
  self.assertEqual(old['classification']['status'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  self.safe(old)
  new=self.snap()
  self.assertEqual(new['classification']['reason'],'M09_STALE_OR_REVOKED')
 def test_06_caller_transaction_in_progress_fails_closed_without_mutation(self):
  self.reserve()
  with self.t.lab.admin() as c:
   c.execute('SELECT 1')
   denied=run(c,self.t.req2,scope=self.t.scope,
      principal=self.t.principal,m09_versions=self.t.versions)
   self.assertEqual(denied['reason'],'CALLER_TRANSACTION_ALREADY_ACTIVE')
   self.safe(denied)
   self.assertEqual(c.execute('SELECT 2 AS x').fetchone()['x'],2)
 def test_07_bad_request_fails_closed(self):
  self.reserve()
  bad=self.snap(request={**self.t.req2,'body_sha256':'not-a-hash'})
  self.assertEqual(bad['status'],'DENIED')
  self.assertIsNone(bad['classification'])
  self.safe(bad)
 def test_08_rollback_without_commit_does_not_fake_receipt(self):
  x=self.t.act(rollback=True)
  self.assertEqual(x['status'],'LAB_RESERVATION_STAGED_BEFORE_COMMIT')
  old=self.snap()
  self.assertEqual(old['classification']['status'],'LAB_COMMIT_UNKNOWN')
  self.assertIs(old['classification']['external_retry_suppressed'],True)
  self.safe(old)
 def test_09_read_only_snapshot_cannot_mutate_source(self):
  self.reserve()
  def unsafe_write():
   with self.t.lab.admin() as c:
    c.execute("UPDATE s0_pre_dispatch_lab.consents SET state='REVOKED'")
   # The snapshot transaction remains read-only after this separate write.
   # Attempting to mutate using the SAME connection is prohibited, tested
   # separately by an interleave that references the active read connection.
  x=self.snap(unsafe_write)
  self.assertEqual(x['classification']['status'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  self.safe(x)
  self.assertEqual(self.snap()['classification']['reason'],
                   'CONSENT_STALE_OR_REVOKED')
 def test_10_interleave_error_is_unavailable_not_committed(self):
  self.reserve()
  def fail():
   raise RuntimeError('simulated source failure')
  x=self.snap(fail)
  self.assertEqual(x['status'],'UNAVAILABLE')
  self.assertIsNone(x['classification'])
  self.safe(x)
  self.assertEqual(self.snap()['classification']['status'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def test_11_multiple_mutations_after_snapshot_never_claim_current_authority(self):
  self.reserve()
  def mutate():
   with self.t.lab.admin() as c:
    c.execute("UPDATE s0_pre_dispatch_lab.templates "
       "SET template_purpose_ref='DIFFERENT_PURPOSE' WHERE template_ref='tpl_A'")
    c.execute("UPDATE s0_pd_v02_lab.quotas SET enabled=false "
       "WHERE window_ref='window_A'")
  old=self.snap(mutate)
  self.assertEqual(old['classification']['status'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  self.safe(old)
  newer=self.snap()
  self.assertEqual(newer['classification']['reason'],
                   'TEMPLATE_CAMPAIGN_GRANT_STALE')
 def test_12_snapshot_disabled_outside_disposable_env(self):
  from unittest.mock import patch
  self.reserve()
  with patch.dict(os.environ,{'M09_PG17_DISPOSABLE':'NO'}):
   x=self.snap()
  self.assertEqual(x['status'],'DENIED')
  self.assertEqual(x['reason'],'DISPOSABLE_PG17_REQUIRED')
  self.safe(x)
 def test_13_same_connection_read_only_forbids_source_update(self):
  import psycopg
  self.reserve()
  with self.t.lab.admin() as c:
   def illegal_same_txn_write():
    c.execute("UPDATE s0_pre_dispatch_lab.consents SET state='REVOKED' "
              "WHERE case_ref='case_A'")
   denied=run(c,self.t.req2,scope=self.t.scope,
       principal=self.t.principal,m09_versions=self.t.versions,
       _lab_interleave=illegal_same_txn_write)
   self.assertEqual(denied['status'],'UNAVAILABLE')
   self.assertIsNone(denied['classification'])
   self.safe(denied)
   self.assertEqual(c.execute('SHOW transaction_isolation').fetchone()[
       'transaction_isolation'],'read committed')
  self.assertEqual(self.snap()['classification']['status'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def test_14_cancel_waits_for_receipt_lock_and_remains_no_dispatch(self):
  import threading,time
  from concurrent.futures import ThreadPoolExecutor
  self.reserve()
  held=threading.Event();release=threading.Event()
  def updater():
   with self.t.lab.admin() as c:
    c.execute("SELECT attempt_ref FROM s0_pd_v02_lab.receipts "
      "WHERE attempt_ref='attempt_A' FOR UPDATE")
    held.set()
    if not release.wait(9): raise TimeoutError('release not signaled')
    c.execute("UPDATE s0_pd_v02_lab.receipts "
     "SET state='LAB_CANCELLED_NO_DISPATCH',"
     "cancel_reason='CANCELLED_BY_S0_LAB' "
     "WHERE attempt_ref='attempt_A'")
   return 'COMMITTED'
  with ThreadPoolExecutor(max_workers=2) as pool:
   locked=pool.submit(updater)
   self.assertTrue(held.wait(8))
   pending=pool.submit(self.t.stop)
   try:
    time.sleep(.15)
    self.assertFalse(pending.done(),'cancel did not await PG17 lock')
   finally:
    release.set()
   self.assertEqual(locked.result(timeout=12),'COMMITTED')
   self.assertEqual(pending.result(timeout=12)['status'],
                    'LAB_CANCEL_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.snap()['classification']['status'],
                   'LAB_CANCELLED_NO_DISPATCH')
if __name__=='__main__':unittest.main()
