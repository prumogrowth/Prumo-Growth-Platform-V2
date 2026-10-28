"""Protected I83 server environment; no separate database vault or identity."""
import ipaddress
import re
from uuid import UUID
from pathlib import Path
from urllib.parse import urlsplit
from local_admin.boundary import Blocked,private,DB,KONG
from local_admin.environment import database,discover


def read_env(directory):
    p=Path(directory)/'edge.env';private(p)
    try:
        values=dict(line.split('=',1) for line in p.read_text().splitlines())
        if not (values['PRUMO_I83_DEDICATED']=='YES'):raise ValueError
        if not (values['PRUMO_I82_DISPOSABLE']=='YES'):raise ValueError
        u=urlsplit(values['PRUMO_I82_DATABASE_URL'])
        if not (u.username=='prumo_s1_admin_edge_local' and u.hostname=='supabase_db_prumo-s0-auth-ci' and u.path=='/postgres' and not(u.query or u.fragment)):raise ValueError
        if not (u.scheme=='postgresql' and u.port==5432 and u.password):raise ValueError
        if not (re.fullmatch('[0-9a-f]{96}',values['PRUMO_I82_HMAC_HEX'])):raise ValueError
        if not (str(UUID(values['PRUMO_I82_KEY_ID']))==values['PRUMO_I82_KEY_ID']):raise ValueError
        if not (values['PRUMO_I82_AUTH_URL']=='http://supabase_kong_prumo-s0-auth-ci:8000'):raise ValueError
        if not (values['PRUMO_I82_ALLOW_ORIGIN']=='http://localhost:3000'):raise ValueError
        if not (ipaddress.IPv4Address(values['PRUMO_I82_DATABASE_IPV4']).is_private):raise ValueError
        if not (values['PRUMO_I82_ANON_KEY']):raise ValueError
        if not (set(values)=={'PRUMO_I83_DEDICATED','PRUMO_I82_DISPOSABLE','PRUMO_I82_DATABASE_URL','PRUMO_I82_DATABASE_IPV4','PRUMO_I82_HMAC_HEX','PRUMO_I82_KEY_ID','PRUMO_I82_AUTH_URL','PRUMO_I82_ALLOW_ORIGIN','PRUMO_I82_ANON_KEY'}):raise ValueError
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
            from integration.i83.provision_local import private_material_transaction
            private_material_transaction(c)
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
        if e.code=='CREDENTIAL_FILE_INVALID':
            # Recovery may remove an invalid profile, never execute it. Still
            # scan its material without treating its URLs/identity as authority.
            p=Path(directory)/'edge.env';private(p)
            v=dict(line.split('=',1) for line in p.read_text().splitlines() if '=' in line)
            values=[v.get('PRUMO_I82_HMAC_HEX'),v.get('PRUMO_I82_DATABASE_URL')]
            try:values.append(urlsplit(v.get('PRUMO_I82_DATABASE_URL','')).password)
            except ValueError:pass
        elif e.code!='STATE_MISSING':raise
    values.extend(extra);needles=[s.encode() for s in values if s]
    for name in (DB,'supabase_auth_prumo-s0-auth-ci',KONG,*container_ids):
        from local_admin.boundary import run
        data=run(['docker','--host=unix:///var/run/docker.sock','logs',name],combined=True)
        if any(n in data for n in needles):raise Blocked('CREDENTIAL_LOG_MATCH')
    p=Path(directory)/'worker.log'
    if p.exists():
        private(p)
        if any(n in p.read_bytes() for n in needles):raise Blocked('CREDENTIAL_LOG_MATCH')
