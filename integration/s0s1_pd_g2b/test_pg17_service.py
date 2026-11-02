"""G2-B physical PG17 cooperative writer/reader locks, never Graph."""
import os,threading,time,unittest
from concurrent.futures import ThreadPoolExecutor
import psycopg
from integration.s0s1_pre_dispatch_v02 import test_pg17_service as inherited
from .pg17_service import reserve,revoke_consent,cancel,observe

@unittest.skipUnless(os.getenv('M09_PG17_DISPOSABLE')=='YES','PG17 only')
class CooperativePhysical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  inherited.PDReadbackPhysical.setUpClass()
  try:
   with inherited.PDReadbackPhysical.lab.admin() as c:
    c.execute("SET s0_meta.disposable='YES'")
    c.execute("SET s0_g2b.install='COOPERATIVE_CASE_GATE_LAB'")
    c.execute((inherited.PDReadbackPhysical.origin/
       'integration/s0s1_pd_g2b/pg17_schema.sql').read_text())
  except BaseException:
   inherited.PDReadbackPhysical.tearDownClass()
   raise
 @classmethod
 def tearDownClass(cls):
  try:
   with inherited.PDReadbackPhysical.lab.admin() as c:
    c.execute('DROP SCHEMA IF EXISTS s0_pd_g2b_lab CASCADE')
  finally:
   inherited.PDReadbackPhysical.tearDownClass()
 def setUp(self):
  self.t=inherited.PDReadbackPhysical('test_01_stage_does_not_attest_commit')
  self.t.setUp()
  with self.t.lab.admin() as c:
   c.execute('TRUNCATE s0_pd_g2b_lab.case_gates')
   c.execute("INSERT INTO s0_pd_g2b_lab.case_gates "
     "(case_ref,store_ref,generation) VALUES ('case_A','store-A',1)")
 def gens(self):
  with self.t.lab.admin() as c:
   return c.execute("SELECT generation FROM s0_pd_g2b_lab.case_gates "
       "WHERE case_ref='case_A'").fetchone()['generation']
 def reserve(self,gen=1,request=None):
  with self.t.lab.admin() as c:
   return reserve(c,request or self.t.req2,scope=self.t.scope,
     principal=self.t.principal,m09_versions=self.t.versions,
     expected_generation=gen)
 def revoke(self,gen=2,rev=1):
  with self.t.lab.admin() as c:
   return revoke_consent(c,case_ref='case_A',store_ref='store-A',
    purpose_ref='lead_followup',expected_generation=gen,
    expected_consent_revision=rev)
 def cancel(self,gen=2):
  with self.t.lab.admin() as c:
   return cancel(c,attempt_ref='attempt_A',case_ref='case_A',
    scope=self.t.scope,principal=self.t.principal,
    m09_versions=self.t.versions,expected_generation=gen)
 def observe(self,gen=2):
  with self.t.lab.admin() as c:
   return observe(c,self.t.req2,scope=self.t.scope,
    principal=self.t.principal,m09_versions=self.t.versions,
    expected_generation=gen)
 def safe(self,x):
  self.assertFalse(x['commit_verified'],x)
  for k in ('source_operational','host_authenticated',
   'current_authority_verified','authenticated_attempt_binding',
   'outbox_authorized','lease_issued','send_authorized',
   'graph_dispatch_authorized','automatic_retry_authorized',
   'production_authorized'): self.assertIs(x[k],False,k)
 def start(self):
  x=self.reserve()
  self.assertEqual(x['status'],'LAB_G2B_RESERVATION_STAGED_BEFORE_COMMIT',x)
  self.assertEqual(x['generation_after_stage'],2)
  self.assertEqual(self.gens(),2)
  self.safe(x)
 def test_01_reserve_and_locked_observe_nonredeemable(self):
  self.start()
  x=self.observe()
  self.assertEqual(x['historical_classification'],
                   'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  self.assertEqual(x['status'],'LAB_G2B_OBSERVATION_STAGED_NO_DISPATCH')
  self.assertEqual(x['observed_generation'],2)
  self.safe(x)
 def test_02_revoke_advances_gate_and_invalidates_old_observation(self):
  self.start()
  r=self.revoke()
  self.assertEqual(r['status'],'LAB_G2B_REVOCATION_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.gens(),3)
  self.assertEqual(self.observe()['reason'],'GENERATION_STALE')
  current=self.observe(3)
  self.assertEqual(current['historical_classification'],'LAB_STALE_NO_DISPATCH')
  self.safe(current)
 def test_03_cancel_advances_gate_and_invalidates_old_observation(self):
  self.start()
  r=self.cancel()
  self.assertEqual(r['status'],'LAB_G2B_CANCEL_STAGED_BEFORE_COMMIT',r)
  self.assertEqual(self.observe()['reason'],'GENERATION_STALE')
  self.assertEqual(self.observe(3)['historical_classification'],
                   'LAB_CANCELLED_NO_DISPATCH')
  self.safe(r)
 def test_04_rollback_reverts_gate_quota_reservation(self):
  with self.t.lab.admin() as c:
   staged=reserve(c,self.t.req2,scope=self.t.scope,
      principal=self.t.principal,m09_versions=self.t.versions,
      expected_generation=1)
   self.assertEqual(staged['generation_after_stage'],2)
   c.rollback()
  self.assertEqual(self.gens(),1)
  self.assertEqual(self.t.totals(),(0,0,0,0))
 def test_05_wrong_epoch_denied_without_consumption(self):
  x=self.reserve(2)
  self.assertEqual(x['reason'],'GENERATION_STALE',x)
  self.assertEqual(self.t.totals(),(0,0,0,0))
 def test_06_cancel_on_wrong_generation_fails_closed(self):
  self.start()
  x=self.cancel(1)
  self.assertEqual(x['reason'],'GENERATION_STALE')
  self.assertEqual(self.t.rb()['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
 def test_07_revoke_wrong_consent_version_denied(self):
  self.start()
  x=self.revoke(2,3)
  self.assertEqual(x['reason'],'CONSENT_REVISION_STALE')
  self.assertEqual(self.gens(),2)
 def test_08_concurrent_reserve_same_generation_one_winner(self):
  barrier=threading.Barrier(2)
  def worker(i):
   rq={**self.t.req2,'attempt_ref':f'attempt_{i}',
       'selection_ref':f'selection_{i}','intent_ref':f'intent_{i}',
       'nonce':f'nonce_{i:08d}'}
   with self.t.lab.admin() as c:
    barrier.wait(timeout=8)
    return reserve(c,rq,scope=self.t.scope,principal=self.t.principal,
       m09_versions=self.t.versions,expected_generation=1)
  with ThreadPoolExecutor(max_workers=2) as pool:
   f=[pool.submit(worker,i) for i in (1,2)]
   got=[x.result(timeout=22) for x in f]
  self.assertEqual(sum(x['status']=='LAB_G2B_RESERVATION_STAGED_BEFORE_COMMIT'
                       for x in got),1,got)
  self.assertEqual(sum(x['reason']=='GENERATION_STALE' for x in got),1,got)
  self.assertEqual(self.gens(),2)
  self.assertEqual(self.t.totals(),(1,1,1,1))
 def test_09_revoke_waits_for_cooperative_observer_row_lock(self):
  self.start()
  held=threading.Event()
  release=threading.Event()
  def observer():
   with self.t.lab.admin() as c:
    x=observe(c,self.t.req2,scope=self.t.scope,
      principal=self.t.principal,m09_versions=self.t.versions,
      expected_generation=2)
    self.assertEqual(x['historical_classification'],
                     'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
    held.set()
    if not release.wait(9):raise TimeoutError('release')
   return x
  with ThreadPoolExecutor(max_workers=2) as pool:
   future=pool.submit(observer)
   self.assertTrue(held.wait(8))
   rev=pool.submit(self.revoke)
   try:
    time.sleep(.18)
    self.assertFalse(rev.done(),'revoke must wait for the observer lock')
   finally:
    release.set()
   self.safe(future.result(timeout=10))
   self.assertEqual(rev.result(timeout=12)['status'],
                    'LAB_G2B_REVOCATION_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.observe()['reason'],'GENERATION_STALE')
 def test_10_noncooperative_writer_is_not_claimed_safe(self):
  self.start()
  # Deliberately bypassing the G2B gate demonstrates the limitation.
  self.t.sql("UPDATE s0_pre_dispatch_lab.consents SET state='REVOKED' "
    "WHERE case_ref='case_A'")
  self.assertEqual(self.gens(),2) # No global enforcement
  result=self.observe(2)
  self.assertEqual(result['historical_classification'],'LAB_STALE_NO_DISPATCH')
  self.safe(result)
 def test_11_runtime_cannot_read_g2b_gate(self):
  with psycopg.connect(self.t.lab.runtime_dsn) as c:
   with self.assertRaises(psycopg.Error):
    c.execute('SELECT * FROM s0_pd_g2b_lab.case_gates')
 def test_12_revoke_before_reservation_blocks_original_consent_check(self):
  x=self.revoke(1)
  self.assertEqual(x['status'],'LAB_G2B_REVOCATION_STAGED_BEFORE_COMMIT')
  got=self.reserve(2)
  self.assertNotEqual(got['status'],'LAB_G2B_RESERVATION_STAGED_BEFORE_COMMIT')
  self.safe(got)
 def test_13_cancel_without_receipt_denied_no_epoch(self):
  x=self.cancel(1)
  self.assertEqual(x['reason'],'RECEIPT_CASE_SCOPE_DENIED')
  self.assertEqual(self.gens(),1)
 def test_14_revoke_second_time_no_generation_bump(self):
  self.start();self.revoke()
  r=self.revoke(3,2)
  self.assertEqual(r['reason'],'CONSENT_ALREADY_REVOKED')
  self.assertEqual(self.gens(),3)
 def test_15_same_reservation_replay_no_new_generation(self):
  self.start()
  duplicate=self.reserve(2)
  self.assertEqual(duplicate['status'],'LAB_G2B_REPLAY_HOLD_NO_DISPATCH')
  self.safe(duplicate)
  self.assertEqual(self.gens(),2)
  self.assertEqual(self.t.totals(),(1,1,1,1))
 def test_16_cancel_replay_no_new_generation_or_quota_refund(self):
  self.start()
  self.cancel()
  duplicate=self.cancel(3)
  self.assertEqual(duplicate['status'],'LAB_G2B_ALREADY_CANCELLED_HOLD')
  self.safe(duplicate)
  self.assertEqual(self.gens(),3)
  self.assertEqual(self.t.totals(),(1,1,1,1))
 def test_17_cancelled_replay_wrong_waba_still_denied(self):
  from dataclasses import replace
  self.start()
  self.cancel()
  other=replace(self.t.scope,waba_id='DIFFERENT_WABA')
  with self.t.lab.admin() as c:
   x=cancel(c,attempt_ref='attempt_A',case_ref='case_A',
      scope=other,principal=self.t.principal,
      m09_versions=self.t.versions,expected_generation=3)
  self.assertEqual(x['reason'],'CANCEL_SCOPE_DENIED',x)
  self.assertEqual(self.gens(),3)
  self.safe(x)
if __name__=='__main__':unittest.main()
