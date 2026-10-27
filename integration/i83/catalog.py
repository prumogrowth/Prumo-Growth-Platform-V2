"""Metadata only: no credential rows, SQL passwords or authentication data."""
import argparse
import json
import hashlib
import os
from pathlib import Path
from unittest.mock import patch
import psycopg
from psycopg.rows import dict_row
from integration.i81 import catalog as baseline
from integration.i83.provision_local import LOGIN,CUSTODIAN,TABLE
from scripts.test_s0_cfi01_auth_rest_local import local_env


def snapshot(c):
    with patch.object(baseline,'ROLES',baseline.ROLES+(LOGIN,CUSTODIAN)):
        value=baseline.snapshot(c)
    with c.cursor(row_factory=dict_row) as cur:
        value['edge_function_acl']=cur.execute("""select p.oid::regprocedure::text as signature,
          has_function_privilege(%s,p.oid,'EXECUTE') as execute
          from pg_proc p join pg_namespace n on n.oid=p.pronamespace
          where n.nspname in('public','prumo_private') order by signature""",(LOGIN,)).fetchall() if c.execute('select exists(select 1 from pg_roles where rolname=%s)',(LOGIN,)).fetchone()[0] else []
    with c.cursor(row_factory=dict_row) as cur:
        value['dedicated_role_limits']=cur.execute('select rolname,rolconnlimit from pg_roles where rolname in(%s,%s) order by rolname',(LOGIN,CUSTODIAN)).fetchall()
        value['dedicated_schema_acl']=cur.execute("""select r.rolname,n.nspname as schema,
          has_schema_privilege(r.oid,n.oid,'USAGE') as usage,has_schema_privilege(r.oid,n.oid,'CREATE') as create
          from pg_roles r cross join pg_namespace n where r.rolname in(%s,%s)
          and n.nspname in('public','prumo_private','auth','prumo_s1_signed_i20') order by r.rolname,n.nspname""",(LOGIN,CUSTODIAN)).fetchall()
        value['dedicated_database_acl']=cur.execute("""select r.rolname,d.datname as database,
          has_database_privilege(r.oid,d.oid,'CONNECT') as connect,has_database_privilege(r.oid,d.oid,'CREATE') as create,
          has_database_privilege(r.oid,d.oid,'TEMP') as temp
          from pg_roles r cross join pg_database d where r.rolname in(%s,%s) and d.datname=current_database() order by r.rolname""",(LOGIN,CUSTODIAN)).fetchall()
    return json.loads(json.dumps(value,default=str))


