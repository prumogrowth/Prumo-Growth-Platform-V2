"""M09-03 disposable PostgreSQL 17 physical tests. No hosted access."""
import importlib.util
import os
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from dataclasses import replace

from .pg17_registry import RegistryPhysical, revoke_channel_in_admin_transaction
from .port import HostScope, M2MPrincipal, FLAGS

try:
    import psycopg
except ImportError:
    psycopg=None


@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE')=='YES' and psycopg,
                     'PG17 isolated Docker fixture required')
class PhysicalRegistryM09(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned=Path(os.environ['M09_PINNED_SOURCE']).resolve()
        cls.origin=Path.cwd()
        cls.extension=(cls.origin/'integration/s0s1_m09_registry/pg17_registry_candidate.sql').read_text()
        spec=importlib.util.spec_from_file_location('pinned_m09_lab_03',
                pinned/'integration/s0_meta_ingress/lab.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.lab=module.Laboratory()
        os.chdir(pinned)
        try:
            cls.lab.start()
            with cls.lab.admin() as c:
                c.execute("SET s0_meta.disposable='YES'")
                c.execute("SET s0_m09.install='CANDIDATE_ONLY'")
                c.execute(cls.extension)
        except BaseException:
            cls.lab.cleanup()
            os.chdir(cls.origin)
            raise

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,'lab'):
            result=cls.lab.cleanup()
            os.chdir(cls.origin)
            for key in ('container_absent','volume_absent','custody_absent',
                        'inherited_catalog_equal'):
                if result.get(key) is not True:
                    raise AssertionError('PG17 cleanup failed: '+key)

    def setUp(self):
        self.p=M2MPrincipal('M09_KEY_A','M09_ISSUER','LAB_S0_M09',1,
                    frozenset({'store-A'}),frozenset({'REGISTRY_READ'}),False)
        self.host={'valid':HostScope('route_A','store-A','APP_A',
                                    'channel_A','100001','200001'),
                   'other':HostScope('route_B','store-B','APP_B',
                                    'channel_B','100002','200002')}
        with self.lab.admin() as c:
            c.execute('TRUNCATE s0_m09_lab.slots, s0_m09_lab.grants, '
                      's0_m09_lab.wabas, s0_m09_lab.apps, '
                      's0_meta_lab.audit,s0_meta_lab.nonces,s0_meta_lab.aliases,'
                      's0_meta_lab.occurrences,s0_meta_lab.batches,'
                      's0_meta_lab.bindings,s0_meta_lab.principals,'
                      's0_meta_lab.routes CASCADE')
            for route,app in [('route_A','APP_A'),('route_B','APP_B')]:
                c.execute('INSERT INTO s0_meta_lab.routes VALUES(%s,%s,1,true)',
                          (route,app))
            c.execute("""INSERT INTO s0_meta_lab.principals
              (key_id,issuer,revision,public_key,route,app,tenant,scopes,
               channels,active,not_before,not_after)
              VALUES ('M09_KEY_A','M09_ISSUER',1,%s,'route_A','APP_A',
              'tenant_A',ARRAY['REGISTRY_READ'],ARRAY['channel_A'],true,
              clock_timestamp()-interval '1 hour',
              clock_timestamp()+interval '1 hour')""",(bytes(32),))
            for route,waba,phone,app,tenant,channel in [
              ('route_A','100001','200001','APP_A','tenant_A','channel_A'),
              ('route_B','100002','200002','APP_B','tenant_B','channel_B')]:
                c.execute('INSERT INTO s0_meta_lab.bindings VALUES(%s,%s,%s,%s,%s,%s,1,true)',
                          (route,waba,phone,app,tenant,channel))
            for app,route,store,tenant in [
              ('APP_A','route_A','store-A','tenant_A'),
              ('APP_B','route_B','store-B','tenant_B')]:
                c.execute("""INSERT INTO s0_m09_lab.apps
                  (app_ref,route_ref,concessionaria_id,tenant,revision,active,
                   valid_from,valid_until)
                  VALUES (%s,%s,%s,%s,1,true,
                    clock_timestamp()-interval '1 hour',
                    clock_timestamp()+interval '1 hour')""",(app,route,store,tenant))
            for waba,app in [('100001','APP_A'),('100002','APP_B')]:
                c.execute('INSERT INTO s0_m09_lab.wabas VALUES(%s,%s)',(waba,app))
            for channel,app,route,waba,phone in [
              ('channel_A','APP_A','route_A','100001','200001'),
              ('channel_B','APP_B','route_B','100002','200002')]:
                c.execute('INSERT INTO s0_m09_lab.grants VALUES(%s,%s,%s,%s,%s,1,true)',
                          (channel,app,route,waba,phone))
            for slot,app,purpose in [
              ('GET_SLOT_A','APP_A','GET_VERIFY_TOKEN'),
              ('POST_SLOT_A','APP_A','POST_APP_SECRET'),
              ('GRAPH_SLOT_A','APP_A','GRAPH_ACCESS_TOKEN'),
              ('GET_SLOT_B','APP_B','GET_VERIFY_TOKEN'),
              ('POST_SLOT_B','APP_B','POST_APP_SECRET'),
              ('GRAPH_SLOT_B','APP_B','GRAPH_ACCESS_TOKEN')]:
                c.execute('INSERT INTO s0_m09_lab.slots VALUES(%s,%s,%s)',
                          (slot,app,purpose))
        self.reader=RegistryPhysical(self.lab.runtime_dsn,
            lambda proof: self.p if proof=='SYNTHETIC_PROOF' else None,
            lambda ref: self.host.get(ref))

    def read(self,**kw):
        return self.reader.read('SYNTHETIC_PROOF','valid',**kw)

    def assert_denied(self,x):
        self.assertNotEqual(x['decision'],'PHYSICAL_REGISTRY_LAB_ONLY')
        self.assertIsNone(x['snapshot'])
        self.assertTrue(all(x[k] is False for k in FLAGS))

    def test_positive_proves_separate_versions_in_pg17(self):
        x=self.read()
        self.assertEqual(x['decision'],'PHYSICAL_REGISTRY_LAB_ONLY')
        self.assertEqual(x['snapshot']['revisions'],
                         {'route':1,'app':1,'binding':1,'grant':1,'principal':1})
        self.assertEqual(x['snapshot']['ownership_evidence_state'],'UNVERIFIED')
        self.assertNotIn('slot_ref',x['snapshot'])
        self.assertTrue(all(x[k] is False for k in FLAGS))

    def test_stable_snapshot_then_stale(self):
        x=self.read()['snapshot']
        self.assertEqual(self.read(expected=x['revisions'],
                 previous_snapshot_ref=x['snapshot_ref'])['decision'],
                 'PHYSICAL_REGISTRY_LAB_ONLY')
        self.assertEqual(self.read(expected=dict(x['revisions'], grant=2))['decision'],
                         'STALE_OR_REVOKED')

    def test_atomic_revoke_original_and_candidate(self):
        x=self.read()['snapshot']
        with self.lab.admin() as c:
            a=revoke_channel_in_admin_transaction(c,'route_A','channel_A',1,1,1,1)
        self.assertEqual(a,'REVOKED_IN_DISPOSABLE_TRANSACTION')
        self.assert_denied(self.read(expected=x['revisions']))
        with self.lab.admin() as c:
            rows=c.execute("""SELECT
              (SELECT active FROM s0_meta_lab.bindings WHERE channel='channel_A') AS source_active,
              (SELECT active FROM s0_m09_lab.grants WHERE canal_id='channel_A') AS grant_active,
              (SELECT revision FROM s0_m09_lab.apps WHERE app_ref='APP_A') AS app_revision,
              (SELECT revision FROM s0_meta_lab.routes WHERE id='route_A') AS route_revision""").fetchone()
        self.assertFalse(rows['source_active'])
        self.assertFalse(rows['grant_active'])
        self.assertEqual(rows['app_revision'],2)
        self.assertEqual(rows['route_revision'],2)

    def test_revoke_wrong_cas_rolls_back_everything(self):
        with self.lab.admin() as c:
            a=revoke_channel_in_admin_transaction(c,'route_A','channel_A',1,5,1,1)
        self.assertEqual(a,'CONFLICT')
        self.assertEqual(self.read()['decision'],'PHYSICAL_REGISTRY_LAB_ONLY')

    def test_second_revoke_conflicts(self):
        with self.lab.admin() as c:
            self.assertEqual(revoke_channel_in_admin_transaction(
                c,'route_A','channel_A',1,1,1,1),'REVOKED_IN_DISPOSABLE_TRANSACTION')
        with self.lab.admin() as c:
            self.assertEqual(revoke_channel_in_admin_transaction(
                c,'route_A','channel_A',1,1,1,1),'CONFLICT')

    def test_runtime_denied_write_and_slot_read(self):
        with psycopg.connect(self.lab.runtime_dsn) as c:
            with self.assertRaises(psycopg.Error):
                c.execute('SELECT * FROM s0_m09_lab.slots')
            c.rollback()
            try:
                c.execute("UPDATE s0_m09_lab.grants SET active=false WHERE canal_id='channel_A'")
            except psycopg.Error:
                c.rollback()
        self.assertEqual(self.read()['decision'],'PHYSICAL_REGISTRY_LAB_ONLY')

    def test_duplicate_phone_is_constraint_not_query(self):
        with self.lab.admin() as c:
            c.execute("INSERT INTO s0_m09_lab.wabas VALUES('100003','APP_A')")
            with self.assertRaises(psycopg.errors.UniqueViolation):
                c.execute("""INSERT INTO s0_m09_lab.grants
                  VALUES('channel_C','APP_A','route_A','100003','200001',1,true)""")

    def test_waba_cannot_belong_two_apps(self):
        with self.lab.admin() as c:
            with self.assertRaises(psycopg.errors.UniqueViolation):
                c.execute("INSERT INTO s0_m09_lab.wabas VALUES('100001','APP_B')")

    def test_slots_cannot_alias_within_or_cross_app(self):
        with self.lab.admin() as c:
            with self.assertRaises(psycopg.errors.UniqueViolation):
                c.execute("INSERT INTO s0_m09_lab.slots VALUES('GET_SLOT_A','APP_B','EXTRA')")
        # Purpose existing in same App cannot get a second alias.
        with self.lab.admin() as c:
            with self.assertRaises(psycopg.errors.UniqueViolation):
                c.execute("INSERT INTO s0_m09_lab.slots VALUES('DUP_SLOT_A','APP_A','GET_VERIFY_TOKEN')")

    def test_cross_store_and_fake_principal(self):
        self.assert_denied(self.reader.read('SYNTHETIC_PROOF','other'))
        self.assert_denied(self.reader.read('BAD_PROOF','valid'))
        self.p=replace(self.p,issuer_ref='different')
        self.assert_denied(self.read())

    def test_orig_source_mismatch_denied(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.bindings SET tenant='FORGED' WHERE channel='channel_A'")
        self.assert_denied(self.read())

    def test_concurrent_revoke_only_one_wins(self):
        fence=threading.Barrier(2)
        def job():
            with self.lab.admin() as c:
                fence.wait()
                return revoke_channel_in_admin_transaction(
                    c,'route_A','channel_A',1,1,1,1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(job) for _ in range(2)]
            outcomes=[f.result(timeout=10) for f in futures]
        self.assertCountEqual(outcomes,['REVOKED_IN_DISPOSABLE_TRANSACTION','CONFLICT'])

    def test_concurrent_duplicate_phone_constraint(self):
        with self.lab.admin() as c:
            c.execute("INSERT INTO s0_m09_lab.wabas VALUES('100003','APP_A')")
            c.execute("INSERT INTO s0_m09_lab.wabas VALUES('100004','APP_A')")
        fence=threading.Barrier(2)
        def job(ch,waba):
            try:
                with self.lab.admin() as c:
                    fence.wait()
                    c.execute('INSERT INTO s0_m09_lab.grants VALUES(%s,%s,%s,%s,%s,1,true)',
                              (ch,'APP_A','route_A',waba,'200010'))
                return 'COMMITTED'
            except psycopg.errors.UniqueViolation:
                return 'UNIQUE_DENIED'
        with ThreadPoolExecutor(max_workers=2) as pool:
            f=[pool.submit(job,'channel_C','100003'),pool.submit(job,'channel_D','100004')]
            got=[z.result(timeout=10) for z in f]
        self.assertCountEqual(got,['COMMITTED','UNIQUE_DENIED'])

if __name__=='__main__':
    unittest.main()
