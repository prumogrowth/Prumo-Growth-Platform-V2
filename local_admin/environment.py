"""Discover only the fixed unlinked disposable stack; never accept URL arguments."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from local_admin.boundary import ROOT,DB,PROJECT,NETWORK,Blocked,run,docker,inspect,digest



def checkout():
    manifest=json.loads((ROOT/'local_admin/dependencies.json').read_text())
    for p,h in manifest['local_sources'].items():
        if digest((ROOT/p).read_bytes())!=h:raise Blocked('CERTIFIED_SOURCE_DRIFT')
    if (ROOT/'supabase/.temp/project-ref').exists():raise Blocked('HOSTED_PROJECT_LINK_FORBIDDEN')
    return manifest


def opt_ins():
    # Historical names are installer guards; this does not run a test suite.
    for v in ('I83','I81','I82'):
        os.environ['PRUMO_'+v+'_DISPOSABLE_TEST']='YES'


def discover():
    checkout();out=run(['supabase','status','--output','env']).decode();v={}
    for line in out.splitlines():
        if '=' in line:
            k,value=line.split('=',1);v[k.strip()]=value.strip().strip('\"').strip("'")
    try:
        api=urlsplit(v['API_URL']);db=urlsplit(v['DB_URL'])
        assert api.scheme=='http' and api.hostname in('localhost','127.0.0.1') and api.port==54321 and api.path in('','/') and not(api.username or api.password or api.query or api.fragment)
        assert db.scheme in('postgres','postgresql') and db.hostname in('localhost','127.0.0.1') and db.port==54322 and db.username=='postgres' and db.path=='/postgres' and not(db.query or db.fragment)
        assert v['ANON_KEY']
    except Exception:raise Blocked('LOCAL_STACK_ADDRESS_INVALID') from None
    return {k:v[k] for k in ('DB_URL','API_URL','ANON_KEY')}


def database():
    import psycopg
    e=discover();opt_ins()
    return psycopg.connect(e['DB_URL'])


def engine():return docker('info','--format','{{.ID}}').decode().strip()


def owned(state):
    if state.get('version')!=1 or state.get('project')!=PROJECT or state.get('root')!=str(ROOT) or state.get('engine')!=engine():raise Blocked('STATE_IDENTITY_INVALID')
    if inspect(DB)!=state.get('db_id'):raise Blocked('STACK_IDENTITY_CHANGED')
    with database() as c:
        row=c.execute("select shobj_description(oid,'pg_database') from pg_database where datname=current_database()").fetchone()
        if row[0]!='PRUMO_I84_DISPOSABLE:'+state['token']:raise Blocked('STACK_MARKER_MISMATCH')
        if c.execute("select current_user,session_user,current_setting('server_version_num')::int/10000").fetchone()!=('postgres','postgres',17):raise Blocked('INSTALLER_IDENTITY_INVALID')


def runtime_env(value):
    e=discover()
    networks=json.loads(docker('inspect','--format','{{json .NetworkSettings.Networks}}',DB))
    addresses=[v['IPAddress'] for k,v in networks.items() if k==NETWORK and v.get('IPAddress')]
    if len(addresses)!=1:raise Blocked('OWN_DATABASE_NETWORK_MISSING')
    return {'PRUMO_I82_DISPOSABLE':'YES','PRUMO_I83_DEDICATED':'YES','PRUMO_I82_AUTH_URL':'http://supabase_kong_'+PROJECT+':8000',
      'PRUMO_I82_DATABASE_URL':value.dsn(e['DB_URL'],True),'PRUMO_I82_DATABASE_IPV4':addresses[0],'PRUMO_I82_ANON_KEY':e['ANON_KEY'],
      'PRUMO_I82_KEY_ID':str(value.key_id),'PRUMO_I82_HMAC_HEX':value.secret.hex(),'PRUMO_I82_ALLOW_ORIGIN':'http://localhost:3000'}
