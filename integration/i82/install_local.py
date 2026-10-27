"""Install only the metadata fence after the unchanged I81 certification suite."""
import os
from pathlib import Path
import psycopg
from scripts.test_s0_cfi01_auth_rest_local import local_env

if __name__=='__main__':
    if os.environ.get('PRUMO_I82_DISPOSABLE_TEST')!='YES':raise RuntimeError('I82 opt-in required')
    with psycopg.connect(local_env()['DB_URL'],autocommit=True) as c:
        c.execute("set prumo.i82_disposable='YES'")
        c.execute(Path('supabase/tests/s1_i82_metadata_fence_local_only.sql').read_text())
    print('I82 metadata fence installed without changing I81 owners/table grants',flush=True)
