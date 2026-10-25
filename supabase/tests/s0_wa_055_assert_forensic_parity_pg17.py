#!/usr/bin/env python3
"""WA51: PG17-only HMAC nonce and original S0 conflict parity under restricted roles."""
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
DSN=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(DSN)
if u.scheme!="postgresql" or u.hostname!="127.0.0.1" or u.port!=5432 or u.username!="postgres" or u.path!="/prumo_s0_test_ci" or u.query or u.fragment:
 raise SystemExit("WA50 LOCAL CI ONLY")
for name in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER","PGSERVICE","PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.environ.get(name):raise SystemExit("WA50 PG override rejected")
CLIENT="prumo_s0_meta_wa48_client_lab"
LOGIN="postgresql://"+CLIENT+"@127.0.0.1:5432/prumo_s0_test_ci"
PASS=secrets.token_urlsafe(40)
KEY=str(uuid.uuid4())
SECRET=secrets.token_bytes(48)
APP="12346000002";WABA="22346000002";PHONE="32346000002"
CHANNEL="f7300000-0000-4000-8000-000000000002"
INTENT="f7400000-0000-4000-8000-000000000002"
FN="prumo_private.meta_wa51_parity_forensic_fixture_s0"
def q(x):return "'"+str(x).replace("'","''")+"'"
def run(sql,client=False,stdin=False):
 env={**os.environ,"PGPASSWORD":PASS if client else os.environ.get("PGPASSWORD","postgres")}
 args=["psql","-X","-qAt","-v","ON_ERROR_STOP=1","-v","VERBOSITY=verbose",LOGIN if client else DSN]
 if not stdin:args+=["-c",sql]
 return subprocess.run(args,input=sql if stdin else None,env=env,text=True,capture_output=True,timeout=35)
def ok(sql,client=False):
 r=run(sql,client)
 if r.returncode:raise AssertionError("WA50 ERROR "+r.stderr[-600:])
 return r.stdout.strip()
def denied(sql,client=True):
 r=run(sql,client)
 assert r.returncode!=0,"unexpected permission/access success"
 assert "42501" in r.stderr or "permission denied" in r.stderr,r.stderr[-350:]
def mark(n):print("WA51-"+str(n).zfill(2)+" PASS",flush=True)
assert run("alter role "+CLIENT+" login password "+q(PASS)+";",stdin=True).returncode==0
ok("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0(key_id,app,secret,active,valid_from,valid_until) values ("+
 q(KEY)+","+q(APP)+",decode("+q(SECRET.hex())+",'hex'),true,clock_timestamp()-interval '10 minutes',clock_timestamp()+interval '1 hour')")
def fixture(event="WA51_EVT",body="a"*64,kind="delivered",app=APP,waba=WABA,phone=PHONE,channel=CHANNEL,intent=INTENT,attempt="ATTEMPT_B",corr="CORR_B",recipient="5581900000000",wamid="wamid.WA40.SHARED",nonce=None,issued=None,mac=None):
 items=[KEY,app,waba,phone,channel,intent,attempt,corr,recipient,wamid,event,kind,body,str(int(time.time()) if issued is None else issued),nonce or str(uuid.uuid4())]
 wire="|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY",*items]).encode()
 return items+[mac if mac is not None else hmac.new(SECRET,wire,hashlib.sha256).hexdigest()]
def cmd(items):
 fields=[q(v) for v in items];fields[13]=str(int(items[13]))
 return "select "+FN+"("+",".join(fields)+")"
def call(**kw):return json.loads(ok(cmd(fixture(**kw)),True))
def block(**kw):denied(cmd(fixture(**kw)))
assert ok("select session_user||'|'||current_user",True)==CLIENT+"|"+CLIENT
mark(1)
def catalog_role(name):return ok("select rolcanlogin::text||':'||rolsuper::text||':'||rolbypassrls::text from pg_roles where rolname="+q(name))
assert catalog_role("prumo_s0_meta_wa50_writer_lab")=="false:false:false"
assert catalog_role("prumo_s0_meta_wa50_binding_guard_lab")=="false:false:false"
mark(2)
s=FN+"(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)"
assert ok("select proowner::regrole::text from pg_proc where oid="+q(s)+"::regprocedure")=="prumo_s0_meta_wa50_writer_lab"
mark(3)
assert ok("select proowner::regrole::text||'|'||prosecdef::text from pg_proc where oid='prumo_private.validar_meta_status_vinculo_fixture_s0()'::regprocedure")=="prumo_s0_meta_wa50_binding_guard_lab|true"
mark(4)
for t in ("meta_vinculos_tentativa_fixture_s0","meta_apps_fixture_s0","meta_canais_fixture_s0","outbox_intencoes_s0"):
 assert ok("select has_table_privilege('prumo_s0_meta_wa50_writer_lab',"+q("prumo_private."+t)+",'UPDATE')")=="f"
mark(5)
# Guard's very limited UPDATE(id) is isolated from the writer and client.
assert ok("select has_column_privilege('prumo_s0_meta_wa50_binding_guard_lab','prumo_private.meta_vinculos_tentativa_fixture_s0','id','UPDATE')")=="t"
assert ok("select has_column_privilege('prumo_s0_meta_wa50_writer_lab','prumo_private.meta_vinculos_tentativa_fixture_s0','id','UPDATE')")=="f"
mark(6)
for role in ("prumo_s0_meta_wa50_writer_lab","prumo_s0_meta_wa50_binding_guard_lab"):
 assert ok("select has_schema_privilege("+q(role)+",'prumo_private','CREATE')")=="f"
