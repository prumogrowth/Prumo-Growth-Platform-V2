#!/usr/bin/env python3
"""WA52: PG17 disposable, real S0 outbox FOR SHARE vs two cancellation orders."""
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
if (u.scheme!="postgresql" or u.hostname!="127.0.0.1" or u.port!=5432
 or u.username!="postgres" or u.path!="/prumo_s0_test_ci" or u.query or u.fragment):
 raise SystemExit("WA52 refuses non-disposable PG17")
for k in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER","PGSERVICE",
 "PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.environ.get(k):raise SystemExit("WA52 libpq override forbidden")
CLIENT="prumo_s0_meta_wa48_client_lab"
LOGIN="postgresql://"+CLIENT+"@127.0.0.1:5432/prumo_s0_test_ci"
PASSWORD=secrets.token_urlsafe(45)
KEY=str(uuid.uuid4())
SECRET=secrets.token_bytes(48)
APP="12346000002";WABA="22346000002";PHONE="32346000002"
SHOP="f7200000-0000-4000-8000-000000000002"
CHANNEL="f7300000-0000-4000-8000-000000000002"
RECIPIENT="5581900000000"
INTENT_A=str(uuid.uuid4())
INTENT_B=str(uuid.uuid4())
FN="prumo_private.meta_wa52_locked_forensic_fixture_s0"
def q(s):return "'"+str(s).replace("'","''")+"'"
def env(client=False):
 return {**os.environ,"PGPASSWORD":PASSWORD if client else os.environ.get("PGPASSWORD","postgres")}
def command_args(client=False):
 return ["psql","-X","-qAt","-v","ON_ERROR_STOP=1","-v","VERBOSITY=verbose",
         LOGIN if client else DSN]
def run(sql,client=False,stdin=False,timeout=22):
 a=command_args(client)
 if not stdin:a+=["-c",sql]
 return subprocess.run(a,input=sql if stdin else None,env=env(client),
                       text=True,capture_output=True,timeout=timeout)
def ok(sql,client=False):
 r=run(sql,client)
 if r.returncode:raise AssertionError("WA52 SQL ERROR: "+r.stderr[-800:])
 return r.stdout.strip()
def fail(sql,client=True):
 r=run(sql,client)
 assert r.returncode!=0,"unexpected authorization success"
 assert "42501" in r.stderr or "permission denied" in r.stderr,r.stderr[-500:]
def mark(n):print("WA52-"+str(n).zfill(2)+" PASS",flush=True)
def role_sql(role):
 return ok("select rolcanlogin::text||':'||rolsuper::text||':'||rolbypassrls::text from pg_roles where rolname="+q(role))
sig="(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)"
def payload(intent=INTENT_A,event="WA52_EVENT",kind="delivered",body="a"*64,
            app=APP,waba=WABA,phone=PHONE,channel=CHANNEL,recipient=RECIPIENT,
            nonce=None,issued=None,mac=None):
 a= intent==INTENT_A
 attempt="WA52_ATTEMPT_A" if a else "WA52_ATTEMPT_B"
 corr="WA52_CORR_A" if a else "WA52_CORR_B"
 wamid="wamid.WA52.A" if a else "wamid.WA52.B"
 args=[KEY,app,waba,phone,channel,intent,attempt,corr,recipient,wamid,
       event,kind,body,str(int(time.time()) if issued is None else issued),
       nonce or str(uuid.uuid4())]
 wire="|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY",*args]).encode()
 return args+[mac if mac is not None else hmac.new(SECRET,wire,hashlib.sha256).hexdigest()]
def sql_call(params):
 a=[q(v) for v in params];a[13]=str(int(params[13]))
 return "select "+FN+"("+",".join(a)+")"
def call(**k):return json.loads(ok(sql_call(payload(**k)),True))
def denied(**k):fail(sql_call(payload(**k)))
def count(sql):return int(ok("select count(*) from "+sql))
def hold(commands,marker,client=False):
 p=subprocess.Popen(command_args(client),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,env=env(client),text=True,bufsize=1)
 p.stdin.write("BEGIN;\n"+commands+"\nSELECT "+q(marker)+";\n")
 p.stdin.flush()
 got=[]
 for _ in range(3):
  line=p.stdout.readline().strip()
  if line==marker:return p,got
  got.append(line)
 raise AssertionError("WA52 held session did not signal: "+repr(got))
def release(p):
 try:
  p.stdin.write("COMMIT;\n\\q\n")
  p.stdin.flush()
  p.stdin.close()
  p.wait(timeout=9)
  if p.returncode:raise AssertionError("held session exit: "+p.stderr.read()[-500:])
 finally:
  if p.poll() is None:
   p.kill();p.wait(timeout=3)
def observed_wait(role,query_fragment):
 for _ in range(24):
  n=count("pg_catalog.pg_stat_activity where datname='prumo_s0_test_ci' "
   "and usename="+q(role)+" and wait_event_type='Lock' "
   "and query ilike "+q("%"+query_fragment+"%"))
  if n:return True
  time.sleep(0.08)
 return False

