#!/usr/bin/env python3
"""WA53 PG17: repaired WA50 lock order with WA49/51/52 cross-route races."""
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
url=urlsplit(DSN)
if (url.scheme!="postgresql" or url.hostname!="127.0.0.1" or
 url.port!=5432 or url.username!="postgres" or
 url.path!="/prumo_s0_test_ci" or url.query or url.fragment):
 raise SystemExit("WA53: disposable PostgreSQL 17 only")
for k in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER","PGSERVICE",
 "PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.environ.get(k):raise SystemExit("WA53 unexpected libpq env override")

CLIENT="prumo_s0_meta_wa48_client_lab"
LOGIN="postgresql://"+CLIENT+"@127.0.0.1:5432/prumo_s0_test_ci"
PASSWORD=secrets.token_urlsafe(43)
SIGNATURE="(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)"
FN50="prumo_private.meta_wa50_restricted_forensic_fixture_s0"
FN49="prumo_private.meta_wa49_scoped_shadow_fixture_s0"
FN51="prumo_private.meta_wa51_parity_forensic_fixture_s0"
FN52="prumo_private.meta_wa52_locked_forensic_fixture_s0"
SCOPES={
"B":dict(app="12346000002",waba="22346000002",phone="32346000002",
 channel="f7300000-0000-4000-8000-000000000002",
 intent="f7400000-0000-4000-8000-000000000002",
 attempt="ATTEMPT_B",corr="CORR_B"),
"A":dict(app="12346000001",waba="22346000001",phone="32346000001",
 channel="f7300000-0000-4000-8000-000000000001",
 intent="f7400000-0000-4000-8000-000000000001",
 attempt="ATTEMPT_A",corr="CORR_A")
}
KEYS={letter:str(uuid.uuid4()) for letter in SCOPES}
SECRETS={letter:secrets.token_bytes(48) for letter in SCOPES}
RECIPIENT="5581900000000"
WAMID="wamid.WA40.SHARED"

def q(s):return "'"+str(s).replace("'","''")+"'"
def cmdargs(client=False):
 return ["psql","-X","-qAt","-v","ON_ERROR_STOP=1","-v","VERBOSITY=verbose",
 LOGIN if client else DSN]
def env(client=False):
 return {**os.environ,"PGPASSWORD":PASSWORD if client else os.environ.get("PGPASSWORD","postgres")}
def execute(sql,client=False,stdin=False,timeout=30):
 args=cmdargs(client)
 if not stdin:args+=["-c",sql]
 return subprocess.run(args,input=sql if stdin else None,env=env(client),
  text=True,capture_output=True,timeout=timeout)
def ok(sql,client=False):
 r=execute(sql,client)
 if r.returncode:raise AssertionError("WA53 SQL failure "+r.stderr[-700:])
 return r.stdout.strip()
def fail(sql,client=True):
 r=execute(sql,client)
 assert r.returncode!=0,"WA53 unexpectedly accepted"
 assert "42501" in r.stderr or "permission denied" in r.stderr,r.stderr[-400:]
def count(where):return int(ok("select count(*) from "+where))
def mark(n):print("WA53-"+str(n).zfill(2)+" PASS",flush=True)

def wire(letter="B",event="WA53_EVENT",kind="delivered",body="a"*64,
         nonce=None,issued=None,mac=None,scope=None):
 v=SCOPES[letter].copy()
 if scope:v.update(scope)
 t=[KEYS[letter],v["app"],v["waba"],v["phone"],v["channel"],
    v["intent"],v["attempt"],v["corr"],RECIPIENT,WAMID,event,
    kind,body,str(int(time.time()) if issued is None else issued),
    nonce or str(uuid.uuid4())]
 payload="|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY",*t]).encode()
 return t+[hmac.new(SECRETS[letter],payload,hashlib.sha256).hexdigest() if mac is None else mac]
def sqlcall(fn,fields):
 s=[q(v) for v in fields];s[13]=str(int(fields[13]))
 return "select "+fn+"("+",".join(s)+")"
