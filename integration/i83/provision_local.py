"""Trusted disposable installer/custody, never an HTTP authority or secret fixture.

No credentials on argv/stdout. Live secrets exist only in memory and the owning
0700 temporary directory; SQL sees a SCRAM verifier, not the plaintext password.
The existing nonce FK gets an INACTIVE zero-material anchor, not the Edge HMAC.
"""
from base64 import b64encode
from dataclasses import dataclass,field
from datetime import timedelta
import hashlib
import hmac
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit,urlunsplit,quote
from uuid import uuid4

import psycopg
from psycopg import sql

LOGIN='prumo_s1_admin_edge_local'
CUSTODIAN='prumo_s1_edge_custodian_local'
TABLE='prumo_private.s1_i83_edge_credentials'


def guard(db):
    if os.environ.get('PRUMO_I83_DISPOSABLE_TEST')!='YES':raise RuntimeError('I83 local opt-in required')
    u=urlsplit(db)
    if u.scheme not in ('postgres','postgresql') or u.hostname not in ('localhost','127.0.0.1') or u.port!=54322 or u.username!='postgres' or u.path!='/postgres' or u.query or u.fragment:
        raise RuntimeError('I83 disposable installer DSN required')


def install(db):
    guard(db)
    try:
        with psycopg.connect(db,autocommit=True) as c:
            c.execute("set prumo.i83_disposable='YES'")
            c.execute(Path('supabase/tests/s1_i83_edge_credentials_local_only.sql').read_text())
    except Exception:
        raise RuntimeError('I83 guarded installation failed (details withheld)') from None


def scram(password):
    salt=secrets.token_bytes(16)
    salted=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,4096)
    stored=hashlib.sha256(hmac.digest(salted,b'Client Key','sha256')).digest()
    server=hmac.digest(salted,b'Server Key','sha256')
    b=lambda v:b64encode(v).decode()
    return 'SCRAM-SHA-256$4096:'+b(salt)+'$'+b(stored)+':'+b(server)


@dataclass(repr=False)
class Credential:
    key_id:object=field(default_factory=uuid4)
    secret:bytes=field(default_factory=lambda:secrets.token_bytes(48))
    password:str=field(default_factory=lambda:secrets.token_urlsafe(48))
    verifier:str=field(init=False)
    def __post_init__(self):self.verifier=scram(self.password)
    def dsn(self,db,internal=False):
        u=urlsplit(db)
        host='supabase_db_prumo-s0-auth-ci:5432' if internal else str(u.hostname)+':'+str(u.port)
        return urlunsplit(('postgresql',LOGIN+':'+quote(self.password,safe='')+'@'+host,'/postgres','',''))
    def sensitive(self,db):
        return [self.password,self.verifier,self.secret.hex(),self.dsn(db),self.dsn(db,True)]


def rotate(db):
    """Atomic old-key tombstones + new key/password; caller restarts local worker.

    SHARE key locks order an in-flight command before revocation, or revocation
    before denial. Password rotation alone does not revoke pooled sessions.
    """
    guard(db);value=Credential()
    try:
        with psycopg.connect(db) as c:
            c.execute("select pg_advisory_xact_lock(hashtextextended('s1-i83:provision',0))")
            assert c.execute('select current_user,session_user').fetchone()==('postgres','postgres')
            # Existing PG17 installer capability only, revoked in the same tx.
            c.execute('grant prumo_s1_edge_custodian_local to postgres with inherit false,set true')
            c.execute('set local role prumo_s1_edge_custodian_local')
            c.execute('select key_id from '+TABLE+' where enabled order by key_id for update')
            c.execute('update '+TABLE+' set enabled=false,secret=null,revoked_at=clock_timestamp() where enabled')
            c.execute('reset role')
            # FK compatibility only; never place the actual signing key here.
            c.execute('insert into prumo_private.cfi01_signing_keys_local(key_id,secret,active) values (%s,%s,false)',(value.key_id,bytes(32)))
            c.execute('set local role prumo_s1_edge_custodian_local')
            c.execute('insert into '+TABLE+'(key_id,secret,not_before,expires_at) values (%s,%s,clock_timestamp()-interval \'1 second\',clock_timestamp()+interval \'1 hour\')',(value.key_id,value.secret))
            c.execute('reset role')
            c.execute('revoke prumo_s1_edge_custodian_local from postgres')
            until=c.execute("select clock_timestamp()+interval '1 hour'").fetchone()[0]
            c.execute(sql.SQL('alter role prumo_s1_admin_edge_local login password {} valid until {}').format(sql.Literal(value.verifier),sql.Literal(until)))
    except Exception:
        raise RuntimeError('I83 credential provisioning failed (credentials withheld)') from None
    return value


def revoke(db,key):
    guard(db)
    with psycopg.connect(db) as c:
        c.execute('grant prumo_s1_edge_custodian_local to postgres with inherit false,set true')
        c.execute('set local role prumo_s1_edge_custodian_local')
        c.execute('update '+TABLE+' set enabled=false,secret=null,revoked_at=clock_timestamp() where key_id=%s and enabled',(key,))
        c.execute('reset role');c.execute('revoke prumo_s1_edge_custodian_local from postgres')


def retire(db):
    guard(db)
    with psycopg.connect(db) as c:
        c.execute('grant prumo_s1_edge_custodian_local to postgres with inherit false,set true')
        c.execute('set local role prumo_s1_edge_custodian_local')
        c.execute('update '+TABLE+' set enabled=false,secret=null,revoked_at=clock_timestamp() where enabled')
        c.execute('reset role');c.execute('revoke prumo_s1_edge_custodian_local from postgres')
        c.execute('alter role prumo_s1_admin_edge_local nologin password null')
    with psycopg.connect(db,autocommit=True) as c:
        c.execute('select pg_terminate_backend(pid) from pg_stat_activity where usename=%s and pid<>pg_backend_pid()',(LOGIN,))
        assert c.execute('select count(*) from '+TABLE+' where enabled or secret is not null').fetchone()[0]==0
        assert c.execute('select rolcanlogin,rolpassword from pg_authid where rolname=%s',(LOGIN,)).fetchone()==(False,None)


def write_env(path,values):
    """The parent directory must already be private; never follows a symlink."""
    p=Path(path)
    if p.parent.stat().st_mode&0o077:raise RuntimeError('I83 private custody directory required')
    data='\n'.join(k+'='+v for k,v in values.items())+'\n'
    tmp=p.with_name(p.name+'.next')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as out:out.write(data)
    os.replace(tmp,p)
