"""I82 delta attestation: no I81 owner/table ACL/policy/trigger/constraint drift."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import psycopg
from integration.i81.catalog import snapshot
from scripts.test_s0_cfi01_auth_rest_local import local_env

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('before','after','final'));args=parser.parse_args()
    if os.environ.get('PRUMO_I82_DISPOSABLE_TEST')!='YES':raise RuntimeError('I82 opt-in required')
    root=Path(os.environ.get('RUNNER_TEMP','/tmp'))
    with psycopg.connect(local_env()['DB_URL']) as c:
        current=json.loads(json.dumps(snapshot(c),default=str))
        if args.phase=='final':
            before=json.loads((root/'prumo_i82_catalog_before.json').read_text())
            after=json.loads((root/'prumo_i82_catalog_after.json').read_text())
            assert current==after,'runtime/probe left catalog residue'
            for name in ('roles','memberships','tables','column_acl','policies','triggers','constraints','effective_function_acl','effective_table_acl'):
                assert before[name]==current[name],name
            new={r['signature']:r for r in current['functions']}
            assert len(new)==len(before['functions'])+1
            for old in before['functions']:
                item=new[old['signature']]
                for field in ('owner','prosecdef','proconfig','acl'):assert old[field]==item[field],(old['signature'],field)
                if old['signature'].startswith(('prumo_private.s1_i79_admin_bridge(','prumo_private.s1_i80_bridge(')):
                    body=c.execute('select prosrc from pg_proc where oid=to_regprocedure(%s)',(old['signature'],)).fetchone()[0]
                    prefix='\n perform prumo_private.s1_i82_metadata_fence();'
                    assert body.count(prefix)==1
                    assert hashlib.sha256(body.replace(prefix,'',1).encode()).hexdigest()==old['body_sha256']
                else:assert old['body_sha256']==item['body_sha256'],old['signature']
            for role in ('anon','authenticated','service_role','prumo_cfi01_pgtest_login','prumo_s0_g1_executor_local'):
                assert not c.execute("select has_function_privilege(%s,'prumo_private.s1_i82_metadata_fence()','EXECUTE')",(role,)).fetchone()[0]
    (root/('prumo_i82_catalog_'+args.phase+'.json')).write_text(json.dumps(current,indent=2)+'\n')
    print('I82-CATALOG',args.phase,'functions',len(current['functions']),'triggers',len(current['triggers']),'constraints',len(current['constraints']),flush=True)
    if args.phase=='final':print('I82-ACCEPTANCE: all I81 owners/data ACL/policies/guards preserved; only one prefix call per bridge and one private INVOKER metadata fence; after=final',flush=True)
