"""Add only I80 to the already-certified disposable I79 stack."""
import os
from pathlib import Path
import psycopg
from scripts.test_s0_cfi01_auth_rest_local import local_env

if os.environ.get('PRUMO_I80_DISPOSABLE_TEST')!='YES':raise RuntimeError('I80 opt-in required')
with psycopg.connect(local_env()['DB_URL'],autocommit=True) as c:
    c.execute("set prumo.i80_disposable='YES'")
    c.execute(Path('supabase/tests/s1_i80_regularizacao_local_only.sql').read_text())
print('I80 installed only in loopback disposable PG17 after I79',flush=True)
