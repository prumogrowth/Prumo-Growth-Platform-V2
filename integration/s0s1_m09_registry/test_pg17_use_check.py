"""M09-08 physical point-of-use CONTROL test matrix on disposable PG17.

The check journal is an audit log, not an authorization for Graph, credential
redemption, HTTP ACK or the distinct PRE_DISPATCH (#10) contract.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import threading
import unittest

try:
    import psycopg
except ImportError:
    psycopg = None

from .pg17_use_check import record_control_check_in_admin_transaction as checkpoint
from .pg17_registry import revoke_channel_in_admin_transaction
from .port import HostScope, M2MPrincipal, Revisions, FLAGS
from . import test_pg17_m2m as m2mtests


@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE')=='YES' and psycopg,
                     'exclusive disposable PostgreSQL 17 fixture required')
class PhysicalPointOfUse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=m2mtests.PhysicalM09Signed
        cls.base.setUpClass.__func__(cls)
        try:
            filename=cls.origin/'integration/s0s1_m09_registry/pg17_use_check.sql'
            sql=filename.read_text()
            with cls.lab.admin() as c:
                c.execute("SET s0_meta.disposable='YES'")
                c.execute("SET s0_m09.install='POINT_OF_USE_CANDIDATE_ONLY'")
                c.execute(sql)
        except BaseException:
            cls.base.tearDownClass.__func__(cls)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.base.tearDownClass.__func__(cls)

    def setUp(self):
        self.base.setUp(self)
        with self.lab.admin() as c:
            c.execute('TRUNCATE s0_m09_lab.point_of_use_checks')
        self.scope=self.host['valid']
        self.principal=self.p
        self.versions=Revisions(1,1,1,1,1)

    def check(self, attempt='attempt-A', *, scope=None, principal=None, versions=None):
        with self.lab.admin() as c:
            return checkpoint(c,scope=scope or self.scope,
                principal=principal or self.principal,
                expected=versions or self.versions,attempt_ref=attempt)

    def deny(self,result):
        self.assertNotEqual(result['decision'],'LAB_CHECK_RECORDED_NO_USE')
        self.assertFalse(result['check_recorded_lab_only'])
        self.assertTrue(all(result[key] is False for key in FLAGS))
        self.assertFalse(result['credential_resolution_authorized'])
        self.assertFalse(result['external_use_authorized'])
        self.assertFalse(result['pre_dispatch_authorized'])

    def test_01_checkpoint_records_one_audit_only(self):
        x=self.check()
        self.assertEqual(x['decision'],'LAB_CHECK_RECORDED_NO_USE')
        self.assertEqual(x['reason'],'AUDIT_ONLY_NO_EXTERNAL_USE')
        self.assertTrue(x['check_recorded_lab_only'])
        self.assertTrue(all(x[k] is False for k in FLAGS))
        self.assertFalse(x['external_use_authorized'])
        self.assertFalse(x['pre_dispatch_authorized'])
        with self.lab.admin() as c:
            n=c.execute('SELECT COUNT(*) AS n FROM s0_m09_lab.point_of_use_checks').fetchone()['n']
        self.assertEqual(n,1)

    def test_02_duplicate_attempt_is_denied(self):
        self.assertEqual(self.check()['decision'],'LAB_CHECK_RECORDED_NO_USE')
        x=self.check()
        self.deny(x)
        self.assertEqual(x['reason'],'DUPLICATE_ATTEMPT')

    def test_03_different_attempts_are_separate_control_logs(self):
        self.assertEqual(self.check('one')['decision'],'LAB_CHECK_RECORDED_NO_USE')
        self.assertEqual(self.check('two')['decision'],'LAB_CHECK_RECORDED_NO_USE')

    def test_04_each_version_is_checked_independently(self):
        for k in ('route','app','binding','grant','principal'):
            values={name:getattr(self.versions,name) for name in
                    ('route','app','binding','grant','principal')}
            values[k]=2
            self.deny(self.check(k,versions=Revisions(**values)))

    def test_05_revocation_first_denies_and_writes_no_journal(self):
        with self.lab.admin() as c:
            a=revoke_channel_in_admin_transaction(
                c,'route_A','channel_A',1,1,1,1)
        self.assertEqual(a,'REVOKED_IN_DISPOSABLE_TRANSACTION')
        self.deny(self.check())
        with self.lab.admin() as c:
            n=c.execute('SELECT COUNT(*) AS n FROM s0_m09_lab.point_of_use_checks').fetchone()['n']
        self.assertEqual(n,0)

    def test_06_old_record_survives_revoke_but_never_authorizes(self):
        self.assertEqual(self.check()['decision'],'LAB_CHECK_RECORDED_NO_USE')
        with self.lab.admin() as c:
            revoke_channel_in_admin_transaction(c,'route_A','channel_A',1,1,1,1)
        self.deny(self.check('new-after-revoke'))
        with self.lab.admin() as c:
            n=c.execute('SELECT COUNT(*) AS n FROM s0_m09_lab.point_of_use_checks').fetchone()['n']
        self.assertEqual(n,1)

    def test_07_runtime_cannot_read_or_append_control_journal(self):
        for sql in ('SELECT * FROM s0_m09_lab.point_of_use_checks',
                    "INSERT INTO s0_m09_lab.point_of_use_checks(attempt_ref) VALUES('not-allowed')"):
            with psycopg.connect(self.lab.runtime_dsn) as c:
                with self.assertRaises(psycopg.Error):
                    c.execute(sql)

    def test_08_commit_rollback_removes_control_record(self):
        try:
            with self.lab.admin() as c:
                self.assertEqual(checkpoint(
                    c,scope=self.scope,principal=self.principal,
                    expected=self.versions,attempt_ref='rollback')[
                    'decision'],'LAB_CHECK_RECORDED_NO_USE')
                raise RuntimeError('simulate aborted transaction')
        except RuntimeError:
            pass
        self.assertEqual(self.check('rollback')['decision'],'LAB_CHECK_RECORDED_NO_USE')

    def test_09_cross_store_and_cross_app_scope_fail(self):
        self.deny(self.check(scope=replace(self.scope,concessionaria_id='store-B')))
        self.deny(self.check(scope=replace(self.scope,app_ref='APP_B')))

    def test_10_wrong_waba_phone_channel_fail(self):
        self.deny(self.check(scope=replace(self.scope,waba_id='100002')))
        self.deny(self.check(scope=replace(self.scope,phone_number_id='300003')))
        self.deny(self.check(scope=replace(self.scope,canal_id='channel_B')))

    def test_11_principal_revision_issuer_scope_or_audience_fail(self):
        self.deny(self.check(principal=replace(self.principal,key_revision=2)))
        self.deny(self.check(principal=replace(self.principal,issuer_ref='FAKE')))
        self.deny(self.check(principal=replace(self.principal,audience='PROD')))
        self.deny(self.check(principal=replace(self.principal,allowed_stores=frozenset())))

    def test_12_db_grant_revocation_without_route_bump_is_denied(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_m09_lab.grants SET active=false WHERE canal_id='channel_A'")
        self.deny(self.check())

    def test_13_db_principal_expiry_fail_closed(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.principals SET not_after=clock_timestamp()-interval '1 minute'")
        self.deny(self.check())

    def test_14_ambiguous_original_phone_fails(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.bindings SET phone='200001' WHERE route='route_B'")
        x=self.check()
        self.deny(x)
        self.assertEqual(x['reason'],'AMBIGUOUS_BINDING')

    def test_15_ambiguous_original_waba_fails(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.bindings SET waba='100001' WHERE route='route_B'")
        x=self.check()
        self.deny(x)
        self.assertEqual(x['reason'],'AMBIGUOUS_BINDING')

    def test_16_concurrent_same_attempt_one_journal_only(self):
        start=threading.Barrier(2)
        def worker():
            with self.lab.admin() as c:
                start.wait(timeout=6)
                return checkpoint(c,scope=self.scope,principal=self.principal,
                    expected=self.versions,attempt_ref='same-attempt')['decision']
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(worker) for _ in range(2)]
            decisions=[f.result(timeout=12) for f in futures]
        self.assertCountEqual(decisions,['LAB_CHECK_RECORDED_NO_USE','DENIED'])
        with self.lab.admin() as c:
            n=c.execute("SELECT COUNT(*) AS n FROM s0_m09_lab.point_of_use_checks WHERE attempt_ref='same-attempt'").fetchone()['n']
        self.assertEqual(n,1)

    def test_17_concurrent_revoke_vs_check_serializes_under_route_lock(self):
        start=threading.Barrier(2)
        def reserve():
            with self.lab.admin() as c:
                start.wait(timeout=6)
                return checkpoint(c,scope=self.scope,principal=self.principal,
                    expected=self.versions,attempt_ref='race')['decision']
        def revoke():
            with self.lab.admin() as c:
                start.wait(timeout=6)
                return revoke_channel_in_admin_transaction(
                    c,'route_A','channel_A',1,1,1,1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(reserve),pool.submit(revoke)]
            decisions=[f.result(timeout=12) for f in futures]
        self.assertEqual(decisions[1],'REVOKED_IN_DISPOSABLE_TRANSACTION')
        self.assertIn(decisions[0],('LAB_CHECK_RECORDED_NO_USE','DENIED'))
        self.deny(self.check('post-race'))
        with self.lab.admin() as c:
            n=c.execute("SELECT COUNT(*) AS n FROM s0_m09_lab.point_of_use_checks WHERE attempt_ref='race'").fetchone()['n']
        self.assertEqual(n,1 if decisions[0]=='LAB_CHECK_RECORDED_NO_USE' else 0)

    def test_18_invalid_attempt_and_unauthorized_proof_denied(self):
        self.deny(self.check(attempt='bad attempt with whitespace'))
        self.deny(self.check(principal=replace(
            self.principal,allowed_purposes=frozenset({'GRAPH_ACCESS_TOKEN'}))))
        self.deny(self.check(scope=replace(self.scope,phone_number_id='BAD')))

if __name__=='__main__':
    unittest.main()
