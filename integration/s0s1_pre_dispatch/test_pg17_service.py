"""S0 #10 disposable PG17 PRE_DISPATCH candidate tests; no real Graph.
The imported M09-08 unittest class is deliberately NOT imported into module
global scope, avoiding duplicate discovery.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from pathlib import Path

try:
    import psycopg
except ImportError:
    psycopg=None

from .pg17_service import reserve_in_admin_transaction
from integration.s0s1_m09_registry import test_pg17_use_check as base_tests


@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE')=='YES' and psycopg,
                     'disposable isolated PG17 source required')
class PreDispatchPhysical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_tests.PhysicalPointOfUse.setUpClass.__func__(cls)
        try:
            ddl=(cls.origin/'integration/s0s1_pre_dispatch/pg17_schema.sql').read_text()
            with cls.lab.admin() as c:
                c.execute("SET s0_meta.disposable='YES'")
                c.execute("SET s0_m09.install='PRE_DISPATCH_CANDIDATE_ONLY'")
                c.execute(ddl)
        except BaseException:
            base_tests.PhysicalPointOfUse.tearDownClass.__func__(cls)
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            with cls.lab.admin() as c:
                c.execute('DROP SCHEMA IF EXISTS s0_pre_dispatch_lab CASCADE')
        finally:
            base_tests.PhysicalPointOfUse.tearDownClass.__func__(cls)

    def setUp(self):
        base_tests.PhysicalPointOfUse.setUp(self)
        with self.lab.admin() as c:
            c.execute('TRUNCATE s0_pre_dispatch_lab.reservations,'
                      's0_pre_dispatch_lab.grants,'
                      's0_pre_dispatch_lab.campaigns,'
                      's0_pre_dispatch_lab.templates,'
                      's0_pre_dispatch_lab.suppressions,'
                      's0_pre_dispatch_lab.consents,'
                      's0_pre_dispatch_lab.cases CASCADE')
            c.execute("""INSERT INTO s0_pre_dispatch_lab.cases
             (case_ref,concessionaria_id,app_ref,route_ref,canal_id,waba_id,
             principal_ref,case_revision,assignment_revision,policy_revision,
             suppression_revision,active,global_opt_out)
             VALUES ('case_A','store-A','APP_A','route_A','channel_A','100001',
             'M09_KEY_A',1,1,1,1,true,false)""")
            c.execute("""INSERT INTO s0_pre_dispatch_lab.consents
             VALUES ('case_A','lead_followup',1,'GRANTED',
             clock_timestamp()+interval '1 hour')""")
            c.execute("""INSERT INTO s0_pre_dispatch_lab.suppressions
             VALUES ('case_A','*',false),('case_A','lead_followup',false),
                    ('case_A','sales_offer',false)""")
            c.execute("""INSERT INTO s0_pre_dispatch_lab.templates
             VALUES ('tpl_A','ver_1','store-A','100001',
                     'followup_message','lead_followup',1,true,true,true,
                     clock_timestamp()+interval '1 hour')""")
            c.execute("""INSERT INTO s0_pre_dispatch_lab.campaigns
             VALUES ('camp_A','case_A','tpl_A','ver_1',1,true,true)""")
            c.execute("""INSERT INTO s0_pre_dispatch_lab.grants
             VALUES ('case_A','M09_KEY_A','tpl_A','ver_1',
                     'camp_A','followup_message',1,true)""")
        self.req={
            'attempt_ref':'attempt_A',
            'selection_ref':'selection_A',
            'case_ref':'case_A',
            'service_ref':'M09_KEY_A',
            'template_ref':'tpl_A',
            'template_version':'ver_1',
            'template_purpose_ref':'followup_message',
            'consent_purpose_ref':'lead_followup',
            'campaign_ref':'camp_A',
            'expected_case_revision':1,
            'expected_assignment_revision':1,
            'expected_policy_revision':1,
            'expected_suppression_revision':1,
            'expected_consent_revision':1,
            'expected_template_revision':1,
            'expected_campaign_revision':1,
            'expected_grant_revision':1,
        }

    def _reserve(self, edits=None):
        with self.lab.admin() as c:
            return reserve_in_admin_transaction(
                c, {**self.req,**(edits or {})},
                scope=self.scope,principal=self.principal,
                m09_versions=self.versions)

    def _denied(self,x,why=None):
        self.assertNotEqual(x['decision'],'LAB_RESERVATION_RECORDED_NO_DISPATCH')
        self.assertFalse(x['lab_reservation_recorded'])
        if why:
            self.assertEqual(x['reason'],why)
        for flag in ('production_authorized','send_authorized',
                     'external_http_ack','graph_authorized',
                     'credential_resolution_authorized',
                     'pre_dispatch_operationally_authorized',
                     'provider_approval_verified',
                     'consent_proven_from_real_source',
                     'commercial_transition_authorized'):
            self.assertFalse(x[flag])

    def _counts(self):
        with self.lab.admin() as c:
            n=c.execute('SELECT COUNT(*) AS n FROM s0_pre_dispatch_lab.reservations').fetchone()['n']
            m=c.execute("SELECT COUNT(*) AS n FROM s0_m09_lab.point_of_use_checks").fetchone()['n']
            return (n,m)

    def test_01_case_selected_and_reserved_lab_only(self):
        out=self._reserve()
        self.assertEqual(out['decision'],'LAB_RESERVATION_RECORDED_NO_DISPATCH')
        self.assertTrue(out['lab_reservation_recorded'])
        self.assertFalse(out['send_authorized'])
        self.assertFalse(out['pre_dispatch_operationally_authorized'])
        self.assertEqual(self._counts(),(1,1))

    def test_02_duplicate_attempt_denies_without_extra_log(self):
        self.assertEqual(self._reserve()['decision'],'LAB_RESERVATION_RECORDED_NO_DISPATCH')
        self._denied(self._reserve(), 'DUPLICATE_ATTEMPT')
        self.assertEqual(self._counts(),(1,1))

    def test_03_replay_new_attempt_same_selection_denied(self):
        self._reserve()
        self._denied(self._reserve({'attempt_ref':'attempt_B'}),'DUPLICATE_ATTEMPT')
        self.assertEqual(self._counts(),(1,1))

    def test_04_invalid_requests_never_call_m09(self):
        for changed in ({'new':'field'}, {'expected_grant_revision':True},
                        {'template_purpose_ref':''},{'attempt_ref':'bad id'}):
            self._denied(self._reserve(changed),'INVALID_REQUEST')
        self.assertEqual(self._counts(),(0,0))

    def test_05_unapproved_paused_or_unverified_media_template_denied(self):
        for statement in ("UPDATE s0_pre_dispatch_lab.templates SET provider_approved=false",
                          "UPDATE s0_pre_dispatch_lab.templates SET active=false",
                          "UPDATE s0_pre_dispatch_lab.templates SET media_verified=false"):
            with self.lab.admin() as c:
                c.execute(statement)
            self._denied(self._reserve(),'TEMPLATE_UNVERIFIED')
            self.assertEqual(self._counts(),(0,0))
            with self.lab.admin() as c:
                c.execute("UPDATE s0_pre_dispatch_lab.templates SET provider_approved=true,active=true,media_verified=true")

    def test_06_consent_denied_unknown_revoked_and_missing_denied(self):
        for state in ('DENIED','UNKNOWN','REVOKED'):
            with self.lab.admin() as c:
                c.execute("UPDATE s0_pre_dispatch_lab.consents SET state=%s",(state,))
            self._denied(self._reserve(),'CONSENT_DENIED')
        with self.lab.admin() as c:
            c.execute("DELETE FROM s0_pre_dispatch_lab.consents")
        self._denied(self._reserve(),'CONSENT_DENIED')
        self.assertEqual(self._counts(),(0,0))

    def test_07_specific_and_global_suppression_denied(self):
        for purpose in ('lead_followup','*'):
            with self.lab.admin() as c:
                c.execute("UPDATE s0_pre_dispatch_lab.suppressions SET active=true WHERE purpose_ref=%s",(purpose,))
            self._denied(self._reserve(),'SUPPRESSED')
            with self.lab.admin() as c:
                c.execute("UPDATE s0_pre_dispatch_lab.suppressions SET active=false WHERE purpose_ref=%s",(purpose,))
        self.assertEqual(self._counts(),(0,0))

    def test_08_other_purpose_suppression_not_a_grant(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_pre_dispatch_lab.suppressions SET active=true WHERE purpose_ref='sales_offer'")
        out=self._reserve()
        self.assertEqual(out['decision'],'LAB_RESERVATION_RECORDED_NO_DISPATCH')
        self.assertFalse(out['send_authorized'])

    def test_09_global_opt_out_and_inactive_case_denied(self):
        for key in ('global_opt_out','active'):
            with self.lab.admin() as c:
                c.execute(f"UPDATE s0_pre_dispatch_lab.cases SET {key}=%s",(
                          True if key=='global_opt_out' else False,))
            self._denied(self._reserve(),'POLICY_DENIED')
            with self.lab.admin() as c:
                c.execute(f"UPDATE s0_pre_dispatch_lab.cases SET {key}=%s",(
                          False if key=='global_opt_out' else True,))

    def test_10_expired_consent_or_template_denied(self):
        for table in ('consents','templates'):
            with self.lab.admin() as c:
                c.execute("UPDATE s0_pre_dispatch_lab."+table+
                  " SET valid_until=clock_timestamp()-interval '1 minute'")
            self._denied(self._reserve(),'EXPIRED')
            with self.lab.admin() as c:
                c.execute("UPDATE s0_pre_dispatch_lab."+table+
                  " SET valid_until=clock_timestamp()+interval '1 hour'")

    def test_11_policy_case_assignment_and_suppression_cas(self):
        for col,req in (('case_revision','expected_case_revision'),
                        ('assignment_revision','expected_assignment_revision'),
                        ('policy_revision','expected_policy_revision'),
                        ('suppression_revision','expected_suppression_revision')):
            self._denied(self._reserve({req:2}),'STALE_OR_CHANGED')
        self.assertEqual(self._counts(),(0,0))

    def test_12_consent_template_campaign_grant_cas(self):
        for req in ('expected_consent_revision','expected_template_revision',
                    'expected_campaign_revision','expected_grant_revision'):
            self._denied(self._reserve({req:2}),'STALE_OR_CHANGED')
        self.assertEqual(self._counts(),(0,0))

    def test_13_other_store_waba_purpose_and_case_denied(self):
        for table,column,value in (
            ('cases','concessionaria_id','store-B'),
            ('cases','waba_id','100002'),
            ('templates','concessionaria_id','store-B'),
            ('templates','consent_purpose_ref','wrong_purpose'),
            ('campaigns','case_ref','case_B'),
            ('grants','template_purpose_ref','sales_offer')
        ):
            if table=='campaigns':
                self._denied(self._reserve({'campaign_ref':'does-not-exist'}))
                continue
            with self.lab.admin() as c:
                c.execute('UPDATE s0_pre_dispatch_lab.'+table+' SET '+column+'=%s',(value,))
            self._denied(self._reserve())
            with self.lab.admin() as c:
                default={
                    'concessionaria_id':'store-A','waba_id':'100001',
                    'consent_purpose_ref':'lead_followup',
                    'template_purpose_ref':'followup_message'}[column]
                c.execute('UPDATE s0_pre_dispatch_lab.'+table+' SET '+column+'=%s',(default,))
        self.assertEqual(self._counts(),(0,0))

    def test_14_campaign_inactive_or_not_eligible(self):
        for col in ('active','eligible'):
            with self.lab.admin() as c:
                c.execute('UPDATE s0_pre_dispatch_lab.campaigns SET '+col+'=false')
            self._denied(self._reserve(),'CAMPAIGN_DENIED')
            with self.lab.admin() as c:
                c.execute('UPDATE s0_pre_dispatch_lab.campaigns SET '+col+'=true')

    def test_15_grant_inactive_or_wrong_service_denied(self):
        with self.lab.admin() as c:
            c.execute('UPDATE s0_pre_dispatch_lab.grants SET active=false')
        self._denied(self._reserve(),'GRANT_DENIED')
        with self.lab.admin() as c:
            c.execute('UPDATE s0_pre_dispatch_lab.grants SET active=true')
        self._denied(self._reserve({'service_ref':'forged'}),'SCOPE_CHANGED')

    def test_16_m09_binding_revoked_denies_before_policy(self):
        from integration.s0s1_m09_registry.pg17_registry import revoke_channel_in_admin_transaction
        with self.lab.admin() as c:
            self.assertEqual(revoke_channel_in_admin_transaction(
                c,'route_A','channel_A',1,1,1,1),'REVOKED_IN_DISPOSABLE_TRANSACTION')
        self._denied(self._reserve(),'STALE_OR_CHANGED')
        self.assertEqual(self._counts(),(0,0))

    def test_17_rollbacks_removes_check_and_reservation(self):
        try:
            with self.lab.admin() as c:
                out=reserve_in_admin_transaction(
                    c,self.req,scope=self.scope,principal=self.principal,
                    m09_versions=self.versions)
                self.assertEqual(out['decision'],'LAB_RESERVATION_RECORDED_NO_DISPATCH')
                raise RuntimeError('simulate disconnected commit')
        except RuntimeError:
            pass
        self.assertEqual(self._counts(),(0,0))
        self.assertEqual(self._reserve()['decision'],'LAB_RESERVATION_RECORDED_NO_DISPATCH')

    def test_18_runtime_cannot_select_or_insert_policy_or_reservation(self):
        for tbl in ('cases','consents','templates','grants','reservations'):
            with psycopg.connect(self.lab.runtime_dsn) as c:
                with self.assertRaises(psycopg.Error):
                    c.execute('SELECT * FROM s0_pre_dispatch_lab.'+tbl)

    def test_19_concurrent_same_attempt_one_reservation_only(self):
        gate=threading.Barrier(2)
        def work():
            with self.lab.admin() as c:
                gate.wait(timeout=8)
                return reserve_in_admin_transaction(
                    c,self.req,scope=self.scope,principal=self.principal,
                    m09_versions=self.versions)['decision']
        with ThreadPoolExecutor(max_workers=2) as pool:
            f=[pool.submit(work) for _ in range(2)]
            decisions=[p.result(timeout=15) for p in f]
        self.assertCountEqual(decisions,
            ['LAB_RESERVATION_RECORDED_NO_DISPATCH','DENIED'])
        self.assertEqual(self._counts(),(1,1))

    def test_20_concurrent_revoke_vs_reservation_serializes(self):
        from integration.s0s1_m09_registry.pg17_registry import revoke_channel_in_admin_transaction
        gate=threading.Barrier(2)
        def reserve():
            with self.lab.admin() as c:
                gate.wait(timeout=8)
                return reserve_in_admin_transaction(
                    c,self.req,scope=self.scope,principal=self.principal,
                    m09_versions=self.versions)['decision']
        def revoke():
            with self.lab.admin() as c:
                gate.wait(timeout=8)
                return revoke_channel_in_admin_transaction(
                    c,'route_A','channel_A',1,1,1,1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(reserve);b=pool.submit(revoke)
            result=a.result(timeout=15); rev=b.result(timeout=15)
        self.assertEqual(rev,'REVOKED_IN_DISPOSABLE_TRANSACTION')
        self.assertIn(result,('DENIED','LAB_RESERVATION_RECORDED_NO_DISPATCH'))
        self._denied(self._reserve({'attempt_ref':'after','selection_ref':'after'}))
        self.assertEqual(self._counts(),(1,1) if result=='LAB_RESERVATION_RECORDED_NO_DISPATCH' else (0,0))

    def test_21_concurrent_consent_revocation_vs_reservation_serializes(self):
        gate=threading.Barrier(2)
        def reserve():
            with self.lab.admin() as c:
                gate.wait(timeout=8)
                return reserve_in_admin_transaction(
                    c,self.req,scope=self.scope,principal=self.principal,
                    m09_versions=self.versions)['decision']
        def consent_revoke():
            with self.lab.admin() as c:
                gate.wait(timeout=8)
                c.execute("UPDATE s0_pre_dispatch_lab.cases SET policy_revision=policy_revision+1 WHERE case_ref='case_A'")
                c.execute("UPDATE s0_pre_dispatch_lab.consents SET state='REVOKED',revision=revision+1 WHERE case_ref='case_A'")
            return True
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(reserve);b=pool.submit(consent_revoke)
            decision=a.result(timeout=15);self.assertTrue(b.result(timeout=15))
        self.assertIn(decision,('DENIED','LAB_RESERVATION_RECORDED_NO_DISPATCH'))
        self._denied(self._reserve({'attempt_ref':'fresh','selection_ref':'fresh'}))
        self.assertEqual(self._counts(),(1,1) if decision=='LAB_RESERVATION_RECORDED_NO_DISPATCH' else (0,0))

    def test_22_commit_unknown_retry_same_ref_cannot_duplicate(self):
        self.assertEqual(self._reserve()['decision'],'LAB_RESERVATION_RECORDED_NO_DISPATCH')
        self._denied(self._reserve(),'DUPLICATE_ATTEMPT')
        self._denied(self._reserve({'attempt_ref':'different'}),'DUPLICATE_ATTEMPT')

    def test_24_caller_cannot_use_other_service_grant(self):
        # An admin can seed an otherwise valid alternate-service grant, but
        # a request cannot impersonate it via caller-supplied service_ref.
        with self.lab.admin() as c:
            c.execute("""INSERT INTO s0_pre_dispatch_lab.grants
             VALUES ('case_A','OTHER_SERVICE','tpl_A','ver_1',
                     'camp_A','followup_message',1,true)""")
        self._denied(self._reserve({'service_ref':'OTHER_SERVICE'}),'SCOPE_CHANGED')
        self.assertEqual(self._counts(),(0,0))

    def test_23_all_eligibility_flags_remain_false_for_lab_success(self):
        o=self._reserve()
        for flag in ('production_authorized','send_authorized','graph_authorized',
                     'credential_resolution_authorized',
                     'pre_dispatch_operationally_authorized',
                     'provider_approval_verified','consent_proven_from_real_source',
                     'commercial_transition_authorized','external_http_ack'):
            self.assertFalse(o[flag])
        self.assertNotIn('slot_ref',o)
        self.assertNotIn('token',o)
        self.assertNotIn('graph_response',o)


if __name__=='__main__':
    unittest.main()
