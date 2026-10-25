#!/usr/bin/env python3
"""WA54: WA40 privileged PG17 path vs restricted WA50/52; real event locks."""
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
 raise SystemExit("WA54: PG17 disposable CI database only")
for k in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER","PGSERVICE","PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT","PGSSLKEY","PGSSLROOTCERT"):
 if os.getenv(k):raise SystemExit("WA54 libpq override denied")
CLIENT="prumo_s0_meta_wa48_client_lab"
LOGIN="postgresql://"+CLIENT+"@127.0.0.1:5432/prumo_s0_test_ci"
PASS=secrets.token_urlsafe(43)
FN40="prumo_private.meta_arquivar_handoff_assinado_fixture_s0"
FN50="prumo_private.meta_wa50_restricted_forensic_fixture_s0"
FN52="prumo_private.meta_wa52_locked_forensic_fixture_s0"
SIG="(uuid,text,text,text,uuid,uuid,text,text,text,text,text,text,text,bigint,uuid,text)"
S={
 "B":("12346000002","22346000002","32346000002",
 "f7300000-0000-4000-8000-000000000002","f7400000-0000-4000-8000-000000000002","ATTEMPT_B","CORR_B"),
 "A":("12346000001","22346000001","32346000001",
 "f7300000-0000-4000-8000-000000000001","f7400000-0000-4000-8000-000000000001","ATTEMPT_A","CORR_A")
}
KA={x:str(uuid.uuid4()) for x in S}
KB={x:str(uuid.uuid4()) for x in S}
SEC_A={x:secrets.token_bytes(48) for x in S}
SEC_B={x:secrets.token_bytes(48) for x in S}
def q(v):return "'"+str(v).replace("'","''")+"'"
def cli_env(client=False):return {**os.environ,"PGPASSWORD":PASS if client else os.environ.get("PGPASSWORD","postgres")}
def cli_args(client=False):return ["psql","-X","-qAt","-v","ON_ERROR_STOP=1","-v","VERBOSITY=verbose",LOGIN if client else DSN]
def run(sql,client=False,timeout=30,stdin=False):
 args=cli_args(client)
 if not stdin:args+=["-c",sql]
 return subprocess.run(args,input=sql if stdin else None,env=cli_env(client),text=True,capture_output=True,timeout=timeout)
def ok(sql,client=False):
 p=run(sql,client)
 if p.returncode:raise AssertionError("WA54 SQL ERROR "+p.stderr[-600:])
 return p.stdout.strip()
def reject(sql,client=False):
 p=run(sql,client)
 assert p.returncode!=0,"WA54 unexpected access"
 assert "42501" in p.stderr or "permission denied" in p.stderr,p.stderr[-500:]
def count(where):return int(ok("select count(*) from "+where))
def mark(i):print("WA54-"+str(i).zfill(2)+" PASS",flush=True)
def bundle(letter="B",event="WA54_EVT",kind="delivered",body="a"*64,
  nonce=None,issued=None,mac=None,bad_scope=False,who="legacy"):
 t=S[letter]
 key=(KA if who=="legacy" else KB)[letter]
 secret=(SEC_A if who=="legacy" else SEC_B)[letter]
 vals=[key,*t[:5],t[5],t[6],"5581900000000","wamid.WA40.SHARED",
       event,kind,body,str(int(time.time()) if issued is None else issued),
       nonce or str(uuid.uuid4())]
 if bad_scope:vals[2]="22346000001" if letter=="B" else "22346000002"
 data="|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY",*vals]).encode()
 return vals+[mac if mac is not None else hmac.new(secret,data,hashlib.sha256).hexdigest()]
def call_sql(fn,values):
 z=[q(v) for v in values];z[13]=str(int(values[13]))
 statement="select "+fn+"("+",".join(z)+")"
 return "SET ROLE prumo_s0_meta_ingress_lab; "+statement if fn==FN40 else statement
def invoke(fn=FN40,letter="B",**kw):
 return json.loads(ok(call_sql(fn,bundle(letter=letter,who="legacy" if fn==FN40 else "restricted",**kw)),fn!=FN40))
