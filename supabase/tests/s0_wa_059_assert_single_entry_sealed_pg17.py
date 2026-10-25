#!/usr/bin/env python3
"""WA55: one PG17-only entrypoint after sealing all legacy test-client doors."""
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

DSN=os.getenv("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(DSN)
if not (u.scheme=="postgresql" and u.hostname=="127.0.0.1" and u.port==5432
 and u.username=="postgres" and u.path=="/prumo_s0_test_ci"
 and not u.query and not u.fragment):
 raise SystemExit("WA55 PG17 disposable only")
for x in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER","PGSERVICE",
 "PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.getenv(x):raise SystemExit("WA55 libpq override "+x)
CLIENT="prumo_s0_meta_wa48_client_lab"
LOGIN="postgresql://"+CLIENT+"@127.0.0.1:5432/prumo_s0_test_ci"
PASSWORD=secrets.token_urlsafe(43)
KEY=str(uuid.uuid4())
SECRET=secrets.token_bytes(48)
APP="12346000002";WABA="22346000002";PHONE="32346000002"
CHANNEL="f7300000-0000-4000-8000-000000000002"
SHOP="f7200000-0000-4000-8000-000000000002"
INTENT=str(uuid.uuid4())
ATTEMPT="WA55_ATTEMPT"
CORR="WA55_CORR"
RECIPIENT="5581900000000"
WAMID="wamid.WA55.SINGLE"
FN="prumo_private.meta_wa55_single_entry_fixture_s0"
TEMPLATE="(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)"
LEGACY=[
 "meta_wa48_shadow_append_fixture_s0","meta_wa49_scoped_shadow_fixture_s0",
 "meta_wa50_restricted_forensic_fixture_s0","meta_wa51_parity_forensic_fixture_s0",
 "meta_wa52_locked_forensic_fixture_s0"]
WA40="prumo_private.meta_arquivar_handoff_assinado_fixture_s0"
def q(x):return "'"+str(x).replace("'","''")+"'"
def getenv(client=False):
 return {**os.environ,"PGPASSWORD":PASSWORD if client else os.environ.get("PGPASSWORD","postgres")}
def arguments(client=False):
 return ["psql","-X","-qAt","-v","ON_ERROR_STOP=1","-v","VERBOSITY=verbose",
         LOGIN if client else DSN]
def execute(sql,client=False,stdin=False,timeout=30):
 args=arguments(client)
 if not stdin:args+=["-c",sql]
 return subprocess.run(args,input=sql if stdin else None,env=getenv(client),
  capture_output=True,text=True,timeout=timeout)
def ok(sql,client=False):
 a=execute(sql,client)
 if a.returncode:raise AssertionError("WA55 SQL ERROR "+a.stderr[-650:])
 return a.stdout.strip()
def denied(sql,client=True):
 a=execute(sql,client)
 assert a.returncode!=0,("WA55 unexpectedly succeeded",sql,a.stdout)
 assert "42501" in a.stderr or "permission denied" in a.stderr,a.stderr[-400:]
def n(sql):return int(ok("select count(*) from "+sql))
def mark(i):print("WA55-"+str(i).zfill(2)+" PASS",flush=True)
def sign(event="WA55_BASE",body="a"*64,kind="delivered",nonce=None,issued=None,
         mac=None,app=APP,attempt=ATTEMPT,intent=INTENT):
 a=[KEY,app,WABA,PHONE,CHANNEL,intent,attempt,CORR,RECIPIENT,WAMID,
    event,kind,body,str(int(time.time()) if issued is None else issued),
    nonce or str(uuid.uuid4())]
 wire="|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY",*a]).encode()
 return a+[mac if mac is not None else hmac.new(SECRET,wire,hashlib.sha256).hexdigest()]
def sqlcall(fn,a):
 x=[q(v) for v in a];x[13]=str(int(a[13]))
 return "select "+fn+"("+",".join(x)+")"