assert run("alter role "+CLIENT+" login password "+q(PASSWORD)+";",stdin=True).returncode==0
assert ok("select session_user||':'||current_user",True)==CLIENT+":"+CLIENT
mark(1)
assert role_sql("prumo_s0_meta_wa52_outbox_guard_lab")=="false:false:false"
mark(2)
assert role_sql("prumo_s0_meta_wa50_writer_lab")=="false:false:false"
mark(3)
assert ok("select proowner::regrole::text from pg_proc where oid="+q(FN+sig)+"::regprocedure")=="prumo_s0_meta_wa50_writer_lab"
mark(4)
assert ok("select proowner::regrole::text from pg_proc where oid='prumo_private.meta_wa52_lock_outbox_fixture_s0(uuid,uuid,uuid)'::regprocedure")=="prumo_s0_meta_wa52_outbox_guard_lab"
mark(5)
assert ok("select has_column_privilege('prumo_s0_meta_wa52_outbox_guard_lab','prumo_private.outbox_intencoes_s0','id','UPDATE')")=="t"
assert ok("select has_column_privilege('prumo_s0_meta_wa50_writer_lab','prumo_private.outbox_intencoes_s0','id','UPDATE')")=="f"
mark(6)
assert ok("select has_function_privilege("+q(CLIENT)+",'prumo_private.meta_wa52_lock_outbox_fixture_s0(uuid,uuid,uuid)','EXECUTE')")=="f"
mark(7)
fail("select prumo_private.meta_wa52_lock_outbox_fixture_s0(null,null,null)")
mark(8)
fail("set role prumo_s0_meta_wa52_outbox_guard_lab")
mark(9)
fail("select * from prumo_private.outbox_intencoes_s0")
mark(10)
fail("select "+FN+"(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)",False)
mark(11)
assert ok("select has_schema_privilege('prumo_s0_meta_wa52_outbox_guard_lab','prumo_private','CREATE')")=="f"
mark(12)
for intent,suffix in ((INTENT_A,"A"),(INTENT_B,"B")):
 ok("insert into prumo_private.outbox_intencoes_s0("
  "id,concessionaria_id,canal_id,contrato,chave_idempotencia,versao_estado_sintetica)"
  " values ("+q(intent)+","+q(SHOP)+","+q(CHANNEL)+",'C03',"+
  q("WA52_INTENT_"+suffix)+",1)")
 status=ok("select prumo_private.registrar_vinculo_meta_tecnico_fixture_s0("+
    ",".join(map(q,[APP,WABA,PHONE,CHANNEL,intent,
       "WA52_ATTEMPT_"+suffix,"WA52_CORR_"+suffix,RECIPIENT,
       "wamid.WA52."+suffix]))+",200)")
 assert json.loads(status)["outcome"]=="LAB_BOUND"
mark(13)
ok("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0("
 "key_id,app,secret,active,valid_from,valid_until) values("+
 q(KEY)+","+q(APP)+",decode("+q(SECRET.hex())+",'hex'),true,"
 "clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')")
a=call(event="WA52_BASELINE")
assert a["outcome"]=="LAB_OBSERVED_UNVERIFIED"
mark(14)
for flag in ("ack_allowed","send_authorized","retry_external","production_authorized",
 "delivery_confirmed","case_transition_authorized","definitive_failure_count_increment",
 "service_authenticated"):
 assert a[flag] is False
mark(15)
assert call(event="WA52_BASELINE")["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(16)
assert call(event="WA52_BASELINE",kind="read")["outcome"]=="LAB_KIND_CONFLICT_QUARANTINED"
mark(17)
assert count("prumo_private.meta_status_conflitos_fixture_s0 where event_ref='WA52_BASELINE'")==1
mark(18)
nonce_before=count("prumo_private.meta_wa48_shadow_nonces_fixture_s0")
denied(event="WA52_INVALID_SCOPE",app="12346000001")
assert count("prumo_private.meta_wa48_shadow_nonces_fixture_s0")==nonce_before
mark(19)
denied(event="WA52_BAD_HMAC",mac="0"*64)
mark(20)

# Status FIRST: row share lock is held by open client transaction;
# cancel UPDATE must wait until that transaction commits.
p,rows=hold(sql_call(payload(event="WA52_STATUS_FIRST"))+";","WA52_STATUS_HELD",client=True)
assert len(rows)==1 and json.loads(rows[0])["outcome"]=="LAB_OBSERVED_UNVERIFIED",rows
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
 f=pool.submit(run,"update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' where id="+q(INTENT_A))
 assert observed_wait("postgres","outbox_intencoes_s0"),"cancel did not wait on row lock"
 mark(21)
 release(p)
 assert f.result(timeout=12).returncode==0
mark(22)
assert ok("select estado from prumo_private.outbox_intencoes_s0 where id="+q(INTENT_A))=="CANCELADA"
mark(23)
assert call(event="WA52_AFTER_CANCEL_A")["outcome"]=="LAB_LATE_UNVERIFIED"
mark(24)

# Cancellation FIRST: hold actual row UPDATE in uncommitted transaction,
# then verify signed client waits and reads CANCELADA after COMMIT.
p,rows=hold("update prumo_private.outbox_intencoes_s0 set estado='CANCELADA' where id="+q(INTENT_B)+";","WA52_CANCEL_HELD")
assert rows==[],rows
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
 f=pool.submit(run,sql_call(payload(intent=INTENT_B,event="WA52_CANCEL_FIRST")),True)
 assert observed_wait(CLIENT,"meta_wa52_locked_forensic_fixture_s0"),"status did not wait on canceled outbox"
 mark(25)
 release(p)
 response=f.result(timeout=12)
 assert response.returncode==0,response.stderr[-600:]
 assert json.loads(response.stdout.strip())["outcome"]=="LAB_LATE_UNVERIFIED"
mark(26)
assert ok("select estado from prumo_private.outbox_intencoes_s0 where id="+q(INTENT_B))=="CANCELADA"
mark(27)
assert call(intent=INTENT_B,event="WA52_AFTER_CANCEL_B")["outcome"]=="LAB_LATE_UNVERIFIED"
mark(28)
print("WA52 28/28 PASS - outbox row-lock/cancellation concurrency PG17",flush=True)
