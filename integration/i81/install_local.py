"""Atomic ownership experiment, only on the certified loopback I80 stack.

No runtime authentication change, role-password handling or hosted migration.
The SQL verifies exact prerequisite bodies before changing owners/ACL/guards.
"""
import os
from pathlib import Path

import psycopg

from scripts.test_s0_cfi01_auth_rest_local import local_env


def install(connection):
    if os.environ.get('PRUMO_I81_DISPOSABLE_TEST') != 'YES':
        raise RuntimeError('I81 disposable opt-in required')
    connection.execute("set prumo.i81_disposable='YES'")
    connection.execute(Path('supabase/tests/s1_i81_admin_ownership_local_only.sql').read_text())


if __name__ == '__main__':
    with psycopg.connect(local_env()['DB_URL'], autocommit=True) as connection:
        install(connection)
    print('I81: atomic administrative ownership installed in disposable PG17', flush=True)
