"""A real I80 preview created BEFORE ownership cutover remains usable AFTER."""
import unittest

import psycopg

from backend import s1_legacy_regularization_local as regularization
from integration.i80.test_regularization import I80Tests
from integration.i81.install_local import install


class CutoverTests(I80Tests):
    def test_i81_existing_preview_survives_atomic_ownership_cutover(self):
        actor,_,_=self.legacy(pending=True)
        preview,_=self.preview(actor)
        before=self.preserved(actor)
        with psycopg.connect(self.db,autocommit=True) as connection:install(connection)
        result=self.apply(preview)
        if result.state!='APPLIED':
            principal=self.gateway._identity.verify('Bearer '+self.director_token)
            proof=self.regularizer.proof(principal,regularization.command(self.apply_wire(preview)))
            try:
                with psycopg.connect(self.dsn) as c:
                    c.execute(regularization.SQL,proof)
                    c.execute('set constraints all immediate')
                    c.rollback()
            except psycopg.Error as error:
                raise RuntimeError('I81 cutover SQL '+str(error.sqlstate)+' '+str(error.diag.message_primary)) from None
        self.assertEqual(result.state,'APPLIED')
        self.assertEqual(self.cargo(actor),'consultor')
        self.assertEqual(self.preserved(actor),before)
        self.assertEqual(self.apply(preview,key='i81-cutover-different-key').state,'CONFLICT')


if __name__=='__main__':
    suite=unittest.TestSuite([CutoverTests('test_i81_existing_preview_survives_atomic_ownership_cutover')])
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
