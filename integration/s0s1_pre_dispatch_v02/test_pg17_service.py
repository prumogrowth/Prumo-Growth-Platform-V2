"""Physical PRE_DISPATCH v0.2 receipt and quota tests, synthetic PG17 only."""
import os,threading,unittest
from concurrent.futures import ThreadPoolExecutor
import psycopg
from integration.s0s1_pre_dispatch import test_pg17_service as base
from .pg17_service import reserve,readback,cancel,FLAGS

@unittest.skipUnless(os.getenv('M09_PG17_DISPOSABLE')=='YES',
                     'disposable PG17 required')
class PDReadbackPhysical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  base.PreDispatchPhysical.setUpClass.__func__(cls)
  try:
   with cls.lab.admin() as c:
    c.execute("SET s0_meta.disposable='YES'")
    c.execute("SET s0_pd.install='READBACK_V02_LAB_ONLY'")
    c.execute((cls.origin/'integration/s0s1_pre_dispatch_v02/pg17_schema.sql').read_text())
  except BaseException:
   base.PreDispatchPhysical.tearDownClass.__func__(cls)
   raise
 @classmethod
 def tearDownClass(cls):
  try:
   with cls.lab.admin() as c:
    c.execute('DROP SCHEMA IF EXISTS s0_pd_v02_lab CASCADE')
  finally:
   base.PreDispatchPhysical.tearDownClass.__func__(cls)
 def setUp(self):
  base.PreDispatchPhysical.setUp(self)
  with self.lab.admin() as c:
   c.execute('TRUNCATE s0_pd_v02_lab.receipts,s0_pd_v02_lab.quotas CASCADE')
   c.execute("""INSERT INTO s0_pd_v02_lab.quotas
     (store_ref,app_ref,phone_ref,window_ref,observed_at,
      valid_until,revision,capacity) VALUES
     ('store-A','APP_A','200001','window_A',
      clock_timestamp(),clock_timestamp()+interval '1 hour',1,2)""")
   t=c.execute("SELECT floor(extract(epoch from clock_timestamp())*1000)::bigint AS ms").fetchone()
  self.req2=dict(self.req,intent_ref='intent_A',
   nonce='nonce_0001',destination_sha256='a'*64,body_sha256='b'*64,
   window_ref='window_A',expected_quota_revision=1,
   expires_ms=t['ms']+115000,max_age_ms=60000)
 def act(self,extra=None,rollback=False):
  with self.lab.admin() as c:
   x=reserve(c,{**self.req2,**(extra or {})},scope=self.scope,
       principal=self.principal,m09_versions=self.versions)
   if rollback:c.rollback()
   return x
 def rb(self,extra=None):
  with self.lab.admin() as c:
   return readback(c,{**self.req2,**(extra or {})},scope=self.scope,
          principal=self.principal,m09_versions=self.versions)
 def stop(self,reason='CANCELLED_BY_S0_LAB'):
  with self.lab.admin() as c:
   return cancel(c,attempt_ref='attempt_A',scope=self.scope,
     principal=self.principal,m09_versions=self.versions,reason=reason)
 def sql(self,statement):
  with self.lab.admin() as c:c.execute(statement)
 def totals(self):
  with self.lab.admin() as c:
   r=c.execute('SELECT count(*) AS n FROM s0_pd_v02_lab.receipts').fetchone()['n']
   q=c.execute('SELECT consumed FROM s0_pd_v02_lab.quotas '
          "WHERE window_ref='window_A'").fetchone()['consumed']
   old=c.execute('SELECT count(*) AS n FROM s0_pre_dispatch_lab.reservations').fetchone()['n']
   m=c.execute('SELECT count(*) AS n FROM s0_m09_lab.point_of_use_checks').fetchone()['n']
  return (r,q,old,m)
 def safe(self,x):
  for k,v in FLAGS.items():self.assertEqual(x[k],v,k)
 def test_01_stage_does_not_attest_commit(self):
  x=self.act();self.assertEqual(x['status'],'LAB_RESERVATION_STAGED_BEFORE_COMMIT')
  self.assertFalse(x['commit_verified']);self.safe(x)
  self.assertEqual(self.totals(),(1,1,1,1))
 def test_02_independent_readback_observes_durable_no_dispatch(self):
  self.act();x=self.rb()
  self.assertEqual(x['status'],'LAB_COMMITTED_RECEIPT_NO_DISPATCH')
  self.assertTrue(x['commit_verified']);self.safe(x)
 def test_03_simulated_commit_failure_does_not_consume_quota(self):
  self.assertEqual(self.act(rollback=True)['status'],'LAB_RESERVATION_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.rb()['status'],'LAB_COMMIT_UNKNOWN')
  self.assertEqual(self.totals(),(0,0,0,0))
 def test_04_exact_replay_does_not_duplicate_or_grant(self):
  self.act();x=self.act()
  self.assertEqual(x['status'],'LAB_REPLAY_REQUIRES_READBACK')
  self.assertFalse(x['commit_verified']);self.safe(x)
  self.assertEqual(self.totals(),(1,1,1,1))
 def test_05_same_nonce_different_intent_denied(self):
  self.act()
  x=self.act(dict(attempt_ref='attempt_B',selection_ref='selection_B',
                  intent_ref='intent_B'))
  self.assertEqual(x['reason'],'REPLAY_OR_SCOPE_COLLISION')
  self.assertEqual(self.totals(),(1,1,1,1))
 def test_06_same_intent_different_attempt_denied(self):
  self.act()
  x=self.act(dict(attempt_ref='attempt_B',selection_ref='selection_B',
                  nonce='nonce_0002'))
  self.assertEqual(x['reason'],'REPLAY_OR_SCOPE_COLLISION')
 def test_07_changed_digest_same_attempt_denied(self):
  self.act()
  self.assertEqual(self.act(dict(body_sha256='c'*64))['reason'],
                   'REPLAY_OR_SCOPE_COLLISION')
 def test_08_readback_wrong_payload_denied(self):
  self.act()
  self.assertEqual(self.rb(dict(destination_sha256='d'*64))['reason'],
                   'SCOPE_OR_PAYLOAD_COLLISION')
 def test_09_cancel_after_commit_no_quota_refund(self):
  self.act();x=self.stop()
  self.assertEqual(x['status'],'LAB_CANCEL_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.rb()['status'],'LAB_CANCELLED_NO_DISPATCH')
  self.assertEqual(self.totals(),(1,1,1,1))
  self.assertEqual(self.act()['reason'],'REPLAY_OR_SCOPE_COLLISION')
 def test_10_cancel_retry_idempotent(self):
  self.act();self.stop()
  self.assertEqual(self.stop()['status'],'LAB_CANCEL_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.totals(),(1,1,1,1))
 def test_11_consent_revoked_after_commit_invalidates(self):
  self.act()
  self.sql("UPDATE s0_pre_dispatch_lab.consents SET state='REVOKED', "
           "revision=2 WHERE case_ref='case_A'")
  self.assertEqual(self.rb()['reason'],'CONSENT_STALE_OR_REVOKED')
 def test_12_case_assignment_changed_after_commit_invalidates(self):
  self.act()
  self.sql("UPDATE s0_pre_dispatch_lab.cases SET assignment_revision=2 "
           "WHERE case_ref='case_A'")
  self.assertEqual(self.rb()['reason'],'CASE_POLICY_STALE')
 def test_13_m09_revocation_after_commit_invalidates(self):
  from integration.s0s1_m09_registry.pg17_registry import revoke_channel_in_admin_transaction
  self.act()
  with self.lab.admin() as c:
   self.assertEqual(revoke_channel_in_admin_transaction(
     c,'route_A','channel_A',1,1,1,1),'REVOKED_IN_DISPOSABLE_TRANSACTION')
  self.assertEqual(self.rb()['reason'],'M09_STALE_OR_REVOKED')
 def test_14_template_revoked_after_commit_invalidates(self):
  self.act()
  self.sql("UPDATE s0_pre_dispatch_lab.templates SET active=false "
           "WHERE template_ref='tpl_A'")
  self.assertEqual(self.rb()['reason'],'TEMPLATE_CAMPAIGN_GRANT_STALE')
 def test_15_quota_disabled_after_commit_invalidates(self):
  self.act()
  self.sql("UPDATE s0_pd_v02_lab.quotas SET enabled=false")
  self.assertEqual(self.rb()['reason'],'QUOTA_REVOKED_OR_EXPIRED')
 def test_16_quota_full_denies_and_rolls_back_old_m09(self):
  self.sql("UPDATE s0_pd_v02_lab.quotas SET consumed=capacity")
  self.assertEqual(self.act()['reason'],'QUOTA_EXHAUSTED')
  self.assertEqual(self.totals(),(0,2,0,0))
 def test_17_quota_revision_stale_denies(self):
  self.sql("UPDATE s0_pd_v02_lab.quotas SET revision=2")
  self.assertEqual(self.act()['reason'],'QUOTA_STALE')
  self.assertEqual(self.totals(),(0,0,0,0))
 def test_18_quota_observation_expired_denies(self):
  self.sql("UPDATE s0_pd_v02_lab.quotas SET observed_at="
           "clock_timestamp()-interval '2 minutes'")
  self.assertEqual(self.act()['reason'],'QUOTA_OBSERVATION_STALE')
 def test_19_request_deadline_expired_denies(self):
  self.assertEqual(self.act(dict(expires_ms=1))['reason'],
                   'EXPIRED_OR_UNBOUNDED')
  self.assertEqual(self.totals(),(0,0,0,0))
 def test_20_new_attempt_new_selection_quota_counts(self):
  self.act()
  x=self.act(dict(attempt_ref='attempt_B',intent_ref='intent_B',
         selection_ref='selection_B',nonce='nonce_0002'))
  self.assertEqual(x['status'],'LAB_RESERVATION_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.totals(),(2,2,2,2))
 def test_21_two_parallel_attempts_single_slot(self):
  self.sql('UPDATE s0_pd_v02_lab.quotas SET consumed=1')
  barrier=threading.Barrier(2)
  def run(k):
   req={**self.req2,
    'attempt_ref':f'attempt_{k}',
    'selection_ref':f'selection_{k}',
    'intent_ref':f'intent_{k}',
    'nonce':f'nonce_{k:08d}'}
   with self.lab.admin() as c:
    barrier.wait(timeout=8)
    return reserve(c,req,scope=self.scope,principal=self.principal,
                   m09_versions=self.versions)
  with ThreadPoolExecutor(max_workers=2) as pool:
   fs=[pool.submit(run,i) for i in (1,2)]
   results=[f.result(timeout=19) for f in fs]
  self.assertEqual(sum(x['status']=='LAB_RESERVATION_STAGED_BEFORE_COMMIT'
                       for x in results),1)
  self.assertEqual(self.totals(),(1,2,1,1))
 def test_22_runtime_rbac_no_receipt_or_quota(self):
  for tbl in ('receipts','quotas'):
   with psycopg.connect(self.lab.runtime_dsn) as c:
    with self.assertRaises(psycopg.Error):
     c.execute('SELECT * FROM s0_pd_v02_lab.'+tbl)
 def test_23_request_bool_revision_fails_closed(self):
  self.assertEqual(self.act(dict(expected_quota_revision=True))['reason'],
                  'INVALID_REQUEST')
  self.assertEqual(self.totals(),(0,0,0,0))
 def test_24_new_suppression_after_receipt_invalidates(self):
  self.act()
  self.sql("UPDATE s0_pre_dispatch_lab.suppressions "
     "SET active=true WHERE purpose_ref='lead_followup'")
  self.assertEqual(self.rb()['reason'],'SUPPRESSED')
 def test_25_quota_observation_changed_without_revision_invalidates(self):
  self.act()
  self.sql("UPDATE s0_pd_v02_lab.quotas "
           "SET observed_at=observed_at-interval '1 second'")
  self.assertEqual(self.rb()['reason'],'QUOTA_REVOKED_OR_EXPIRED')
 def test_26_quota_window_end_changed_without_revision_invalidates(self):
  self.act()
  self.sql("UPDATE s0_pd_v02_lab.quotas "
           "SET valid_until=valid_until+interval '1 second'")
  self.assertEqual(self.rb()['reason'],'QUOTA_REVOKED_OR_EXPIRED')
 def test_27_stale_quota_after_reservation_never_grants_send(self):
  self.act()
  self.sql("UPDATE s0_pd_v02_lab.quotas SET revision=revision+1")
  r=self.rb()
  self.assertEqual(r['status'],'LAB_STALE_NO_DISPATCH')
  self.safe(r)
if __name__=='__main__':unittest.main()