mark(7)
for t in ("meta_status_forense_fixture_s0","meta_status_conflitos_fixture_s0","meta_vinculos_tentativa_fixture_s0"):
 denied("select * from prumo_private."+t,True)
mark(8)
denied("set role prumo_s0_meta_wa50_writer_lab")
mark(9)
denied("set role prumo_s0_meta_wa50_binding_guard_lab")
mark(10)
denied("insert into prumo_private.meta_status_forense_fixture_s0(vinculo_id,event_ref,body_sha256,provider_status) values (gen_random_uuid(),'FORGED',repeat('f',64),'delivered')")
mark(11)
denied("select "+FN+"(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)",False)
mark(12)
assert ok("select proowner::regrole::text from pg_proc where oid='prumo_private.archivar_status_meta_tecnico_fixture_s0(text,text,text,uuid,uuid,text,text,text,text,text,text,text)'::regprocedure")=="postgres"
mark(13)
prior=int(ok("select count(*) from prumo_private.meta_status_forense_fixture_s0"))
r=call()
assert r["outcome"]=="LAB_OBSERVED_UNVERIFIED" and r["authoritative_lab_forensic_appended"] is True
mark(14)
assert int(ok("select count(*) from prumo_private.meta_status_forense_fixture_s0"))==prior+1
mark(15)
for flag in ("service_authenticated","production_authorized","ack_allowed","send_authorized","retry_external","delivery_confirmed","case_transition_authorized","definitive_failure_count_increment"):
 assert r[flag] is False
mark(16)
for field,value in (("app","12346000001"),("waba","22346000001"),("phone","32346000001"),("channel","f7300000-0000-4000-8000-000000000001"),("intent","f7400000-0000-4000-8000-000000000001"),("attempt","ATTEMPT_A"),("corr","CORR_A"),("recipient","5581999999999"),("wamid","wamid.WRONG")):
 block(**{field:value})
mark(17)
assert int(ok("select count(*) from prumo_private.meta_status_forense_fixture_s0"))==prior+1
mark(18)
block(mac="0"*64);mark(19)
block(issued=int(time.time())-1000);mark(20)
one=fixture(event="WA51_NONCE")
assert json.loads(ok(cmd(one),True))["outcome"]=="LAB_OBSERVED_UNVERIFIED"
denied(cmd(one));mark(21)
assert call()["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(22)
assert call(body="b"*64)["outcome"]=="LAB_BODY_VARIANT_QUARANTINED"
mark(23)
r=call(kind="read")
assert r["outcome"]=="LAB_KIND_CONFLICT_QUARANTINED"
mark(24)
assert ok("select count(*) from prumo_private.meta_status_conflitos_fixture_s0 where event_ref='WA51_EVT'")=="1"
mark(25)
before=ok("select count(*) from prumo_private.meta_status_forense_fixture_s0")
roll=fixture(event="WA51_ROLLBACK")
assert run("begin; "+cmd(roll)+"; rollback;",True).returncode==0
assert ok("select count(*) from prumo_private.meta_status_forense_fixture_s0")==before
mark(26)
race=fixture(event="WA51_RACE")
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(lambda _:run(cmd(race),True),range(2)))
assert sum(x.returncode==0 for x in results)==1 and sum(x.returncode!=0 for x in results)==1
mark(27)
assert ok("select prumo_private.meta_wa48_shadow_revoke_fixture_s0("+q(KEY)+")")=="LAB_REVOKED"
block(event="WA51_AFTER_REVOKE")
mark(28)
assert ok("select has_function_privilege("+q(CLIENT)+","+q("prumo_private.meta_wa51_verify_nonce_only_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)")+",'EXECUTE')")=="f"
mark(29)
assert ok("select has_table_privilege('prumo_s0_meta_wa50_writer_lab','prumo_private.meta_status_forense_fixture_s0','DELETE')")=="f"
mark(30)
helper="prumo_private.meta_wa51_verify_nonce_only_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)"
assert ok("select proowner::regrole::text from pg_proc where oid="+q(helper)+"::regprocedure")=="prumo_s0_meta_wa48_executor_lab"
mark(31)
assert ok("select has_function_privilege('prumo_s0_meta_wa50_writer_lab',"+q(helper)+",'EXECUTE')")=="t"
mark(32)
denied("select prumo_private.meta_wa51_verify_nonce_only_fixture_s0(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)")
mark(33)
assert ok("select count(*) from prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id="+q(KEY))=="0"
mark(34)
assert ok("select (position('WA48_KIND_CONFLICT' in pg_get_functiondef("+q("prumo_private.meta_wa48_shadow_append_fixture_s0(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,bigint,uuid,text)")+"::regprocedure))>0)::text")=="true"
mark(35)
fndef=ok("select pg_get_functiondef("+q(s)+"::regprocedure)")
assert fndef.index("'wa39:'")<fndef.index("meta_wa51_verify_nonce_only_fixture_s0")
mark(36)
print("WA51 36/36 PASS - forensic conflict parity and event-before-key lock PG17 ONLY",flush=True)
