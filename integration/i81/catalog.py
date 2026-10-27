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
    result['memberships'] = rows('''select r.rolname as role,m.rolname as member,g.rolname as grantor,
        a.admin_option,a.inherit_option,a.set_option from pg_auth_members a
        join pg_roles r on r.oid=a.roleid join pg_roles m on m.oid=a.member join pg_roles g on g.oid=a.grantor
        where r.rolname=any(%s) or m.rolname=any(%s) order by r.rolname,m.rolname,g.rolname''', (list(ROLES),list(ROLES)))
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


def validate_final(before, after, final):
    """Probes may change synthetic data, never leave a privilege/catalog delta."""
    if after != final:raise AssertionError('I81: probe left catalog/ACL/ownership drift')
    for key in ('triggers','constraints'):
        if before[key] != after[key]:raise AssertionError('I81: original '+key+' changed')
    for key in ('effective_function_acl','effective_table_acl'):
        # Compare every pre-existing role/object result, including SQL logins,
        # service_role and existing HMAC/CFI executors. New owners are separate.
        retained = {json.dumps(row,sort_keys=True,default=str) for row in after[key]}
        owner_transfers=('prumo_private.s1_i79_admin_bridge(', 'prumo_private.s1_i80_bridge(', 'prumo_private.s1_i79_consistencia(')
        compared=[row for row in before[key] if not(key=='effective_function_acl' and row['rolname']=='postgres'
                    and row['function'].startswith(owner_transfers))]
        if not all(json.dumps(row,sort_keys=True,default=str) in retained for row in compared):
            raise AssertionError('I81: original effective consumer ACL changed: '+key)
    old_tables={row['relation']:row for row in before['tables']}
    for row in after['tables']:
        old=old_tables[row['relation']]
        if any(row[k]!=old[k] for k in ('owner','relkind','relrowsecurity','relforcerowsecurity')):
            raise AssertionError('I81: table ownership or RLS changed')
    patched_bodies={'prumo_private.s1_exigir_executor_interno_equipe()',
        'prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)',
        'prumo_private.s1_i80_snapshot(uuid,uuid)'}
    changed_owners={
        'prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)': 'prumo_s1_admin_domain_local',
        'prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid)': 'prumo_s1_admin_domain_local',
        'prumo_private.s1_i79_consistencia()': 'prumo_s1_professional_validator_local'}
    final_functions={row['signature']:row for row in final['functions']}
    for old in before['functions']:
        signature=old['signature'];new=final_functions[signature]
        if new['owner']!=changed_owners.get(signature,old['owner']):
            raise AssertionError('I81: unexpected function ownership change')
        if any(new[k]!=old[k] for k in ('prosecdef','proconfig')):
            raise AssertionError('I81: function security mode/config changed')
        if signature not in patched_bodies and new['body_sha256']!=old['body_sha256']:
            raise AssertionError('I81: unrelated function body changed')
    new_roles={'prumo_s1_admin_domain_local','prumo_s1_professional_validator_local'}
    if any(row['member'] in new_roles or (row['role'] in new_roles and not(
            row['member']=='postgres' and row['admin_option'] and not row['inherit_option'] and not row['set_option']))
           for row in final['memberships']):
        raise AssertionError('I81: temporary membership survived')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('before','after','final'))
    args=parser.parse_args()
    if os.environ.get('PRUMO_I81_DISPOSABLE_TEST')!='YES':raise RuntimeError('I81 opt-in required')
    with psycopg.connect(local_env()['DB_URL']) as connection: result=snapshot(connection)
    output=Path(os.environ.get('RUNNER_TEMP','/tmp'))/('prumo_i81_catalog_'+args.phase+'.json')
    output.write_text(json.dumps(result,indent=2,default=str)+'\n')
    print('I81-CATALOG',args.phase,'functions',len(result['functions']),'triggers',len(result['triggers']),'roles',len(result['roles']),flush=True)
    if args.phase=='final':
        before=json.loads(output.with_name('prumo_i81_catalog_before.json').read_text())
        after=json.loads(output.with_name('prumo_i81_catalog_after.json').read_text())
        # JSON round-trip normalizes psycopg tuple/array representations.
        validate_final(before,after,json.loads(output.read_text()))
        print('I81-CATALOG-ACCEPTANCE: consumer ACLs, all original triggers/constraints/RLS and post-probe catalog preserved',flush=True)
