"""Physical #14 checks; isolated PG17, synthetic events and actors only."""
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
try:
    import psycopg
except ImportError:
    psycopg=None
from integration.s0s1_f02 import test_pg17_service as inherited
from .pg17_service import open_case,owner_queue,manager_summary

@unittest.skipUnless(os.getenv('M09_PG17_DISPOSABLE')=='YES' and psycopg,
                     'disposable PG17 only')
class FrontendReadPhysical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        inherited.F02Physical.setUpClass.__func__(cls)
        try:
            with cls.lab.admin() as c:
                c.execute("SET s0_meta.disposable='YES'")
                c.execute("SET s0_frontend.install='READ_LAB_ONLY'")
                c.execute((cls.origin/'integration/s0s1_frontend_read/pg17_schema.sql').read_text())
        except BaseException:
            inherited.F02Physical.tearDownClass.__func__(cls)
            raise
    @classmethod
    def tearDownClass(cls):
        try:
            with cls.lab.admin() as c:
                c.execute('DROP SCHEMA IF EXISTS s0_frontend_lab CASCADE')
        finally:
            inherited.F02Physical.tearDownClass.__func__(cls)

    def setUp(self):
        inherited.F02Physical.setUp(self)
        with self.lab.admin() as c:
            c.execute('TRUNCATE s0_frontend_lab.open_attempts,'
              's0_frontend_lab.read_cursors,s0_frontend_lab.events,'
              's0_frontend_lab.cases CASCADE')
            c.execute("""INSERT INTO s0_frontend_lab.cases
             (case_ref,store_ref,owner_ref,assignment_revision,case_revision,
              inbox_revision,actionable,active) VALUES
             ('case_A','store-A','seller_A',1,1,1,true,true),
             ('case_B','store-A','seller_A',1,1,1,false,true),
             ('case_X','store-B','seller_X',1,1,1,true,true)""")
            c.execute("""INSERT INTO s0_frontend_lab.events
             (case_ref,event_seq,event_ref,event_kind,inbound_visible,
              occurred_at,source_verified) VALUES
             ('case_A',1,'A_in1','INBOUND',true,'2026-11-01T10:00:00Z',true),
             ('case_B',1,'B_in1','INBOUND',true,'2026-11-01T09:00:00Z',true),
             ('case_X',1,'X_in1','INBOUND',true,'2026-11-01T08:00:00Z',true)""")
        self.expected=dict(assignment_revision=1,case_revision=1,inbox_revision=1)

    def open(self,*,ref='open_A',case='case_A',store='store-A',
             actor='seller_A',role='OWNER',versions=None):
        with self.lab.admin() as c:
            return open_case(c,open_ref=ref,case_ref=case,store_ref=store,
                actor_ref=actor,role=role,allowed_stores=(store,),
                expected=versions or self.expected)
    def queue(self,store='store-A',actor='seller_A',role='OWNER'):
        with self.lab.admin() as c:
            return owner_queue(c,store_ref=store,actor_ref=actor,role=role,
                               allowed_stores=(store,))
    def manager(self,store='store-A'):
        with self.lab.admin() as c:
            return manager_summary(c,store_ref=store,actor_ref='manager_A',
                        role='SUPERVISOR',allowed_stores=(store,))
    def append(self,case='case_A',kind='INBOUND',visible=True,
               verified=True,when='2026-11-01T10:05:00Z'):
        with self.lab.admin() as c:
            c.execute('SELECT case_ref FROM s0_frontend_lab.cases '
              'WHERE case_ref=%s FOR UPDATE',(case,))
            nextseq=c.execute('SELECT COALESCE(MAX(event_seq),0)+1 AS n '
              'FROM s0_frontend_lab.events WHERE case_ref=%s',(case,)).fetchone()['n']
            c.execute('UPDATE s0_frontend_lab.cases '
              'SET inbox_revision=inbox_revision+1 WHERE case_ref=%s',(case,))
            c.execute('INSERT INTO s0_frontend_lab.events '
              '(case_ref,event_seq,event_ref,event_kind,inbound_visible,'
              'occurred_at,source_verified) VALUES (%s,%s,%s,%s,%s,%s,%s)',
              (case,nextseq,f'{case}_{nextseq}',kind,
               visible if kind=='INBOUND' else False,when,verified))
    def count(self):
        with self.lab.admin() as c:
            x=c.execute('SELECT COUNT(*) AS n FROM s0_frontend_lab.open_attempts').fetchone()
            return x['n']
    def cursor(self,case='case_A',owner='seller_A'):
        with self.lab.admin() as c:
            x=c.execute('SELECT read_through_seq AS n FROM '
              's0_frontend_lab.read_cursors WHERE case_ref=%s AND owner_ref=%s',
              (case,owner)).fetchone()
            return x['n'] if x else 0

    def test_01_titular_open_immediate_without_dwell(self):
        x=self.open()
        self.assertEqual(x['decision'],'LAB_READ_RECORDED_BEFORE_COMMIT')
        self.assertEqual(x['unread_inbound_count'],0)
        self.assertTrue(x['operator_read_confirmed'])
        self.assertEqual(x['human_reply_pending'],'DOT')
        self.assertEqual(self.cursor(),1)
        self.assertFalse(x['production_authorized'])

    def test_02_supervisor_open_never_marks_owner_read(self):
        x=self.open(ref='manager1',actor='manager_A',role='SUPERVISOR')
        self.assertEqual(x['decision'],'SUPERVISORY_VIEW_NO_READ')
        self.assertEqual(self.cursor(),0)
        self.assertEqual(self.count(),0)

    def test_03_new_inbound_after_read_reopens_count(self):
        self.open()
        self.append()
        q=self.queue()['rows'][0]
        self.assertEqual(q['unread_inbound_count'],1)
        self.assertEqual(q['human_reply_pending'],'COUNT')
        self.assertFalse(q['operator_read_confirmed'])

    def test_04_local_draft_never_becomes_human_reply(self):
        self.open();self.append(kind='LOCAL_DRAFT',visible=False)
        x=self.queue()['rows'][0]
        self.assertEqual(x['human_reply_pending'],'DOT')

    def test_05_api_accepted_never_proves_human_reply(self):
        self.open();self.append(kind='API_ACCEPTED',visible=False)
        self.assertEqual(self.queue()['rows'][0]['human_reply_pending'],'DOT')

    def test_06_published_human_reply_clears_only_previous_inbound(self):
        self.open()
        self.append(kind='HUMAN_REPLY_PUBLISHED',visible=False)
        self.assertEqual(self.queue()['rows'][0]['human_reply_pending'],'NONE')
        self.append(when='2026-11-01T10:10:00Z')
        self.assertEqual(self.queue()['rows'][0]['human_reply_pending'],'COUNT')

    def test_07_unverified_human_reply_is_not_accepted(self):
        self.open()
        self.append(kind='HUMAN_REPLY_PUBLISHED',visible=False,verified=False)
        item=next(x for x in self.queue()['rows'] if x['case_ref']=='case_A')
        self.assertEqual(item['human_reply_pending'],'DOT')

    def test_08_historical_read_without_composer(self):
        x=self.open(ref='old',case='case_B')
        self.assertEqual(x['human_reply_pending'],'DOT')
        self.assertTrue(x['historical_read_only'])
        self.assertFalse(x['composer_enabled'])

    def test_09_manager_aggregate_matches_owner_attention_without_ids(self):
        self.open()
        x=self.manager()
        self.assertEqual(x['cases_total'],2)
        self.assertEqual(x['cases_reply_pending'],2)
        self.assertEqual(x['cases_unread'],1)
        self.assertEqual(x['cases_read_without_reply'],1)
        self.assertNotIn('case_A',str(x))
        self.assertNotIn('seller_A',str(x))

    def test_10_queue_order_from_verified_time_not_status_labels(self):
        x=self.queue()['rows']
        self.assertEqual([z['case_ref'] for z in x],['case_A','case_B'])
        self.append('case_B',when='2026-11-01T11:00:00Z')
        self.assertEqual(self.queue()['rows'][0]['case_ref'],'case_B')

    def test_11_latest_unknown_timestamp_is_not_invented(self):
        self.append(when=None)
        x=self.queue()['rows']
        unknown=next(a for a in x if a['case_ref']=='case_A')
        self.assertIsNone(unknown['last_activity_at'])
        self.assertEqual(unknown['activity_time_state'],'UNKNOWN')
        self.assertEqual(x[-1]['case_ref'],'case_A')

    def test_12_unverified_latest_timestamp_does_not_inherit_old_time(self):
        self.append(verified=False)
        x=next(a for a in self.queue()['rows'] if a['case_ref']=='case_A')
        self.assertIsNone(x['last_activity_at'])

    def test_13_stale_version_denies_with_no_cursor(self):
        for col in self.expected:
            vals={**self.expected,col:2}
            self.assertEqual(self.open(ref='v_'+col,versions=vals)['decision'],'DENIED')
        self.assertEqual(self.cursor(),0)

    def test_14_wrong_operator_denied(self):
        x=self.open(actor='somebody_else')
        self.assertEqual(x['reason'],'NOT_CURRENT_OWNER')
        self.assertEqual(self.count(),0)

    def test_15_other_store_denied_even_if_actor_is_same(self):
        x=self.open(store='store-B')
        self.assertEqual(x['reason'],'SCOPE_DENIED')
        self.assertEqual(self.count(),0)

    def test_16_duplicate_open_ref_replays_without_new_read(self):
        self.assertEqual(self.open()['decision'],'LAB_READ_RECORDED_BEFORE_COMMIT')
        self.assertEqual(self.open()['decision'],'LAB_OPEN_REPLAY_NO_ADDITIONAL_READ')
        self.assertEqual(self.count(),1)

    def test_17_same_open_ref_for_different_case_is_collision(self):
        self.open()
        x=self.open(case='case_B')
        self.assertEqual(x['reason'],'OPEN_REF_COLLISION')
        self.assertEqual(self.cursor('case_B'),0)

    def test_18_stale_replay_after_new_inbound_does_not_mark_new_read(self):
        self.open();self.append()
        x=self.open()
        self.assertEqual(x['reason'],'STALE_OR_REASSIGNED')
        self.assertEqual(self.cursor(),1)

    def test_19_actor_reassignment_invalidates_original_owner(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_frontend_lab.cases SET owner_ref='seller_NEW',"
              "assignment_revision=2 WHERE case_ref='case_A'")
        self.assertEqual(self.open()['decision'],'DENIED')
        self.assertEqual(self.open(actor='seller_NEW',versions={
          **self.expected,'assignment_revision':2})['decision'],
          'LAB_READ_RECORDED_BEFORE_COMMIT')
        self.assertEqual(self.cursor('case_A','seller_A'),0)

    def test_20_hidden_inbound_does_not_inflate_counter(self):
        self.open();self.append(visible=False)
        rows=self.queue()['rows']
        self.assertEqual(rows[0]['unread_inbound_count'],0)
        self.assertEqual(rows[0]['human_reply_pending'],'DOT')

    def test_21_rollback_does_not_record_read(self):
        try:
            with self.lab.admin() as c:
                x=open_case(c,open_ref='rollback',case_ref='case_A',
                    store_ref='store-A',actor_ref='seller_A',role='OWNER',
                    allowed_stores=('store-A',),expected=self.expected)
                self.assertEqual(x['decision'],'LAB_READ_RECORDED_BEFORE_COMMIT')
                raise RuntimeError('disconnect')
        except RuntimeError:
            pass
        self.assertEqual(self.cursor(),0)
        self.assertEqual(self.count(),0)

    def test_22_runtime_has_no_schema_access(self):
        for table in ('cases','events','read_cursors','open_attempts'):
            with psycopg.connect(self.lab.runtime_dsn) as c:
                with self.assertRaises(psycopg.Error):
                    c.execute('SELECT * FROM s0_frontend_lab.'+table)

    def test_23_manager_cannot_receive_case_owner_queue(self):
        self.assertEqual(self.queue(actor='manager_A',role='SUPERVISOR')['decision'],'DENIED')
        self.assertEqual(self.manager('store-B')['cases_total'],1)
        self.assertEqual(self.cursor(),0)

    def test_24_same_open_ref_concurrent_one_recorded(self):
        gate=threading.Barrier(2)
        def run():
            with self.lab.admin() as c:
                gate.wait(timeout=8)
                return open_case(c,open_ref='race',case_ref='case_A',
                    store_ref='store-A',actor_ref='seller_A',role='OWNER',
                    allowed_stores=('store-A',),expected=self.expected)['decision']
        with ThreadPoolExecutor(max_workers=2) as pool:
            f=[pool.submit(run),pool.submit(run)]
            self.assertCountEqual([x.result(timeout=15) for x in f],
                ['LAB_READ_RECORDED_BEFORE_COMMIT',
                 'LAB_OPEN_REPLAY_NO_ADDITIONAL_READ'])
        self.assertEqual(self.count(),1)

    def test_25_concurrent_new_inbound_and_open_does_not_mark_unseen(self):
        gate=threading.Barrier(2)
        def read():
            with self.lab.admin() as c:
                gate.wait(timeout=8)
                return open_case(c,open_ref='race',case_ref='case_A',
                  store_ref='store-A',actor_ref='seller_A',role='OWNER',
                  allowed_stores=('store-A',),expected=self.expected)['decision']
        def incoming():
            gate.wait(timeout=8)
            self.append()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(read);b=pool.submit(incoming)
            outcome=a.result(timeout=15);b.result(timeout=15)
        self.assertIn(outcome,('DENIED','LAB_READ_RECORDED_BEFORE_COMMIT'))
        self.assertEqual(self.queue()['rows'][0]['human_reply_pending'],'COUNT')
        self.assertEqual(self.queue()['rows'][0]['unread_inbound_count'],1)

if __name__=='__main__':
    unittest.main()
