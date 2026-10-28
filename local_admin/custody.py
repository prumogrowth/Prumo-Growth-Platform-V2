"""Protected I83 server environment; no separate database vault or identity."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from local_admin.boundary import Blocked,private,EDGE,DB,KONG,docker
from local_admin.environment import database,discover


def read_env(directory):
    p=Path(directory)/'edge.env';private(p)
    try:
        values=dict(line.split('=',1) for line in p.read_text().splitlines())
        assert values['PRUMO_I83_DEDICATED']=='YES'
        assert values['PRUMO_I82_DISPOSABLE']=='YES'
        u=urlsplit(values['PRUMO_I82_DATABASE_URL'])
        assert u.username=='prumo_s1_admin_edge_local' and u.hostname=='supabase_db_prumo-s0-auth-ci' and u.path=='/postgres' and not(u.query or u.fragment)
        assert len(values['PRUMO_I82_HMAC_HEX'])==96
    except Exception:raise Blocked('CREDENTIAL_FILE_INVALID') from None
    return values


def credential_state(directory):
    from uuid import UUID
    from urllib.parse import urlunsplit
    import psycopg
    try:v=read_env(directory)
    except Blocked as error:
        return 'MISSING' if error.code=='STATE_MISSING' else 'INVALID'
    try:
        key=UUID(v['PRUMO_I82_KEY_ID']);secret=bytes.fromhex(v['PRUMO_I82_HMAC_HEX'])
        with database() as c:
            row=c.execute("""select enabled,secret=%s,not_before<=clock_timestamp(),expires_at>clock_timestamp()
              from prumo_private.s1_i83_edge_credentials where key_id=%s""",(secret,key)).fetchone()
            login=c.execute("select rolcanlogin from pg_roles where rolname='prumo_s1_admin_edge_local'").fetchone()[0]
        if not row or not row[0] or not login:return 'REVOKED'
        if not row[2] or not row[3]:return 'EXPIRED'
        if not row[1]:return 'INVALID'
        u=urlsplit(v['PRUMO_I82_DATABASE_URL']);db=urlsplit(discover()['DB_URL'])
        dsn=urlunsplit((u.scheme,u.netloc.replace('supabase_db_prumo-s0-auth-ci:5432',str(db.hostname)+':'+str(db.port)),u.path,'',''))
        with psycopg.connect(dsn,connect_timeout=5) as c:
            if c.execute('select session_user,current_user').fetchone()!=('prumo_s1_admin_edge_local',)*2:return 'INVALID'
        return 'VALID'
    except Exception:return 'INVALID'


def scan(directory,container_ids=(),extra=()):
    values=[]
    try:
        v=read_env(directory);values=[v['PRUMO_I82_HMAC_HEX'],v['PRUMO_I82_DATABASE_URL'],urlsplit(v['PRUMO_I82_DATABASE_URL']).password]
    except Blocked as e:
        if e.code!='STATE_MISSING':raise
    values.extend(extra);needles=[s.encode() for s in values if s]
    for name in (DB,'supabase_auth_prumo-s0-auth-ci',KONG,*container_ids):
        from local_admin.boundary import run
        data=run(['docker','--host=unix:///var/run/docker.sock','logs',name],combined=True)
        if any(n in data for n in needles):raise Blocked('CREDENTIAL_LOG_MATCH')
    p=Path(directory)/'worker.log'
    if p.exists():
        private(p)
        if any(n in p.read_bytes() for n in needles):raise Blocked('CREDENTIAL_LOG_MATCH')