def call(**kw):return json.loads(ok(sqlcall(FN,sign(**kw)),True))
def hold(sql,marker):
 p=subprocess.Popen(arguments(True),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
  stderr=subprocess.PIPE,env=getenv(True),text=True,bufsize=1)
 p.stdin.write("BEGIN;\n"+sql+";\nSELECT "+q(marker)+";\n")
 p.stdin.flush()
 lines=[]
 for _ in range(3):
  line=p.stdout.readline().strip()
  if line==marker:return p,lines
  lines.append(line)
 p.kill();p.wait(timeout=3)
 raise AssertionError("WA55 did not hold connection "+repr(lines))
def release(p):
 try:
  p.stdin.write("COMMIT;\n\\q\n");p.stdin.flush();p.stdin.close()
  p.wait(timeout=10)
  if p.returncode:raise AssertionError("WA55 held client failed "+p.stderr.read()[-400:])
 finally:
  if p.poll() is None:p.kill();p.wait(timeout=3)
def wait_cancel_lock():
 for _ in range(30):
  qn=n("pg_catalog.pg_stat_activity where usename='postgres' and"
   " datname='prumo_s0_test_ci' and wait_event_type='Lock' and"
   " query ilike '%update prumo_private.outbox_intencoes_s0%'")
  if qn:return True
  time.sleep(0.08)
 return False

assert execute("alter role "+CLIENT+" login password "+q(PASSWORD)+";",stdin=True).returncode==0
assert ok("select session_user||':'||current_user",True)==CLIENT+":"+CLIENT
mark(1)
assert ok("select proowner::regrole::text from pg_proc where oid="+q(FN+TEMPLATE)+"::regprocedure")=="prumo_s0_meta_wa50_writer_lab"
mark(2)
assert ok("select prosecdef::text from pg_proc where oid="+q(FN+TEMPLATE)+"::regprocedure")=="true"
mark(3)
for role in ("prumo_s0_meta_wa50_writer_lab","prumo_s0_meta_wa52_outbox_guard_lab"):
 assert ok("select rolcanlogin::text||':'||rolsuper::text||':'||rolbypassrls::text from pg_roles where rolname="+q(role))=="false:false:false"
mark(4)
assert ok("select has_function_privilege("+q(CLIENT)+","+q(FN+TEMPLATE)+",'EXECUTE')")=="t"
mark(5)
for role in ("service_role","anon","authenticated","prumo_s0_meta_ingress_lab"):
 assert ok("select has_function_privilege("+q(role)+","+q(FN+TEMPLATE)+",'EXECUTE')")=="f"
mark(6)
for item in LEGACY:
 assert ok("select has_function_privilege("+q(CLIENT)+","+q("prumo_private."+item+TEMPLATE)+",'EXECUTE')")=="f",item
mark(7)
assert ok("select has_function_privilege('prumo_s0_meta_ingress_lab',"+q(WA40+TEMPLATE)+",'EXECUTE')")=="f"
mark(8)
for item in LEGACY:
 denied(sqlcall("prumo_private."+item,sign(event="WA55_DENY_"+item[:8])))
mark(9)
denied("set role prumo_s0_meta_wa50_writer_lab")
mark(10)
denied("select * from prumo_private.meta_status_forense_fixture_s0")
mark(11)
denied("select "+FN+"(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)",False)
mark(12)
for tab in ("meta_vinculos_tentativa_fixture_s0","outbox_intencoes_s0"):
 assert ok("select has_table_privilege('prumo_s0_meta_wa50_writer_lab',"+q("prumo_private."+tab)+",'UPDATE')")=="f"
mark(13)
assert ok("select has_schema_privilege('prumo_s0_meta_wa50_writer_lab','prumo_private','CREATE')")=="f"
mark(14)
assert ok("select has_function_privilege('prumo_s0_meta_wa50_writer_lab',"+
 q("prumo_private.meta_wa52_locked_forensic_fixture_s0"+TEMPLATE)+",'EXECUTE')")=="t"
mark(15)
assert ok("select has_function_privilege("+q(CLIENT)+","+
 q("prumo_private.meta_wa52_locked_forensic_fixture_s0"+TEMPLATE)+",'EXECUTE')")=="f"
mark(16)

ok("insert into prumo_private.outbox_intencoes_s0("
 "id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica)"
 " values("+q(INTENT)+","+q(SHOP)+","+q(CHANNEL)+",'C03','WA55_SINGLE_INTENT',1)")
