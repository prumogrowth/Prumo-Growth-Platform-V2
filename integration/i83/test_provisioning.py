"""Real PG17 installer refusal and rollback; no credential values generated."""
import os
from pathlib import Path
import unittest
import psycopg
from integration.i83.catalog import snapshot
from scripts.test_s0_cfi01_auth_rest_local import local_env

class ProvisioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('PRUMO_I83_DISPOSABLE_TEST')!='YES':raise RuntimeError('I83 opt-in required')
        cls.db=local_env()['DB_URL'];cls.ddl=Path('supabase/tests/s1_i83_edge_credentials_local_only.sql').read_text()
    def setUp(self):
        with psycopg.connect(self.db) as c:self.before=snapshot(c)
    def tearDown(self):
        with psycopg.connect(self.db) as c:self.assertEqual(snapshot(c),self.before)
    def test_no_opt_in_no_partial_objects(self):
        with psycopg.connect(self.db,autocommit=True) as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(self.ddl)
            c.execute('rollback')
    def test_failure_after_all_patches_rolls_back_everything(self):
        with psycopg.connect(self.db,autocommit=True) as c:
            c.execute("set prumo.i83_disposable='YES'");c.execute("set prumo.i83_fail_before_commit='YES'")
            with self.assertRaises(psycopg.errors.CheckViolation):c.execute(self.ddl)
            c.execute('rollback')
    def test_unreviewed_signed_acl_refused(self):
        with psycopg.connect(self.db,autocommit=True) as c:
            c.execute('begin');c.execute('grant prumo_s0_g1_executor_local to postgres with inherit false,set true');c.execute('set local role prumo_s0_g1_executor_local')
            c.execute('grant execute on function prumo_private.s1_i79_admin_signed(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid,bigint,uuid,text) to authenticated');c.execute('reset role')
            c.execute("set local prumo.i83_disposable='YES'")
            with self.assertRaisesRegex(psycopg.errors.InsufficientPrivilege,'I83_SIGNED_ACL_DRIFT'):c.execute(self.ddl)
            c.execute('rollback')

if __name__=='__main__':unittest.main(verbosity=2)
