"""PG17 lab physical ownership checks; no model, message, production authority."""
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
try:
    import psycopg
except ImportError:
    psycopg=None
from integration.s0s1_frontend_read import test_pg17_service as base
from .pg17_service import begin_turn,definitive_handoff,recheck_proposal,NO_AUTH

@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE')=='YES' and psycopg,
                     'disposable PG17 only')
class F01OwnershipPhysical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base.FrontendReadPhysical.setUpClass.__func__(cls)
        try:
            with cls.lab.admin() as c:
                c.execute("SET s0_meta.disposable='YES'")
                c.execute("SET s0_f01.install='OWNER_HANDOFF_LAB_ONLY'")
                c.execute((cls.origin/'integration/s0s1_f01_ownership/pg17_schema.sql').read_text())
        except BaseException:
            base.FrontendReadPhysical.tearDownClass.__func__(cls)
            raise
    @classmethod
    def tearDownClass(cls):
        try:
            with cls.lab.admin() as c:
                c.execute('DROP SCHEMA IF EXISTS s0_f01_lab CASCADE')
        finally:
            base.FrontendReadPhysical.tearDownClass.__func__(cls)
    def setUp(self):
        base.FrontendReadPhysical.setUp(self)
        with self.lab.admin() as c:
            c.execute('TRUNCATE s0_f01_lab.publication_checks,'
                      's0_f01_lab.handoff_events,s0_f01_lab.turns,'
                      's0_f01_lab.cases CASCADE')
            c.execute("""INSERT INTO s0_f01_lab.cases (
                case_ref,store_ref,person_ref,service_ref,owner_route,
                case_revision,cycle_revision,assignment_revision,
                catalog_revision,knowledge_revision,policy_revision,
                route_revision,consent_revision) VALUES
                ('case_A','store-A','person_A','f01_service_A','AI',
                 1,1,1,1,1,1,1,1),
                ('case_B','store-B','person_B','f01_service_B','AI',
                 1,1,1,1,1,1,1,1)""")
        self.scope={'case_ref':'case_A','store_ref':'store-A',
                    'person_ref':'person_A','service_ref':'f01_service_A'}
        self.expected={k:1 for k in ('case','cycle','assignment','catalog',
                                     'knowledge','policy','route','consent')}
        self.hash='a'*64
    def start(self,ref='turn_A',scope=None,versions=None):
        with self.lab.admin() as c:
            return begin_turn(c,turn_ref=ref,scope=scope or self.scope,
                              expected=versions or self.expected)
    def handoff(self,ref='handoff_A',scope=None,versions=None):
        with self.lab.admin() as c:
            return definitive_handoff(c,event_ref=ref,scope=scope or self.scope,
                                      expected=versions or self.expected)
    def review(self,ref='turn_A',scope=None,versions=None,hash_value=None):
        with self.lab.admin() as c:
            return recheck_proposal(c,turn_ref=ref,scope=scope or self.scope,
                expected=versions or self.expected,
                candidate_digest=hash_value or self.hash)
    def counts(self):
        with self.lab.admin() as c:
            return tuple(c.execute('SELECT count(*) AS n FROM s0_f01_lab.'+p)
                 .fetchone()['n'] for p in ('turns','handoff_events',
                                            'publication_checks'))
    def flags(self,x):
        self.assertTrue(x['lab_only'])
        self.assertTrue(all(x[k] is False for k in NO_AUTH))
    def test_01_ai_turn_recorded_no_model_authority(self):
        x=self.start();self.assertEqual(x['status'],'LAB_TURN_RECORDED_NO_MODEL')
        self.flags(x);self.assertEqual(self.counts(),(1,0,0))
    def test_02_exact_turn_replay_no_duplicate(self):
        self.start();self.assertEqual(self.start()['status'],'LAB_TURN_REPLAY_ONLY')
        self.assertEqual(self.counts(),(1,0,0))
    def test_03_turn_ref_collision_other_case_denied(self):
        self.start()
        other={**self.scope,'case_ref':'case_B'}
        x=self.start(scope=other)
        self.assertEqual(x['status'],'DENIED')
        self.assertEqual(self.counts(),(1,0,0))
    def test_04_initial_scope_cross_store_person_service_denied(self):
        for field,value in [('store_ref','store-B'),('person_ref','person_B'),
                            ('service_ref','f01_service_B'),('case_ref','case_X')]:
            x=self.start(ref='bad_'+field,scope={**self.scope,field:value})
            self.assertEqual(x['reason'],'SCOPE_DENIED')
        self.assertEqual(self.counts(),(0,0,0))
    def test_05_each_of_eight_revisions_independently_denied(self):
        for key in self.expected:
            x=self.start(ref='bad_'+key,versions={**self.expected,key:2})
            self.assertEqual(x['reason'],'STALE_VERSIONS')
        self.assertEqual(self.counts(),(0,0,0))
    def test_06_optout_or_channel_ineligible_block(self):
        for field,setting in [('opt_out',True),('channel_eligible',False)]:
            with self.lab.admin() as c:
                c.execute('UPDATE s0_f01_lab.cases SET '+field+'=%s '
                          "WHERE case_ref='case_A'",(setting,))
            self.assertEqual(self.start()['reason'],'POLICY_DENIED')
            with self.lab.admin() as c:
                c.execute('UPDATE s0_f01_lab.cases SET '+field+'=%s '
                          "WHERE case_ref='case_A'",(not setting,))
    def test_07_post_remittance_and_post_sale_block(self):
        for field in ('post_remittance','post_sale'):
            with self.lab.admin() as c:
                c.execute('UPDATE s0_f01_lab.cases SET '+field+
                          "=true WHERE case_ref='case_A'")
            self.assertEqual(self.start()['reason'],'POLICY_DENIED')
            with self.lab.admin() as c:
                c.execute('UPDATE s0_f01_lab.cases SET '+field+
                          "=false WHERE case_ref='case_A'")
    def test_08_handoff_durably_switches_to_human(self):
        x=self.handoff()
        self.assertEqual(x['status'],'LAB_HANDOFF_DURABLY_RECORDED_NO_PUBLISH')
        self.flags(x);self.assertEqual(self.counts(),(0,1,0))
        with self.lab.admin() as c:
            k=c.execute("SELECT owner_route,handoff_sequence FROM "
              "s0_f01_lab.cases WHERE case_ref='case_A'").fetchone()
        self.assertEqual(k['owner_route'],'HUMAN')
        self.assertEqual(k['handoff_sequence'],1)
    def test_09_handoff_exact_replay_is_irreversible(self):
        self.handoff()
        x=self.handoff();self.assertEqual(x['status'],'LAB_HANDOFF_REPLAY_HUMAN_ONLY')
        self.assertEqual(self.counts(),(0,1,0))
    def test_10_handoff_other_event_ref_denies(self):
        self.handoff()
        self.assertEqual(self.handoff(ref='other')['reason'],'HUMAN_ONLY')
    def test_11_late_ai_turn_denied_after_handoff(self):
        self.handoff()
        self.assertEqual(self.start()['reason'],'HUMAN_ONLY')
        self.assertEqual(self.counts(),(0,1,0))
    def test_12_handoff_precedes_stale_revision_denial(self):
        self.handoff()
        x=self.start(versions={**self.expected,'case':2})
        self.assertEqual(x['reason'],'HUMAN_ONLY')
    def test_13_db_trigger_blocks_direct_ai_reopen(self):
        self.handoff()
        with self.assertRaises(psycopg.Error):
            with self.lab.admin() as c:
                c.execute("UPDATE s0_f01_lab.cases SET "
                  "owner_route='AI',handoff_definitive=false,humanized=false "
                  "WHERE case_ref='case_A'")
        self.assertEqual(self.start()['reason'],'HUMAN_ONLY')
    def test_14_new_inbound_version_bump_cannot_restart_ai(self):
        self.handoff()
        with self.lab.admin() as c:
            c.execute("UPDATE s0_f01_lab.cases SET "
                "cycle_revision=cycle_revision+1 WHERE case_ref='case_A'")
        self.assertEqual(self.start()['reason'],'HUMAN_ONLY')
    def test_15_normal_recheck_records_no_publication(self):
        self.start();x=self.review()
        self.assertEqual(x['status'],'LAB_RECHECK_RECORDED_NO_PUBLISH')
        self.flags(x);self.assertEqual(self.counts(),(1,0,1))
    def test_16_exact_recheck_replay_no_extra_record(self):
        self.start();self.review()
        self.assertEqual(self.review()['status'],'LAB_RECHECK_REPLAY_NO_PUBLISH')
        self.assertEqual(self.counts(),(1,0,1))
    def test_17_changed_model_digest_conflict_denied(self):
        self.start();self.review()
        self.assertEqual(self.review(hash_value='b'*64)['reason'],'PROPOSAL_CONFLICT')
    def test_18_missing_turn_cannot_recheck(self):
        self.assertEqual(self.review()['reason'],'MISSING_OR_CHANGED_TURN')
        self.assertEqual(self.counts(),(0,0,0))
    def test_19_handoff_after_inference_denies_recheck(self):
        self.start();self.handoff()
        self.assertEqual(self.review()['reason'],'HUMAN_ONLY')
        self.assertEqual(self.counts(),(1,1,0))
    def test_20_policy_mutated_after_turn_denies_recheck(self):
        self.start()
        with self.lab.admin() as c:
            c.execute("UPDATE s0_f01_lab.cases SET opt_out=true, "
              "policy_revision=policy_revision+1 WHERE case_ref='case_A'")
        self.assertEqual(self.review()['reason'],'POLICY_DENIED')
    def test_21_late_turn_recheck_denies_deadline(self):
        self.start()
        with self.lab.admin() as c:
            c.execute("UPDATE s0_f01_lab.turns SET "
              "deadline_at=clock_timestamp()-interval '1 minute' ")
        self.assertEqual(self.review()['reason'],'TURN_EXPIRED')
    def test_22_runtime_cannot_read_owner_or_write_handoff(self):
        for table in ('cases','turns','handoff_events','publication_checks'):
            with psycopg.connect(self.lab.runtime_dsn) as c:
                with self.assertRaises(psycopg.Error):
                    c.execute('SELECT * FROM s0_f01_lab.'+table)
    def test_23_concurrent_two_handoff_attempts_one_winner(self):
        gate=threading.Barrier(2)
        def job(ref):
            with self.lab.admin() as c:
                gate.wait(timeout=7)
                return definitive_handoff(c,event_ref=ref,
                   scope=self.scope,expected=self.expected)['status']
        with ThreadPoolExecutor(max_workers=2) as pool:
            xs=[pool.submit(job,'one'),pool.submit(job,'two')]
            results=[x.result(timeout=15) for x in xs]
        self.assertCountEqual(results,['LAB_HANDOFF_DURABLY_RECORDED_NO_PUBLISH',
                                        'DENIED'])
        self.assertEqual(self.counts(),(0,1,0))
    def test_24_handoff_racing_publish_check_never_grants_publish(self):
        self.start()
        gate=threading.Barrier(2)
        def check():
            with self.lab.admin() as c:
                gate.wait(timeout=7)
                return recheck_proposal(c,turn_ref='turn_A',
                  scope=self.scope,expected=self.expected,
                  candidate_digest=self.hash)
        def human():
            with self.lab.admin() as c:
                gate.wait(timeout=7)
                return definitive_handoff(c,event_ref='handoff_A',
                  scope=self.scope,expected=self.expected)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(check);b=pool.submit(human)
            reviewed=a.result(timeout=15);transferred=b.result(timeout=15)
        self.assertEqual(transferred['status'],
                         'LAB_HANDOFF_DURABLY_RECORDED_NO_PUBLISH')
        self.flags(reviewed);self.flags(transferred)
        self.assertIn(reviewed['status'],
            ('DENIED','LAB_RECHECK_RECORDED_NO_PUBLISH'))
        self.assertEqual(self.review()['reason'],'HUMAN_ONLY')
    def test_25_transaction_rollback_keeps_ai_owner(self):
        try:
            with self.lab.admin() as c:
                status=definitive_handoff(c,event_ref='rollback',
                   scope=self.scope,expected=self.expected)['status']
                self.assertEqual(status,'LAB_HANDOFF_DURABLY_RECORDED_NO_PUBLISH')
                raise RuntimeError('simulate abort')
        except RuntimeError: pass
        self.assertEqual(self.counts(),(0,0,0))
        self.assertEqual(self.start()['status'],'LAB_TURN_RECORDED_NO_MODEL')

if __name__=='__main__':
    unittest.main()
