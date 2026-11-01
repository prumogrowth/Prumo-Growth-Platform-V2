"""Physical v0.2 Frontend history and after-commit readback tests, PG17 ONLY."""
import os,threading,unittest
from concurrent.futures import ThreadPoolExecutor
try:
 import psycopg
except ImportError:
 psycopg=None
from integration.s0s1_frontend_read import test_pg17_service as base
from .pg17_service import open_owned,readback,owner_history

@unittest.skipUnless(os.getenv('M09_PG17_DISPOSABLE')=='YES' and psycopg,
                     'disposable PG17 only')
class FrontendV02Physical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  base.FrontendReadPhysical.setUpClass.__func__(cls)
 @classmethod
 def tearDownClass(cls):
  base.FrontendReadPhysical.tearDownClass.__func__(cls)
 def setUp(self):
  base.FrontendReadPhysical.setUp(self)
  with self.lab.admin() as c:
   c.execute("UPDATE s0_frontend_lab.cases SET active=false "
             "WHERE case_ref='case_B'")
   c.execute("""INSERT INTO s0_frontend_lab.cases
     (case_ref,store_ref,owner_ref,assignment_revision,case_revision,
     inbox_revision,active,actionable) VALUES
     ('case_C','store-A','seller_A',1,1,1,false,false)""")
   c.execute("""INSERT INTO s0_frontend_lab.events
     (case_ref,event_seq,event_ref,event_kind,inbound_visible,
     occurred_at,source_verified) VALUES
     ('case_C',1,'C_in1','INBOUND',true,NULL,false)""")
  self.v=dict(assignment_revision=1,case_revision=1,inbox_revision=1)
 def _args(self,ref='open_A',case='case_A',store='store-A',
           actor='seller_A',role='OWNER',v=None):
  return dict(open_ref=ref,case_ref=case,store_ref=store,
     actor_ref=actor,role=role,allowed_stores=(store,),
     expected=v if v is not None else dict(self.v))
 def stage(self,**kwargs):
  with self.lab.admin() as c:
   return open_owned(c,**self._args(**kwargs))
 def proof(self,**kwargs):
  with self.lab.admin() as c:
   return readback(c,**self._args(**kwargs))
 def history(self,store='store-A',actor='seller_A',role='OWNER'):
  with self.lab.admin() as c:
   return owner_history(c,store_ref=store,actor_ref=actor,role=role,
                        allowed_stores=(store,))
 def cursor(self,case='case_A',owner='seller_A'):
  with self.lab.admin() as c:
   a=c.execute('SELECT read_through_seq AS n FROM s0_frontend_lab.read_cursors '
     'WHERE case_ref=%s AND owner_ref=%s',(case,owner)).fetchone()
   return a['n'] if a else 0
 def attempts(self):
  with self.lab.admin() as c:
   return c.execute('SELECT count(*) AS n FROM s0_frontend_lab.open_attempts').fetchone()['n']
 def inbound(self,case='case_A',time='2026-11-01T12:00:00Z'):
  with self.lab.admin() as c:
   c.execute('SELECT case_ref FROM s0_frontend_lab.cases '
             'WHERE case_ref=%s FOR UPDATE',(case,))
   seq=c.execute('SELECT COALESCE(MAX(event_seq),0)+1 AS n '
     'FROM s0_frontend_lab.events WHERE case_ref=%s',(case,)).fetchone()['n']
   c.execute('UPDATE s0_frontend_lab.cases '
     'SET inbox_revision=inbox_revision+1 WHERE case_ref=%s',(case,))
   c.execute('INSERT INTO s0_frontend_lab.events '
     '(case_ref,event_seq,event_ref,event_kind,inbound_visible,'
     'occurred_at,source_verified) VALUES(%s,%s,%s,%s,%s,%s,%s)',
     (case,seq,case+'_'+str(seq),'INBOUND',True,time,True))
 def safe(self,r):
  self.assertTrue(r['lab_only'])
  self.assertFalse(r['host_principal_authenticated'])
  self.assertFalse(r['inbound_origin_verified'])
  self.assertFalse(r['production_authorized'])
  self.assertFalse(r['send_authorized'])
 def test_01_active_open_staged_not_authority(self):
  a=self.stage();self.assertEqual(a['status'],'LAB_OPEN_STAGED_BEFORE_COMMIT')
  self.assertEqual(a['read_confirmation_state'],'NOT_CONFIRMED')
  self.assertFalse(a['display_read_confirmed']);self.safe(a)
  self.assertEqual(self.cursor(),1)
 def test_02_readback_new_connection_proves_committed_original_cutoff(self):
  self.stage();x=self.proof()
  self.assertEqual(x['status'],'LAB_COMMITTED_READBACK')
  self.assertTrue(x['original_open_committed'])
  self.assertTrue(x['display_read_confirmed'])
  self.assertEqual(x['read_through_seq'],1)
  self.assertFalse(x['newer_inbound_after_open']);self.safe(x)
 def test_03_historical_inactive_open_marks_read(self):
  x=self.stage(ref='old',case='case_B')
  self.assertEqual(x['conversation_mode'],'HISTORICAL_READ_ONLY')
  self.assertFalse(x['composer_enabled'])
  self.assertEqual(self.cursor('case_B'),1)
  a=self.proof(ref='old',case='case_B')
  self.assertTrue(a['display_read_confirmed'])
  self.assertEqual(a['human_reply_pending'],'DOT')
  self.assertFalse(a['composer_enabled'])
 def test_04_historical_queue_includes_inactive_and_nonactionable(self):
  q=self.history()
  self.assertEqual(q['status'],'LAB_HISTORY_OWNER_PROJECTION')
  self.assertEqual({z['case_ref'] for z in q['rows']},{'case_B','case_C'})
  self.assertTrue(all(z['historical_read_only'] and not z['composer_enabled']
                     for z in q['rows']))
  self.assertNotIn('case_X',str(q))
 def test_05_history_unknown_timestamp_not_fabricated(self):
  x=next(z for z in self.history()['rows'] if z['case_ref']=='case_C')
  self.assertIsNone(x['last_activity_at'])
  self.assertEqual(x['activity_time_state'],'UNKNOWN')
 def test_06_historical_count_to_dot_no_composer(self):
  before=next(z for z in self.history()['rows'] if z['case_ref']=='case_B')
  self.assertEqual(before['human_reply_pending'],'COUNT')
  self.stage(ref='archive',case='case_B')
  after=next(z for z in self.history()['rows'] if z['case_ref']=='case_B')
  self.assertEqual(after['human_reply_pending'],'DOT')
  self.assertFalse(after['composer_enabled'])
 def test_07_supervisor_open_does_not_write_cursor_or_open(self):
  x=self.stage(ref='manager',actor='manager_A',role='SUPERVISOR')
  self.assertEqual(x['status'],'LAB_SUPERVISORY_VIEW_NO_READ')
  self.assertEqual(self.cursor(),0);self.assertEqual(self.attempts(),0)
 def test_08_supervisor_cannot_readback_owner_receipt(self):
  self.stage()
  x=self.proof(actor='manager_A',role='SUPERVISOR')
  self.assertEqual(x['status'],'DENIED')
  self.assertFalse(x.get('display_read_confirmed',False))
 def test_09_unknown_commit_or_rollback_has_no_proof(self):
  try:
   with self.lab.admin() as c:
    x=open_owned(c,**self._args(ref='abort'))
    self.assertEqual(x['status'],'LAB_OPEN_STAGED_BEFORE_COMMIT')
    raise RuntimeError('simulated disconnect before COMMIT')
  except RuntimeError: pass
  y=self.proof(ref='abort')
  self.assertEqual(y['status'],'LAB_COMMIT_UNRESOLVED')
  self.assertEqual(y['read_confirmation_state'],'UNKNOWN')
  self.assertFalse(y['display_read_confirmed'])
  self.assertEqual(self.cursor(),0)
 def test_10_timeout_after_successful_commit_recovered_by_readback(self):
  self.stage(ref='timeout')
  x=self.proof(ref='timeout')
  self.assertEqual(x['status'],'LAB_COMMITTED_READBACK')
  self.assertTrue(x['display_read_confirmed'])
 def test_11_exact_retry_no_new_open_or_cursor_movement(self):
  self.stage()
  a=self.stage()
  self.assertEqual(a['status'],'LAB_OPEN_REPLAY_STAGED_NOT_COMMIT_PROOF')
  self.assertFalse(a['display_read_confirmed'])
  self.assertEqual(self.attempts(),1)
  self.assertEqual(self.cursor(),1)
 def test_12_retry_after_new_inbound_keeps_original_cutoff(self):
  self.stage();self.inbound()
  retry=self.stage()
  self.assertEqual(retry['status'],'LAB_OPEN_REPLAY_STAGED_NOT_COMMIT_PROOF')
  self.assertEqual(retry['read_through_seq'],1)
  self.assertEqual(self.cursor(),1)
  x=self.proof()
  self.assertEqual(x['read_confirmation_state'],
                   'COMMITTED_OLD_CUTOFF_WITH_NEW_INBOUND_LAB')
  self.assertFalse(x['display_read_confirmed'])
  self.assertTrue(x['original_open_committed'])
  self.assertTrue(x['newer_inbound_after_open'])
  self.assertEqual(x['unread_inbound_count'],1)
 def test_13_new_open_with_stale_inbox_denied(self):
  self.inbound()
  self.assertEqual(self.stage(ref='new')['reason'],'STALE_OR_REASSIGNED')
  self.assertEqual(self.cursor(),0)
 def test_14_new_open_with_new_version_reads_new_message(self):
  self.stage();self.inbound()
  v={**self.v,'inbox_revision':2}
  a=self.stage(ref='new',v=v)
  self.assertEqual(a['status'],'LAB_OPEN_STAGED_BEFORE_COMMIT')
  self.assertEqual(a['read_through_seq'],2)
  self.assertTrue(self.proof(ref='new',v=v)['display_read_confirmed'])
 def test_15_reassignment_denies_old_readback_and_retry(self):
  self.stage()
  with self.lab.admin() as c:
   c.execute("UPDATE s0_frontend_lab.cases SET owner_ref='new_owner',"
             "assignment_revision=2 WHERE case_ref='case_A'")
  self.assertEqual(self.proof()['reason'],'STALE_OR_REASSIGNED')
  self.assertEqual(self.stage()['reason'],'NOT_CURRENT_OWNER')
  self.assertFalse(self.proof().get('display_read_confirmed',False))
 def test_16_new_owner_new_open_not_inheriting_old_receipt(self):
  self.stage()
  with self.lab.admin() as c:
   c.execute("UPDATE s0_frontend_lab.cases SET owner_ref='new_owner',"
             "assignment_revision=2 WHERE case_ref='case_A'")
  v={**self.v,'assignment_revision':2}
  self.assertEqual(self.stage(ref='new',actor='new_owner',v=v)['status'],
                   'LAB_OPEN_STAGED_BEFORE_COMMIT')
  self.assertEqual(self.cursor(owner='seller_A'),1)
  self.assertEqual(self.proof(ref='new',actor='new_owner',v=v)['status'],
                   'LAB_COMMITTED_READBACK')
 def test_17_open_ref_collision_different_case_denies(self):
  self.stage()
  x=self.stage(case='case_B')
  self.assertEqual(x['reason'],'OPEN_REF_COLLISION')
  self.assertEqual(self.cursor('case_B'),0)
 def test_18_wrong_store_never_gets_historical(self):
  self.assertEqual(self.stage(case='case_B',store='store-B')['reason'],
                   'SCOPE_DENIED')
  self.assertEqual(self.history(store='store-B')['rows'],[])
 def test_19_wrong_owner_denied_on_inactive_history(self):
  self.assertEqual(self.stage(ref='bad',case='case_B',
             actor='other')['reason'],'NOT_CURRENT_OWNER')
  self.assertEqual(self.cursor('case_B'),0)
 def test_20_history_supervisor_cannot_enumerate(self):
  self.assertEqual(self.history(actor='manager_A',role='SUPERVISOR')['status'],
                   'DENIED')
 def test_21_inactive_history_remains_without_composer_after_new_inbound(self):
  self.stage(ref='old',case='case_B')
  self.inbound('case_B')
  x=self.proof(ref='old',case='case_B')
  self.assertFalse(x['display_read_confirmed'])
  self.assertFalse(x['composer_enabled'])
  self.assertEqual(x['unread_inbound_count'],1)
 def test_22_runtime_rbac_still_denies_open_receipt(self):
  with psycopg.connect(self.lab.runtime_dsn) as c:
   with self.assertRaises(psycopg.Error):
    c.execute('SELECT * FROM s0_frontend_lab.open_attempts')
 def test_23_two_parallel_same_open_ref_only_one_record(self):
  gate=threading.Barrier(2)
  def work():
   with self.lab.admin() as c:
    gate.wait(timeout=8)
    return open_owned(c,**self._args())['status']
  with ThreadPoolExecutor(max_workers=2) as pool:
   fs=[pool.submit(work),pool.submit(work)]
   statuses=[z.result(timeout=15) for z in fs]
  self.assertCountEqual(statuses,[
    'LAB_OPEN_STAGED_BEFORE_COMMIT',
    'LAB_OPEN_REPLAY_STAGED_NOT_COMMIT_PROOF'])
  self.assertEqual(self.attempts(),1)
  self.assertTrue(self.proof()['display_read_confirmed'])
 def test_24_inbound_race_does_not_ack_unseen_message(self):
  gate=threading.Barrier(2)
  def openit():
   with self.lab.admin() as c:
    gate.wait(timeout=8)
    return open_owned(c,**self._args())['status']
  def arrive():
   gate.wait(timeout=8)
   self.inbound()
  with ThreadPoolExecutor(max_workers=2) as pool:
   a=pool.submit(openit);b=pool.submit(arrive)
   status=a.result(timeout=15);b.result(timeout=15)
  self.assertIn(status,('DENIED','LAB_OPEN_STAGED_BEFORE_COMMIT'))
  if status=='LAB_OPEN_STAGED_BEFORE_COMMIT':
   x=self.proof()
   self.assertFalse(x['display_read_confirmed'])
   self.assertTrue(x['newer_inbound_after_open'])
  self.assertEqual(self.cursor()<=1,True)
 def test_25_missing_open_ref_readback_remains_unknown(self):
  x=self.proof(ref='never_opened')
  self.assertEqual(x['status'],'LAB_COMMIT_UNRESOLVED')
  self.assertFalse(x['display_read_confirmed'])
 def test_27_old_receipt_never_inherits_newer_open_cutoff(self):
  self.stage()
  self.inbound()
  v={**self.v,'inbox_revision':2}
  self.assertEqual(self.stage(ref='newer',v=v)['read_through_seq'],2)
  old=self.proof()
  self.assertEqual(old['status'],'LAB_COMMITTED_READBACK')
  self.assertEqual(old['read_through_seq'],1)
  self.assertEqual(old['unread_inbound_count'],1)
  self.assertEqual(old['human_reply_pending'],'COUNT')
  self.assertFalse(old['display_read_confirmed'])
  self.assertTrue(self.proof(ref='newer',v=v)['display_read_confirmed'])
 def test_28_reassigned_historical_case_not_visible_to_old_owner(self):
  self.stage(ref='historic',case='case_B')
  with self.lab.admin() as c:
   c.execute("UPDATE s0_frontend_lab.cases SET owner_ref='new_owner', "
             "assignment_revision=2 WHERE case_ref='case_B'")
  self.assertEqual(self.proof(ref='historic',case='case_B')['reason'],
                   'STALE_OR_REASSIGNED')
  self.assertNotIn('case_B',[z['case_ref'] for z in self.history()['rows']])
 def test_26_bad_versions_and_non_owner_roles_fail_closed(self):
  self.assertEqual(self.stage(v={'inbox_revision':1})['status'],'DENIED')
  self.assertEqual(self.proof(role='operator')['status'],'DENIED')
  self.assertEqual(self.history(role='operator')['status'],'DENIED')

if __name__=='__main__':unittest.main()