linked=json.loads(ok("select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0("+
 ",".join(map(q,[APP,WABA,PHONE,CHANNEL,INTENT,ATTEMPT,CORR,RECIPIENT,WAMID]))+",200)"))
assert linked["outcome"]=="LAB_BOUND"
mark(17)
ok("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0("
 "key_id,app,secret,active,valid_from,valid_until) values("+
 q(KEY)+","+q(APP)+",decode("+q(SECRET.hex())+",'hex'),true,"
 "clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')")
mark(18)
nonce0=n("prumo_private.meta_wa48_shadow_nonces_fixture_s0")
denied(sqlcall(FN,sign(event="WA55_SCOPE_DENIED",app="12346000001")))
assert n("prumo_private.meta_wa48_shadow_nonces_fixture_s0")==nonce0
mark(19)
denied(sqlcall(FN,sign(event="WA55_MAC_BAD",mac="0"*64)))
mark(20)
r=call()
assert r["outcome"]=="LAB_OBSERVED_UNVERIFIED" and r["entrypoint"]=="WA55_PG17_SINGLE_LAB_ONLY"
mark(21)
assert n("prumo_private.meta_status_forense_fixture_s0 where event_ref='WA55_BASE'")==1
mark(22)
for key in ("service_authenticated","runtime_principal_authenticated","ack_allowed",
 "send_authorized","retry_external","production_authorized","delivery_confirmed",
 "case_transition_authorized","definitive_failure_count_increment"):
 assert r[key] is False,(key,r)
assert r["legacy_paths_directly_executable"] is False
mark(23)
assert call()["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(24)
assert call(body="b"*64)["outcome"]=="LAB_BODY_VARIANT_QUARANTINED"
mark(25)
assert call(kind="read")["outcome"]=="LAB_KIND_CONFLICT_QUARANTINED"
assert n("prumo_private.meta_status_conflitos_fixture_s0 where event_ref='WA55_BASE'")==1
mark(26)
repeat=sign(event="WA55_NONCE")
assert json.loads(ok(sqlcall(FN,repeat),True))["outcome"]=="LAB_OBSERVED_UNVERIFIED"
denied(sqlcall(FN,repeat))
mark(27)
prior=n("prumo_private.meta_status_forense_fixture_s0")
rolled=sign(event="WA55_ROLL")
assert execute("begin; "+sqlcall(FN,rolled)+"; rollback;",True).returncode==0
assert n("prumo_private.meta_status_forense_fixture_s0")==prior
mark(28)
assert n("prumo_private.meta_wa48_shadow_nonces_fixture_s0 where nonce="+q(rolled[14]))==0
mark(29)

p,lines=hold(sqlcall(FN,sign(event="WA55_STATUS_FIRST")),"WA55_LOCK_HELD")
assert len(lines)==1 and json.loads(lines[0])["outcome"]=="LAB_OBSERVED_UNVERIFIED",lines
try:
 with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
  job=pool.submit(execute,"update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' where id="+q(INTENT))
  assert wait_cancel_lock(),"WA55 canonical row lock failed to block cancellation"
  mark(30)
  release(p)
  outcome=job.result(timeout=10)
  assert outcome.returncode==0,outcome.stderr[-400:]
finally:
 if p.poll() is None:
  try:release(p)
  except Exception:pass
mark(31)
assert ok("select estado from prumo_private.outbox_intencoes_s0 where id="+q(INTENT))=="CANCELADA"
assert call(event="WA55_AFTER_CANCEL")["outcome"]=="LAB_LATE_UNVERIFIED"
mark(32)
assert ok("select prumo_private.meta_wa48_shadow_revoke_fixture_s0("+q(KEY)+")")=="LAB_REVOKED"
mark(33)
denied(sqlcall(FN,sign(event="WA55_KEY_REVOKED")))
mark(34)
assert n("prumo_private.meta_wa48_shadow_receipts_fixture_s0 where key_id="+q(KEY))==0
mark(35)
assert n("prumo_private.meta_status_forense_fixture_s0 where "
 "ack_allowed or send_authorized or retry_external or production_authorized "
 "or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment")==0
mark(36)
print("WA55 36/36 PASS - single sealed client entrypoint in PG17 only",flush=True)
