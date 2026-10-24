#!/usr/bin/env python3
"""WA49: real S0 fixture binding READ under restricted PG17 owner; SHADOW only."""
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
url=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(url)
if (u.scheme!="postgresql" or u.hostname!="127.0.0.1" or u.port!=5432
 or u.username!="postgres" or u.path!="/prumo_s0_test_ci" or u.query or u.fragment):
 raise SystemExit("WA49: disposable local PG17 ONLY")
for k in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER","PGSERVICE",
 "PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.environ.get(k):raise SystemExit("WA49: environment override denied")
CLIENT="prumo_s0_meta_wa48_client_lab"
LOGIN="postgresql://"+CLIENT+"@127.0.0.1:5432/prumo_s0_test_ci"
PASS=secrets.token_urlsafe(42)
KEY=str(uuid.uuid4())
SECRET=secrets.token_bytes(48)
APP="12346000002";WABA="22346000002";PHONE="32346000002"
CHANNEL="f7300000-0000-4000-8000-000000000002"
INTENT="f7400000-0000-4000-8000-000000000002"
def q(x):return "'"+str(x).replace("'","''")+"'"
def execute(s,client=False,stdin=False):
 env={**os.environ,"PGPASSWORD":PASS if client else os.environ.get("PGPASSWORD","postgres")}
 args=["psql","-X","-qAt","-v","ON_ERROR_STOP=1","-v","VERBOSITY=verbose",
       LOGIN if client else url]
 if not stdin:args+=["-c",s]
 return subprocess.run(args,input=s if stdin else None,text=True,capture_output=True,env=env,timeout=25)
def ok(sql,client=False):
 r=execute(sql,client)
 if r.returncode:raise AssertionError("WA49 SQL error: "+r.stderr[-440:])
 return r.stdout.strip()
def denied(sql,client=True):
 r=execute(sql,client)
 assert r.returncode!=0,"unexpected acceptance"
 assert "42501" in r.stderr or "permission denied" in r.stderr,r.stderr[-300:]
def mark(n):print("WA49-"+str(n).zfill(2)+" PASS",flush=True)
# Separate random ephemeral password, so this test can run independently.
assert execute("alter role "+CLIENT+" login password "+q(PASS)+";",stdin=True).returncode==0
ok("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0("
 "key_id,app,secret,active,valid_from,valid_until) values ("+
 q(KEY)+","+q(APP)+",decode("+q(SECRET.hex())+",'hex'),true,"
 "clock_timestamp()-interval '10 minutes',clock_timestamp()+interval '1 hour')")
FN="prumo_private.meta_wa49_scoped_shadow_fixture_s0"
def args(event="WA49_EVT",app=APP,waba=WABA,phone=PHONE,channel=CHANNEL,
 intent=INTENT,attempt="ATTEMPT_B",corr="CORR_B",recipient="5581900000000",
 wamid="wamid.WA40.SHARED",kind="delivered",body="a"*64,nonce=None,issued=None,
 mac=None):
 t=[KEY,app,waba,phone,channel,intent,attempt,corr,recipient,wamid,event,
    kind,body,str(int(time.time()) if issued is None else issued),
    nonce or str(uuid.uuid4())]
 payload="|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY",*t]).encode()
 return t+[hmac.new(SECRET,payload,hashlib.sha256).hexdigest() if mac is None else mac]
def command(a):
 v=[q(x) for x in a];v[13]=str(int(a[13]))
 return "select "+FN+"("+",".join(v)+")"
def call(**kw):return json.loads(ok(command(args(**kw)),True))
assert ok("select current_user||':'||session_user",True)==CLIENT+":"+CLIENT
mark(1)
signature=FN+"(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)"
assert ok("select proowner::regrole::text from pg_proc where oid="+q(signature)+"::regprocedure")=="prumo_s0_meta_wa48_executor_lab"
mark(2)
assert ok("select rolcanlogin::text||':'||rolsuper::text||':'||rolbypassrls::text from pg_roles where rolname='prumo_s0_meta_wa48_executor_lab'")=="false:false:false"
mark(3)
for table in ("meta_vinculos_tentativa_fixture_s0","meta_apps_fixture_s0","meta_canais_fixture_s0","outbox_intencoes_s0"):
 assert ok("select has_table_privilege('prumo_s0_meta_wa48_executor_lab',"+q("prumo_private."+table)+",'UPDATE')")=="f"
