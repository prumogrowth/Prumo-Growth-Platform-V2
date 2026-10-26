#!/usr/bin/env python3
"""Inspect the final sealed PG17 state and exercise narrow lock privileges.

No real identities/keys. The old WITH CHECK true policy is reproduced only in
a rolled-back transaction to demonstrate the proven outbox DML permission.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

url = urlsplit(os.environ['PRUMO_TEST_DATABASE_URL'])
assert url.scheme == 'postgresql' and url.hostname == '127.0.0.1' and url.port == 5432
assert url.path == '/prumo_s0_test_ci' and url.username == 'postgres'
assert not url.query and not url.fragment
for name in ('PGHOSTADDR', 'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER',
             'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS'):
    assert not os.environ.get(name), name


def query(text, check=True):
    return subprocess.run(['psql', '-XqAt', '-v', 'ON_ERROR_STOP=1', '-v',
                           'VERBOSITY=verbose', os.environ['PRUMO_TEST_DATABASE_URL'],
                           '-c', text], capture_output=True, text=True, check=check)


def js(text):
    return json.loads(query(text).stdout)


roles = js("""select json_agg(row_to_json(r)) from (
 select rolname,rolcanlogin,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,
 rolreplication from pg_roles where rolname like 'prumo_s0_meta_%' order by rolname) r""")
assert roles and all(not any(v for k, v in role.items() if k not in ('rolname', 'rolcanlogin')) for role in roles)
# Original WA48+ tests explicitly enable a synthetic client LOGIN with a random
# local password. Owners stay NOLOGIN; cluster removal is the cleanup boundary.
assert all(role['rolcanlogin'] == (role['rolname'] == 'prumo_s0_meta_wa48_client_lab') for role in roles)
print('META-SEC-01 PASS: owners NOLOGIN; synthetic client LOGIN only; all roles restricted')
assert query("""select count(*) from pg_auth_members m join pg_roles r on r.oid=m.member
 where r.rolname='prumo_s0_meta_wa48_client_lab'""").stdout.strip() == '0'
print('META-SEC-02 PASS: client cannot assume an executor')
functions = js("""select json_agg(row_to_json(f)) from (
 select p.proname,r.rolname owner,p.prosecdef,p.proconfig,
 has_function_privilege('anon',p.oid,'execute') anon_exec,
 has_function_privilege('authenticated',p.oid,'execute') authenticated_exec,
 has_function_privilege('service_role',p.oid,'execute') service_exec,
 has_function_privilege('prumo_s0_meta_wa48_client_lab',p.oid,'execute') client_exec
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 join pg_roles r on r.oid=p.proowner where n.nspname='prumo_private'
 and (p.proname like 'meta_%fixture_s0' or p.proname like '%meta_status%fixture_s0')
 order by p.proname) f""")
assert functions and all(not f['anon_exec'] and not f['authenticated_exec'] and not f['service_exec'] for f in functions)
assert all(not f['prosecdef'] or f['proconfig'] == ['search_path=""'] for f in functions)
client_routes = [f['proname'] for f in functions if f['client_exec']]
assert client_routes == ['meta_wa55_single_entry_fixture_s0'], client_routes
entry = next(f for f in functions if f['proname'] == client_routes[0])
assert entry['owner'] == 'prumo_s0_meta_wa50_writer_lab'
print('META-SEC-03 PASS: single restricted entry; anon/authenticated/service_role denied')
tables = js("""select json_agg(row_to_json(t)) from (
 select c.relname,c.relowner::regrole::text owner,c.relrowsecurity,
 has_table_privilege('anon',c.oid,'select,insert,update,delete,truncate') anon_access,
 has_table_privilege('authenticated',c.oid,'select,insert,update,delete,truncate') authenticated_access,
 has_table_privilege('service_role',c.oid,'select,insert,update,delete,truncate') service_access,
 has_any_column_privilege('anon',c.oid,'select,insert,update') anon_column_access,
 has_any_column_privilege('authenticated',c.oid,'select,insert,update') authenticated_column_access,
 has_any_column_privilege('service_role',c.oid,'select,insert,update') service_column_access,
 has_table_privilege('prumo_s0_meta_wa48_client_lab',c.oid,'select,insert,update,delete,truncate') client_access,
 has_any_column_privilege('prumo_s0_meta_wa48_client_lab',c.oid,'select,insert,update') client_column_access
 from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='prumo_private' and c.relname like 'meta_%' and c.relkind='r'
 order by c.relname) t""")
assert tables and all(t['relrowsecurity'] and not any(v for k,v in t.items()
                        if k not in ('relname','owner','relrowsecurity')) for t in tables)
print('META-SEC-04 PASS: Meta tables RLS; no direct API/client access')

outbox = 'prumo_private.outbox_intencoes_s0'
guard = 'prumo_s0_meta_wa52_outbox_guard_lab'
# Reproduce original permission with a no-op UPDATE; no rows or policy persist.
result = query(f"""begin;
 alter policy wa52_guard_outbox_update on {outbox} with check(true);
 set local role {guard};
 with changed as (update {outbox} set id=id returning id) select count(*) from changed;
 rollback;""")
assert int(result.stdout.strip()) > 0
print('META-SEC-05 PASS: original WITH CHECK true admits outbox UPDATE(id); rolled back')
for number, role, table in [
    (6, guard, outbox),
    (7, 'prumo_s0_meta_wa50_binding_guard_lab', 'prumo_private.meta_vinculos_tentativa_fixture_s0'),
]:
    # FORCE the same update path even if it leaves the UUID unchanged.
    denied = query(f'begin; set local role {role}; update {table} set id=id; rollback;', check=False)
    assert denied.returncode and '42501' in denied.stderr, denied.stderr
    locked = query(f'begin; set local role {role}; select id from {table} limit 1 for share; rollback;')
    assert locked.stdout.strip(), role
    print(f'META-SEC-{number:02} PASS: UPDATE(id) denied; FOR SHARE still works')

evidence = {'roles': roles, 'functions': functions, 'tables': tables,
            'legacy_client_routes': client_routes, 'security_probes': '7/7'}
Path(sys.argv[1]).write_text(json.dumps(evidence, indent=2) + '\n')
