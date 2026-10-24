#!/usr/bin/env python3
"""WA48: isolated PG17-only authenticated lab login + non-superuser shadow."""
import concurrent.futures
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import time
import uuid
from urllib.parse import urlsplit

dsn=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(dsn)
if (u.scheme!="postgresql" or u.hostname!="127.0.0.1" or
    u.port!=5432 or u.username!="postgres" or u.path!="/prumo_s0_test_ci"
    or u.query or u.fragment):
    raise SystemExit("WA48 refuses hosted or alternate database")
for name in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER","PGSERVICE",
             "PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT","PGSSLKEY",
             "PGSSLROOTCERT"):
    if os.environ.get(name):
        raise SystemExit("WA48 refuses libpq override")
client="prumo_s0_meta_wa48_client_lab"
client_dsn="postgresql://"+client+"@127.0.0.1:5432/prumo_s0_test_ci"
password=secrets.token_urlsafe(40)
key_id=str(uuid.uuid4())
secret=secrets.token_bytes(48)
app="12346000002"
channel="f7300000-0000-4000-8000-000000000002"
intent="f7400000-0000-4000-8000-000000000002"
def quote(v):
    return "'"+str(v).replace("'","''")+"'"
def execute(query,as_client=False,stdin=False):
    env=dict(os.environ)
    env["PGPASSWORD"]=password if as_client else os.environ.get("PGPASSWORD","postgres")
    cmd=["psql","-X","-qAt","-v","ON_ERROR_STOP=1","-v","VERBOSITY=verbose",
         client_dsn if as_client else dsn]
    if not stdin:
        cmd+=["-c",query]
    return subprocess.run(cmd,input=query if stdin else None,env=env,
                          text=True,capture_output=True,timeout=25)
def ok(query,as_client=False):
    r=execute(query,as_client)
    if r.returncode:
        raise AssertionError("Unexpected SQL error: "+r.stderr[-400:])
    return r.stdout.strip()
def no(query,as_client=True):
    r=execute(query,as_client)
    assert r.returncode!=0,"Unexpected SQL acceptance"
    assert "42501" in r.stderr or "permission denied" in r.stderr,r.stderr[-400:]
def mark(n):
    print("WA48-"+str(n).zfill(2)+" PASS",flush=True)
# Ephemeral password is provisioned through psql stdin, never committed/logged.
provision=execute("ALTER ROLE "+client+" LOGIN PASSWORD "+quote(password)+";",stdin=True)
assert provision.returncode==0,provision.stderr[-250:]
ok("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0("
   "key_id,app,secret,active,valid_from,valid_until) values ("+
   quote(key_id)+","+quote(app)+",decode("+quote(secret.hex())+
   ",'hex'),true,clock_timestamp()-interval '10 minutes',"
   "clock_timestamp()+interval '1 hour')")
def packet(event="WA48_EVT_A",body="a"*64,kind="delivered",nonce=None,
           issued=None,for_app=app,mac=None):
    nonce=nonce or str(uuid.uuid4())
    issued=int(time.time()) if issued is None else issued
    items=[key_id,for_app,"22346000002","32346000002",
           channel,intent,"ATTEMPT_B","CORR_B","5581900000000",
           "wamid.WA40.SHARED",event,kind,body,str(issued),nonce]
    msg="|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY",*items]).encode()
    signature=hmac.new(secret,msg,hashlib.sha256).hexdigest() if mac is None else mac
    return items+[signature]
def query(items):
    values=[quote(v) for v in items]
    values[13]=str(int(items[13]))
    return ("select prumo_private.meta_wa48_shadow_append_fixture_s0("+
            ",".join(values)+")")
def issue(**kw):
    return json.loads(ok(query(packet(**kw)),True))
assert ok("select session_user||':'||current_user",True)==client+":"+client
mark(1)
roles=ok("select rolname||':'||rolcanlogin||':'||rolsuper||':'||rolbypassrls "
 "from pg_roles where rolname like 'prumo_s0_meta_wa48_%' order by rolname")
