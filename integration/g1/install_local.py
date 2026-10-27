"""Install G1 delta before original S1 SQL tests populate their rollback fixture.

Uses the same local CLI boundary as all S0 integration suites. Never hosted.
"""
import os
from pathlib import Path
import psycopg
from scripts.test_s0_cfi01_auth_rest_local import local_env


def main():
    if os.environ.get('PRUMO_G1_DISPOSABLE_TEST')!='YES':
        raise RuntimeError('G1 opt-in required')
    with psycopg.connect(local_env()['DB_URL'],autocommit=True) as connection:
        connection.execute("set prumo.g1_disposable='YES'")
        connection.execute(Path('supabase/tests/s0_g1_manual_queue_local_only.sql').read_text())
    print('G1 delta installed in disposable loopback PG17, before legacy SQL fixture data',flush=True)


if __name__=='__main__':main()
