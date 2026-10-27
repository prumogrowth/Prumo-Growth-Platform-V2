"""Real transactional DDL refusal/rollback before installing the I81 delta."""
import os
from pathlib import Path
import unittest

import psycopg

from integration.i81.catalog import snapshot
from scripts.test_s0_cfi01_auth_rest_local import local_env


class ProvisioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('PRUMO_I81_DISPOSABLE_TEST')!='YES':raise RuntimeError('I81 opt-in required')
        cls.db=local_env()['DB_URL']
        cls.ddl=Path('supabase/tests/s1_i81_admin_ownership_local_only.sql').read_text()
    def setUp(self):
        with psycopg.connect(self.db) as c:self.before=snapshot(c)
    def tearDown(self):
        with psycopg.connect(self.db) as c:self.assertEqual(snapshot(c),self.before)
    def test_01_no_sql_opt_in_no_mutation(self):
        with psycopg.connect(self.db,autocommit=True) as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(self.ddl)
            c.execute('rollback')
    def test_02_unknown_guard_fails_closed_no_partial_role_or_policy(self):
        with psycopg.connect(self.db,autocommit=True) as c:
            c.execute('begin')
            definition=c.execute("select pg_get_functiondef('prumo_private.s1_exigir_executor_interno_equipe()'::regprocedure)").fetchone()[0]
            c.execute(definition.replace('begin','begin\n -- unexpected drift',1))
            c.execute("set local prumo.i81_disposable='YES'")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(self.ddl)
            c.execute('rollback')
    def test_03_failure_after_all_owner_transfers_rolls_back_entire_catalog(self):
        with psycopg.connect(self.db,autocommit=True) as c:
            c.execute("set prumo.i81_disposable='YES'")
            c.execute("set prumo.i81_fail_before_commit='YES'")
            with self.assertRaises(psycopg.errors.CheckViolation):c.execute(self.ddl)
            c.execute('rollback')


if __name__=='__main__':unittest.main(verbosity=2)