assert client+":true:false:false" in roles and "prumo_s0_meta_wa48_executor_lab:false:false:false" in roles
mark(2)
signature="prumo_private.meta_wa48_shadow_append_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)"
assert ok("select proowner::regrole::text from pg_proc where oid="+quote(signature)+"::regprocedure")=="prumo_s0_meta_wa48_executor_lab"
mark(3)
no("select * from prumo_private.meta_wa48_shadow_keys_fixture_s0")
mark(4)
no("insert into prumo_private.meta_wa48_shadow_nonces_fixture_s0(nonce,key_id) values ("+
 quote(uuid.uuid4())+","+quote(key_id)+")")
mark(5)
no("insert into prumo_private.meta_wa48_shadow_receipts_fixture_s0(key_id,event_ref,body_hash,kind) values ("+
 quote(key_id)+",'FORGED',repeat('f',64),'sent')")
mark(6)
no("set role prumo_s0_meta_wa48_executor_lab")
mark(7)
no("select prumo_private.meta_wa48_shadow_revoke_fixture_s0("+quote(key_id)+")")
mark(8)
first=packet()
result=json.loads(ok(query(first),True))
assert result["outcome"]=="LAB_SHADOW_OBSERVED" and result["lab_only"] is True
mark(9)
for flag in ("service_authenticated","ack_allowed","send_authorized",
 "retry_external","production_authorized","delivery_confirmed",
 "case_transition_authorized","s0_write_authorized"):
    assert result[flag] is False,flag
mark(10)
assert ok("select count(*) from prumo_private.meta_wa48_shadow_nonces_fixture_s0")=="1"
assert ok("select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0")=="1"
mark(11)
no(query(first))
mark(12)
assert issue()["outcome"]=="LAB_EXACT_REPLAY"
assert ok("select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0")=="1"
mark(13)
no(query(packet(event="WA48_BAD_MAC",mac="0"*64)))
mark(14)
no(query(packet(event="WA48_OTHER_APP",for_app="99999999999")))
mark(15)
no(query(packet(event="WA48_OLD",issued=int(time.time())-1000)))
mark(16)
no(query(packet(event="WA48_INVALID_BODY",body="invalid")))
mark(17)
before=ok("select count(*) from prumo_private.meta_wa48_shadow_nonces_fixture_s0")
rolled=packet(event="WA48_ROLLBACK")
assert execute("begin; "+query(rolled)+"; rollback;",True).returncode==0
assert ok("select count(*) from prumo_private.meta_wa48_shadow_nonces_fixture_s0")==before
assert ok("select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0 where event_ref='WA48_ROLLBACK'")=="0"
mark(18)
race=packet(event="WA48_RACE")
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(lambda _:execute(query(race),True),range(2)))
assert sum(x.returncode==0 for x in results)==1
assert sum(x.returncode!=0 for x in results)==1
mark(19)
assert issue(event="WA48_EVT_A",body="b"*64)["outcome"]=="LAB_BODY_VARIANT_QUARANTINED"
mark(20)
no(query(packet(event="WA48_EVT_A",body="a"*64,kind="read")))
mark(21)
assert ok("select prumo_private.meta_wa48_shadow_revoke_fixture_s0("+quote(key_id)+")")=="LAB_REVOKED"
mark(22)
no(query(packet(event="WA48_AFTER_REVOKE")))
mark(23)
assert ok("select prumo_private.meta_wa48_shadow_revoke_fixture_s0("+quote(key_id)+")")=="LAB_ALREADY_REVOKED"
mark(24)
assert ok("select has_schema_privilege('prumo_s0_meta_wa48_executor_lab','prumo_private','CREATE')")=="f"
mark(25)
assert ok("select has_function_privilege("+quote(client)+","+quote("prumo_private.meta_arquivar_handoff_assinado_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)")+",'EXECUTE')")=="f"
mark(26)
for table in ("meta_wa48_shadow_keys_fixture_s0","meta_wa48_shadow_nonces_fixture_s0","meta_wa48_shadow_receipts_fixture_s0"):
    assert ok("select has_table_privilege("+quote(client)+","+quote("prumo_private."+table)+",'UPDATE')")=="f"
mark(27)
assert ok("select proowner::regrole::text from pg_proc where oid='prumo_private.meta_arquivar_handoff_assinado_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)'::regprocedure")=="postgres"
mark(28)
print("WA48 28/28 PG17 SHADOW ONLY; no commercial/hosted authorization",flush=True)
