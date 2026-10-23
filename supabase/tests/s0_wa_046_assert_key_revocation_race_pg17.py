#!/usr/bin/env python3
"""WA42: a real PG17 blocking interleaving between key-revoke and signed status.
Only local disposable PostgreSQL, fake keys and fake Meta IDs; no service LOGIN.
"""
import hashlib
import hmac
import os
import subprocess
import time
import uuid
from urllib.parse import urlsplit

url=os.environ.get("PRUMO_TEST_DATABASE_URL","")
u=urlsplit(url)
if not (u.scheme=="postgresql" and u.hostname=="127.0.0.1" and
 u.port==5432 and u.username=="postgres" and u.path=="/prumo_s0_test_ci"
 and not u.query and not u.fragment):
 raise SystemExit("WA42 refuses any non-local PG17 DSN")
for name in ("PGHOST","PGHOSTADDR","PGPORT","PGDATABASE","PGUSER",
 "PGSERVICE","PGSERVICEFILE","PGOPTIONS","PGSSLMODE","PGSSLCERT",
 "PGSSLKEY","PGSSLROOTCERT"):
 if os.environ.get(name):raise SystemExit("WA42 refuses libpq override "+name)
rootenv={"PATH":os.getenv("PATH","/usr/bin:/bin"),"HOME":os.getenv("HOME","/tmp"),
 "LC_ALL":"C","PGCONNECT_TIMEOUT":"5"}
def spawn(sql,app):
 env={**rootenv,"PGAPPNAME":app}
 return subprocess.Popen(["psql","-X","-qAt","-v","ON_ERROR_STOP=1",
  "-v","VERBOSITY=verbose",url,"-c",sql],env=env,text=True,
  stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def run(sql,app="wa42_probe"):
 p=spawn(sql,app)
 out,err=p.communicate(timeout=15)
 return p.returncode,out.strip(),err
def query(sql):
 rc,out,err=run(sql)
 assert rc==0,(out,err[-500:])
 return out
def mark(n):print(f"WA42-R{n:02} PASS",flush=True)
key="f7500000-0000-4000-8000-000000000002"
assert query("SELECT ativo FROM prumo_private.meta_servico_chaves_fixture_s0 "
 "WHERE chave_id='"+key+"'")=="t"
mark(1)
lock="pg_catalog.hashtextextended('wa42-meta-key:"+key+"',42)"
# The holder uses a separate PG17 connection; an observer confirms lock
# ownership BEFORE the admin revocation is allowed to race against it.
holder=spawn("BEGIN; SELECT pg_catalog.pg_advisory_xact_lock("+lock+"); "
 "SELECT pg_catalog.pg_sleep(4); COMMIT;","wa42_lock_holder")
try:
 acquired=False
 for _ in range(45):
  if holder.poll() is not None:break
  if query("SELECT pg_catalog.pg_try_advisory_xact_lock("+lock+")")=="f":
   acquired=True;break
  time.sleep(0.04)
 assert acquired,"WA42: holder did not acquire transaction lock"
 mark(2)
 revoker=spawn("SELECT prumo_private.meta_revogar_chave_fixture_s0('"+key+"');",
               "wa42_revoker")
 try:
  blocked=False
  for _ in range(60):
   if revoker.poll() is not None:break
   count=query("SELECT count(*) FROM pg_catalog.pg_stat_activity "
     "WHERE application_name='wa42_revoker' AND wait_event_type='Lock'")
   if count=="1":blocked=True;break
   time.sleep(0.04)
  assert blocked,"WA42: revoke did not block behind signer lock"
  mark(3)
  # A later signed callback queues AFTER revocation. Despite valid MAC,
  # its key is inactive when it obtains the same advisory lock.
  issued=int(time.time())
  nonce=str(uuid.uuid4())
  body="c"*64
  event="EVT_WA42_RACE"
  args=[key,"12346000002","22346000002","32346000002",
    "f7300000-0000-4000-8000-000000000002",
    "f7400000-0000-4000-8000-000000000002","ATTEMPT_B","CORR_B",
    "5581900000000","wamid.WA40.SHARED",event,"delivered",body,
    str(issued),nonce]
  material="|".join(["prumo-meta-handoff-lab-v1","FORENSIC_APPEND_ONLY"]+args)
  mac=hmac.new(b"T"*48,material.encode("utf-8"),hashlib.sha256).hexdigest()
  sql="SET ROLE prumo_s0_meta_ingress_lab; SELECT "+\
   "prumo_private.meta_arquivar_handoff_assinado_fixture_s0("+\
   ",".join("'"+x+"'" for x in args+[mac])+");"
  signed=spawn(sql,"wa42_signed_callback")
  try:
   rout,rerr=revoker.communicate(timeout=12)
   assert revoker.returncode==0 and "LAB_REVOKED" in rout,(rout,rerr[-300:])
   mark(4)
   sout,serr=signed.communicate(timeout=12)
   assert signed.returncode!=0 and "42501" in serr,(sout,serr[-500:])
   assert "META_HANDOFF_KEY_DENIED" in serr,serr[-500:]
   mark(5)
  finally:
   if signed.poll() is None:signed.kill()
 finally:
  if revoker.poll() is None:revoker.kill()
 hout,herr=holder.communicate(timeout=5)
 assert holder.returncode==0,(hout,herr[-300:])
 mark(6)
finally:
 if holder.poll() is None:holder.kill()
assert query("SELECT ativo FROM prumo_private.meta_servico_chaves_fixture_s0 "
 "WHERE chave_id='"+key+"'")=="f"
mark(7)
assert query("SELECT count(*) FROM prumo_private.meta_servico_nonces_fixture_s0 "
 "WHERE nonce='"+nonce+"'")=="0"
mark(8)
assert query("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 "
 "WHERE event_ref='EVT_WA42_RACE'")=="0"
mark(9)
rc,_,err=run("SET ROLE prumo_s0_meta_ingress_lab; "
 "SELECT prumo_private.meta_revogar_chave_fixture_s0('"+key+"')")
assert rc!=0 and "42501" in err,err[-400:]
mark(10)
assert query("SELECT count(*) FROM prumo_private.meta_status_forense_fixture_s0 "
 "WHERE send_authorized OR ack_allowed OR retry_external OR "
 "production_authorized OR delivery_confirmed OR "
 "case_transition_authorized OR definitive_failure_count_increment")=="0"
mark(11)
print("WA42-R: 11/11 physical key-revoke blocking proofs (PG17 only)",flush=True)