def sess(statement,marker,client=False):
 p=subprocess.Popen(cli_args(client),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
   env=cli_env(client),text=True,bufsize=1)
 p.stdin.write("BEGIN;\n"+statement+";\nSELECT "+q(marker)+";\n")
 p.stdin.flush()
 rows=[]
 for _ in range(4):
  line=p.stdout.readline().strip()
  if line==marker:return p,rows
  rows.append(line)
 p.kill();p.wait(timeout=4)
 raise AssertionError("WA54 session failed "+repr(rows))
def close(p):
 try:
  p.stdin.write("COMMIT;\n\\q\n");p.stdin.flush();p.stdin.close();p.wait(timeout=11)
  if p.returncode:raise AssertionError("WA54 transaction failed "+p.stderr.read()[-600:])
 finally:
  if p.poll() is None:p.kill();p.wait(timeout=4)
def wait_for(role,needle):
 for _ in range(40):
  if count("pg_catalog.pg_stat_activity where datname='prumo_s0_test_ci' and usename="+q(role)+
   " and wait_event_type='Lock' and query ilike "+q("%"+needle+"%")):return True
  time.sleep(0.06)
 return False
def race(first,second,label):
 event="WA54_"+label
 a=call_sql(first,bundle(event=event,who="legacy" if first==FN40 else "restricted"))
 p,rows=sess(a,"WA54_HOLD_"+label,first!=FN40)
 assert len(rows)==1,rows
 first_out=json.loads(rows[0])
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
   second_sql=call_sql(second,bundle(event=event,who="legacy" if second==FN40 else "restricted"))
   future=executor.submit(run,second_sql,second!=FN40)
   who=CLIENT if second!=FN40 else "postgres"
   assert wait_for(who,second.split(".")[-1]),"WA54 missing real lock wait: "+label
   close(p)
   result=future.result(timeout=14)
   assert result.returncode==0,result.stderr[-700:]
   last=json.loads(result.stdout.strip())
   return first_out,last
 finally:
  if p.poll() is None:
   try:close(p)
   except Exception:pass

assert run("alter role "+CLIENT+" login password "+q(PASS)+";",stdin=True).returncode==0
mark(1)
assert ok("select session_user||':'||current_user",True)==CLIENT+":"+CLIENT
mark(2)
assert ok("select proowner::regrole::text from pg_proc where oid="+q(FN40+SIG)+"::regprocedure")=="postgres"
mark(3)
assert ok("select prosecdef::text from pg_proc where oid="+q(FN40+SIG)+"::regprocedure")=="true"
mark(4)
code=ok("select pg_get_functiondef("+q(FN40+SIG)+"::regprocedure)")
assert code.index("for share of a,m,b,o")<code.index("hashtextextended('wa39:'")<code.index("meta_verificar_handoff_fixture_s0(")
mark(5)
archive=ok("select pg_get_functiondef('prumo_private.archivar_status_meta_tecnico_fixture_s0(text,text,text,uuid,uuid,text,text,text,text,text,text,text)'::regprocedure)")
assert "for share of a,m,b,o" in archive and "hashtextextended('wa39:'" in archive
mark(6)
assert ok("select rolcanlogin::text||':'||rolsuper::text||':'||rolbypassrls::text from pg_roles where rolname='prumo_s0_meta_ingress_lab'")=="false:false:false"
mark(7)
assert ok("select has_function_privilege('prumo_s0_meta_ingress_lab',"+q(FN40+SIG)+",'EXECUTE')")=="t"
mark(8)
assert ok("select has_function_privilege("+q(CLIENT)+","+q(FN40+SIG)+",'EXECUTE')")=="f"
mark(9)
assert ok("select has_function_privilege('service_role',"+q(FN40+SIG)+",'EXECUTE')")=="f"
mark(10)
reject("select "+FN40+"(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null)")
mark(11)
reject("set role prumo_s0_meta_ingress_lab",True)
mark(12)
for letter in S:
 ok("insert into prumo_private.meta_servico_chaves_fixture_s0("
  "chave_id,app_technical_ref,segredo,valido_desde,valido_ate,ativo) values("+
  q(KA[letter])+","+q(S[letter][0])+",decode("+q(SEC_A[letter].hex())+
  ",'hex'),clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '1 hour',true)")
 ok("insert into prumo_private.meta_wa48_shadow_keys_fixture_s0("
  "key_id,app,secret,active,valid_from,valid_until) values("+
  q(KB[letter])+","+q(S[letter][0])+",decode("+q(SEC_B[letter].hex())+
  ",'hex'),true,clock_timestamp()-interval '2 minutes',clock_timestamp()+interval '1 hour')")