mark(4)
assert ok("select has_schema_privilege('prumo_s0_meta_wa48_executor_lab','prumo_private','CREATE')")=="f"
mark(5)
for table in ("meta_vinculos_tentativa_fixture_s0","meta_apps_fixture_s0","meta_canais_fixture_s0","outbox_intencoes_s0"):
 denied("select * from prumo_private."+table,True)
mark(6)
denied("select * from prumo_private.meta_wa48_shadow_keys_fixture_s0",True)
mark(7)
denied("set role prumo_s0_meta_wa48_executor_lab",True)
mark(8)
denied("select "+FN+"(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)",False)
mark(9)
before=ok("select count(*) from prumo_private.meta_status_forense_fixture_s0")
r=call();assert r["outcome"]=="LAB_SHADOW_OBSERVED" and r["s0_scope_matched"] is True
assert r["authoritative_s0_written"] is False and r["authoritative_scope_snapshot_locked"] is False
mark(10)
assert ok("select count(*) from prumo_private.meta_status_forense_fixture_s0")==before
mark(11)
for flag in ("service_authenticated","ack_allowed","send_authorized","production_authorized",
 "retry_external","delivery_confirmed","case_transition_authorized","s0_write_authorized"):
 assert r[flag] is False,flag
mark(12)
def block(**kw):denied(command(args(**kw)),True)
block(app="12346000001");mark(13)
block(waba="22346000001");mark(14)
block(phone="32346000001");mark(15)
block(channel="f7300000-0000-4000-8000-000000000001");mark(16)
block(intent="f7400000-0000-4000-8000-000000000001");mark(17)
block(attempt="ATTEMPT_A");mark(18)
block(corr="CORR_A");mark(19)
block(recipient="5581999999999");mark(20)
block(wamid="wamid.NOT_BOUND");mark(21)
block(mac="0"*64);mark(22)
block(issued=int(time.time())-1000);mark(23)
block(kind="unknown");mark(24)
first=args(event="WA49_NONCE")
assert json.loads(ok(command(first),True))["outcome"]=="LAB_SHADOW_OBSERVED"
block_items=execute(command(first),True)
assert block_items.returncode!=0 and "42501" in block_items.stderr
mark(25)
assert call()["outcome"]=="LAB_EXACT_REPLAY"
mark(26)
assert call(body="b"*64)["outcome"]=="LAB_BODY_VARIANT_QUARANTINED"
mark(27)
block(kind="read")
# Different kind for same event/hash conflicts with existing shadow record.
mark(28)
assert ok("select count(*) from prumo_private.meta_status_forense_fixture_s0")==before
mark(29)
nonce_before=ok("select count(*) from prumo_private.meta_wa48_shadow_nonces_fixture_s0")
roll=args(event="WA49_ROLLBACK")
assert execute("begin; "+command(roll)+"; rollback;",True).returncode==0
assert ok("select count(*) from prumo_private.meta_wa48_shadow_nonces_fixture_s0")==nonce_before
mark(30)
race=args(event="WA49_RACE")
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 res=list(pool.map(lambda _:execute(command(race),True),range(2)))
assert sum(t.returncode==0 for t in res)==1 and sum(t.returncode!=0 for t in res)==1
mark(31)
assert ok("select prumo_private.meta_wa48_shadow_revoke_fixture_s0("+q(KEY)+")")=="LAB_REVOKED"
mark(32)
block(event="WA49_REVOKED");mark(33)
assert ok("select count(*) from prumo_private.meta_status_forense_fixture_s0")==before
mark(34)
print("WA49 34/34 PASS - S0 read-only scope + PG17 shadow",flush=True)