def invoke(fn=FN50,**kw):return json.loads(ok(sqlcall(fn,wire(**kw)),True))
def hold(sql,marker):
 p=subprocess.Popen(cmdargs(True),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
  stderr=subprocess.PIPE,env=env(True),text=True,bufsize=1)
 p.stdin.write("BEGIN;\n"+sql+";\nSELECT "+q(marker)+";\n")
 p.stdin.flush()
 seen=[]
 for _ in range(4):
  line=p.stdout.readline().strip()
  if line==marker:return p,seen
  seen.append(line)
 p.kill();p.wait(timeout=4)
 raise AssertionError("held session not ready "+repr(seen))
def release(p):
 try:
  p.stdin.write("COMMIT;\n\\q\n");p.stdin.flush();p.stdin.close()
  p.wait(timeout=12)
  if p.returncode:raise AssertionError("held client error "+p.stderr.read()[-350:])
 finally:
  if p.poll() is None:p.kill();p.wait(timeout=4)
def wait_blocked(function):
 for _ in range(30):
  waiting=count("pg_catalog.pg_stat_activity where datname='prumo_s0_test_ci'"+
  " and usename="+q(CLIENT)+" and wait_event_type='Lock'"+
  " and query ilike "+q("%"+function+"%"))
  if waiting:return True
  time.sleep(0.09)
 return False
def race(first,second,tag,first_letter="B",second_letter="B",release_after=True):
 ev="WA53_"+tag
 p,lines=hold(sqlcall(first,wire(letter=first_letter,event=ev)),"WA53_HELD_"+tag)
 assert len(lines)==1,("no first result",lines)
 first_out=json.loads(lines[0])
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
   job=pool.submit(execute,sqlcall(second,wire(letter=second_letter,event=ev)),True)
   assert wait_blocked(second.split(".")[-1]),"Second route did not wait at "+tag
   release(p)
   response=job.result(timeout=16)
   assert response.returncode==0,response.stderr[-550:]
   result=json.loads(response.stdout.strip())
   return first_out,result
 finally:
  if p.poll() is None:
   try:release(p)
   except Exception:pass

assert execute("alter role "+CLIENT+" login password "+q(PASSWORD)+";",stdin=True).returncode==0
mark(1)
assert ok("select session_user||':'||current_user",True)==CLIENT+":"+CLIENT
mark(2)
for letter in SCOPES:
 ok("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0("
  "key_id,app,secret,active,valid_from,valid_until) values("+
  q(KEYS[letter])+","+q(SCOPES[letter]["app"])+
  ",decode("+q(SECRETS[letter].hex())+",'hex'),true,"
  "clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '2 hours')")
mark(3)
assert ok("select proowner::regrole::text from pg_proc where oid="+q(FN50+SIGNATURE)+"::regprocedure")=="prumo_s0_meta_wa50_writer_lab"
mark(4)
fdef=ok("select pg_get_functiondef("+q(FN50+SIGNATURE)+"::regprocedure)")
assert fdef.index("WA50_SCOPE_DENIED")<fdef.index("hashtextextended('wa39:'")<fdef.index("meta_wa48_shadow_append_fixture_s0")
mark(5)
assert ok("select prosecdef::text from pg_proc where oid="+q(FN50+SIGNATURE)+"::regprocedure")=="true"
mark(6)
assert ok("select has_function_privilege("+q(CLIENT)+","+q(FN50+SIGNATURE)+",'EXECUTE')")=="t"
mark(7)
assert ok("select has_function_privilege('service_role',"+q(FN50+SIGNATURE)+",'EXECUTE')")=="f"
mark(8)
for t in ("outbox_intencoes_s0","meta_vinculos_tentativa_fixture_s0",
 "meta_status_forense_fixture_s0"):
 assert ok("select has_table_privilege('prumo_s0_meta_wa50_writer_lab',"+
  q("prumo_private."+t)+",'UPDATE')")=="f"
