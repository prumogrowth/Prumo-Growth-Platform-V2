"""Physical PG17 candidate tests. Only run on a disposable dedicated Docker VM.

Set M09_PINNED_SOURCE to the exact checkout of S0 Meta Ingress
01ffdb093013664b73b18d23f92aac2202578210. The runner must confirm SHA.
"""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from dataclasses import replace

from .pg17_binding import Pg17BindingReader
from .port import HostScope, M2MPrincipal, FLAGS

try:
    import psycopg
except ImportError:
    psycopg = None


@unittest.skipUnless(os.environ.get('M09_PG17_DISPOSABLE') == 'YES' and psycopg,
                     'requires disposable pinned PostgreSQL 17 laboratory')
class PhysicalM09(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = Path(os.environ['M09_PINNED_SOURCE']).resolve()
        if not (pinned / 'integration/s0_meta_ingress/schema.sql').is_file():
            raise RuntimeError('missing pinned S0 source')
        spec = importlib.util.spec_from_file_location(
            'pinned_m09_pg_lab', pinned / 'integration/s0_meta_ingress/lab.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.old_dir = Path.cwd()
        cls.lab = module.Laboratory()
        os.chdir(pinned)
        try:
            cls.lab.start()
        except BaseException:
            cls.lab.cleanup()
            os.chdir(cls.old_dir)
            raise

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'lab'):
            cleanup = cls.lab.cleanup()
            os.chdir(cls.old_dir)
            for resource in ['container_absent','volume_absent','custody_absent','inherited_catalog_equal']:
                if not cleanup.get(resource):
                    raise AssertionError('PG17 disposal/inherited catalog failed: ' + resource)

    def setUp(self):
        self.p = M2MPrincipal('M09_KEY_A', 'M09_LAB_ISSUER', 'LAB_S0_M09', 1,
                  frozenset({'store-A'}), frozenset({'REGISTRY_READ'}), False)
        self.routes = {'valid': HostScope('route_A','store-A','APP_A',
                                  'channel_A','100001','200001'),
                       'other': HostScope('route_B','store-B','APP_B',
                                  'channel_B','100002','200002')}
        self.mapping = {'tenant_A':'store-A','tenant_B':'store-B'}
        self._seed()
        self.reader = Pg17BindingReader(
            self.lab.runtime_dsn, lambda proof: self.p if proof == 'VALID_FIXTURE' else None,
            lambda ref: self.routes.get(ref),self.mapping)

    def _seed(self):
        with self.lab.admin() as c:
            c.execute('TRUNCATE s0_meta_lab.audit, s0_meta_lab.nonces, '
                      's0_meta_lab.aliases,s0_meta_lab.occurrences,s0_meta_lab.batches,'
                      's0_meta_lab.bindings,s0_meta_lab.principals,s0_meta_lab.routes CASCADE')
            for route, app in [('route_A','APP_A'),('route_B','APP_B')]:
                c.execute('INSERT INTO s0_meta_lab.routes VALUES(%s,%s,1,true)',
                          (route,app))
            c.execute("""INSERT INTO s0_meta_lab.principals
                (key_id,issuer,revision,public_key,route,app,tenant,scopes,channels,
                active,not_before,not_after)
                VALUES(%s,%s,1,%s,'route_A','APP_A','tenant_A',
                ARRAY['REGISTRY_READ'],ARRAY['channel_A'],true,
                clock_timestamp()-interval '1 hour',
                clock_timestamp()+interval '1 hour')""",
                ('M09_KEY_A','M09_LAB_ISSUER',bytes(32)))
            for route, waba, phone, app, tenant, channel in [
                ('route_A','100001','200001','APP_A','tenant_A','channel_A'),
                ('route_B','100002','200002','APP_B','tenant_B','channel_B')]:
                c.execute('INSERT INTO s0_meta_lab.bindings VALUES(%s,%s,%s,%s,%s,%s,1,true)',
                          (route,waba,phone,app,tenant,channel))

    def read(self, **kw):
        return self.reader.read('VALID_FIXTURE','valid',**kw)

    def deny(self, x):
        self.assertNotEqual(x['decision'],'PG17_BINDING_VERIFIED_LAB_ONLY')
        self.assertIsNone(x['physical'])
        self.assertTrue(all(x[f] is False for f in FLAGS))

    def test_physical_positive_with_partial_revisions_only(self):
        x = self.read()
        self.assertEqual(x['decision'],'PG17_BINDING_VERIFIED_LAB_ONLY')
        self.assertEqual(x['physical']['versions'],{'route':1,'binding':1,'principal':1})
        self.assertEqual(x['physical']['unproven_revisions'], ['app','grant'])
        self.assertNotIn('slot_ref',str(x))
        self.assertTrue(all(x[f] is False for f in FLAGS))

    def test_physical_readback_and_stale_versions(self):
        x = self.read()['physical']
        y = self.read(expected_versions=x['versions'],
                      expected_snapshot_ref=x['snapshot_ref'])
        self.assertEqual(y['decision'],'PG17_BINDING_VERIFIED_LAB_ONLY')
        self.deny(self.read(expected_versions={'route':2,'binding':1,'principal':1}))
        self.deny(self.read(expected_snapshot_ref='a'*64))

    def test_control_revocation_invalidates_old_snapshot(self):
        original=self.read()['physical']
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.bindings SET active=false,revision=revision+1 "
                      "WHERE route='route_A' AND channel='channel_A'")
            c.execute("UPDATE s0_meta_lab.routes SET revision=revision+1 "
                      "WHERE id='route_A'")
        self.deny(self.read(expected_snapshot_ref=original['snapshot_ref']))

    def test_m2m_identity_scope_rejected(self):
        self.deny(self.reader.read('FAKE','valid'))
        self.p=replace(self.p,key_revision=2)
        self.deny(self.read())
        self.p=replace(self.p,key_revision=1,issuer_ref='UNKNOWN')
        self.deny(self.read())

    def test_cross_store_not_authorized(self):
        self.deny(self.reader.read('VALID_FIXTURE','other'))
        self.routes['valid']=replace(self.routes['valid'],concessionaria_id='store-B')
        self.deny(self.read())

    def test_tenant_mapping_mismatch_denied(self):
        self.reader._tenant_to_store={'tenant_A':'store-B','tenant_B':'store-B'}
        self.deny(self.read())

    def test_duplicate_phone_across_routes_denied(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.bindings SET phone='200001' WHERE route='route_B'")
        self.assertEqual(self.read()['reason'],'AMBIGUOUS_BINDING')

    def test_duplicate_waba_across_routes_denied(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.bindings SET waba='100001' WHERE route='route_B'")
        self.assertEqual(self.read()['reason'],'AMBIGUOUS_BINDING')

    def test_db_role_scope_no_mutation_privilege(self):
        with psycopg.connect(self.lab.runtime_dsn) as c:
            with self.assertRaises(psycopg.Error):
                c.execute("UPDATE s0_meta_lab.bindings SET active=false WHERE route='route_A'")
        self.assertEqual(self.read()['decision'],'PG17_BINDING_VERIFIED_LAB_ONLY')

    def test_inactive_expired_channel_and_principal(self):
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.principals SET not_after=clock_timestamp()-interval '1 second'")
        self.deny(self.read())
        with self.lab.admin() as c:
            c.execute("UPDATE s0_meta_lab.principals SET not_after=clock_timestamp()+interval '1 hour'")
            c.execute("UPDATE s0_meta_lab.bindings SET active=false WHERE route='route_A'")
        self.deny(self.read())

    def test_no_implicit_graph_or_http_permission(self):
        self.deny(self.read(purpose='GRAPH_ACCESS_TOKEN'))
        self.deny(self.read(purpose='POST_APP_SECRET'))
        self.deny(self.read(purpose='GET_VERIFY_TOKEN'))


if __name__ == '__main__':
    unittest.main()
