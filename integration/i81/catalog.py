"""Metadata-only effective ownership/ACL evidence; never application/Auth rows."""
import argparse
import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from scripts.test_s0_cfi01_auth_rest_local import local_env

ROLES = ('postgres', 'anon', 'authenticated', 'service_role',
         'prumo_cfi01_pgtest_login', 'prumo_s1_signed_login_ci',
         'prumo_s0_g1_executor_local', 'prumo_cfi01_atomic_owner_local',
         'prumo_s1_admin_domain_local', 'prumo_s1_professional_validator_local')


def snapshot(connection):
    def rows(query, params=()):
        with connection.cursor(row_factory=dict_row) as cursor:
            return cursor.execute(query, params).fetchall()
    scopes = "n.nspname in('public','prumo_private')"
    result = {'roles': rows('''select rolname,rolcanlogin,rolinherit,rolsuper,rolcreatedb,
        rolcreaterole,rolreplication,rolbypassrls from pg_roles
        where rolname=any(%s) order by rolname''', (list(ROLES),))}
    result['memberships'] = rows('''select r.rolname as role,m.rolname as member,
        a.admin_option,a.inherit_option,a.set_option from pg_auth_members a
        join pg_roles r on r.oid=a.roleid join pg_roles m on m.oid=a.member
        where r.rolname=any(%s) or m.rolname=any(%s) order by r.rolname,m.rolname''', (list(ROLES),list(ROLES)))
    result['functions'] = rows(f'''select p.oid::regprocedure::text as signature,
        pg_get_userbyid(p.proowner) as owner,p.prosecdef,p.proconfig,p.proacl::text as acl,
        encode(sha256(convert_to(p.prosrc,'UTF8')),'hex') as body_sha256
        from pg_proc p join pg_namespace n on n.oid=p.pronamespace
        where {scopes} order by signature''')
    result['tables'] = rows(f'''select c.oid::regclass::text as relation,
        pg_get_userbyid(c.relowner) as owner,c.relkind,c.relrowsecurity,c.relforcerowsecurity,c.relacl::text as acl
        from pg_class c join pg_namespace n on n.oid=c.relnamespace
        where {scopes} and c.relkind in('r','p','S','v') order by relation''')
    result['column_acl'] = rows(f'''select c.oid::regclass::text as relation,a.attname,a.attacl::text as acl
        from pg_attribute a join pg_class c on c.oid=a.attrelid join pg_namespace n on n.oid=c.relnamespace
        where {scopes} and a.attacl is not null order by relation,a.attnum''')
    result['policies'] = rows('''select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check
        from pg_policies where schemaname in('public','prumo_private')
        order by schemaname,tablename,policyname''')
    result['triggers'] = rows(f'''select t.tgrelid::regclass::text as relation,t.tgname,t.tgenabled,
        t.tgfoid::regprocedure::text as function,t.tgdeferrable,t.tginitdeferred,
        pg_get_triggerdef(t.oid) as definition from pg_trigger t
        join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace
        where {scopes} and not t.tgisinternal order by relation,t.tgname''')
    result['constraints'] = rows(f'''select c.oid::regclass::text as relation,x.conname,
        x.condeferrable,x.condeferred,pg_get_constraintdef(x.oid) as definition
        from pg_constraint x join pg_class c on c.oid=x.conrelid join pg_namespace n on n.oid=c.relnamespace
        where {scopes} order by relation,x.conname''')
    # PL/pgSQL textual dependencies are NOT exhaustively recorded in pg_depend.
    # Keep actual catalog dependencies and explain the runtime tests separately.
    result['catalog_dependencies'] = rows('''select p.oid::regprocedure::text as function,
        d.refclassid::regclass::text as referenced_catalog,d.refobjid,d.deptype
        from pg_depend d join pg_proc p on d.classid='pg_proc'::regclass and d.objid=p.oid
        join pg_namespace n on n.oid=p.pronamespace where n.nspname='prumo_private'
        order by function,referenced_catalog,d.refobjid,d.deptype''')
    result['effective_function_acl'] = rows(f'''select r.rolname,p.oid::regprocedure::text as function,
        has_function_privilege(r.oid,p.oid,'EXECUTE') as execute
        from pg_roles r cross join pg_proc p join pg_namespace n on n.oid=p.pronamespace
        where r.rolname=any(%s) and {scopes} and p.prosecdef order by r.rolname,function''', (list(ROLES),))
    result['effective_table_acl'] = rows(f'''select r.rolname,c.oid::regclass::text as relation,
        has_table_privilege(r.oid,c.oid,'SELECT') as select_all,
        has_any_column_privilege(r.oid,c.oid,'SELECT') as select_any,
        has_any_column_privilege(r.oid,c.oid,'INSERT') as insert_any,
        has_any_column_privilege(r.oid,c.oid,'UPDATE') as update_any,
        has_table_privilege(r.oid,c.oid,'DELETE') as delete,
        has_table_privilege(r.oid,c.oid,'TRUNCATE') as truncate
        from pg_roles r cross join pg_class c join pg_namespace n on n.oid=c.relnamespace
        where r.rolname=any(%s) and {scopes} and c.relkind in('r','p') order by r.rolname,relation''', (list(ROLES),))
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('before','after','final'))
    args=parser.parse_args()
    if os.environ.get('PRUMO_I81_DISPOSABLE_TEST')!='YES':raise RuntimeError('I81 opt-in required')
    with psycopg.connect(local_env()['DB_URL']) as connection: result=snapshot(connection)
    output=Path(os.environ.get('RUNNER_TEMP','/tmp'))/('prumo_i81_catalog_'+args.phase+'.json')
    output.write_text(json.dumps(result,indent=2,default=str)+'\n')
    print('I81-CATALOG',args.phase,'functions',len(result['functions']),'triggers',len(result['triggers']),'roles',len(result['roles']),flush=True)