mark(9)
assert ok("select has_schema_privilege('prumo_s0_meta_wa50_writer_lab','prumo_private','CREATE')")=="f"
mark(10)
fail("set role prumo_s0_meta_wa50_writer_lab")
mark(11)
fail("select * from prumo_private.meta_status_forense_fixture_s0")
mark(12)
nonce_start=count("prumo_private.meta_wa48_shadow_nonces_fixture_s0")
bad=wire(event="WA53_SCOPE_DENY",scope={"waba":"22346000001"})
fail(sqlcall(FN50,bad))
assert count("prumo_private.meta_wa48_shadow_nonces_fixture_s0")==nonce_start
mark(13)
fail(sqlcall(FN50,wire(event="WA53_MAC",mac="0"*64)))
mark(14)
r=invoke(event="WA53_BASELINE")
assert r["outcome"]=="LAB_OBSERVED_UNVERIFIED"
mark(15)
assert invoke(event="WA53_BASELINE")["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(16)
assert invoke(event="WA53_BASELINE",body="b"*64)["outcome"]=="LAB_BODY_VARIANT_QUARANTINED"
mark(17)
fail(sqlcall(FN50,wire(event="WA53_BASELINE",kind="read")))
mark(18)
for flag in ("service_authenticated","ack_allowed","send_authorized",
 "retry_external","production_authorized","delivery_confirmed",
 "case_transition_authorized","definitive_failure_count_increment"):
 assert r[flag] is False
mark(19)

# Two genuine PG17 transactions on the same S0 binding and same event:
# WA50 must acquire event lock before its WA48 key/nonce lock.
one,two=race(FN50,FN49,"WA50_TO_WA49")
assert one["outcome"]=="LAB_OBSERVED_UNVERIFIED" and two["outcome"]=="LAB_EXACT_REPLAY"
mark(20)
assert two["authoritative_s0_written"] is False
mark(21)
one,two=race(FN50,FN51,"WA50_TO_WA51")
assert one["outcome"]=="LAB_OBSERVED_UNVERIFIED" and two["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(22)
assert count("prumo_private.meta_status_forense_fixture_s0 where event_ref='WA53_WA50_TO_WA51'")==1
mark(23)
one,two=race(FN50,FN52,"WA50_TO_WA52")
assert one["outcome"]=="LAB_OBSERVED_UNVERIFIED" and two["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(24)
assert count("prumo_private.meta_status_forense_fixture_s0 where event_ref='WA53_WA50_TO_WA52'")==1
mark(25)
one,two=race(FN51,FN50,"WA51_TO_WA50")
assert one["outcome"]=="LAB_OBSERVED_UNVERIFIED" and two["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(26)
assert count("prumo_private.meta_status_forense_fixture_s0 where event_ref='WA53_WA51_TO_WA50'")==1
mark(27)

# Same event_ref but distinct bindings: hold B transaction and prove shop A
# can append without waiting on B's event lock.
p,lines=hold(sqlcall(FN50,wire(event="WA53_SAME_EVENT_MULTI_SHOP")),"WA53_MULTISHOP_HELD")
assert json.loads(lines[0])["outcome"]=="LAB_OBSERVED_UNVERIFIED"
try:
 cross=execute(sqlcall(FN50,wire(letter="A",event="WA53_SAME_EVENT_MULTI_SHOP")),True,timeout=7)
 assert cross.returncode==0,cross.stderr[-650:]
 assert json.loads(cross.stdout.strip())["outcome"]=="LAB_OBSERVED_UNVERIFIED"
 mark(28)
finally:release(p)
assert count("prumo_private.meta_status_forense_fixture_s0 where event_ref='WA53_SAME_EVENT_MULTI_SHOP'")==2
mark(29)
assert ok("select prumo_private.meta_wa48_shadow_revoke_fixture_s0("+q(KEYS["B"])+")")=="LAB_REVOKED"
mark(30)
fail(sqlcall(FN50,wire(event="WA53_REVOKED")))
mark(31)
assert ok("select has_table_privilege('prumo_s0_meta_wa50_writer_lab','prumo_private.meta_status_forense_fixture_s0','DELETE')")=="f"
mark(32)
print("WA53 32/32 PASS - fixed event-before-key and cross-route PG17 races",flush=True)