def validate(before,after,final,c):
    # The role starts and ends disabled. Rotation changes secret data only;
    # no credential values or expiry/UUID rows belong in this catalog snapshot.
    assert after==final,'I83 leftover catalog/ACL/role drift'
    for section in ('triggers',):
        assert before[section]==final[section],section
    for section in ('column_acl','policies','constraints','tables','effective_table_acl','effective_function_acl','catalog_dependencies'):
        old={json.dumps(r,sort_keys=True) for r in before[section]}
        new={json.dumps(r,sort_keys=True) for r in final[section]}
        assert old<=new,section
    assert len(final['tables'])==len(before['tables'])+1
    assert len(final['policies'])==len(before['policies'])+2
    assert len(final['functions'])==len(before['functions'])
    assert len(final['roles'])==len(before['roles'])+2
    assert len(final['memberships'])==len(before['memberships'])+2
    funcs={r['signature']:r for r in final['functions']}
    for old in before['functions']:
        now=funcs[old['signature']]
        for k in ('owner','prosecdef','proconfig'):assert now[k]==old[k],(old['signature'],k)
        if old['signature'].startswith(('prumo_private.s1_i79_admin_signed(','prumo_private.s1_i80_signed(')):
            assert now['acl'].replace(',prumo_s1_admin_edge_local=X/prumo_s0_g1_executor_local','')==old['acl']
        else:assert now['acl']==old['acl'],old['signature']
        if old['signature'].startswith(('prumo_private.s1_i79_admin_signed(','prumo_private.s1_i80_signed(','prumo_private.s1_i79_admin_bridge(','prumo_private.s1_i80_bridge(')):
            body=c.execute('select prosrc from pg_proc where oid=to_regprocedure(%s)',(old['signature'],)).fetchone()[0]
            admission="session_user not in('prumo_cfi01_pgtest_login','prumo_s1_admin_edge_local')"
            assert body.count(admission)==1
            body=body.replace(admission,"session_user<>'prumo_cfi01_pgtest_login'")
            if '_signed(' in old['signature']:
                variable='v_secret' if 'i79_' in old['signature'] else 'secret_value'
                old_lookup='select secret into '+variable+' from prumo_private.cfi01_signing_keys_local where key_id=p_key and active for share;'
                new_lookup="if session_user='prumo_s1_admin_edge_local' then\n  select secret into "+variable+" from prumo_private.s1_i83_edge_credentials where key_id=p_key and enabled and not_before<=clock_timestamp() and expires_at>clock_timestamp() for share;\n else "+old_lookup+' end if;'
                expiry=" if session_user='prumo_s1_admin_edge_local' and not exists(select 1 from prumo_private.s1_i83_edge_credentials where key_id=p_key and enabled and not_before<=clock_timestamp() and expires_at>clock_timestamp()) then raise exception 'I83_KEY_EXPIRED_AFTER_WAIT' using errcode='42501';end if;\n"
                assert body.count(new_lookup)==1 and body.count(expiry)==1
                body=body.replace(new_lookup,old_lookup).replace(expiry,'')
            assert hashlib.sha256(body.encode()).hexdigest()==old['body_sha256'],'original business body differs beyond dedicated admission/key lookup/expiry'
        else:assert now['body_sha256']==old['body_sha256'],old['signature']
    for role in final['roles']:
        if role['rolname'] in (LOGIN,CUSTODIAN):assert all(not role[k] for k in role if k!='rolname'),role['rolname']
    for m in final['memberships']:
        if m['role'] in (LOGIN,CUSTODIAN):assert (m['member'],m['grantor'],m['admin_option'],m['inherit_option'],m['set_option'])==('postgres','supabase_admin',True,False,False)
        assert m['member'] not in(LOGIN,CUSTODIAN)
    for r in final['dedicated_schema_acl']:assert not r['create']
    for r in final['dedicated_database_acl']:assert not r['create']
    for r in final['dedicated_role_limits']:
        if r['rolname']==LOGIN:assert r['rolconnlimit']==4
    allowed=[r for r in final['edge_function_acl'] if r['execute']]
    assert len(allowed)==2 and all(r['signature'].startswith(('prumo_private.s1_i79_admin_signed(','prumo_private.s1_i80_signed(')) for r in allowed)
    for r in final['effective_table_acl']:
        if r['rolname']==LOGIN or (r['rolname']==CUSTODIAN and r['relation']!=TABLE):assert all(not v for k,v in r.items() if k not in('rolname','relation'))


if __name__=='__main__':
    if os.environ.get('PRUMO_I83_DISPOSABLE_TEST')!='YES':raise RuntimeError('I83 opt-in required')
    phase=argparse.ArgumentParser();phase.add_argument('phase',choices=('before','after','final'));arg=phase.parse_args().phase
    root=Path(os.environ.get('RUNNER_TEMP','/tmp'))
    with psycopg.connect(local_env()['DB_URL']) as c:
        current=snapshot(c)
        if arg=='final':
            validate(json.loads((root/'prumo_i83_catalog_before.json').read_text()),json.loads((root/'prumo_i83_catalog_after.json').read_text()),current,c)
            assert c.execute('select count(*) from '+TABLE+' where enabled or secret is not null').fetchone()[0]==0
            assert c.execute('select count(*) from pg_stat_activity where usename=%s',(LOGIN,)).fetchone()[0]==0
    (root/('prumo_i83_catalog_'+arg+'.json')).write_text(json.dumps(current,indent=2)+'\n')
    print('I83-CATALOG',arg,{k:len(current[k]) for k in ('roles','memberships','functions','tables','policies','triggers','constraints')},flush=True)
    if arg=='final':print('I83-ACCEPTANCE: after=final, original owners/data ACL/guards preserved; dedicated login has exactly two domain functions and no table data privileges; no live credential material or sessions',flush=True)
