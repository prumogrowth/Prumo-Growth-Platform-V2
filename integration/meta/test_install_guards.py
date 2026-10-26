#!/usr/bin/env python3
"""Real PG17 negatives: no persistent catalog effects on a wrong local DB.

Uses the disposable cluster's existing `postgres` maintenance database, without
bootstrap dependencies: a correct guard must reject before touching any object.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit

url = urlsplit(os.environ['PRUMO_TEST_DATABASE_URL'])
assert url.scheme == 'postgresql' and url.hostname == '127.0.0.1'
assert url.port == 5432 and url.path == '/prumo_s0_test_ci'
assert url.username == 'postgres' and not url.query and not url.fragment
for name in ('PGHOSTADDR', 'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER',
             'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS'):
    assert not os.environ.get(name), name
maintenance = urlunsplit(url._replace(path='/postgres'))


def sql(query):
    result = subprocess.run(['psql', '-XqAt', '-v', 'ON_ERROR_STOP=1', maintenance,
                             '-c', query], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def snapshot():
    # Includes objects, role flags/memberships and default ACLs, never passwords.
    queries = [
        "select row(oid,nspname,nspowner,nspacl)::text from pg_namespace order by oid",
        "select row(oid,relname,relnamespace,relowner,relacl,relrowsecurity)::text from pg_class order by oid",
        "select row(oid,proname,pronamespace,proowner,proacl,prosrc,proconfig)::text from pg_proc order by oid",
        "select row(oid,rolname,rolcanlogin,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolinherit,rolreplication)::text from pg_roles order by oid",
        "select row(roleid,member,grantor,admin_option,inherit_option,set_option)::text from pg_auth_members order by roleid,member,grantor",
        "select row(oid,defaclrole,defaclnamespace,defaclobjtype,defaclacl)::text from pg_default_acl order by oid",
        "select row(oid,polname,polrelid,polroles,polqual,polwithcheck)::text from pg_policy order by oid",
    ]
    return hashlib.sha256('\n'.join(sql(q) for q in queries).encode()).hexdigest()


before = snapshot()
files = sorted(Path(sys.argv[1]).glob('supabase/migrations/2026102300*.sql'))
assert len(files) == 12
for file in files:
    result = subprocess.run(['psql', '-Xq', '-v', 'ON_ERROR_STOP=1', maintenance,
                             '-f', str(file)], capture_output=True, text=True)
    assert result.returncode != 0 and 'S0_META_DISPOSABLE_INSTALL_ONLY' in result.stderr, file.name
    assert snapshot() == before, file.name
    print('META-GUARD-' + file.name[10:12] + ' PASS', flush=True)
print('META-GUARDS: 12/12 standalone refusals; catalog/roles/ACL unchanged')