mark(13)
fresh=invoke(event="WA54_BASELINE")
assert fresh["outcome"]=="LAB_OBSERVED_UNVERIFIED"
mark(14)
for flag in ("ack_allowed","send_authorized","retry_external","production_authorized",
 "delivery_confirmed","case_transition_authorized","definitive_failure_count_increment",
 "service_authenticated","s0_production_authorized"):
 assert fresh[flag] is False
mark(15)
assert invoke(event="WA54_BASELINE")["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(16)
assert invoke(event="WA54_BASELINE",body="b"*64)["outcome"]=="LAB_BODY_VARIANT_QUARANTINED"
mark(17)
assert invoke(event="WA54_BASELINE",kind="read")["outcome"]=="LAB_KIND_CONFLICT_QUARANTINED"
mark(18)
assert count("prumo_private.meta_status_conflitos_fixture_s0 where event_ref='WA54_BASELINE'")==1
mark(19)
bad=bundle(event="WA54_INVALID",mac="0"*64)
reject(call_sql(FN40,bad))
mark(20)
before=count("prumo_private.meta_servico_nonces_fixture_s0")
reject(call_sql(FN40,bundle(event="WA54_SCOPE_DENIED",bad_scope=True)))
assert count("prumo_private.meta_servico_nonces_fixture_s0")==before
mark(21)
a,b=race(FN40,FN52,"LEGACY_THEN_LOCKED")
assert a["outcome"]=="LAB_OBSERVED_UNVERIFIED" and b["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(22)
assert count("prumo_private.meta_status_forense_fixture_s0 where event_ref='WA54_LEGACY_THEN_LOCKED'")==1
mark(23)
a,b=race(FN52,FN40,"LOCKED_THEN_LEGACY")
assert a["outcome"]=="LAB_OBSERVED_UNVERIFIED" and b["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(24)
assert count("prumo_private.meta_status_forense_fixture_s0 where event_ref='WA54_LOCKED_THEN_LEGACY'")==1
mark(25)
a,b=race(FN40,FN50,"LEGACY_THEN_RESTRICTED")
assert a["outcome"]=="LAB_OBSERVED_UNVERIFIED" and b["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(26)
a,b=race(FN50,FN40,"RESTRICTED_THEN_LEGACY")
assert a["outcome"]=="LAB_OBSERVED_UNVERIFIED" and b["outcome"]=="LAB_EXACT_BODY_REPLAY"
mark(27)
# Different shops never contend on the scoped WA39 event lock.
p,rows=sess(call_sql(FN40,bundle(event="WA54_MULTI_SHOP")),"WA54_MULTI_HOLD")
assert len(rows)==1
try:
 a=run(call_sql(FN52,bundle(letter="A",event="WA54_MULTI_SHOP",who="restricted")),True,timeout=8)
 assert a.returncode==0,a.stderr[-500:]
 state=ok("select estado from prumo_private.outbox_intencoes_s0 where id="+q(S["A"][4]))
 expected="LAB_LATE_UNVERIFIED" if state=="CANCELADA" else "LAB_OBSERVED_UNVERIFIED"
 assert json.loads(a.stdout.strip())["outcome"]==expected
 mark(28)
finally:close(p)
assert count("prumo_private.meta_status_forense_fixture_s0 where event_ref='WA54_MULTI_SHOP'")==2
mark(29)
assert ok("select prumo_private.meta_revogar_chave_fixture_s0("+q(KA["B"])+")")=="LAB_REVOKED"
mark(30)
reject(call_sql(FN40,bundle(event="WA54_AFTER_REVOKE")))
mark(31)
assert count("prumo_private.meta_status_forense_fixture_s0 where ack_allowed or send_authorized or retry_external or production_authorized or delivery_confirmed or case_transition_authorized or definitive_failure_count_increment")==0
mark(32)
print("WA54 32/32 PASS - WA40 S0 scope/event before key and cross-route PG17",flush=True)
